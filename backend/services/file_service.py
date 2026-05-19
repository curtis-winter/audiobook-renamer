from pathlib import Path
import os
import shutil
from datetime import datetime
import re
import logging
import hashlib
from services.metadata_service import metadata_service

# Configure logging
logger = logging.getLogger(__name__)

class FileService:
    
    def _get_field_value(self, metadata, field_name):
        """Get field value from metadata"""
        clean_name = field_name.strip('%')
        return metadata.get(clean_name, '')
    
    def _sanitize_path(self, text):
        """Remove invalid characters from file/folder names"""
        if not text:
            return ''
        text = str(text)
        replacements = {
            ':': '-', '<': '-', '>': '-', '"': "'",
            '/': '-', '\\': '-', '|': '-', '?': '', '*': '',
            '\t': ' ', '\n': ' ', '\r': ' ',
        }
        for char, repl in replacements.items():
            text = text.replace(char, repl)
        text = re.sub(r'[\s-]+', ' ', text).strip(' .')
        return text if text else 'Unknown'
    
    def _process_functions(self, template, metadata):
        """Process functional statements in template"""
        result = template
        
        # Process if_field:{{if_field:fieldname:value}} or {{if_field:fieldname:yes:no}}
        def process_if(match):
            field = match.group(1)
            if ':' in match.group(2):  # if/else format: yes:no
                yes_part, no_part = match.group(2).split(':', 1)
                field_val = self._get_field_value(metadata, field)
                return yes_part if field_val else no_part
            else:  # simple format: value
                field_val = self._get_field_value(metadata, field)
                value = match.group(2)
                return value.replace('{field}', str(field_val)) if '{field}' in value and field_val else (value if field_val else '')
        
        result = re.sub(r'\{\{if_field:([^:]+):([^}]+)\}\}', process_if, result)
        
        # Process pad_left:{{pad_left:fieldname:width}}
        def process_pad(match):
            field = match.group(1)
            width = int(match.group(2))
            field_val = self._get_field_value(metadata, field)
            return str(field_val).zfill(width) if field_val else ''
        
        result = re.sub(r'\{\{pad_left:([^:]+):(\d+)\}\}', process_pad, result)
        
        # Process uppercase:{{uppercase:fieldname}}
        def process_uppercase(match):
            field = match.group(1)
            field_val = self._get_field_value(metadata, field)
            return str(field_val).upper() if field_val else ''
        
        result = re.sub(r'\{\{uppercase:([^}]+)\}\}', process_uppercase, result)
        
        # Process lowercase:{{lowercase:fieldname}}
        def process_lowercase(match):
            field = match.group(1)
            field_val = self._get_field_value(metadata, field)
            return str(field_val).lower() if field_val else ''
        
        result = re.sub(r'\{\{lowercase:([^}]+)\}\}', process_lowercase, result)
        
        # Process default:{{default:fieldname:default_value}}
        def process_default(match):
            field = match.group(1)
            default_value = match.group(2)
            field_val = self._get_field_value(metadata, field)
            return field_val if field_val else default_value
        
        result = re.sub(r'\{\{default:([^:]+):([^}]+)\}\}', process_default, result)
        
        # Process replace:{{replace:fieldname:old:new}}
        def process_replace(match):
            field = match.group(1)
            old_new = match.group(2).split(':', 1)
            if len(old_new) == 2:
                old, new = old_new
                field_val = self._get_field_value(metadata, field)
                return str(field_val).replace(old, new) if field_val else ''
            return ''
        
        result = re.sub(r'\{\{replace:([^:]+):([^}]+)\}\}', process_replace, result)
        
        return result
    
    def _get_replacements_dict(self, metadata):
        """Get dictionary of template replacements from metadata"""
        return {
            # Primary fields
            '%album%': self._sanitize_path(metadata.get('album') or metadata.get('title') or 'Unknown'),
            '%title%': self._sanitize_path(metadata.get('title') or metadata.get('album') or 'Unknown'),
            '%year%': metadata.get('year') or '',
            '%track%': str(metadata.get('track', '')) if metadata.get('track') else '',
            
            # Artist/Author fields
            '%artist%': self._sanitize_path(metadata.get('artist') or ''),
            '%albumartist%': metadata.get('album_artist') or '',
            '%album_artists%': metadata.get('album_artists', []),
            '%authors%': metadata.get('authors', []),
            
            # Series fields
            '%series%': self._sanitize_path(metadata.get('series') or ''),
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
    
    AUDIO_EXTENSIONS = {'.mp3', '.m4b', '.m4a', '.flac', '.ogg', '.wav', '.wma', '.aax', '.aa', '.m4p'}

    def _get_file_id(self, file_path: str) -> str:
        """Generate deterministic file ID from path"""
        return hashlib.sha256(file_path.encode()).hexdigest()[:16]

    def get_audio_files(self, folder: str) -> list:
        """Get all audio files in folder"""
        if not os.path.exists(folder):
            return []

        files = []
        for root, dirs, filenames in os.walk(folder):
            for filename in filenames:
                file_ext = Path(filename).suffix.lower()
                if file_ext in self.AUDIO_EXTENSIONS:
                    file_path = os.path.join(root, filename)
                    try:
                        stat = os.stat(file_path)
                        file_id = self._get_file_id(file_path)
                        files.append({
                            'id': file_id,
                            'path': file_path,
                            'filename': filename,
                            'size': stat.st_size,
                            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            'metadata': None
                        })
                    except OSError:
                        continue

        return files

    def get_file_path_by_id(self, file_id: str, base_folder: str) -> str:
        """Get file path by ID - reconstruct from ID using path hash"""
        if not os.path.exists(base_folder):
            return None

        for root, dirs, filenames in os.walk(base_folder):
            for filename in filenames:
                file_ext = Path(filename).suffix.lower()
                if file_ext in self.AUDIO_EXTENSIONS:
                    file_path = os.path.join(root, filename)
                    if self._get_file_id(file_path) == file_id:
                        return file_path
        return None
    
    def generate_filename(self, metadata: dict, template: str, original_file_path: str = None) -> str:
        """Generate filename from template"""
        # Process functions first
        template = self._process_functions(template, metadata)
        filename = template
        
        # Get replacements dictionary
        replacements = self._get_replacements_dict(metadata)
        
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
        # Process functions first
        folder_path = self._process_functions(folder_template, metadata)
        
        # Get replacements dictionary
        replacements = self._get_replacements_dict(metadata)
        
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
            logger.error(f"Error applying metadata and moving: {e}")
            return (False, None)

file_service = FileService()
