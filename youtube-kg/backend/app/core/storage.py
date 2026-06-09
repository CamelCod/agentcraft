import io
from functools import lru_cache

import boto3
from botocore.client import Config

from app.config import get_settings

settings = get_settings()


@lru_cache
def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=f"{'https' if settings.minio_secure else 'http'}://{settings.minio_endpoint}",
        aws_access_key_id=settings.minio_access_key,
        aws_secret_access_key=settings.minio_secret_key,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )


def upload_bytes(bucket: str, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
    get_s3_client().put_object(Bucket=bucket, Key=key, Body=data, ContentType=content_type)
    return key


def upload_file(bucket: str, key: str, file_path: str) -> str:
    get_s3_client().upload_file(file_path, bucket, key)
    return key


def download_bytes(bucket: str, key: str) -> bytes:
    response = get_s3_client().get_object(Bucket=bucket, Key=key)
    return response["Body"].read()


def get_presigned_url(bucket: str, key: str, expires_in: int = 3600) -> str:
    return get_s3_client().generate_presigned_url(
        "get_object", Params={"Bucket": bucket, "Key": key}, ExpiresIn=expires_in
    )


def delete_object(bucket: str, key: str) -> None:
    get_s3_client().delete_object(Bucket=bucket, Key=key)
