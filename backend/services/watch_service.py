import os
import asyncio
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading

class AudioFileHandler(FileSystemEventHandler):
    AUDIO_EXTENSIONS = {'.mp3', '.m4b', '.m4a', '.flac', '.ogg', '.wav', '.wma'}

    def __init__(self, callback=None, on_change=None):
        self.callback = callback
        self.on_change = on_change

    def _is_audio(self, path: str) -> bool:
        return Path(path).suffix.lower() in self.AUDIO_EXTENSIONS

    def on_created(self, event):
        if event.is_directory:
            return
        if self._is_audio(event.src_path):
            if self.on_change:
                self.on_change()
            if self.callback:
                self.callback(event.src_path)

    def on_moved(self, event):
        if event.is_directory:
            return
        if self._is_audio(event.dest_path):
            if self.on_change:
                self.on_change()
            if self.callback:
                self.callback(event.dest_path)

    def on_deleted(self, event):
        if event.is_directory:
            return
        if self._is_audio(event.src_path):
            if self.on_change:
                self.on_change()

    def on_modified(self, event):
        if event.is_directory:
            return
        if self._is_audio(event.src_path):
            if self.on_change:
                self.on_change()

class WatchService:
    def __init__(self):
        self.observer = None
        self._is_watching = False
        self.handler = None

    def start_watching(self, folder: str, callback=None, on_change=None):
        """Start watching a folder for new audio files."""
        if self._is_watching:
            self.stop_watching()

        if not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)

        self._folder = folder
        self.handler = AudioFileHandler(callback=callback, on_change=on_change)
        self.observer = Observer()
        self.observer.schedule(self.handler, folder, recursive=True)
        self.observer.start()
        self._is_watching = True

    def stop_watching(self):
        """Stop watching"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self._is_watching = False

    def is_watching(self) -> bool:
        return self._is_watching

watch_service = WatchService()
