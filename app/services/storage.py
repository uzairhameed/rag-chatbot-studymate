import os
from pathlib import Path
from typing import BinaryIO
from uuid import uuid4

import boto3
from dotenv import load_dotenv

load_dotenv()

AWS_REGION=os.getenv("AWS_REGION")
S3_BUCKET_NAME=os.getenv("S3_BUCKET_NAME")

if not AWS_REGION:
    raise RuntimeError("AWS_REGION is missing from the environment")
if not S3_BUCKET_NAME:
    raise RuntimeError("S3_BUCKET_NAME is missing from the environment")

# Boto3 finds credentials through the AWS CLI configuration, not this project.
s3_client=boto3.client("s3", region_name=AWS_REGION)


def build_storage_key(room_id: int, filename: str) -> str:
    """Create a unique S3 path while keeping the file extension."""
    extension = Path(filename).suffix.lower()
    return f"rooms/{room_id}/files/{uuid4().hex}{extension}"


def upload_fileobj(
        file_obj: BinaryIO,
        storage_key: str,
        content_type: str | None =None,
) -> None:
    """Upload a file stream to S3 under the provided object key"""
    s3_client.upload_fileobj(
        file_obj,
        S3_BUCKET_NAME,
        storage_key,
        ExtraArgs={
            "ContentType": content_type or "application/octet-stream",
        },
    )

def download_fileobj(storage_key: str, file_obj: BinaryIO) -> None:
    """Write an S3 object into a file stream for later processing."""
    s3_client.download_fileobj(
        S3_BUCKET_NAME,
        storage_key,
        file_obj,
    )