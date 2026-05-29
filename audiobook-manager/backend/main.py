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

app = FastAPI(title="Audiobook Manager")

# Allow all origins for development, configure for production
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

config = Config.load()

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
    return file_service.get_audio_files(config.watch_folder)

@app.get("/api/files/{file_id}/metadata")
async def get_file_metadata(file_id: str):
    file_path = file_service.get_file_path_by_id(file_id, config.watch_folder)
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
    file_path = file_service.get_file_path_by_id(update_data.file_id, config.watch_folder)
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
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(lambda: Path(path).exists() and not any(Path(path).iterdir())),
            timeout=5.0
        )
    except asyncio.TimeoutError:
        logger.warning(f"Timeout checking if {path} is empty")
        return False

@app.post("/api/apply")
async def apply_changes(update_data: MetadataUpdate):
    file_path = file_service.get_file_path_by_id(update_data.file_id, config.watch_folder)
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
    """Delete an empty folder"""
    try:
        path = Path(folder_path)
        try:
            is_empty = await asyncio.wait_for(
                asyncio.to_thread(lambda: path.exists() and path.is_dir() and not any(path.iterdir())),
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
            return {"success": False, "message": "Folder is not empty"}
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.get("/api/folders")
async def get_folders(path: str = "/"):
    """Get list of folders at the specified path"""
    try:
        # Handle root path or empty path
        if path == "" or path == "/":
            path_obj = Path("/")
            path_display = "/"
        else:
            path_obj = Path(path)
            path_display = path
        
        if not path_obj.exists():
            return {"current": path_display, "folders": []}
        
        try:
            items = list(path_obj.iterdir())
        except PermissionError:
            return {"current": path_display, "folders": []}
        
        folders = []
        for item in items:
            try:
                if item.is_dir() and not item.name.startswith('.'):
                    folders.append(item.name)
            except:
                continue
        
        folders.sort()
        
        return {"current": path_display, "folders": folders}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/watch/status")
async def get_watch_status():
    return {"active": watch_service.is_watching(), "folder": config.watch_folder}

@app.post("/api/watch/start")
async def start_watch():
    watch_service.start_watching(config.watch_folder)
    return {"message": "Watch started"}

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
            
            return {"success": True, "output_path": output_path, "empty_folders": empty_folders, "task_id": task_id}
        else:
            raise HTTPException(status_code=400, detail=result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error combining files: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, timeout_keep_alive=600)
