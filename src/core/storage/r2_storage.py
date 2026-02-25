import os
from .r2_client import get_r2_client
from io import BytesIO


class R2StorageService:
    def __init__(self):
        self.client = get_r2_client()
        self.bucket = os.getenv("R2_BUCKET_NAME")
        self.public_url = os.getenv("R2_PUBLIC_URL")

    def upload_bytes(
        self,
        content: bytes,
        key: str,
        content_type: str = "application/pdf",
    ) -> str:
        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=BytesIO(content),
            ContentType=content_type,
        )
        return f"{self.public_url}/{key}"