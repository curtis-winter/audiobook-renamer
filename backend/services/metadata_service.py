from mutagen.mp3 import MP3
from mutagen.id3 import ID3, ID3NoHeaderError
from mutagen.flac import FLAC
from pathlib import Path
import os
import logging

# Configure logging
logger = logging.getLogger(__name__)

class MetadataService:
    AUDIO_EXTENSIONS = {'.mp3', '.m4b', '.m4a', '.flac', '.ogg', '.wav', '.wma'}
    
    def read_metadata(self, file_path: str) -> dict:
        """Read metadata from audio file"""
        try:
            file_ext = Path(file_path).suffix.lower()
            
            if file_ext == '.mp3':
                return self._read_mp3(file_path)
            elif file_ext in ['.m4a', '.m4b']:
                return self._read_m4a(file_path)
            elif file_ext == '.flac':
                return self._read_flac(file_path)
            else:
                return self._read_generic(file_path)
        except Exception as e:
            return {"error": str(e)}
    
    def write_metadata(self, file_path: str, metadata: dict) -> bool:
        """Write metadata to audio file"""
        try:
            file_ext = Path(file_path).suffix.lower()
            
            if file_ext == '.mp3':
                return self._write_mp3(file_path, metadata)
            elif file_ext in ['.m4a', '.m4b']:
                return self._write_m4a(file_path, metadata)
            elif file_ext == '.flac':
                return self._write_flac(file_path, metadata)
            else:
                return self._write_generic(file_path, metadata)
        except Exception as e:
            logger.error(f"Error writing metadata: {e}")
            return False
    
    def _read_mp3(self, file_path: str) -> dict:
        """Read MP3 metadata"""
        try:
            audio = MP3(file_path, ID3=ID3)
            tags = audio.tags
            
            if not tags:
                return {}
            
            return {
                'title': tags.get('TIT2', [''])[0] if tags.get('TIT2') else None,
                'subtitle': tags.get('TIT3', [''])[0] if tags.get('TIT3') else None,
                'artist': tags.get('TPE1', [''])[0] if tags.get('TPE1') else None,
                'album_artist': tags.get('TPE2', [''])[0] if tags.get('TPE2') else None,
                'composer': tags.get('TCOM', [''])[0] if tags.get('TCOM') else None,
                'year': tags.get('TDRC', [''])[0] if tags.get('TDRC') else None,
                'comment': tags.get('COMM', [''])[0] if tags.get('COMM') else None,
                'album': tags.get('TALB', [''])[0] if tags.get('TALB') else None,
                'track': tags.get('TRCK', [''])[0] if tags.get('TRCK') else None,
                'publisher': tags.get('TPUB', [''])[0] if tags.get('TPUB') else None,
                'copyright': tags.get('TCOP', [''])[0] if tags.get('TCOP') else None,
                'series': tags.get('TXXX:Series', [''])[0] if tags.get('TXXX:Series') else None,
                'series_part': tags.get('TXXX:Series Part', [''])[0] if tags.get('TXXX:Series Part') else None,
            }
        except ID3NoHeaderError:
            return {}
    
    def _read_m4a(self, file_path: str) -> dict:
        """Read M4A/M4B metadata"""
        from mutagen.mp4 import MP4
        try:
            audio = MP4(file_path)
            tags = audio.tags
            
            if not tags:
                return {}
            
            return {
                'title': tags.get('\xa9nam', [None])[0],
                'artist': tags.get('\xa9ART', [None])[0],
                'album_artist': tags.get('aART', [None])[0],
                'composer': tags.get('\xa9wrt', [None])[0],
                'year': tags.get('\xa9day', [None])[0],
                'comment': tags.get('\xa9cmt', [None])[0],
                'album': tags.get('\xa9alb', [None])[0],
                'track': tags.get('trkn', [None])[0],
                'publisher': tags.get('\xa9pub', [None])[0],
                'series': tags.get('\xa9grp', [None])[0],
            }
        except Exception:
            return {}
    
    def _read_flac(self, file_path: str) -> dict:
        """Read FLAC metadata"""
        try:
            audio = FLAC(file_path)
            tags = audio.tags
            
            if not tags:
                return {}
            
            return {
                'title': tags.get('TITLE', [None])[0],
                'artist': tags.get('ARTIST', [None])[0],
                'album_artist': tags.get('ALBUMARTIST', [None])[0],
                'composer': tags.get('COMPOSER', [None])[0],
                'year': tags.get('YEAR', [None])[0],
                'comment': tags.get('COMMENT', [None])[0],
                'album': tags.get('ALBUM', [None])[0],
                'track': tags.get('TRACKNUMBER', [None])[0],
                'publisher': tags.get('PUBLISHER', [None])[0],
                'copyright': tags.get('COPYRIGHT', [None])[0],
            }
        except Exception:
            return {}
    
    def _read_generic(self, file_path: str) -> dict:
        """Generic metadata reader"""
        try:
            audio = MP3(file_path) if file_path.endswith('.mp3') else None
            if audio and audio.tags:
                return self._read_mp3(file_path)
            return {}
        except Exception:
            return {}
    
    def _write_mp3(self, file_path: str, metadata: dict) -> bool:
        """Write MP3 metadata"""
        try:
            audio = MP3(file_path)
            if audio.tags is None:
                audio.add_tags()
            
            tags = audio.tags
            
            if metadata.get('title'):
                tags['TIT2'] = metadata['title']
            if metadata.get('artist'):
                tags['TPE1'] = metadata['artist']
            if metadata.get('album_artist'):
                tags['TPE2'] = metadata['album_artist']
            if metadata.get('composer'):
                tags['TCOM'] = metadata['composer']
            if metadata.get('year'):
                tags['TDRC'] = metadata['year']
            if metadata.get('comment'):
                tags['COMM'] = metadata['comment']
            if metadata.get('album'):
                tags['TALB'] = metadata['album']
            if metadata.get('track'):
                tags['TRCK'] = metadata['track']
            if metadata.get('publisher'):
                tags['TPUB'] = metadata['publisher']
            if metadata.get('copyright'):
                tags['TCOP'] = metadata['copyright']
            if metadata.get('subtitle'):
                tags['TIT3'] = metadata['subtitle']
            if metadata.get('series'):
                tags['TXXX:Series'] = metadata['series']
            if metadata.get('series_part'):
                tags['TXXX:Series Part'] = metadata['series_part']
            if metadata.get('narrator'):
                tags['TPE3'] = metadata['narrator']
            if metadata.get('genre'):
                tags['TCON'] = metadata['genre']
            if metadata.get('language'):
                tags['TLAN'] = metadata['language']
            if metadata.get('asin'):
                tags['TXXX:ASIN'] = metadata['asin']

            audio.save()
            return True
        except Exception as e:
            logger.error(f"Error writing MP3 metadata: {e}")
            return False
    
    def _write_m4a(self, file_path: str, metadata: dict) -> bool:
        """Write M4A/M4B metadata"""
        from mutagen.mp4 import MP4
        try:
            audio = MP4(file_path)
            
            if metadata.get('title'):
                audio['\xa9nam'] = metadata['title']
            if metadata.get('artist'):
                audio['\xa9ART'] = metadata['artist']
            if metadata.get('album_artist'):
                audio['aART'] = metadata['album_artist']
            if metadata.get('composer'):
                audio['\xa9wrt'] = metadata['composer']
            if metadata.get('year'):
                audio['\xa9day'] = metadata['year']
            if metadata.get('comment'):
                audio['\xa9cmt'] = metadata['comment']
            if metadata.get('album'):
                audio['\xa9alb'] = metadata['album']
            if metadata.get('track'):
                try:
                    audio['trkn'] = (int(metadata['track']), 0)
                except (ValueError, TypeError):
                    pass
            if metadata.get('series'):
                audio['\xa9grp'] = metadata['series']
            if metadata.get('series_part'):
                try:
                    audio['disk'] = (int(metadata['series_part']), 0)
                except (ValueError, TypeError):
                    pass
            if metadata.get('subtitle'):
                audio['\xa9dsc'] = metadata['subtitle']
            if metadata.get('narrator'):
                audio['----:com.apple.iTunes:NARRATOR'] = metadata['narrator'].encode('utf-8')
            if metadata.get('genre'):
                audio['\xa9gen'] = metadata['genre']
            if metadata.get('language'):
                audio['\xa9lng'] = metadata['language']
            if metadata.get('asin'):
                audio['----:com.apple.iTunes:ASIN'] = metadata['asin'].encode('utf-8')

            audio.save()
            return True
        except Exception as e:
            import traceback
            logger.error(f"Error writing M4A metadata: {e}\n{traceback.format_exc()}")
            return False
    
    def _write_flac(self, file_path: str, metadata: dict) -> bool:
        """Write FLAC metadata"""
        try:
            audio = FLAC(file_path)
            
            if metadata.get('title'):
                audio['TITLE'] = metadata['title']
            if metadata.get('artist'):
                audio['ARTIST'] = metadata['artist']
            if metadata.get('album_artist'):
                audio['ALBUMARTIST'] = metadata['album_artist']
            if metadata.get('composer'):
                audio['COMPOSER'] = metadata['composer']
            if metadata.get('year'):
                audio['YEAR'] = metadata['year']
            if metadata.get('comment'):
                audio['COMMENT'] = metadata['comment']
            if metadata.get('album'):
                audio['ALBUM'] = metadata['album']
            if metadata.get('track'):
                audio['TRACKNUMBER'] = metadata['track']
            if metadata.get('subtitle'):
                audio['SUBTITLE'] = metadata['subtitle']
            if metadata.get('series'):
                audio['SERIES'] = metadata['series']
            if metadata.get('series_part'):
                audio['SERIES_PART'] = metadata['series_part']
            if metadata.get('narrator'):
                audio['NARRATOR'] = metadata['narrator']
            if metadata.get('genre'):
                audio['GENRE'] = metadata['genre']
            if metadata.get('language'):
                audio['LANGUAGE'] = metadata['language']
            if metadata.get('asin'):
                audio['ASIN'] = metadata['asin']
            if metadata.get('publisher'):
                audio['PUBLISHER'] = metadata['publisher']
            if metadata.get('copyright'):
                audio['COPYRIGHT'] = metadata['copyright']

            audio.save()
            return True
        except Exception as e:
            logger.error(f"Error writing FLAC metadata: {e}")
            return False
    
    def _write_generic(self, file_path: str, metadata: dict) -> bool:
        """Generic metadata writer"""
        if file_path.endswith('.mp3'):
            return self._write_mp3(file_path, metadata)
        elif file_path.endswith(('.m4a', '.m4b')):
            return self._write_m4a(file_path, metadata)
        elif file_path.endswith('.flac'):
            return self._write_flac(file_path, metadata)
        return False

metadata_service = MetadataService()
