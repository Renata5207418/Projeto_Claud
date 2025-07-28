from pathlib import Path
from dotenv import load_dotenv
import os

ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / ".env")


class Settings:
    """
        Contém todas as configurações lidas do ambiente.

        Atributos:
          triage_db_path (Path)      – SQLite com status de triagem (triagem_db_path).
          separados_dir (Path)       – pasta de entrada com subpastas “ID-APELIDO”.
          gcloud_project_id (str)    – ID do projeto GCP para Document AI e GCS.
          gcloud_location (str)      – região do serviço Document AI (ex.: "us").
          gcloud_processor_id (str) – ID do Document AI processor.
          gcloud_processor_version_id (str) – versão do processor.
          gcs_bucket_tomados (str)   – bucket onde gravar PDFs ‘tomados’.
          gcs_prefix_resultados (str)– subpasta no bucket (default: "tomados_saida").
          google_application_credentials (Path) – arquivo JSON de credenciais ADC.
          gcloud_mime_type (str)     – MIME type (ex.: "application/pdf").
          page_selector (list[int]) – lista de páginas a processar (ex.: [1,3,5]).
          tempo_espera (int)         – segundos entre requisições ao Document AI.
    """
    triage_db_path = Path(os.getenv("TRIAGE_DB_PATH"))
    separados_dir = Path(os.getenv("SEPARADOS_DIR"))
    gcloud_project_id = os.getenv("GCLOUD_PROJECT_ID")
    gcloud_location = os.getenv("GCLOUD_LOCATION")
    gcloud_processor_id = os.getenv("GCLOUD_PROCESSOR_ID")
    gcloud_processor_version_id = os.getenv("GCLOUD_PROCESSOR_VERSION_ID")
    gcs_bucket_tomados = os.getenv("GCS_BUCKET_TOMADOS")
    gcs_prefix_resultados = os.getenv("GCS_PREFIX_RESULTADOS", "tomados_saida")
    google_application_credentials = Path(os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
    gcloud_mime_type = os.getenv("GCLOUD_MIME_TYPE")
    page_selector = [int(x) for x in os.getenv("PAGE_SELECTOR", "1").split(",")]
    tempo_espera = int(os.getenv("TEMPO_ESPERA", "16"))


settings = Settings()
