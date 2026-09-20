"""Raw book files in S3-compatible storage, keyed by source id."""
from __future__ import annotations

import os
from pathlib import Path

import boto3
from botocore.exceptions import ClientError


def _client():
    return boto3.client(
        "s3",
        endpoint_url=os.environ.get("S3_ENDPOINT") or None,
        aws_access_key_id=os.environ.get("MINIO_ROOT_USER") or None,
        aws_secret_access_key=os.environ.get("MINIO_ROOT_PASSWORD") or None,
        region_name=os.environ.get("S3_REGION", "us-east-1"),
    )


def bucket() -> str:
    return os.environ.get("S3_BUCKET", "shepherd-books")


def ensure_bucket() -> None:
    c = _client()
    try:
        c.head_bucket(Bucket=bucket())
    except ClientError:
        c.create_bucket(Bucket=bucket())


def upload_book(source_id: str, path: Path) -> str:
    key = f"{source_id}/{path.name}"
    _client().upload_file(str(path), bucket(), key)
    return f"s3://{bucket()}/{key}"


def download(uri: str, dest_dir: Path) -> Path:
    assert uri.startswith("s3://"), uri
    b, key = uri[5:].split("/", 1)
    dest = dest_dir / Path(key).name
    _client().download_file(b, key, str(dest))
    return dest


def open_book(uri: str):
    """(streaming body, byte size) of a stored book, for serving it to a reader."""
    b, key = uri[5:].split("/", 1)
    obj = _client().get_object(Bucket=b, Key=key)
    return obj["Body"], obj["ContentLength"]


def delete(uri: str) -> None:
    b, key = uri[5:].split("/", 1)
    _client().delete_object(Bucket=b, Key=key)
