import logging
import sys
from datetime import datetime
from config.settings import settings

# Diretório onde ficam todos os arquivos de log
logs_dir = settings.root_dir / "logs"
logs_dir.mkdir(parents=True, exist_ok=True)


def configure_logging(name: str = "onvio_rpa") -> logging.Logger:
    """
    Retorna um logger configurado com:
      • Nível INFO (ou superior)
      • FileHandler apontando para logs_dir/bot_onvio.log
      • StreamHandler para stdout

    Parâmetros:
      name: nome do logger (útil para separar logs por módulo)

    Uso:
      log = configure_logging(__name__)
      log.info("mensagem de teste")
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Adiciona mês/ano ao nome do log
    now = datetime.now()
    log_file = logs_dir / f"bot_onvio_{now.strftime('%Y-%m')}.log"
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    logger.addHandler(sh)

    return logger
