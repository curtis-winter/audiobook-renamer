from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import asyncio
import logging
import json
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from services import metadata_service, file_service, watch_service, api_service
from models import AudiobookFile, MetadataUpdate, Config, CombineFiles

config = Config.load()


def _on_watch_change():
    """Called by the file watcher whenever the watch folder changes; busts the file index."""
    file_service.invalidate_file_index()


def _on_new_file(path: str):
    """Called by the file watcher for newly-detected audio files."""
    logger.info(f"Watch detected new audio file: {path}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    watch_service.start_watching(
        config.watch_folder,
        callback=_on_new_file,
        on_change=_on_watch_change,
    )
    logger.info(f"Started watching: {config.watch_folder}")
    try:
        yield
    finally:
        watch_service.stop_watching()


app = FastAPI(title="Audiobook Renamer", lifespan=lifespan)

# Allow all origins for development, configure for production
allowed_origins_raw = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
allowed_origins = [o.strip() for o in allowed_origins_raw if o.strip() and o.strip() != "*"]

# CORS spec forbids allow_credentials=True with a wildcard origin. This app has no
# auth cookies, so default to no credentials unless the operator explicitly opts in.
allow_credentials_env = os.getenv("ALLOW_CREDENTIALS", "false").lower() == "true"
allow_credentials = allow_credentials_env and "*" not in allowed_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins or [],
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)
if "*" in allowed_origins_raw:
    logger.warning("ALLOWED_ORIGINS contains '*'; credentials are not permitted in that mode")

progress_queues = {}
combine_progress_queue = asyncio.Queue()

async def progress_generator(queue_id):
    queue = asyncio.Queue()
    progress_queues[queue_id] = queue
    try:
        while True:
            try:
                progress_data = await asyncio.wait_for(queue.get(), timeout=30)
                if progress_data.get('done'):
                    yield f"data: {json.dumps(progress_data)}\n\n"
                    break
                yield f"data: {json.dumps(progress_data)}\n\n"
            except asyncio.TimeoutError:
                yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
    finally:
        if queue_id in progress_queues:
            del progress_queues[queue_id]

