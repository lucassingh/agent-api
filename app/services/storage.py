import os
import uuid
from datetime import datetime
from typing import Optional
import aiofiles
from fastapi import UploadFile, HTTPException
import magic  # python-magic
from ..core.config import settings


class AudioStorageService:
    def __init__(self):
        self.audio_dir = "static/audio"
        os.makedirs(self.audio_dir, exist_ok=True)
    
    def _validate_audio_file(self, file: UploadFile) -> None:
        """Validate audio file size and type"""
        # Check file size
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to beginning
        
        if file_size > settings.MAX_AUDIO_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Max size is {settings.MAX_AUDIO_FILE_SIZE // (1024*1024)}MB"
            )
        
        # Check file type using magic
        allowed_types = settings.ALLOWED_AUDIO_TYPES
        
        # Read first bytes to detect type
        file_content = file.file.read(2048)
        file.file.seek(0)  # Reset to beginning
        
        try:
            mime_type = magic.from_buffer(file_content, mime=True)
            
            if mime_type not in allowed_types:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid file type: {mime_type}. Allowed types: {', '.join(allowed_types)}"
                )
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Could not determine file type: {str(e)}"
            )
    
    async def save_audio_file(self, file: UploadFile, user_id: int, incident_id: Optional[int] = None) -> str:
        """Save uploaded audio file and return its path"""
        print(f"DEBUG: Validando archivo: {file.filename}")
        self._validate_audio_file(file)
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Determine file extension from MIME type
        file_content = await file.read(2048)
        await file.seek(0)  # Reset to beginning
        
        print(f"DEBUG: Bytes leídos: {len(file_content)}")
        
        try:
            mime_type = magic.from_buffer(file_content, mime=True)
            print(f"DEBUG: MIME type detectado: {mime_type}")
        except Exception as e:
            print(f"DEBUG: Error detectando MIME: {e}")
            raise HTTPException(
                status_code=400,
                detail=f"Could not determine file type: {str(e)}"
            )
        
        file_extension = self._get_file_extension(mime_type, file.filename)
        print(f"DEBUG: Extensión: {file_extension}")
        
        filename = f"{user_id}_{timestamp}_{uuid.uuid4().hex[:8]}.{file_extension}"
        print(f"DEBUG: Nombre archivo: {filename}")
        
        # Create user directory if it doesn't exist
        user_dir = os.path.join(self.audio_dir, str(user_id))
        print(f"DEBUG: Directorio usuario: {user_dir}")
        
        os.makedirs(user_dir, exist_ok=True)
        
        file_path = os.path.join(user_dir, filename)
        print(f"DEBUG: Ruta completa: {file_path}")
        
        # Save file
        try:
            async with aiofiles.open(file_path, 'wb') as out_file:
                content = await file.read()
                print(f"DEBUG: Contenido a escribir: {len(content)} bytes")
                await out_file.write(content)
            print(f"DEBUG: Archivo guardado exitosamente")
        except Exception as e:
            print(f"DEBUG: Error escribiendo archivo: {e}")
            # Try to delete partially written file
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except:
                pass
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save file: {str(e)}"
            )
        
        return file_path
    
    def _get_file_extension(self, mime_type: str, original_filename: Optional[str] = None) -> str:
        """Map MIME type to file extension"""
        extensions = {
            "audio/mpeg": "mp3",
            "audio/mp3": "mp3",
            "audio/wav": "wav",
            "audio/x-wav": "wav",
            "audio/ogg": "ogg",
            "audio/oga": "oga",
            "audio/x-ms-wma": "wma",
            "audio/aac": "aac",
            "audio/flac": "flac",
            "audio/x-flac": "flac",
            "audio/x-m4a": "m4a",
            "audio/mp4": "m4a",
        }
        
        # Try to get extension from MIME type
        if mime_type in extensions:
            return extensions[mime_type]
        
        # Fallback to original filename extension
        if original_filename and '.' in original_filename:
            return original_filename.split('.')[-1].lower()
        
        # Default to mp3
        return "mp3"
    
    def get_audio_url(self, file_path: str) -> str:
        """Get URL for audio file"""
        # Remove 'static/' prefix for URL
        if file_path.startswith('static/'):
            return file_path[7:]  # Remove 'static/'
        return file_path
    
    def delete_audio_file(self, file_path: str) -> bool:
        """Delete audio file"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception:
            return False


# Crear instancia global
audio_storage = AudioStorageService()