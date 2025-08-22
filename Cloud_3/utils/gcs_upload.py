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


def any_blob(bucket: str, prefix: str) -> bool:
    return any(True for _ in _storage.bucket(bucket).list_blobs(prefix=prefix, max_results=1))


def upload_txt_dir(local_dir: Path, bucket: str, dest_prefix: str) -> int:
    if not dest_prefix.endswith("/"):
        dest_prefix += "/"
    count = 0
    for txt in local_dir.glob("*.txt"):
        upload_file(txt, bucket, dest_prefix + txt.name)
        count += 1
    _log.info("Upload dir → %s arquivo(s) de %s para gs://%s/%s", count, local_dir, bucket, dest_prefix)
    return count
