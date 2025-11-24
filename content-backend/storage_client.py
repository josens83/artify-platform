"""
Supabase Storage Client for managing assets (images, videos)
Handles upload, download, URL generation, and thumbnail creation
"""
import os
import hashlib
import mimetypes
from typing import Optional, Tuple
from datetime import timedelta
from io import BytesIO
from PIL import Image
import requests
import magic

from logger import get_logger

logger = get_logger("storage")

# File upload security configuration
ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
ALLOWED_VIDEO_EXTENSIONS = {'.mp4', '.mov', '.avi', '.webm'}
ALLOWED_MIME_TYPES = {
    'image/jpeg', 'image/png', 'image/gif', 'image/webp',
    'video/mp4', 'video/quicktime', 'video/x-msvideo', 'video/webm'
}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_IMAGE_SIZE = 5 * 1024 * 1024   # 5 MB


class StorageClient:
    """
    Client for managing file storage with Supabase Storage
    Falls back to local storage if Supabase is not configured
    """

    def __init__(self):
        """Initialize storage client"""
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
        self.storage_bucket = os.getenv("STORAGE_BUCKET", "artify-assets")
        self.local_storage_path = os.getenv("LOCAL_STORAGE_PATH", "./uploads")

        # Check if Supabase is configured
        self.use_supabase = bool(self.supabase_url and self.supabase_key)

        if self.use_supabase:
            self.storage_url = f"{self.supabase_url}/storage/v1"
            self.headers = {
                "apikey": self.supabase_key,
                "Authorization": f"Bearer {self.supabase_key}"
            }
            logger.info(f"StorageClient initialized with Supabase: {self.storage_bucket}")
        else:
            # Ensure local storage directory exists
            os.makedirs(self.local_storage_path, exist_ok=True)
            logger.warning("StorageClient using local storage (Supabase not configured)")

    def validate_file(
        self,
        file_data: bytes,
        file_name: str,
        file_type: str = "image"
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate file before upload

        Args:
            file_data: File bytes
            file_name: Original file name
            file_type: Expected file type (image, video)

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check file size
        file_size = len(file_data)
        max_size = MAX_IMAGE_SIZE if file_type == "image" else MAX_FILE_SIZE

        if file_size > max_size:
            return False, f"File size ({file_size / 1024 / 1024:.2f}MB) exceeds limit ({max_size / 1024 / 1024}MB)"

        if file_size == 0:
            return False, "File is empty"

        # Check file extension
        file_ext = os.path.splitext(file_name)[1].lower()
        allowed_extensions = ALLOWED_IMAGE_EXTENSIONS if file_type == "image" else ALLOWED_VIDEO_EXTENSIONS

        if file_ext not in allowed_extensions:
            return False, f"File extension '{file_ext}' not allowed. Allowed: {allowed_extensions}"

        # Detect actual MIME type using python-magic
        try:
            mime = magic.Magic(mime=True)
            detected_mime = mime.from_buffer(file_data)

            if detected_mime not in ALLOWED_MIME_TYPES:
                return False, f"File type '{detected_mime}' not allowed"

            # Verify MIME type matches expected type
            if file_type == "image" and not detected_mime.startswith("image/"):
                return False, f"Expected image file, got '{detected_mime}'"

            if file_type == "video" and not detected_mime.startswith("video/"):
                return False, f"Expected video file, got '{detected_mime}'"

            logger.debug(f"File validation passed: {file_name} ({detected_mime}, {file_size} bytes)")
            return True, None

        except Exception as e:
            logger.error(f"MIME type detection error: {str(e)}")
            return False, f"Could not verify file type: {str(e)}"

    def upload_file(
        self,
        file_data: bytes,
        file_name: str,
        content_type: str = None,
        folder: str = "creatives",
        validate: bool = True
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Upload file to storage with security validation

        Args:
            file_data: File bytes
            file_name: Original file name
            content_type: MIME type
            folder: Folder/prefix for organization
            validate: Whether to validate file (default: True)

        Returns:
            Tuple of (success, file_url, error_message)
        """
        try:
            # Validate file if enabled
            if validate:
                file_type = "image" if content_type and content_type.startswith("image") else "video"
                is_valid, error_msg = self.validate_file(file_data, file_name, file_type)

                if not is_valid:
                    logger.warning(f"File validation failed: {error_msg}")
                    return False, None, error_msg
            # Generate unique file name
            file_hash = hashlib.md5(file_data).hexdigest()[:12]
            file_ext = os.path.splitext(file_name)[1]
            unique_name = f"{file_hash}{file_ext}"
            file_path = f"{folder}/{unique_name}"

            # Detect content type if not provided
            if not content_type:
                content_type, _ = mimetypes.guess_type(file_name)
                if not content_type:
                    content_type = "application/octet-stream"

            if self.use_supabase:
                # Upload to Supabase Storage
                url = f"{self.storage_url}/object/{self.storage_bucket}/{file_path}"
                headers = {
                    **self.headers,
                    "Content-Type": content_type
                }

                response = requests.post(url, headers=headers, data=file_data)

                if response.status_code in [200, 201]:
                    # Get public URL
                    public_url = f"{self.supabase_url}/storage/v1/object/public/{self.storage_bucket}/{file_path}"
                    logger.info(f"File uploaded to Supabase: {file_path}")
                    return True, public_url, None
                else:
                    error_msg = f"Supabase upload failed: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    return False, None, error_msg

            else:
                # Save to local storage
                local_path = os.path.join(self.local_storage_path, folder)
                os.makedirs(local_path, exist_ok=True)

                full_path = os.path.join(local_path, unique_name)
                with open(full_path, 'wb') as f:
                    f.write(file_data)

                # Return relative URL (would need to be served by web server)
                local_url = f"/uploads/{folder}/{unique_name}"
                logger.info(f"File saved locally: {full_path}")
                return True, local_url, None

        except Exception as e:
            error_msg = f"File upload error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, None, error_msg

    def create_thumbnail(
        self,
        image_data: bytes,
        max_size: Tuple[int, int] = (300, 300),
        quality: int = 85
    ) -> Optional[bytes]:
        """
        Create thumbnail from image data

        Args:
            image_data: Original image bytes
            max_size: Maximum thumbnail dimensions (width, height)
            quality: JPEG quality (1-100)

        Returns:
            Thumbnail image bytes or None
        """
        try:
            # Open image
            img = Image.open(BytesIO(image_data))

            # Convert RGBA to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background

            # Create thumbnail
            img.thumbnail(max_size, Image.Resampling.LANCZOS)

            # Save to bytes
            output = BytesIO()
            img.save(output, format='JPEG', quality=quality, optimize=True)
            output.seek(0)

            logger.debug(f"Thumbnail created: {img.size}")
            return output.getvalue()

        except Exception as e:
            logger.error(f"Thumbnail creation error: {str(e)}", exc_info=True)
            return None

    def upload_with_thumbnail(
        self,
        image_data: bytes,
        file_name: str,
        folder: str = "creatives"
    ) -> Tuple[bool, Optional[str], Optional[str], Optional[str]]:
        """
        Upload image and create thumbnail

        Returns:
            Tuple of (success, main_url, thumbnail_url, error_message)
        """
        # Upload main image
        success, main_url, error = self.upload_file(
            image_data,
            file_name,
            content_type="image/jpeg",
            folder=folder
        )

        if not success:
            return False, None, None, error

        # Create and upload thumbnail
        thumbnail_data = self.create_thumbnail(image_data)
        if thumbnail_data:
            thumb_name = f"thumb_{file_name}"
            _, thumbnail_url, _ = self.upload_file(
                thumbnail_data,
                thumb_name,
                content_type="image/jpeg",
                folder=f"{folder}/thumbnails"
            )
        else:
            thumbnail_url = None

        return True, main_url, thumbnail_url, None

    def delete_file(self, file_url: str) -> bool:
        """
        Delete file from storage

        Args:
            file_url: File URL to delete

        Returns:
            Success boolean
        """
        try:
            if self.use_supabase:
                # Extract file path from URL
                # Format: https://xxx.supabase.co/storage/v1/object/public/{bucket}/{path}
                if "/object/public/" in file_url:
                    file_path = file_url.split(f"/object/public/{self.storage_bucket}/")[1]

                    url = f"{self.storage_url}/object/{self.storage_bucket}/{file_path}"
                    response = requests.delete(url, headers=self.headers)

                    if response.status_code in [200, 204]:
                        logger.info(f"File deleted from Supabase: {file_path}")
                        return True
                    else:
                        logger.error(f"Supabase delete failed: {response.status_code}")
                        return False
            else:
                # Delete from local storage
                # Extract local path from URL
                if file_url.startswith("/uploads/"):
                    local_path = os.path.join(
                        self.local_storage_path,
                        file_url.replace("/uploads/", "")
                    )
                    if os.path.exists(local_path):
                        os.remove(local_path)
                        logger.info(f"File deleted locally: {local_path}")
                        return True

            return False

        except Exception as e:
            logger.error(f"File deletion error: {str(e)}", exc_info=True)
            return False

    def generate_signed_url(
        self,
        file_path: str,
        expires_in: int = 3600
    ) -> Optional[str]:
        """
        Generate signed URL with expiration (Supabase only)

        Args:
            file_path: File path in storage
            expires_in: Expiration time in seconds

        Returns:
            Signed URL or None
        """
        if not self.use_supabase:
            logger.warning("Signed URLs only available with Supabase")
            return None

        try:
            url = f"{self.storage_url}/object/sign/{self.storage_bucket}/{file_path}"
            payload = {"expiresIn": expires_in}

            response = requests.post(url, headers=self.headers, json=payload)

            if response.status_code == 200:
                data = response.json()
                signed_path = data.get("signedURL")
                if signed_path:
                    full_url = f"{self.supabase_url}/storage/v1{signed_path}"
                    return full_url

            logger.error(f"Signed URL generation failed: {response.status_code}")
            return None

        except Exception as e:
            logger.error(f"Signed URL error: {str(e)}", exc_info=True)
            return None


# Singleton instance
_storage_client: Optional[StorageClient] = None


def get_storage_client() -> StorageClient:
    """Get or create storage client instance"""
    global _storage_client
    if _storage_client is None:
        _storage_client = StorageClient()
    return _storage_client
