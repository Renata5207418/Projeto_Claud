from pathlib import Path
from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# ------------------------------------------------------
# 1) Determina raiz do projeto e carrega .env
# ------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parents[1]
# Carrega TODAS as chaves definidas em ROOT_DIR/.env para as variáveis de ambiente
load_dotenv(ROOT_DIR / ".env")


class Settings(BaseSettings):
    """
    Classe de configuração central, com:
      • credenciais de acesso (ONVIO_USER, ONVIO_PASS)
      • caminhos de diretório (DOWNLOAD_DIR, BAIXADOS_DIR, SEPARADOS_DIR)
      • outras constantes (sleep_seconds, max_attempts, portal_url etc.)
    """
    onvio_user: str = Field(..., alias="ONVIO_USER")
    onvio_pass: str = Field(..., alias="ONVIO_PASS")

    # ——— URL do portal
    portal_url: str = (
        "https://onvio.com.br/br-portal-do-cliente/service-requesting/general"
    )

    download_dir: Path = Field(..., alias="DOWNLOAD_DIR")
    baixados_dir: Path = Field(..., alias="BAIXADOS_DIR")
    separados_dir: Path = Field(..., alias="SEPARADOS_DIR")

    root_dir: Path = ROOT_DIR
    chrome_profile: Path = ROOT_DIR / ".chrome_profile"
    db_path: Path = ROOT_DIR / "os_status.db"

    sleep_seconds: int = 200
    max_attempts: int = 3

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
# ------------------------------------------------------
# 2) Cria automaticamente as pastas necessárias
#    (evita erro “diretório não encontrado” em tempo de execução)
# ------------------------------------------------------
for p in (settings.download_dir,
          settings.baixados_dir,
          settings.separados_dir,
          settings.chrome_profile):
    p.mkdir(parents=True, exist_ok=True)
