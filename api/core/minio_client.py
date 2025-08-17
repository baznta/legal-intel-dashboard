"""
MinIO client for document storage operations.
"""

from minio import Minio
from minio.error import S3Error
from fastapi import UploadFile
import structlog
from typing import Optional, Dict, Any
import io
import uuid

from core.config import settings

logger = structlog.get_logger()

# Initialize MinIO client
minio_client = Minio(
    settings.minio_endpoint,
    access_key=settings.minio_access_key,
    secret_key=settings.minio_secret_key,
    secure=settings.minio_secure,
    region="us-east-1"  # Default region
)

# Convenience functions
def download_file(object_name: str) -> Optional[bytes]:
    """Download a file from MinIO."""
    try:
        response = minio_client.get_object(settings.minio_bucket_name, object_name)
        file_content = response.read()
        response.close()
        response.release_conn()
        
        logger.info(f"File downloaded successfully: {object_name}")
        return file_content
        
    except S3Error as e:
        logger.error(f"MinIO download error for {object_name}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error downloading {object_name}: {e}")
        return None


class MinIOClient:
    """MinIO client wrapper with error handling and logging."""
    
    def __init__(self):
        self.client = minio_client
        self.bucket_name = settings.minio_bucket_name
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Ensure the bucket exists, create if it doesn't."""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"Created MinIO bucket: {self.bucket_name}")
            else:
                logger.info(f"MinIO bucket exists: {self.bucket_name}")
        except S3Error as e:
            logger.error(f"Failed to ensure bucket exists: {e}")
            raise
    
    def upload_file_object(
        self,
        file_object: UploadFile,
        object_name: str,
        file_size: int,
        content_type: Optional[str] = None
    ) -> bool:
        """Upload a file object to MinIO."""
        try:
            # Read file content
            file_content = file_object.read()
            
            # Create file-like object
            file_stream = io.BytesIO(file_content)
            
            # Upload to MinIO
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                data=file_stream,
                length=file_size,
                content_type=content_type or "application/octet-stream"
            )
            
            logger.info(f"File uploaded successfully: {object_name}")
            return True
            
        except S3Error as e:
            logger.error(f"MinIO upload error for {object_name}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error uploading {object_name}: {e}")
            return False
    
    def download_file(self, object_name: str) -> Optional[bytes]:
        """Download a file from MinIO."""
        try:
            response = self.client.get_object(self.bucket_name, object_name)
            file_content = response.read()
            response.close()
            response.release_conn()
            
            logger.info(f"File downloaded successfully: {object_name}")
            return file_content
            
        except S3Error as e:
            logger.error(f"MinIO download error for {object_name}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error downloading {object_name}: {e}")
            return None
    
    def delete_file(self, object_name: str) -> bool:
        """Delete a file from MinIO."""
        try:
            self.client.remove_object(self.bucket_name, object_name)
            logger.info(f"File deleted successfully: {object_name}")
            return True
            
        except S3Error as e:
            logger.error(f"MinIO delete error for {object_name}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting {object_name}: {e}")
            return False
    
    def get_file_info(self, object_name: str) -> Optional[Dict[str, Any]]:
        """Get file information from MinIO."""
        try:
            stat = self.client.stat_object(self.bucket_name, object_name)
            
            file_info = {
                "size": stat.size,
                "last_modified": stat.last_modified,
                "etag": stat.etag,
                "content_type": stat.content_type,
                "metadata": stat.metadata
            }
            
            logger.info(f"File info retrieved for: {object_name}")
            return file_info
            
        except S3Error as e:
            logger.error(f"MinIO stat error for {object_name}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting file info for {object_name}: {e}")
            return None
    
    def generate_presigned_url(
        self,
        object_name: str,
        method: str = "GET",
        expires: int = 3600
    ) -> Optional[str]:
        """Generate a presigned URL for file access."""
        try:
            url = self.client.presigned_url(
                method=method,
                bucket_name=self.bucket_name,
                object_name=object_name,
                expires=expires
            )
            
            logger.info(f"Presigned URL generated for: {object_name}")
            return url
            
        except S3Error as e:
            logger.error(f"MinIO presigned URL error for {object_name}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error generating presigned URL for {object_name}: {e}")
            return None
    
    def list_files(self, prefix: str = "", recursive: bool = True) -> list:
        """List files in the bucket with optional prefix."""
        try:
            objects = self.client.list_objects(
                bucket_name=self.bucket_name,
                prefix=prefix,
                recursive=recursive
            )
            
            file_list = [obj.object_name for obj in objects]
            logger.info(f"Listed {len(file_list)} files with prefix: {prefix}")
            return file_list
            
        except S3Error as e:
            logger.error(f"MinIO list error: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error listing files: {e}")
            return []
    
    def health_check(self) -> bool:
        """Check MinIO health."""
        try:
            # Try to list buckets
            self.client.list_buckets()
            return True
        except Exception as e:
            logger.error(f"MinIO health check failed: {e}")
            return False


# Global MinIO client instance
minio_client_instance = MinIOClient()


# Convenience functions
def upload_file_object(
    file_object: UploadFile,
    object_name: str,
    file_size: int,
    content_type: Optional[str] = None
) -> bool:
    """Upload a file object to MinIO."""
    return minio_client_instance.upload_file_object(
        file_object, object_name, file_size, content_type
    )


def download_file(object_name: str) -> Optional[bytes]:
    """Download a file from MinIO."""
    return minio_client_instance.download_file(object_name)


def delete_file(object_name: str) -> bool:
    """Delete a file from MinIO."""
    return minio_client_instance.delete_file(object_name)


def get_file_info(object_name: str) -> Optional[Dict[str, Any]]:
    """Get file information from MinIO."""
    return minio_client_instance.get_file_info(object_name)


def generate_presigned_url(
    object_name: str,
    method: str = "GET",
    expires: int = 3600
) -> Optional[str]:
    """Generate a presigned URL for file access."""
    return minio_client_instance.generate_presigned_url(object_name, method, expires)


def list_files(prefix: str = "", recursive: bool = True) -> list:
    """List files in the bucket with optional prefix."""
    return minio_client_instance.list_files(prefix, recursive)


def health_check() -> bool:
    """Check MinIO health."""
    return minio_client_instance.health_check() 