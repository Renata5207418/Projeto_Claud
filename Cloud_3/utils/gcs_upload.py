from google.cloud import storage
from pathlib import Path
import logging

_log = logging.getLogger(__name__)
_storage = storage.Client()


def upload_file(local_path: Path, bucket: str, blob_name: str) -> str:
    """
    Envia 1 arquivo para gs://{bucket}/{blob_name}. Retorna a URL.
    """
    blob = _storage.bucket(bucket).blob(blob_name)
    blob.upload_from_filename(local_path)
    _log.info("Upload → gs://%s/%s", bucket, blob_name)
    return f"gs://{bucket}/{blob_name}"
