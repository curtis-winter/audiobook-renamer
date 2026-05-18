from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Union
import json
from pathlib import Path
import os

class AudioMetadata(BaseModel):
    title: Optional[str] = None
    subtitle: Optional[str] = None
    artist: Optional[str] = None
    album_artist: Optional[str] = None
    composer: Optional[str] = None
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
    narrator: Optional[str] = None
    asin: Optional[str] = None
    language: Optional[str] = None
    runtime: Optional[Any] = None
    format: Optional[str] = None
    
    class Config:
        extra = "allow"

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
    watch_folder: str = Field(default="/mnt/watch")
    output_folder: str = Field(default="/mnt/output")
    filename_template: str = Field(default="%albumartist% - %album% (%year%)")
    folder_template: str = Field(default="%albumartist%/%series%/%year% - %album%")
    
    def save(self):
        config_path = Path("/config/config.json")
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w") as f:
            json.dump(self.dict(), f, indent=2)
    
    @classmethod
    def load(cls) -> "Config":
        config_path = Path("/config/config.json")
        if config_path.exists():
            try:
                with open(config_path, "r") as f:
                    return cls(**json.load(f))
            except Exception:
                pass
        return cls()
