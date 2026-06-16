from pathlib import Path
import os
import shutil
import asyncio
import time
from datetime import datetime
import re
import logging
import hashlib
import tempfile
from typing import List, Optional
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
    _INDEX_TTL_SECONDS = 5.0

    def __init__(self):
        self._file_index: dict = {}
        self._index_folder: Optional[str] = None
        self._index_built_at: float = 0.0
        self._index_lock = asyncio.Lock()

    def _get_file_id(self, file_path: str) -> str:
        """Generate deterministic file ID from path"""
        return hashlib.sha256(file_path.encode()).hexdigest()[:16]

    def _walk_audio_files(self, folder: str) -> list:
        """Walk folder and return list of (file_id, full_path) tuples."""
        results = []
        for root, _dirs, filenames in os.walk(folder):
            for filename in filenames:
                file_ext = Path(filename).suffix.lower()
                if file_ext in self.AUDIO_EXTENSIONS:
                    file_path = os.path.join(root, filename)
                    results.append((self._get_file_id(file_path), file_path))
        return results

    async def _get_file_index(self, folder: str, force_refresh: bool = False) -> dict:
        """Return an in-memory id->path index, rebuilding it if stale or for a different folder."""
        now = time.monotonic()
        stale = (
            force_refresh
            or self._index_folder != folder
            or (now - self._index_built_at) > self._INDEX_TTL_SECONDS
        )
        if not stale and self._file_index:
            return self._file_index

        async with self._index_lock:
            now = time.monotonic()
            stale = (
                force_refresh
                or self._index_folder != folder
                or (now - self._index_built_at) > self._INDEX_TTL_SECONDS
            )
            if stale:
                if not os.path.exists(folder):
                    self._file_index = {}
                else:
                    entries = await asyncio.to_thread(self._walk_audio_files, folder)
                    self._file_index = dict(entries)
                self._index_folder = folder
                self._index_built_at = time.monotonic()
            return self._file_index

    def invalidate_file_index(self):
        """Force the next index lookup to rebuild (call from the watcher)."""
        self._index_built_at = 0.0

    async def get_audio_files(self, folder: str) -> list:
        """Get all audio files in folder, reusing the in-memory index when possible."""
        if not os.path.exists(folder):
            return []

        index = await self._get_file_index(folder, force_refresh=True)
        files = []
        for file_id, file_path in index.items():
            try:
                stat = os.stat(file_path)
                files.append({
                    'id': file_id,
                    'path': file_path,
                    'filename': os.path.basename(file_path),
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'metadata': None
                })
            except OSError:
                continue
        files.sort(key=lambda f: f['filename'].lower())
        return files

    async def get_file_path_by_id(self, file_id: str, base_folder: str) -> Optional[str]:
        """Get file path by ID using the in-memory index, falling back to a scan if missing."""
        if not os.path.exists(base_folder):
            return None

        index = await self._get_file_index(base_folder)
        path = index.get(file_id)
        if path and not os.path.exists(path):
            self.invalidate_file_index()
            index = await self._get_file_index(base_folder, force_refresh=True)
            path = index.get(file_id)
        return path
    
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

        # Resolve and validate path to prevent traversal
        full_path = os.path.join(base_folder, folder_path)
        resolved_path = os.path.normpath(full_path)
        normalized_base = os.path.normpath(base_folder)

        try:
            is_within = os.path.commonpath([resolved_path, normalized_base]) == normalized_base
        except ValueError:
            is_within = False

        if not is_within:
            logger.warning(f"Path traversal attempt detected: {folder_path}")
            folder_path = 'Invalid'
            full_path = os.path.join(base_folder, folder_path)

        return full_path
    
    async def apply_metadata_and_move(self, file_path: str, metadata: dict,
                                       filename_template: str,
                                       folder_template: str,
                                       output_base: str,
                                       progress_callback=None) -> tuple:
        """Apply metadata and move file - returns (success: bool, new_path: str).

        Mirrors the combine pipeline: pass the source through ffmpeg (stream-copy
        or re-encode), apply the metadata to the produced output, then move/delete
        the source. Falls back to the legacy direct-mutagen path if ffmpeg fails."""
        try:
            new_folder_path = self.generate_filepath(metadata, folder_template, output_base)
            new_filename = self.generate_filename(metadata, filename_template, file_path)
            new_path = os.path.join(new_folder_path, new_filename)

            os.makedirs(os.path.dirname(new_path), exist_ok=True)

            # In-place rename: no ffmpeg pass needed (and would fail with same in/out)
            same_path = os.path.abspath(file_path) == os.path.abspath(new_path)

            if not same_path:
                ffmpeg_ok = await self._ffmpeg_process_single(file_path, new_path, progress_callback)
                if ffmpeg_ok:
                    meta_ok = metadata_service.write_metadata(new_path, metadata)
                    if not meta_ok:
                        logger.warning(f"Failed to write metadata to ffmpeg output: {new_path}")
                    try:
                        if os.path.exists(file_path):
                            os.remove(file_path)
                            logger.info(f"Removed source after ffmpeg: {file_path}")
                    except OSError as e:
                        logger.error(f"Failed to remove source {file_path}: {e}")
                    return (True, new_path)
                logger.warning(f"ffmpeg single-file pass failed for {file_path}, falling back to mutagen-only path")

            # Fallback: write metadata in place and move (legacy behavior)
            success = metadata_service.write_metadata(file_path, metadata)
            if not success:
                return (False, None)
            shutil.move(file_path, new_path)
            return (True, new_path)
        except Exception as e:
            logger.error(f"Error applying metadata and moving: {e}")
            return (False, None)
    
    async def _get_total_duration(self, file_paths: List[str]) -> float:
        """Get total duration of audio files in seconds using ffprobe"""
        total = 0.0
        for path in file_paths:
            try:
                cmd = [
                    'ffprobe', '-v', 'error',
                    '-show_entries', 'format=duration',
                    '-of', 'default=noprint_wrappers=1:nokey=1',
                    path
                ]
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.DEVNULL
                )
                stdout, _ = await process.communicate()
                if stdout:
                    total += float(stdout.decode().strip())
            except Exception as e:
                logger.warning(f"Could not get duration for {path}: {e}")
        return total

    async def _run_ffmpeg_with_progress(self, cmd: List[str], progress_start: int, progress_end: int, total_duration: float, progress_callback) -> int:
        """Run ffmpeg and parse stderr for progress updates"""
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE
        )

        time_pattern = re.compile(r'time=(\d+):(\d+):(\d+)\.(\d+)')
        result = None
        last_report = -1
        stderr_lines = []

        while True:
            line = await process.stderr.readline()
            if not line:
                break
            line = line.decode('utf-8', errors='replace').strip()
            stderr_lines.append(line)

            m = time_pattern.search(line)
            if m and total_duration > 0:
                hours, mins, secs, _ = int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))
                current_time = hours * 3600 + mins * 60 + secs
                pct = min(int((current_time / total_duration) * (progress_end - progress_start) + progress_start), progress_end)
                if pct != last_report:
                    last_report = pct
                    await progress_callback(pct, f"Combining audio... ({current_time // 60}m {current_time % 60}s / {int(total_duration) // 60}m {int(total_duration) % 60}s)")

        await process.wait()
        if process.returncode != 0:
            logger.error(f"FFmpeg command failed with return code {process.returncode}")
            logger.error(f"FFmpeg stderr: {' '.join(stderr_lines)}")
        return process.returncode

    @staticmethod
    def _codec_args_for(target_path: str) -> list:
        """Pick a sane re-encode codec for the target container."""
        ext = Path(target_path).suffix.lower()
        if ext in ('.m4b', '.m4a', '.mp4', '.aac'):
            return ['-c:a', 'aac', '-b:a', '192k']
        if ext == '.mp3':
            return ['-c:a', 'libmp3lame', '-b:a', '192k']
        if ext == '.flac':
            return ['-c:a', 'flac']
        if ext in ('.ogg', '.oga'):
            return ['-c:a', 'libvorbis', '-b:a', '192k']
        if ext == '.opus':
            return ['-c:a', 'libopus', '-b:a', '192k']
        if ext == '.wav':
            return ['-c:a', 'pcm_s16le']
        return ['-c:a', 'aac', '-b:a', '192k']

    async def _ffmpeg_process_single(self, source_path: str, target_path: str,
                                      progress_callback=None) -> bool:
        """Process a single audio file through ffmpeg. Mirrors the combine logic:
        try stream-copy first (fast, lossless), fall back to re-encoding. Returns
        True on success. The caller is responsible for writing metadata and removing
        the source file."""
        if not os.path.exists(source_path):
            logger.error(f"ffmpeg single: source does not exist: {source_path}")
            return False

        if progress_callback:
            await progress_callback(20, "Processing audio...")

        # Attempt 1: stream-copy (fast, no quality loss, handles most same-format remuxes)
        cmd_copy = [
            'ffmpeg', '-y', '-i', source_path,
            '-c', 'copy', '-map', '0', '-map_metadata', '0',
            target_path,
        ]
        process = await asyncio.create_subprocess_exec(
            *cmd_copy,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await process.communicate()
        if process.returncode == 0 and os.path.exists(target_path):
            if progress_callback:
                await progress_callback(50, "Stream copy complete")
            return True

        # Attempt 2: re-encode (handles format conversion and files that can't be stream-copied)
        if progress_callback:
            await progress_callback(25, "Re-encoding audio...")

        cmd_recode = [
            'ffmpeg', '-y', '-i', source_path,
            '-map', '0', '-map_metadata', '0',
            '-vn', '-sn',
            '-avoid_negative_ts', 'make_zero',
            *self._codec_args_for(target_path),
            target_path,
        ]
        process = await asyncio.create_subprocess_exec(
            *cmd_recode,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await process.communicate()
        if process.returncode == 0 and os.path.exists(target_path):
            if progress_callback:
                await progress_callback(50, "Re-encode complete")
            return True

        tail = (stderr or b'').decode('utf-8', errors='replace')[-500:]
        logger.error(f"ffmpeg single-file processing failed for {source_path}: {tail}")
        # Clean up any partial output ffmpeg may have left behind
        if os.path.exists(target_path):
            try:
                os.remove(target_path)
            except OSError:
                pass
        return False

    async def _concat_via_demuxer(self, file_paths: List[str], output_path: str, total_duration: float, progress_callback=None) -> int:
        """Concatenate files using ffmpeg concat demuxer (more suitable for large numbers of files)"""
        try:
            # Create temporary directory for concat list
            import tempfile
            import os
            tmpdir = tempfile.mkdtemp(dir=os.path.dirname(output_path), prefix="concat_demuxer_")
            try:
                # Create concat file list
                concat_list = os.path.join(tmpdir, "list.txt")
                with open(concat_list, 'w', encoding='utf-8') as f:
                    for path in file_paths:
                        # Escape single quotes in path
                        escaped_path = path.replace("'", "'\\''")
                        f.write(f"file '{escaped_path}'\n")
                
                # First attempt: try to copy (fast)
                cmd_copy = [
                    'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
                    '-i', concat_list,
                    '-c', 'copy',
                    output_path
                ]
                
                logger.info("Attempting concat demuxer with copy")
                result = await self._run_ffmpeg_with_progress(
                    cmd_copy, 15, 30, total_duration, progress_callback
                )
                
                if result == 0 and os.path.exists(output_path):
                    logger.info("Concat demuxer with copy succeeded")
                    return result
                
                # If copy failed, try re-encoding
                logger.warning(f"Copy failed (result={result}), re-encoding via concat demuxer...")
                if progress_callback:
                    await progress_callback(30, "Re-encoding audio...")
                
                cmd_recode = [
                    'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
                    '-i', concat_list,
                    '-c:a', 'aac', '-b:a', '192k',
                    '-avoid_negative_ts', 'make_zero',
                    output_path
                ]
                
                result = await self._run_ffmpeg_with_progress(
                    cmd_recode, 30, 45, total_duration, progress_callback
                )
                
                return result
            finally:
                # Clean up temporary directory
                import shutil
                shutil.rmtree(tmpdir, ignore_errors=True)
        except Exception as e:
            logger.error(f"Error in concat demuxer: {e}")
            return 1

    async def _finalize_combined_file(
        self,
        combined_file_path: str,
        file_paths: List[str],
        metadata: Optional[dict],
        new_filename: Optional[str],
        new_path: Optional[str],
        output_folder: str,
        progress_callback,
    ) -> tuple:
        """Write metadata, move to final location, delete sources, collect empty folders.
        Returns (final_path, empty_folders, deleted_files)."""
        if progress_callback:
            await progress_callback(50, "Writing metadata...")

        if metadata:
            success = metadata_service.write_metadata(combined_file_path, metadata)
            if not success:
                logger.warning("Failed to write metadata to combined file")

        if progress_callback:
            await progress_callback(75, "Moving to destination...")

        if new_filename or new_path:
            target_dir = new_path if new_path else output_folder
            target_filename = new_filename if new_filename else os.path.basename(combined_file_path)
            if not target_filename.lower().endswith('.m4b'):
                target_filename += '.m4b'
            final_path = os.path.join(target_dir, target_filename)

            os.makedirs(target_dir, exist_ok=True)
            shutil.move(combined_file_path, final_path)
            combined_file_path = final_path

        if progress_callback:
            await progress_callback(90, "Cleaning up...")

        deleted_files = []
        for path in file_paths:
            try:
                if os.path.exists(path):
                    os.remove(path)
                    deleted_files.append(path)
                    logger.info(f"Deleted source file: {path}")
            except Exception as e:
                logger.error(f"Failed to delete source file {path}: {e}")

        empty_folders = []
        for path in file_paths:
            folder = os.path.dirname(path)
            try:
                is_safe_to_delete = await asyncio.wait_for(
                    asyncio.to_thread(self._is_folder_safe_to_delete, folder),
                    timeout=5.0
                )
                if is_safe_to_delete:
                    empty_folders.append(folder)
                    logger.info(f"Marking folder for deletion (contains only ignorable files): {folder}")
            except asyncio.TimeoutError:
                logger.warning(f"Timeout checking if {folder} is safe to delete")
                continue
            except Exception as e:
                logger.warning(f"Could not check folder {folder}: {e}")

        if progress_callback:
            await progress_callback(100, "Complete!")

        return (combined_file_path, empty_folders, deleted_files)

    async def combine_audio_files(self, file_ids: List[str], watch_folder: str, output_folder: str, output_title: str = None, metadata: dict = None, new_filename: str = None, new_path: str = None, progress_callback=None) -> tuple:
        """Combine multiple audio files into a single M4B with chapter markers"""
        try:
            file_paths = []
            for file_id in file_ids:
                path = await self.get_file_path_by_id(file_id, watch_folder)
                if path:
                    file_paths.append(path)

            if len(file_paths) < 2:
                return (False, "Need at least 2 files to combine")

            file_paths.sort(key=self._natural_sort_key)
            os.makedirs(output_folder, exist_ok=True)

            if output_title:
                safe_title = self._sanitize_path(output_title)
                temp_filename = f"{safe_title}.m4b"
            else:
                base_name = os.path.splitext(os.path.basename(file_paths[0]))[0]
                temp_filename = f"{base_name}.m4b"

            temp_output_path = os.path.join(output_folder, temp_filename)

            if progress_callback:
                await progress_callback(10, "Combining audio files...")

            total_duration = await self._get_total_duration(file_paths)
            logger.info(f"Total duration of source files: {total_duration}s")

            result = -1
            symlink_attempt_failed = False

            try:
                tmpdir = tempfile.mkdtemp(dir=output_folder, prefix="combine_")
                try:
                    concat_entries = []
                    for i, path in enumerate(file_paths):
                        ext = Path(path).suffix or '.mp3'
                        link_path = os.path.join(tmpdir, f"p{i:04d}{ext}")
                        os.symlink(path, link_path)
                        concat_entries.append(link_path)

                    concat_list = os.path.join(tmpdir, "list.txt")
                    with open(concat_list, 'w') as f:
                        for lp in concat_entries:
                            f.write(f"file '{lp}'\n")

                    cmd = [
                        'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
                        '-i', concat_list,
                        '-c', 'copy',
                        temp_output_path
                    ]
                    logger.info("Running fast copy via symlink concat")
                    result = await self._run_ffmpeg_with_progress(
                        cmd, 10, 45, total_duration, progress_callback
                    )

                    if result != 0 or not os.path.exists(temp_output_path):
                        logger.warning(f"Copy failed (result={result}), re-encoding via symlink concat...")
                        if progress_callback:
                            await progress_callback(15, "Re-encoding audio...")
                        cmd_recode = [
                            'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
                            '-i', concat_list,
                            '-c:a', 'aac', '-b:a', '192k',
                            '-avoid_negative_ts', 'make_zero',
                            temp_output_path
                        ]
                        result = await self._run_ffmpeg_with_progress(
                            cmd_recode, 15, 45, total_duration, progress_callback
                        )
                finally:
                    shutil.rmtree(tmpdir, ignore_errors=True)
            except OSError as e:
                logger.warning(f"Symlink concat not possible ({e}), using concat demuxer approach")
                symlink_attempt_failed = True

            if symlink_attempt_failed or result != 0 or not os.path.exists(temp_output_path):
                if progress_callback:
                    await progress_callback(15, "Combining audio files...")
                result = await self._concat_via_demuxer(file_paths, temp_output_path, total_duration, progress_callback)

            if result != 0 or not os.path.exists(temp_output_path):
                logger.error(f"FFmpeg failed with code {result}")
                return (False, "Failed to combine files")

            final_path, empty_folders, deleted_files = await self._finalize_combined_file(
                temp_output_path, file_paths, metadata, new_filename, new_path, output_folder, progress_callback
            )
            return (True, (final_path, empty_folders, deleted_files))
        except Exception as e:
            logger.error(f"Error combining files: {e}")
            return (False, str(e))
    
    def _natural_sort_key(self, s):
        import re
        return [int(c) if c.isdigit() else c.lower() for c in re.split(r'([0-9]+)', os.path.basename(s))]

    def _is_folder_safe_to_delete(self, folder_path):
        """
        Check if folder contains only ignorable files (safe to delete for cleanup).
        Ignores common metadata/artifact files but preserves actual media/content.
        """
        # Define ignorable file patterns
        ignorable_extensions = {
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff',  # Images
            '.ico', '.webp', '.svg'
        }
        ignorable_names = {
            'Thumbs.db', '.DS_Store', 'Desktop.ini',
            '.gitkeep', '.gitignore', '.htaccess',
            'folder.jpg', 'folder.png', 'cover.jpg', 'cover.png',
            'coverart.jpg', 'coverart.png', 'artist.jpg', 'artist.png',
            'logo.jpg', 'logo.png', 'banner.jpg', 'banner.png'
        }
        
        try:
            with os.scandir(folder_path) as entries:
                for entry in entries:
                    if entry.is_file():
                        name = entry.name.lower()
                        # Check exact name matches
                        if name in ignorable_names:
                            continue
                        # Check extensions
                        ext = os.path.splitext(name)[1].lower()
                        if ext in ignorable_extensions:
                            continue
                        # If we reach here, it's a significant file
                        return False
                    elif entry.is_dir():
                        # Subdirectories mean we shouldn't delete
                        return False
                # Only ignorable files or empty folder
                return True
        except (OSError, PermissionError):
            return False  # Safe default: don't delete if we can't read

file_service = FileService()
