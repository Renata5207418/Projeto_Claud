import time
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from config.settings import settings
from utils.logging_config import configure_logging
from utils.helpers import espera_download, mover_arquivos, CSS, formatar_erro_usuario
from scripts.login import run as do_login
from db import db, message_queue

log = configure_logging("download")

# ─── Constantes de estratégia ──────────────────────────────────────────
COOLDOWN_MIN = 15          # minutos entre retentativas
N_INICIAL = 10          # IDs visíveis que serão semeados no 1º run
MOTIVO_EXCESSO = "excesso de anexos"
LIMITE_ANEXOS = 60

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
    opts.add_argument("--disable-popup-blocking")
    opts.add_argument("--safebrowsing-disable-download-protection")

    chrome_prefs = {
        "download.prompt_for_download": False,
        "directory_upgrade": True,
        "safebrowsing.enabled": True,
        "profile.default_content_setting_values.automatic_downloads": 1,

    }
    opts.add_experimental_option("prefs", chrome_prefs)

    driver = webdriver.Chrome(options=opts)
    driver.maximize_window()
    return driver


# ─── Portal helpers ───────────────────────────────────────────────────
def abrir_os(driver: webdriver.Chrome, os_id: int) -> bool:
    campo = driver.find_element(By.CSS_SELECTOR, CSS["pesquisa"])
    campo.clear()
    campo.send_keys(str(os_id), Keys.ENTER)        # força o filtro

    try:
        # ── 1) ESPERA a primeira célula da grade mostrar o ID solicitado
        WebDriverWait(driver, 6).until(
            lambda d: (
                    d.find_element(By.CSS_SELECTOR,
                                   "div[data-qe-id='col-identifier-row-0']")
                    .text.strip() == str(os_id)
            )
        )

        # ── 2) SÓ AGORA clica no ícone de detalhes
        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, CSS["detalhes"]))
        ).click()
        time.sleep(1.5)
        return True

    except Exception:
        log.info("OS %s ainda não disponível – grid não retornou a linha.", os_id)
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
    first_seed_min = settings.first_seed_min_id

    # --- primeira execução ---------------------------------------------------
    if not ids_exist:
        if first_seed_min:
            if topo < first_seed_min:
                log.warning(
                    "first_seed_min_id=%d é maior que o topo atual (%d). "
                    "Nada para semear neste ciclo.", first_seed_min, topo)
                return
            novos = range(first_seed_min, topo + 1)
        else:
            novos = lista_ids_portal(driver, N_INICIAL)

        for os_id in novos:
            db.upsert_os(os_id, status="pendente")

        log.info("Primeira execução: semeados IDs de %s a %s",
                 novos[0], novos[-1])
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
    # 0. Limpa pasta de download antes de começar
    for f in settings.download_dir.iterdir():
        if f.is_file():
            f.unlink()

    # 0.1 Tenta abrir OS
    if not abrir_os(driver, os_id):
        db.mark_status(os_id, "aguardando", inc_try=True)
        return

    apelido = None
    try:
        apelido = driver.find_element(By.CSS_SELECTOR, CSS["apelido"]).text.strip()
        beat(f"baixando {os_id}-{apelido}", status="running")

        # 1. Conta anexos
        anexos = driver.find_elements(By.CSS_SELECTOR, CSS["anexos"])
        qtd_anexos = len(anexos)
        log.info("OS %s: %d anexos detectados", os_id, qtd_anexos)

        # 1.1 Limite de anexos
        if qtd_anexos > LIMITE_ANEXOS:
            db.mark_status(os_id, "falha", inc_try=False,
                           extra={"apelido": apelido, "motivo": MOTIVO_EXCESSO})  # NEW
            fechar_os(driver)
            log.warning("OS %s excedeu limite, pulando.", os_id)
            return

        resultados = []

        # 2. Download de cada anexo  (re-localiza o elemento a cada volta)  # NEW
        for idx in range(1, qtd_anexos + 1):
            elm = driver.find_elements(By.CSS_SELECTOR, CSS["anexos"])[idx - 1]
            antes = {p.name for p in settings.download_dir.iterdir()}
            driver.execute_script("arguments[0].click()", elm)
            novos = espera_download(settings.download_dir, antes, post_delay=2)
            log.info("OS %s: anexo %d/%d baixado: %s", os_id, idx, qtd_anexos, novos)
            resultados += novos

        # 3. Espera terminar (.crdownload ou .tmp)                       # NEW
        max_wait = max(200, qtd_anexos * 10)      # timeout proporcional  # NEW
        waited = 0
        while any(f.suffix in (".crdownload", ".tmp") for f in settings.download_dir.iterdir()):
            time.sleep(1)
            waited += 1
            if waited > max_wait:
                raise Exception("Timeout > {} s esperando downloads".format(max_wait))

        # 4. Confere quantidade
        arquivos_baixados = [f for f in settings.download_dir.iterdir()
                             if f.is_file() and f.suffix not in (".crdownload", ".tmp")]
        if len(arquivos_baixados) != qtd_anexos:
            db.mark_status(os_id, "falha", inc_try=True, extra={"apelido": apelido})
            raise Exception("Quant. baixada ({}) ≠ esperada ({})".format(
                len(arquivos_baixados), qtd_anexos))

        # 5. Move para pasta destino
        pasta = f"{os_id}-{apelido}"
        destino = settings.baixados_dir / pasta
        mover_arquivos(arquivos_baixados, destino)

        # 6. Gera TXT com assunto e descrição
        assunto = driver.find_element(By.CSS_SELECTOR, CSS["assunto"]).text.strip()
        descricao = driver.find_element(By.CSS_SELECTOR, CSS["descricao"]).text.strip()
        with open(destino / "!!!ABRA_MENSAGEM_DO_CLIENTE!!!.txt", "w", encoding="utf-8") as f:
            f.write(f"Assunto: {assunto}\nDetalhe: {descricao}")

        # 7. Cópia para pasta “separados”
        destino_sep = settings.separados_dir / pasta
        if destino_sep.exists():
            shutil.rmtree(destino_sep)
        shutil.copytree(destino, destino_sep)

        # 8. Atualiza status + fila
        db.mark_status(os_id, "sucesso", extra=dict(
            apelido=apelido, assunto=assunto, descricao=descricao,
            anexos_total=len(arquivos_baixados)))
        message_queue.publish(os_id)

    except Exception as exc:
        log.error("Erro na OS %s", os_id, exc_info=True)
        extra = {"apelido": apelido, "motivo": str(exc)} if apelido else {"motivo": str(exc)}
        db.mark_status(os_id, "falha", inc_try=True, extra=extra)

    finally:
        fechar_os(driver)
        # Limpa o download_dir pós-processamento
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
        semear_ids(driver)
        reenfileirar_lacunas()

        for os_id in db.list_by_status(("pendente",)):
            baixar_anexos(driver, os_id)
            time.sleep(2)

        for os_id in db.list_for_retry("aguardando", settings.max_attempts, COOLDOWN_MIN):
            baixar_anexos(driver, os_id)
            time.sleep(2)

        for os_id in db.list_for_retry("falha", settings.max_attempts, COOLDOWN_MIN):
            motivo = db.get_motivo(os_id)
            if motivo and MOTIVO_EXCESSO in motivo.lower():
                continue
            baixar_anexos(driver, os_id)
            time.sleep(2)


# ─── Main ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    db.init_db()
    log.info("Bot iniciado – first_seed_min_id=%s", settings.first_seed_min_id)
    log.info("Bot de download iniciado")

    while True:
        beat("Aguardando novas solicitações", status="idle")
        try:
            loop_download()
        except Exception as e:
            log.exception("Falha inesperada no loop")
            user_msg = formatar_erro_usuario(e)
            beat(f"Erro: {user_msg}", status="error")

        total_sleep = settings.sleep_seconds
        interval = 30
        slept = 0
        while slept < total_sleep:
            time.sleep(min(interval, total_sleep - slept))
            slept += interval
            beat("Aguardando novas solicitações", status="idle")
