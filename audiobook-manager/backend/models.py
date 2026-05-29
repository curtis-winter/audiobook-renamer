from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List, Union
import json
from pathlib import Path
import os

CONFIG_PATH = os.getenv("CONFIG_PATH", "/config/config.json")

class AudioMetadata(BaseModel):
    title: Optional[str] = None
    subtitle: Optional[str] = None
    artist: Optional[str] = None
    album_artist: Optional[str] = None
    composer: Optional[str] = None
    narrator: Optional[str] = None
    year: Optional[str] = None
    comment: Optional[str] = None
    series: Optional[str] = None
    series_part: Optional[str] = None
    album_sort: Optional[str] = None
    publisher: Optional[str] = None
    copyright: Optional[str] = None
    rating: Optional[str] = None
    cover: Optional[str] = None
    album: Optional[str] = None
    track: Optional[Any] = None
    asin: Optional[str] = None
    isbn: Optional[str] = None
    genre: Optional[str] = None
    language: Optional[str] = None
    runtime: Optional[Any] = None
    format: Optional[str] = None
    explicit: Optional[str] = None
    release_date: Optional[str] = None
    content_group: Optional[str] = None
    movement: Optional[str] = None
    movement_name: Optional[str] = None
    
    model_config = ConfigDict(extra="allow")

class AudiobookFile(BaseModel):
    id: str
    path: str
    filename: str
    size: int
    modified: str
    metadata: Optional[AudioMetadata] = None

class MetadataUpdate(BaseModel):
    file_id: str
    metadata: AudioMetadata

class Config(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    watch_folder: str = Field(default="/mnt/watch", alias="watchFolder")
    output_folder: str = Field(default="/mnt/output", alias="outputFolder")
    filename_template: str = Field(default="%albumartist% - %album% (%year%)", alias="filenameTemplate")
    folder_template: str = Field(default="%albumartist%/%series%/%year% - %album%", alias="folderTemplate")
    
    def save(self):
        config_path = Path(CONFIG_PATH)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w") as f:
            json.dump(self.dict(), f, indent=2)

    @classmethod
    def load(cls) -> "Config":
        config_path = Path(CONFIG_PATH)
        if config_path.exists():
            try:
                with open(config_path, "r") as f:
                    return cls(**json.load(f))
            except Exception:
                pass
        return cls()

class CombineFiles(BaseModel):
    file_ids: List[str]
    output_title: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    new_filename: Optional[str] = None
    new_path: Optional[str] = None
