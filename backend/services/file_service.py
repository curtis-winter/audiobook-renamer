from pathlib import Path
import os
import uuid
import shutil
from datetime import datetime
from services.metadata_service import metadata_service

class FileService:
    AUDIO_EXTENSIONS = {'.mp3', '.m4b', '.m4a', '.flac', '.ogg', '.wav', '.wma', '.aax', '.aa', '.m4p'}
    # Also include files with no extension (common for audiobooks)
    _file_mapping = {}
    
    def get_audio_files(self, folder: str) -> list:
        """Get all audio files in folder"""
        if not os.path.exists(folder):
            return []
        
        files = []
        for root, dirs, filenames in os.walk(folder):
            for filename in filenames:
                file_ext = Path(filename).suffix.lower()
                # Only include files with known audio extensions
                if file_ext in self.AUDIO_EXTENSIONS:
                    file_path = os.path.join(root, filename)
                    try:
                        stat = os.stat(file_path)
                        file_id = str(uuid.uuid4())
                        self._file_mapping[file_id] = file_path
                        files.append({
                            'id': file_id,
                            'path': file_path,
                            'filename': filename,
                            'size': stat.st_size,
                            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            'metadata': None
                        })
                    except OSError:
                        # Skip files that can't be accessed
                        continue
        
        return files
    
    def get_file_path_by_id(self, file_id: str, base_folder: str) -> str:
        """Get file path by ID"""
        if file_id in self._file_mapping:
            return self._file_mapping[file_id]
        
        for root, dirs, filenames in os.walk(base_folder):
            for filename in filenames:
                file_ext = Path(filename).suffix.lower()
                if file_ext in self.AUDIO_EXTENSIONS:
                    file_path = os.path.join(root, filename)
                    if filename in file_path:
                        return file_path
        return None
    
    def generate_filename(self, metadata: dict, template: str, original_file_path: str = None) -> str:
        """Generate filename from template"""
        filename = template
        
        # Build replacements dictionary with all available fields
        replacements = {
            # Primary fields
            '%album%': metadata.get('album') or metadata.get('title') or 'Unknown',
            '%title%': metadata.get('title') or metadata.get('album') or 'Unknown',
            '%year%': metadata.get('year') or '',
            '%track%': str(metadata.get('track', '')) if metadata.get('track') else '',
            
            # Artist/Author fields
            '%artist%': metadata.get('artist') or '',
            '%albumartist%': metadata.get('album_artist') or '',
            '%album_artists%': metadata.get('album_artists', []),
            '%authors%': metadata.get('authors', []),
            
            # Series fields
            '%series%': metadata.get('series') or '',
            '%series_part%': metadata.get('series_part') or '',
            '%series-part%': metadata.get('series_part') or '',
            
            # Narrator fields
            '%composer%': metadata.get('composer') or '',  # Narrator maps to COMPOSER
            '%narrator%': metadata.get('narrator') or '',
            
            # Publisher fields
            '%publisher%': metadata.get('publisher') or '',
            
            # Other fields
            '%subtitle%': metadata.get('subtitle') or '',
            '%comment%': metadata.get('comment') or '',
            '%genre%': metadata.get('genre') or '',
            '%language%': metadata.get('language') or '',
            '%format%': metadata.get('format') or '',
            '%asin%': metadata.get('asin') or '',
            
            # Album sort (special handling)
            '%album_sort%': metadata.get('album_sort') or '',
            
            # Series combination
            '%series_full%': f"{metadata.get('series', '')} {metadata.get('series_part', '')}".strip(),
        }
        
        for key, value in replacements.items():
            if isinstance(value, list):
                filename = filename.replace(key, ', '.join(str(v) for v in value) if value else '')
            else:
                # Clean up the value - remove special characters that might cause issues
                clean_value = str(value) if value else ''
                filename = filename.replace(key, clean_value)
        
        # Handle %track% replacement - use actual track number, not series_part
        track_val = metadata.get('track')
        if '%track%' in filename and track_val:
            # Handle track as list like [1, 0] or string
            if isinstance(track_val, list):
                track_num = track_val[0] if track_val else '1'
            else:
                track_num = track_val
            filename = filename.replace('%track%', str(track_num).zfill(2))
        
        # Preserve original file extension
        if original_file_path:
            ext = Path(original_file_path).suffix
            if ext:
                filename = filename + ext
        
        return filename
    
    def generate_filepath(self, metadata: dict, folder_template: str, base_folder: str) -> str:
        """Generate full file path from template"""
        folder_path = folder_template
        
        replacements = {
            # Primary fields
            '%album%': metadata.get('album') or metadata.get('title') or 'Unknown',
            '%title%': metadata.get('title') or metadata.get('album') or 'Unknown',
            '%year%': metadata.get('year') or '',
            '%track%': str(metadata.get('track', '')) if metadata.get('track') else '',
            
            # Artist/Author fields
            '%artist%': metadata.get('artist') or '',
            '%albumartist%': metadata.get('album_artist') or '',
            
            # Series fields
            '%series%': metadata.get('series') or '',
            '%series_part%': metadata.get('series_part') or '',
            '%series-part%': metadata.get('series_part') or '',
            
            # Narrator fields
            '%composer%': metadata.get('composer') or '',
            '%narrator%': metadata.get('narrator') or '',
            
            # Publisher fields
            '%publisher%': metadata.get('publisher') or '',
            
            # Other fields
            '%subtitle%': metadata.get('subtitle') or '',
            '%genre%': metadata.get('genre') or '',
            '%language%': metadata.get('language') or '',
            '%format%': metadata.get('format') or '',
            '%asin%': metadata.get('asin') or '',
            
            # Series combination
            '%series_full%': f"{metadata.get('series', '')} {metadata.get('series_part', '')}".strip(),
        }
        
        for key, value in replacements.items():
            clean_value = str(value) if value else ''
            folder_path = folder_path.replace(key, clean_value)
        
        # Clean up any double slashes
        while '//' in folder_path:
            folder_path = folder_path.replace('//', '/')
        
        return os.path.join(base_folder, folder_path)
    
    async def apply_metadata_and_move(self, file_path: str, metadata: dict, 
                                       filename_template: str, 
                                       folder_template: str,
                                       output_base: str) -> tuple:
        """Apply metadata and move file - returns (success: bool, new_path: str)"""
        try:
            new_folder_path = self.generate_filepath(metadata, folder_template, output_base)
            new_filename = self.generate_filename(metadata, filename_template, file_path)
            new_path = os.path.join(new_folder_path, new_filename)
            
            os.makedirs(os.path.dirname(new_path), exist_ok=True)
            
            success = metadata_service.write_metadata(file_path, metadata)
            if not success:
                return (False, None)
            
            shutil.move(file_path, new_path)
            return (True, new_path)
        except Exception as e:
            print(f"Error applying metadata and moving: {e}")
            return (False, None)

file_service = FileService()
