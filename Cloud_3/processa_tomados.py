import os
import time
import json
from datetime import datetime, timezone
import logging
from pathlib import Path
from config.settings import settings
from db.triage_consulta import set_tomados_concluido, claim_pendentes
from utils.tratamentos import (
    pattern_codservico, pattern_valor, pattern_data, pattern_cnpj, limpeza_cnpj,
    pattern_numero, soma_csrf
)
from utils.acumuladores import acumuladores
from utils.consulta_for import dados_fornecedor
from utils.tratamentos_csv import exe
from utils.gcs_upload import upload_file
from google.api_core import exceptions
from utils.document_ai import process_document

# Configura o logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
log = logging.getLogger("tomados")

SEPARADOS_DIR = Path(settings.separados_dir)
TEMPO_ESPERA = settings.tempo_espera
HEARTBEAT = Path(__file__).parent / "heartbeat.json"


def beat(msg: str = "ok"):
    """
    Atualiza (ou cria) heartbeat.json com timestamp UTC e mensagem.
    Útil para monitorar a saúde do processo externamente.
    """
    data = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "msg": msg,
    }
    HEARTBEAT.write_text(json.dumps(data))


def processar_empresa(empresa_pasta: Path):
    """
        Processa todos os PDFs na subpasta TOMADOS/ de `empresa_pasta`.

        Para cada PDF:
          1. Chama Document AI (`process_document`) para extrair entidades
          2. Aplica patterns para limpar CNPJ, datas, valores e códigos
          3. Consulta dados do prestador (`dados_fornecedor`) para obter
             razão_social, UF, município e CNAE
          4. Calcula `acumulador` via dicionário `acumuladores`
          5. Soma CSRF (PIS+COFINS+CSLL) com `soma_csrf`
          6. Monta `lista_csv` com todos os campos na ordem esperada
          7. Renomeia o PDF para incluir número da nota e razão_social
          8. Acumula linha CSV em `GERAL.txt` na pasta da empresa
          9. Aguarda `TEMPO_ESPERA` segundos antes do próximo PDF

        Ao final de todos os PDFs:
          - Gera CSV/TOMADOS por tomador via `csv_pipeline`
          - Faz upload de `GERAL.txt` e arquivos TXT para o bucket GCS
    """
    beat(f"empresa {empresa_pasta.name}")
    empresa_nome = empresa_pasta.name
    log.info(f"[{empresa_nome}] Iniciando processamento para empresa: {empresa_nome}")

    tomados_dir = empresa_pasta / 'TOMADOS'
    if not tomados_dir.exists() or not any(tomados_dir.glob("*.pdf")):
        log.info(f"[{empresa_nome}] Sem arquivos na pasta TOMADOS.")
        return

    csv_line = ''
    for arquivo in tomados_dir.glob("*.pdf"):
        log.info(f"[{empresa_nome}] Iniciando processamento do arquivo: {arquivo.name}")

        try:
            response = process_document(
                project_id=settings.gcloud_project_id,
                location=settings.gcloud_location,
                processor_id=settings.gcloud_processor_id,
                file_path=str(arquivo),
                mime_type="application/pdf",
                processor_version_id=settings.gcloud_processor_version_id
            )
            log.info(f"[{empresa_nome}] Documento {arquivo.name} processado com sucesso.")
        except exceptions.GoogleAPICallError as api_error:
            log.error(f"[{empresa_nome}] Erro de API Google ao processar '{arquivo.name}': {api_error}")
            continue
        except Exception as e:
            log.error(f"[{empresa_nome}] Erro geral ao processar '{arquivo.name}': {e}")
            continue

        prestador = pattern_cnpj(response.get('cnpj_prestador', ''))
        numero_nota = pattern_numero(response.get('numero_nota', ''))
        tomador = pattern_cnpj(response.get('cnpj_tomador', ''))
        valor_total = pattern_valor(response.get('valor_total', '0,00'))
        cod_servico = pattern_codservico(response.get('codigo_servico', ''))
        cofins = pattern_valor(response.get('cofins', '0,00'))
        data_emissao = pattern_data(response.get('data_emissao', ''))
        ir = pattern_valor(response.get('ir', '0,00'))
        pis = pattern_valor(response.get('pis', '0,00'))
        csll = pattern_valor(response.get('csll', '0,00'))
        inss = pattern_valor(response.get('valor_inss', '0,00'))

        prestador_clean = limpeza_cnpj(prestador)
        dados_prestador = dados_fornecedor(prestador_clean)
        acumulador = acumuladores.get(dados_prestador['cnae'], '')

        try:
            csrf = soma_csrf(pis, cofins, csll)
        except Exception as e:
            log.error(f"[{empresa_nome}] Erro ao calcular CSRF: {e}")
            csrf = soma_csrf('', '', '')

        lista_csv = [
            prestador, dados_prestador['razao_social'], dados_prestador['uf'], dados_prestador['municipio'], '',
            numero_nota, '', data_emissao, '0', acumulador, '',
            valor_total, '', valor_total, valor_total, '', '', '',
            ir, '', '', '', csrf, inss, '', '', '', tomador
        ]

        novo_nome = tomados_dir / f'{numero_nota} {dados_prestador["razao_social"]}-{os.urandom(3).hex()}.pdf'
        os.rename(arquivo, novo_nome)
        log.info(f"[{empresa_nome}] Arquivo {arquivo.name} renomeado para {novo_nome.name}")

        csv_line += ";".join(lista_csv) + '\n'

        # GERAL.txt NA PASTA DA EMPRESA
        with open(empresa_pasta / 'GERAL.txt', 'a', encoding='utf-8') as geral:
            geral.write(";".join(lista_csv) + '\n')
            log.info(f"[{empresa_nome}] Linha adicionada ao GERAL.txt")

        time.sleep(TEMPO_ESPERA)

    # 1) gera o(s) CSV localmente
    exe(csv_line, empresa_pasta)

    # 2) envia somente GERAL.txt
    geral_path = empresa_pasta / "GERAL.txt"
    if geral_path.exists():
        blob = f"{settings.gcs_prefix_resultados}/{empresa_nome}/{geral_path.name}"
        upload_file(geral_path, settings.gcs_bucket_tomados, blob)

    # 3) envia apenas arquivos que começam por TOMADOS* e são .txt
    for tomado in empresa_pasta.glob("TOMADOS*.*"):
        if tomado.suffix.lower() != ".txt":
            continue
        blob = f"{settings.gcs_prefix_resultados}/{empresa_nome}/{tomado.name}"
        upload_file(tomado, settings.gcs_bucket_tomados, blob)

    log.info("[%s] Processamento finalizado", empresa_nome)


