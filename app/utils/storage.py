from ..config.database import get_supabase_client
from fastapi import UploadFile, HTTPException
import uuid
import os
from typing import Optional

class StorageManager:
    def __init__(self, bucket_name: str = "documents"):
        self.bucket_name = bucket_name
        self._client = None

    @property
    def client(self):
        if not self._client:
            self._client = get_supabase_client(use_service_role=True)
        return self._client

    async def upload_file(
        self,
        file: UploadFile,
        company_id: str,
        custom_path: Optional[str] = None
    ) -> str:
        """
        Upload a file to Supabase Storage and return the path
        """
        try:
            # Validate file
            if not file or not file.filename:
                raise HTTPException(status_code=400, detail="Invalid file")

            # Create unique filename
            file_extension = os.path.splitext(file.filename)[1]
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            
            # Define storage path
            storage_path = custom_path or f"companies/{company_id}/{unique_filename}"
            
            # Read file content
            content = await file.read()
            
            # Upload to Supabase Storage
            result = self.client.storage\
                .from_(self.bucket_name)\
                .upload(
                    path=storage_path,
                    file=content,
                    file_options={"content-type": file.content_type}
                )

            if not result.data:
                raise HTTPException(status_code=500, detail="Failed to upload file")

            return storage_path

        except Exception as e:
            print(f"Error in upload_file: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def delete_file(self, storage_path: str) -> bool:
        """
        Delete a file from Supabase Storage
        """
        try:
            result = self.client.storage\
                .from_(self.bucket_name)\
                .remove([storage_path])

            return True if result.data else False

        except Exception as e:
            print(f"Error in delete_file: {str(e)}")
            return False

    def get_public_url(self, storage_path: str) -> str:
        """
        Get public URL for a file
        """
        try:
            result = self.client.storage\
                .from_(self.bucket_name)\
                .get_public_url(storage_path)

            return result

        except Exception as e:
            print(f"Error in get_public_url: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

# Create and export storage instance
storage = StorageManager()

__all__ = ['storage', 'StorageManager']  # Add both to exports