from selenium.common.exceptions import WebDriverException
import time
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from config.settings import settings
from utils.logging_config import configure_logging
from utils.helpers import espera_download, mover_arquivos, CSS
from scripts.login import run as do_login
from db import db, message_queue

log = configure_logging("download")

# ─── Constantes de estratégia ──────────────────────────────────────────
COOLDOWN_MIN = 15          # minutos entre retentativas
N_INICIAL = 10          # IDs visíveis que serão semeados no 1º run

HEARTBEAT = Path(__file__).resolve().parents[1] / "heartbeat.json"


def beat(msg: str = "ok", *, status: str = "idle"):
    HEARTBEAT.write_text(json.dumps({
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "status": status,
        "msg": msg,
    }, ensure_ascii=False))


# ─── Selenium helper ──────────────────────────────────────────────────
def get_driver() -> webdriver.Chrome:
    opts = Options()
    opts.add_argument(f"--user-data-dir={settings.chrome_profile}")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=opts)
    driver.maximize_window()
    return driver


# ─── Portal helpers ───────────────────────────────────────────────────
def abrir_os(driver: webdriver.Chrome, os_id: int) -> bool:
    campo = driver.find_element(By.CSS_SELECTOR, CSS["pesquisa"])
    campo.clear()
    campo.send_keys(str(os_id))
    time.sleep(3)
    try:
        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, CSS["detalhes"]))
        ).click()
        time.sleep(1.5)
        return True
    except Exception:
        log.info("OS %s ainda não disponível", os_id)
        return False


def fechar_os(driver):
    try:
        driver.find_element(By.CSS_SELECTOR, CSS["fechar"]).click()
        time.sleep(0.5)
    except Exception:
        pass


def ultimo_id_portal(driver) -> int:
    seletores = [
        "div.wj-cell.wj-state-active[data-qe-id^='col-identifier-row']",
        "tbody tr:first-child td:first-child",
    ]
    for css in seletores:
        try:
            el = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, css))
            )
            if (texto := el.text.strip()).isdigit():
                return int(texto)
        except Exception:
            continue
    raise RuntimeError("Não achei ID no grid.")


# ─── IDs visíveis no grid (máx n) ─────────────────────────────────────
def lista_ids_portal(driver, n: int) -> list[int]:
    seletores = [
        "div.wj-cell[data-qe-id^='col-identifier-row']",
        "tbody tr td:first-child"
    ]
    for sel in seletores:
        els = driver.find_elements(By.CSS_SELECTOR, sel)
        if els:
            return [int(e.text.strip()) for e in els[:n] if e.text.strip().isdigit()]
    return []


# ─── Semeadura (respeita banco) ───────────────────────────────────────
def semear_ids(driver):
    """
    • 1ª execução (DB vazio)  → grava até 10 IDs realmente visíveis.
    • Demais execuções        → grava apenas IDs > max_db.
    """
    try:
        topo = ultimo_id_portal(driver)          # maior ID visível agora
    except RuntimeError:
        beat("Grid não disponível ainda", status="idle")
        log.info("Grid não disponível; aguardando próximo ciclo")
        return

    ids_exist = db.list_by_status(("pendente", "aguardando", "sucesso", "falha"))

    # --- primeira execução ---------------------------------------------------
    if not ids_exist:
        visiveis = lista_ids_portal(driver, N_INICIAL)
        for os_id in visiveis:
            db.upsert_os(os_id, status="pendente")
        log.info("Primeira execução: semeados IDs %s", visiveis)
        return

    # --- execuções seguintes --------------------------------------------------
    max_db = max(ids_exist)
    if topo > max_db:
        novos = range(max_db + 1, topo + 1)
        for os_id in novos:
            db.upsert_os(os_id, status="pendente")
        log.info("Novos IDs semeados (%d)", len(novos))


# ─── Rotina de download ───────────────────────────────────────────────
def baixar_anexos(driver, os_id: int):
    if not abrir_os(driver, os_id):
        db.upsert_os(os_id, status="aguardando", last_try=datetime.now(timezone.utc))
        return
    apelido = None
    try:
        apelido = driver.find_element(By.CSS_SELECTOR, CSS["apelido"]).text.strip()
        beat(f"baixando {os_id}-{apelido}", status="running")

        resultados = []
        for elm in driver.find_elements(By.CSS_SELECTOR, CSS["anexos"]):
            antes = {p.name for p in settings.download_dir.iterdir()}
            driver.execute_script("arguments[0].click()", elm)
            resultados += espera_download(settings.download_dir, antes)

        pasta = f"{os_id}-{apelido}"
        destino = settings.baixados_dir / pasta
        mover_arquivos(resultados, destino)

        assunto = driver.find_element(By.CSS_SELECTOR, CSS["assunto"]).text.strip()
        descricao = driver.find_element(By.CSS_SELECTOR, CSS["descricao"]).text.strip()
        with open(destino / "!!!ABRA_MENSAGEM_DO_CLIENTE!!!.txt", "w", encoding="utf-8") as f:
            f.write(f"Assunto: {assunto}\nDetalhe: {descricao}")

        destino_sep = settings.separados_dir / pasta
        if destino_sep.exists():
            shutil.rmtree(destino_sep)
        shutil.copytree(destino, destino_sep)

        db.mark_status(os_id, "sucesso", extra=dict(
            apelido=apelido, assunto=assunto, descricao=descricao,
            anexos_total=len(resultados)))
        message_queue.publish(os_id)

    except Exception as exc:
        log.error("Erro na OS %s", os_id, exc_info=True)
        extra = {"apelido": apelido} if apelido else None
        db.mark_status(os_id, "falha", inc_try=True, extra=extra)
    finally:
        fechar_os(driver)
        for f in settings.download_dir.iterdir():
            if f.is_file():
                f.unlink()


# ─── Resiliência (buracos apenas min_db..max_db) ──────────────────────
def reenfileirar_lacunas():
    todos = db.list_by_status(("pendente", "sucesso", "falha", "aguardando"))
    if not todos:
        return
    min_id, max_id = min(todos), max(todos)
    faltantes = set(range(min_id, max_id + 1)) - set(todos)
    for os_id in faltantes:
        db.upsert_os(os_id, status="pendente")
    if faltantes:
        log.info("Lacunas detectadas → %d reinseridos", len(faltantes))


# ─── Loop principal ───────────────────────────────────────────────────
def loop_download():
    with get_driver() as driver:
        do_login(driver)

        semear_ids(driver)                           # seed / avanço

        for os_id in db.list_by_status(("pendente",)):
            baixar_anexos(driver, os_id)

        for os_id in db.list_for_retry("aguardando", settings.max_attempts, COOLDOWN_MIN):
            baixar_anexos(driver, os_id)

        for os_id in db.list_for_retry("falha", settings.max_attempts, COOLDOWN_MIN):
            baixar_anexos(driver, os_id)


# ─── Main ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    db.init_db()
    log.info("Bot de download iniciado")

    while True:
        beat("Aguardando novas solicitações", status="idle")
        try:
            loop_download()
        except Exception as e:
            log.exception("Falha inesperada no loop")
            user_msg = (e.msg.split("Stacktrace:")[0].strip()
                        if isinstance(e, WebDriverException) and getattr(e, "msg", None)
                        else str(e).splitlines()[0])
            beat(f"Erro: {user_msg}", status="error")

        time.sleep(settings.sleep_seconds)
