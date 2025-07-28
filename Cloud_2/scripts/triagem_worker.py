import time
import json
from datetime import datetime, timezone
from pathlib import Path
from config.settings import settings
from utils.logging_config import configure_logging
from db.triagem_db import (
    list_download_ids,
    list_separacao_ids,
    register_separacao,
    extrair_apelido,
    set_triagem_status,
)
from db.queue_client import pull_one, requeue
from db import triagem_db
from scripts import triagem

log = configure_logging("triage")
triagem_db.init()
HEARTBEAT = Path(__file__).resolve().parents[1] / "heartbeat.json"


def beat(msg: str = "ok"):
    """Atualiza o arquivo de heartbeat."""
    data = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "msg": msg,
    }
    HEARTBEAT.write_text(json.dumps(data))


def seed_missing() -> None:
    """Enfileira OS baixadas mas ainda não processadas."""
    baixados = set(list_download_ids())
    processados = set(list_separacao_ids())
    pendentes = sorted(baixados - processados)
    for os_id in pendentes:
        requeue(os_id)
    log.info("✓ Seed inicial: enfileiradas %d OS pendentes", len(pendentes))


# ─────────────────────────────────────────────────────────────────────────────
# Processamento de uma única OS
# ─────────────────────────────────────────────────────────────────────────────
def process_os(job_id: int) -> None:
    """Processa uma única OS conforme job_id."""
    pasta_entry = next(
        (p for p in settings.separados_dir.iterdir() if p.name.startswith(f"{job_id}-")),
        None,
    )
    if not pasta_entry:
        raise FileNotFoundError(f"Pasta {job_id}-??? não encontrada em {settings.separados_dir}")

    # --- SKIP: já existe processamento_concluido.txt ---
    status_file = pasta_entry / "processamento_concluido.txt"
    if status_file.exists():
        log.info("Skip OS %s: achou %s", job_id, status_file.name)
        apelido = extrair_apelido(pasta_entry.name)

        set_triagem_status(
            job_id,
            "Triada",
            extra=dict(
                gerou_tomados=int((pasta_entry / "TOMADOS").exists()),
                gerou_extrato=int((pasta_entry / "EXTRATO").exists()),
                cliente_path="já processado (TXT)",
            ),
        )
        register_separacao(
            os_id=job_id,
            pasta=apelido,
            pasta_cliente="já processado (TXT)",
            tomados="SIM" if (pasta_entry / "TOMADOS").exists() else "NÃO",
            extrato="SIM" if (pasta_entry / "EXTRATO").exists() else "NÃO",
        )
        return

    # --- PROCESSA de verdade ---
    set_triagem_status(job_id, "processando")
    try:
        triagem.exe(pasta_entry.name)
        cliente_path = triagem.mover_cliente(pasta_entry.name)
        apelido = extrair_apelido(pasta_entry.name)

        set_triagem_status(
            job_id,
            "Triada",
            extra=dict(
                gerou_tomados=int((pasta_entry / "TOMADOS").exists()),
                gerou_extrato=int((pasta_entry / "EXTRATO").exists()),
                cliente_path=cliente_path,
            ),
        )
        register_separacao(
            os_id=job_id,
            pasta=apelido,
            pasta_cliente=cliente_path,
            tomados="SIM" if (pasta_entry / "TOMADOS").exists() else "NÃO",
            extrato="SIM" if (pasta_entry / "EXTRATO").exists() else "NÃO",
        )
        return

    except Exception as e:
        log.error("Falha na OS %s: %s", job_id, e, exc_info=True)
        tent = triagem_db.get_tentativas(job_id) + 1
        set_triagem_status(job_id, "falha", inc_try=True)
        if tent < settings.max_attempts:
            requeue(job_id)


if __name__ == "__main__":
    log.info("Worker Cloud_2 iniciado")
    seed_missing()
    while True:
        job_id = pull_one()
        if job_id is None:
            beat("Aguardando novas solicitações")
            time.sleep(settings.sleep_seconds)
            continue

        # Encontra o nome da pasta para o log antes de processar
        pasta_entry = next((p for p in settings.separados_dir.iterdir() if p.name.startswith(f"{job_id}-")), None)
        if pasta_entry:
            beat(f"Processando {pasta_entry.name}")
            process_os(job_id)
            beat(f"Concluído {pasta_entry.name}")
        else:
            log.warning("Job %d recebido, mas a pasta correspondente não foi encontrada. Ignorando.", job_id)
            beat(f"Erro: pasta para job {job_id} não encontrada")

        time.sleep(0.1)