def main():
    """
    Entry point para processamento em batch:

    1. Obtém lista de os_id pendentes (`tomados_status = 'Pendente'`)
    2. Para cada os_id, encontra a pasta `<os_id>-...` em SEPARADOS_DIR
    3. Se existir TOMADOS/ com PDFs, chama `processar_empresa`
    4. Após, marca `tomados_status = 'Concluído'` no DB
    """
    for os_id in claim_pendentes():
        # Procura a(s) pasta(s) correspondentes pelo padrão do nome
        pastas = [p for p in SEPARADOS_DIR.iterdir() if p.is_dir() and p.name.startswith(str(os_id))]
        for empresa_pasta in pastas:
            tomados_dir = empresa_pasta / "TOMADOS"
            if not tomados_dir.exists() or not any(tomados_dir.glob("*.pdf")):
                log.info(f"[{empresa_pasta.name}] Nenhum arquivo para processar.")
                continue
            # Processa os arquivos
            log.info(f"[{empresa_pasta.name}] Iniciando processamento dos arquivos na pasta.")
            processar_empresa(empresa_pasta)
            # Marca como processado no banco
            set_tomados_concluido(os_id)
            log.info(f"[{empresa_pasta.name}] Marcado como processado no banco.")


def processar_os_pubsub(os_id, pasta_nome):
    """
    Handler para o subscriber Pub/Sub:
    - Recebe os_id e pasta (nome da pasta)
    - Monta o Path da pasta e chama `processar_empresa`
    - Marca `tomados_status = 'Concluído'` após processamento
    """
    from pathlib import Path
    empresa_pasta = Path(settings.separados_dir) / pasta_nome
    if not empresa_pasta.exists():
        log.warning(f"Pasta {empresa_pasta} não encontrada para OS {os_id}")
        return
    processar_empresa(empresa_pasta)
    set_tomados_concluido(os_id)
    log.info(f"[{pasta_nome}] Marcado como processado no banco.")


if __name__ == "__main__":
    while True:
        beat("Aguardando novas solicitações")
        try:
            main()
            beat("Processamento concluído para todos os pendentes")
        except Exception as e:
            log.error("Falha ao processar os tomados: %s", e, exc_info=True)
            beat(f"Erro ao processar os tomados: {e}")

        log.info("Aguardando próximo ciclo...")
        time.sleep(30)
