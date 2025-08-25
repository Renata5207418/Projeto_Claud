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
    """
        Retorna True se existir pelo menos 1 objeto com ESTE PREFIXO.
        Use:
          - any_blob(bucket, f"{prefix}/GERAL.txt")   -> checa GERAL.txt (quase-exato)
          - any_blob(bucket, f"{prefix}/TOMADOS")     -> checa TOMADOS*.txt
    """
    return any(True for _ in _storage.bucket(bucket).list_blobs(prefix=prefix, max_results=1))


def upload_permitidos(empresa_pasta: Path, bucket: str, gcs_prefix: str) -> int:
    """
    Envia apenas GERAL.txt e TOMADOS*.txt. Retorna quantos TOMADOS*.txt foram enviados.
    """
    enviados_tomados = 0

    # Envia GERAL.txt se existir
    geral = empresa_pasta / "GERAL.txt"
    if geral.exists():
        upload_file(geral, bucket, f"{gcs_prefix}/{geral.name}")

    # Envia apenas TOMADOS*.txt
    for p in empresa_pasta.glob("TOMADOS*.txt"):
        upload_file(p, bucket, f"{gcs_prefix}/{p.name}")
        enviados_tomados += 1

    return enviados_tomados