@app.get("/api/progress/{task_id}")
async def get_progress(task_id: str):
    """SSE endpoint for real-time progress updates"""
    return StreamingResponse(
        progress_generator(task_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

@app.get("/api/progress-stream")
async def get_combine_progress():
    """SSE endpoint for combine progress only"""
    return StreamingResponse(
        progress_generator("combine"),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

@app.get("/api/config")
async def get_config():
    return {
        "watchFolder": config.watch_folder,
        "outputFolder": config.output_folder,
        "filenameTemplate": config.filename_template,
        "folderTemplate": config.folder_template,
    }

@app.post("/api/config")
async def update_config(cfg: Config):
    config.watch_folder = cfg.watch_folder
    config.output_folder = cfg.output_folder
    config.filename_template = cfg.filename_template
    config.folder_template = cfg.folder_template
    config.save()
    file_service.invalidate_file_index()
    if watch_service.is_watching():
        watch_service.start_watching(
            config.watch_folder,
            callback=_on_new_file,
            on_change=_on_watch_change,
        )
    return {
        "watchFolder": config.watch_folder,
        "outputFolder": config.output_folder,
        "filenameTemplate": config.filename_template,
        "folderTemplate": config.folder_template,
    }

@app.get("/api/files")
async def get_files():
    if not os.path.exists(config.watch_folder):
        return []
    return await file_service.get_audio_files(config.watch_folder)

@app.get("/api/files/{file_id}/metadata")
async def get_file_metadata(file_id: str):
    file_path = await file_service.get_file_path_by_id(file_id, config.watch_folder)
    if not file_path:
        raise HTTPException(status_code=404, detail="File not found")
    return metadata_service.read_metadata(file_path)

@app.post("/api/search")
async def search_metadata(q: str = "", search_type: str = "all"):
    if not q:
        return []
    results = await api_service.search_audiobook(q, search_type)
    return results

@app.get("/api/metadata/{source}/{book_id}")
async def get_metadata(source: str, book_id: str):
    metadata = await api_service.get_book_metadata(source, book_id)
    return metadata

@app.post("/api/preview")
async def preview_changes(update_data: MetadataUpdate):
    file_path = await file_service.get_file_path_by_id(update_data.file_id, config.watch_folder)
    if not file_path:
        raise HTTPException(status_code=404, detail="File not found")
    
    current_metadata = metadata_service.read_metadata(file_path)
    metadata_dict = update_data.metadata.dict(exclude_none=True)
    preview = {
        "file_id": update_data.file_id,
        "original_path": str(file_path),
        "original_metadata": current_metadata,
        "new_filename": file_service.generate_filename(metadata_dict, config.filename_template),
        "new_path": file_service.generate_filepath(metadata_dict, config.folder_template, config.output_folder),
        "metadata_changes": update_data.metadata,
    }
    return preview

async def _is_dir_empty(path: str) -> bool:
    """Check if directory is empty or contains only ignorable files."""
    try:
        # Import here to avoid circular imports
        from services.file_service import file_service
        return await asyncio.wait_for(
            asyncio.to_thread(file_service._is_folder_safe_to_delete, path),
            timeout=5.0
        )
    except asyncio.TimeoutError:
        logger.warning(f"Timeout checking if {path} is empty or contains only ignorable files")
        return False
    except Exception as e:
        logger.error(f"Error checking if {path} is empty: {e}")
        return False

@app.post("/api/apply")
async def apply_changes(update_data: MetadataUpdate):
    file_path = await file_service.get_file_path_by_id(update_data.file_id, config.watch_folder)
    if not file_path:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Validate required fields
    metadata_dict = update_data.metadata.dict(exclude_none=True)
    title = metadata_dict.get('title', '')
    if not title or not title.strip():
        raise HTTPException(status_code=400, detail="Title is required")
    
    # Check for filename conflicts
    new_filename = file_service.generate_filename(metadata_dict, config.filename_template)
    new_folder = file_service.generate_filepath(metadata_dict, config.folder_template, config.output_folder)
    target_path = Path(new_folder) / new_filename
    
    if target_path.exists() and str(target_path) != str(file_path):
        raise HTTPException(status_code=409, detail=f"Target file already exists: {new_filename}")
    
    # Get the parent folder before moving
    original_folder = str(Path(file_path).parent)
    
    success, new_path = await file_service.apply_metadata_and_move(
        file_path, 
        metadata_dict, 
        config.filename_template,
        config.folder_template,
        config.output_folder
    )
    
    # Check for empty folders (with timeout to prevent hanging on network mounts)
    empty_folders = []
    if success and original_folder:
        try:
            if original_folder.startswith(config.watch_folder):
                if await _is_dir_empty(original_folder):
                    empty_folders.append(original_folder)
                parent = Path(original_folder).parent
                while str(parent) != config.watch_folder:
                    parent_str = str(parent)
                    if await _is_dir_empty(parent_str):
                        empty_folders.append(parent_str)
                    parent = parent.parent
        except Exception as e:
            logger.error(f"Error checking empty folders: {e}")
    
    return {
        "success": success, 
        "message": "Changes applied successfully" if success else "Failed to apply changes",
        "new_path": new_path,
        "empty_folders": empty_folders
    }

@app.post("/api/delete-folder")
async def delete_folder(folder_path: str):
    """Delete a folder if it's empty or contains only ignorable files"""
    try:
        # Import here to avoid circular imports
        from services.file_service import file_service
        
        path = Path(folder_path)
        try:
            is_empty = await asyncio.wait_for(
                asyncio.to_thread(file_service._is_folder_safe_to_delete, str(path)),
                timeout=5.0
            )
        except asyncio.TimeoutError:
            return {"success": False, "message": "Timeout checking folder"}

        if is_empty:
            path.rmdir()
            return {"success": True, "message": f"Deleted folder: {folder_path}"}
        elif not path.exists():
            return {"success": False, "message": "Folder does not exist"}
        else:
            return {"success": False, "message": "Folder contains significant files and cannot be deleted"}
    except Exception as e:
        return {"success": False, "message": str(e)}

def _safe_roots() -> list:
    """Return a list of absolute paths the folder browser is allowed to expose."""
    roots = []
    # Always allow the general media mount point so users can browse
    # and select any folder under /mnt/media as watch/output
    roots.append("/mnt/media")
    for raw in (config.watch_folder, config.output_folder):
        if not raw:
            continue
        try:
            roots.append(str(Path(raw).resolve()))
        except (OSError, RuntimeError):
            continue
    return roots


def _is_within_safe_root(path: str) -> bool:
    for root in _safe_roots():
        try:
            if os.path.commonpath([path, root]) == root:
                return True
        except ValueError:
            continue
    return False


@app.get("/api/folders")
async def get_folders(path: str = "/"):
    """Get list of folders at the specified path. Restricted to configured watch/output roots."""
    try:
        path_obj = Path(path)
        if not path_obj.is_absolute():
            path_obj = (Path("/") / path).resolve()
        else:
            path_obj = path_obj.resolve()

        if not _is_within_safe_root(str(path_obj)):
            return {"current": str(path_obj), "folders": [], "error": "Path is outside allowed roots"}

        if not path_obj.exists():
            return {"current": str(path_obj), "folders": []}

        try:
            items = list(path_obj.iterdir())
        except PermissionError:
            return {"current": str(path_obj), "folders": []}

        folders = []
        for item in items:
            try:
                if item.is_dir() and not item.name.startswith('.'):
                    folders.append(item.name)
            except OSError:
                continue

        folders.sort()

        return {"current": str(path_obj), "folders": folders}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/watch/status")
async def get_watch_status():
    return {"active": watch_service.is_watching(), "folder": config.watch_folder}

@app.post("/api/watch/start")
async def start_watch():
    watch_service.start_watching(
        config.watch_folder,
        callback=_on_new_file,
        on_change=_on_watch_change,
    )
    file_service.invalidate_file_index()
    return {"message": "Watch started", "folder": config.watch_folder}

@app.post("/api/watch/stop")
async def stop_watch():
    watch_service.stop_watching()
    return {"message": "Watch stopped"}

async def report_progress(queue_id, progress_type, current, total, message=""):
    """Report progress to the queue"""
    if queue_id in progress_queues:
        percentage = int((current / total) * 100) if total > 0 else 0
        await progress_queues[queue_id].put({
            "type": progress_type,
            "current": current,
            "total": total,
            "percentage": percentage,
            "message": message
        })

async def send_progress_to_queue(queue_id, progress_data):
    """Helper to send progress data to queue"""
    if queue_id in progress_queues:
        await progress_queues[queue_id].put(progress_data)

@app.post("/api/combine")
async def combine_files(combine_data: CombineFiles):
    """Combine multiple audio files into a single M4B"""
    task_id = "combine"
    logger.info(f"Starting combine operation, progress_queues keys: {list(progress_queues.keys())}")
    logger.info(f"Received file_ids: {combine_data.file_ids}")
    logger.info(f"Config watch folder: {config.watch_folder}")
    
    # Get source file paths before combining for potential cleanup
    source_file_paths = []
    for file_id in combine_data.file_ids:
        file_path = await file_service.get_file_path_by_id(file_id, config.watch_folder)
        logger.info(f"File ID {file_id} maps to path: {file_path}")
        if file_path:
            source_file_paths.append(file_path)
        else:
            logger.warning(f"Could not find file for ID: {file_id}")
    
    async def progress_callback(percentage, message):
        logger.info(f"Progress callback: {percentage}% - {message}")
        if task_id in progress_queues:
            logger.info(f"Putting progress to queue: {percentage}%")
            await progress_queues[task_id].put({
                "type": "progress",
                "percentage": percentage,
                "message": message
            })
        else:
            logger.warning(f"Queue {task_id} not found in progress_queues: {list(progress_queues.keys())}")
    
    try:
        success, result = await file_service.combine_audio_files(
            combine_data.file_ids,
            config.watch_folder,
            config.output_folder,
            combine_data.output_title,
            combine_data.metadata,
            combine_data.new_filename,
            combine_data.new_path,
            progress_callback
        )
        
        if success:
            output_path = result[0] if isinstance(result, tuple) else result
            empty_folders = result[1] if isinstance(result, tuple) and len(result) > 1 else []
            deleted_files = result[2] if isinstance(result, tuple) and len(result) > 2 else []
            
            return {
                "success": True, 
                "output_path": output_path, 
                "empty_folders": empty_folders,
                "deleted_files": deleted_files,
                "task_id": task_id
            }
        else:
            raise HTTPException(status_code=400, detail=result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error combining files: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, timeout_keep_alive=1800)
