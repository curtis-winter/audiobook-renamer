import os
import asyncio
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading

class AudioFileHandler(FileSystemEventHandler):
    AUDIO_EXTENSIONS = {'.mp3', '.m4b', '.m4a', '.flac', '.ogg', '.wav', '.wma'}
    
    def __init__(self, callback=None):
        self.callback = callback
        self.observer = None
    
    def on_created(self, event):
        if event.is_directory:
            return
        
        file_ext = Path(event.src_path).suffix.lower()
        if file_ext in self.AUDIO_EXTENSIONS:
            if self.callback:
                self.callback(event.src_path)
    
    def on_moved(self, event):
        if event.is_directory:
            return
        
        file_ext = Path(event.dest_path).suffix.lower()
        if file_ext in self.AUDIO_EXTENSIONS:
            if self.callback:
                self.callback(event.dest_path)

class WatchService:
    def __init__(self):
        self.observer = None
        self.is_watching = False
        self.handler = None
    
    def start_watching(self, folder: str, callback=None):
        """Start watching a folder for new audio files"""
        if self.is_watching:
            return
        
        if not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)
        
        self.handler = AudioFileHandler(callback)
        self.observer = Observer()
        self.observer.schedule(self.handler, folder, recursive=True)
        self.observer.start()
        self.is_watching = True
    
    def stop_watching(self):
        """Stop watching"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.is_watching = False
    
    def is_watching(self) -> bool:
        return self.is_watching

watch_service = WatchService()
