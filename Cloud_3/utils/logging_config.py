import logging
from pathlib import Path
from datetime import datetime


def configure_logging(name: str) -> logging.Logger:
    from config.settings import ROOT_DIR

    log_dir = ROOT_DIR / "logs"
    log_dir.mkdir(exist_ok=True)

    now = datetime.now()
    log_file = log_dir / f"{name}_{now.strftime('%Y-%m')}.log"

    logger = logging.getLogger(name)
    if logger.hasHandlers():
        logger.handlers.clear()
    logger.setLevel(logging.INFO)

    fh = logging.FileHandler(log_file, encoding="utf-8")
    sh = logging.StreamHandler()

    fmt = logging.Formatter("%(asctime)s %(levelname)-8s [%(name)s] %(message)s")
    for h in (fh, sh):
        h.setFormatter(fmt)
        logger.addHandler(h)

    return logger
