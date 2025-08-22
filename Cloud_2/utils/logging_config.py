import logging
from datetime import datetime
from pathlib import Path


def configure_logging(name: str) -> logging.Logger:
    """
       Cria e retorna um logger configurado.

       Parâmetros:
         name: nome do logger (usado no logger e no nome do arquivo de log)

       Comportamento:
         1. Determina `log_dir` como a pasta "logs" na raiz do projeto.
         2. Garante que `log_dir` exista.
         3. Cria um logger com nível INFO.
         4. Adiciona:
            - FileHandler em `logs/<name>.log`
            - StreamHandler para saída no console
         5. Aplica formato padrão: timestamp, nível, nome e mensagem.

       Uso:
         log = configure_logging("triagem_worker")
         log.info("Mensagem de log")
    """
    project_root = Path(__file__).resolve().parents[1]
    log_dir = project_root / "logs"
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
