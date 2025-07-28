from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


# Raiz do projeto: pasta acima de “config/”
ROOT_DIR = Path(__file__).resolve().parents[1]
# Carrega variáveis de ambiente definidas em .env (não versionado)
load_dotenv(ROOT_DIR / ".env")


class Settings(BaseSettings):
    """
    Modelo de configurações com validação automática:
      • Tipos fortemente tipados (Path, int, str)
      • Leitura de aliases de variáveis de ambiente
      • Ignora chaves extras em .env
    """
    queue_db_path: Path = Field(..., alias="QUEUE_DB_PATH")
    separados_dir: Path = Field(..., alias="SEPARADOS_DIR")
    clientes_dir: Path = Field(..., alias="CLIENTES_DIR")
    testes_dir: Path = Field(..., alias="TESTES_DIR")
    pubsub_topic_cloud3: str = Field(..., alias="PUBSUB_TOPIC_CLOUD3")
    pubsub_project_id: str = Field(..., alias="PUBSUB_PROJECT_ID")
    gcs_bucket_tomados: str = Field(..., alias="GCS_BUCKET_TOMADOS")
    gcs_prefix_tomados: str = Field(..., alias="GCS_PREFIX_TOMADOS")
    triage_db_path: Path = ROOT_DIR / "triage_status.db"
    max_attempts: int = 3
    sleep_seconds: int = 10

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
settings.separados_dir.mkdir(parents=True, exist_ok=True)
