from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import asyncio
from pathlib import Path

from services import metadata_service, file_service, watch_service, api_service
from models import AudiobookFile, MetadataUpdate, Config

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

@app.get("/api/config")
def get_config_dict():
    return {
        "watchFolder": config.watch_folder,
        "outputFolder": config.output_folder,
        "filenameTemplate": config.filename_template,
        "folderTemplate": config.folder_template,
    }

@app.get("/api/config")
async def get_config():
    return get_config_dict()

@app.post("/api/config")
async def update_config(cfg: Config):
    config.watch_folder = cfg.watch_folder
    config.output_folder = cfg.output_folder
    config.filename_template = cfg.filename_template
    config.folder_template = cfg.folder_template
    config.save()
    return get_config_dict()

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

@app.post("/api/apply")
async def apply_changes(update_data: MetadataUpdate):
    file_path = file_service.get_file_path_by_id(update_data.file_id, config.watch_folder)
    if not file_path:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Get the parent folder before moving
    original_folder = str(Path(file_path).parent)
    
    metadata_dict = update_data.metadata.dict(exclude_none=True)
    success, new_path = await file_service.apply_metadata_and_move(
        file_path, 
        metadata_dict, 
        config.filename_template,
        config.folder_template,
        config.output_folder
    )
    
    # Check for empty folders
    empty_folders = []
    if success and original_folder:
        # Check if the original folder is now empty
        try:
            if Path(original_folder).exists() and not any(Path(original_folder).iterdir()):
                empty_folders.append(original_folder)
            # Also check parent folders that might be empty now
            parent = Path(original_folder).parent
            while parent != Path(config.watch_folder) and parent.exists():
                if parent.exists() and not any(parent.iterdir()) and str(parent) != config.watch_folder:
                    empty_folders.append(str(parent))
                parent = parent.parent
        except Exception as e:
            print(f"Error checking empty folders: {e}")
    
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
        if path.exists() and path.is_dir():
            # Check if empty
            if not any(path.iterdir()):
                path.rmdir()
                return {"success": True, "message": f"Deleted folder: {folder_path}"}
            else:
                return {"success": False, "message": "Folder is not empty"}
        return {"success": False, "message": "Folder does not exist"}
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
