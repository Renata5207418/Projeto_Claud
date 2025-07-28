import logging
import sys
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
    # Se já tiver handlers, assume que já foi configurado e retorna
    if logger.handlers:
        return logger

    # Define o nível mínimo de captura de logs
    logger.setLevel(logging.INFO)

    # Formato das mensagens de log
    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 1) Handler de arquivo
    log_file = logs_dir / "bot_onvio.log"
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    # 2) Handler de console (stdout)
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    logger.addHandler(sh)

    return logger
