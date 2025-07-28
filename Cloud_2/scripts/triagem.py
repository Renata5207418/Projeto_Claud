import time
import datetime
import requests
import logging
import rarfile
import base64
import os
import shutil
import PyPDF2
import io
import random
from config.settings import settings
from datetime import date
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from utils.extensoes import organiza_extensao
from utils.logging_config import configure_logging
from utils.extract import scan_e_extraia_recursivo, extrair_arquivos_compactados
from functools import wraps
from requests.exceptions import HTTPError, Timeout as ReqTimeout
from zipfile import BadZipFile
from PyPDF2.errors import PdfReadError
from dateutil.relativedelta import relativedelta
from db.banco_dominio import obter_codigo_empresa
from db.triagem_db import init as triagem_init


# ────────────────────────────────────────────────────────────────────────────
# Configuração inicial
# ────────────────────────────────────────────────────────────────────────────
log = configure_logging("bot_triagem")
root = logging.getLogger()
if not root.handlers:
    for h in log.handlers:
        root.addHandler(h)
root.setLevel(log.level)

triagem_init()

# Caminhos principais (vêm de settings/.env)
rarfile.UNRAR_TOOL = r"C:\Program Files\WinRAR\UnRAR.exe"
BASE_CLIENTES = str(settings.clientes_dir)
BASE_TRIAGEM = str(settings.separados_dir)
BASE_TESTES = str(settings.testes_dir)

# Mapeamento de tipos para pastas finais
PASTAS = {
    'guia': 'DOCUMENTOS GERAIS',
    'boleto': 'DOCUMENTOS GERAIS',
    'invoice_exterior': 'INVOICE',
    'fatura_consumo': 'DOCUMENTOS GERAIS',
    'comprovante_pagamento': 'DOCUMENTOS GERAIS',
    'danfe': 'DANFE',
    'nota_servico': 'TOMADOS',
    'extrato': 'EXTRATO'
}
TOMADOS_DIR = 'TOMADOS'
LOW_CONFIDENCE_DIR = 'LOW_CONFIDENCE'
ERRO_PROCESSAMENTO_DIR = 'ERRO_PROCESSAMENTO'
LIMITE_PAGINAS_DIR = 'LIMITE_PAGINAS'


# ────────────────────────────────────────────────────────────────────────────
# Decorator de logging e tratamento de exceções
# ────────────────────────────────────────────────────────────────────────────
def log_and_handle_exceptions(func):
    """
    Envolve funções de processamento para:
      - Logar início e fim em INFO
      - Capturar erros HTTP, de compactação e leitura de PDF
      - Logar stack-trace em erros inesperados
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if args and isinstance(args[0], str) and len(args[0]) < 100:
            logging.info(f"[{func.__name__}] início — {args[0]}")
        else:
            logging.info(f"[{func.__name__}] início")
        try:
            result = func(*args, **kwargs)
            logging.info(f"[{func.__name__}] concluído com sucesso")
            return result
        except (HTTPError, ReqTimeout) as err:
            logging.error(f"[{func.__name__}] erro HTTP ou timeout: {err}", exc_info=True)
        except BadZipFile:
            logging.error(f"[{func.__name__}] arquivo ZIP corrompido", exc_info=True)
        except rarfile.Error as err:
            logging.error(f"[{func.__name__}] erro RAR: {err}", exc_info=True)
        except PdfReadError as err:
            logging.error(f"[{func.__name__}] erro ao ler PDF: {err}", exc_info=True)
        except Exception as err:
            logging.error(f"[{func.__name__}] erro inesperado: {err}", exc_info=True)
    return wrapper


def competencia_anterior(ref=None):
    """
    Retorna (mes, ano) do mês anterior ao fornecido (ou de hoje, se None).
    Ex.: ref=2025-06-11 → retorna ("05", "2025")
    """
    ref = ref or date.today()               # 2025-06-11  ➜  ref
    comp = ref - relativedelta(months=1)    # 2025-05-11  ➜  comp
    return f"{comp:%m}", f"{comp:%Y}"


# Estruturas de diretório
PASTA_FINAL = 'TRIAGEM_ROBO'


# ────────────────────────────────────────────────────────────────────────────
# Pipeline de classificação via Document AI (“Robson”)
# ────────────────────────────────────────────────────────────────────────────
@log_and_handle_exceptions
def requisicao_robson(pdf_base64: str) -> list:
    """
    Envia PDF (base64) para o Document AI Processor e retorna
    [tipo, confiança] ordenados pela maior confiança.
    Fallback em caso de resposta inesperada: ["extrato", 0.4].

    Atenção: o caminho de credenciais está fixo; mova para settings/.env.
    """
    credentials_path = r'C:\Users\usuario\PycharmProjects\Claudio_completo\processamento_claudio\claudio-418319-d3c155f4d0a0.json'
    credentials = service_account.Credentials.from_service_account_file(
        credentials_path,
        scopes=['https://www.googleapis.com/auth/cloud-platform']
    )

    credentials.refresh(Request())
    url = ("https://us-documentai.googleapis.com/v1/projects/428021588438/locations/us/processors/c18612c9a6186eba/"
           "processorVersions/a22a73a1fec09ef3:process")

    headers = {
        "Authorization": f"Bearer {credentials.token}",
        "Content-Type": "application/json; charset=utf-8"
    }

    data = {
        "skipHumanReview": True,
        "rawDocument": {
            "mimeType": "application/pdf",
            "content": f"{pdf_base64}"}
    }

    response = requests.post(url,
                             headers=headers,
                             json=data)

    try:
        json_retorno = response.json()['document']['entities']
        retorno_ordenado = sorted(json_retorno, key=lambda x: x['confidence'], reverse=True)
        classificacao_dict = retorno_ordenado[0]
        classificacao = [classificacao_dict['type'],
                         classificacao_dict['confidence']]
    except Exception as err:
        logging.warning(
            "[requisicao_robson] resposta inesperada; usando fallback "
            "(tipo=extrato, conf=0.4) — detalhe: %s",
            err,
        )
        classificacao = ["extrato", 0.4]

    return classificacao


@log_and_handle_exceptions
def pagina_unica(documento):
    """
    Extrai a primeira página de um PDF único e classifica via requisicao_robson.
    Aguarda 1.5s entre chamadas para não exceder quotas.
    """
    with open(documento, 'rb') as doc_unico:
        pdf_unico = PyPDF2.PdfReader(doc_unico)
        dados = PyPDF2.PdfWriter()
        dados.add_page(pdf_unico.pages[0])
        bytes_doc = io.BytesIO()
        dados.write(bytes_doc)
        value_bytes = bytes_doc.getvalue()

        response = base64.b64encode(value_bytes).decode('utf-8')
        retorno_robson = requisicao_robson(response)
        time.sleep(1.5)
        return retorno_robson


@log_and_handle_exceptions
def varias_paginas(documento):
    """
    Classifica multi-páginas:
     - Se > 250 páginas, move inteiro para LIMITE_PAGINAS_DIR e ignora.
     - Para cada página, classifica; se for nota_servico com confiança >0.99, faz split TOMADOS.
     - Retorna classificação da primeira página.
    """

    def split_tomados(base64_string, nome):
        """Gera PDF de primeira página em pasta TOMADOS."""
        # decodifica e abre o PDF
        pdf_bytes = base64.b64decode(base64_string)
        pdf_file_like = io.BytesIO(pdf_bytes)
        reader = PyPDF2.PdfReader(pdf_file_like)
        page_writer = PyPDF2.PdfWriter()
        page_writer.add_page(reader.pages[0])

        rel = os.path.relpath(nome, BASE_TRIAGEM)
        pasta_mesa = rel.split(os.sep, 1)[0]

        pasta_tomados = os.path.join(BASE_TRIAGEM, pasta_mesa, TOMADOS_DIR)
        os.makedirs(pasta_tomados, exist_ok=True)

        split_name = f"SPLIT_DOCUMENTO_{random.randint(10000, 99999)}_{os.path.basename(nome)}"
        destino = os.path.join(pasta_tomados, split_name)
        with open(destino, 'wb') as novo_pdf:
            page_writer.write(novo_pdf)
        logging.info(f"[varias_paginas] página TOMADO salva: {destino}")

    caminho_absoluto_documento = os.path.abspath(documento)
    with open(caminho_absoluto_documento, 'rb') as document:
        pdf_completo = PyPDF2.PdfReader(document)

        if len(pdf_completo.pages) > 250:
            logging.info(f"PDF {documento} possui mais de 300 páginas, movendo para a pasta '{LIMITE_PAGINAS_DIR}'.")
            os.makedirs(LIMITE_PAGINAS_DIR, exist_ok=True)
            document.close()

            novo_caminho = os.path.join(LIMITE_PAGINAS_DIR, os.path.basename(documento))
            shutil.move(caminho_absoluto_documento, novo_caminho)

            return ['ignore', 0]

        index = 0
        primeira_pagina = ''
        for page in pdf_completo.pages:
            writer = PyPDF2.PdfWriter()
            writer.add_page(page)
            bytes_buffer = io.BytesIO()
            writer.write(bytes_buffer)
            writer_bytes = bytes_buffer.getvalue()
            base = base64.b64encode(writer_bytes).decode('utf-8')
            robson = requisicao_robson(base)

            if robson[0] == 'nota_servico' and robson[1] > 0.99:
                split_tomados(base, documento)

            primeira_pagina = robson if index == 0 else primeira_pagina
            time.sleep(1.5)
            index += 1

    return primeira_pagina


@log_and_handle_exceptions
def exe(pasta_mesa):
    """
     Executa pipeline de triagem para a pasta `pasta_mesa`:
       1) extrai compactados
       2) Normaliza extensões com `organiza_extensao()`
       3) categoriza cada arquivo e move para subpastas
       4) gera relatório final em processamento_concluido.txt
     """
    logging.info(f"=== Iniciando extração da pasta separada: {pasta_mesa} ===")
    diretorio = os.path.join(BASE_TESTES, 'SEPARADOS', pasta_mesa)

    # 1) Extrai ZIP/RAR internos (recursivo) e organiza extensões
    scan_e_extraia_recursivo(diretorio)
    organiza_extensao()

    # 2) Monta lista de todos os arquivos em qualquer subpasta
    arquivos_para_processar = []
    for root, _, files in os.walk(diretorio):
        for nome in files:
            arquivos_para_processar.append(os.path.join(root, nome))

    total_arquivos = len(arquivos_para_processar)
    arquivos_processados = 0

    logging.info(f"Total de arquivos detectados: {total_arquivos}")

    for caminho in arquivos_para_processar:
        rel = os.path.relpath(caminho, diretorio)
        ext = os.path.splitext(caminho)[1].lower()
        logging.info(f"Processando: {rel}")

        try:
            # --- 1) Extrair zips/rares que ainda restarem ---
            if ext in ('.zip', '.rar'):
                sucesso = extrair_arquivos_compactados(caminho, os.path.dirname(caminho))
                if sucesso:
                    os.remove(caminho)
                else:
                    # Move para ERRO_PROCESSAMENTO se falhou
                    erro_dir = os.path.join(diretorio, ERRO_PROCESSAMENTO_DIR)
                    os.makedirs(erro_dir, exist_ok=True)
                    shutil.move(caminho, os.path.join(erro_dir, os.path.basename(caminho)))
                    logging.info(f"{rel} → ERRO_PROCESSAMENTO (falha na extração de ZIP/RAR)")
                continue

            # --- 2) Mover planilhas ---
            if ext in ('.xlsx', '.xls'):
                planilhas_dir = os.path.join(diretorio, 'PLANILHAS')
                os.makedirs(planilhas_dir, exist_ok=True)
                shutil.move(caminho, os.path.join(planilhas_dir, os.path.basename(caminho)))
                logging.info(f"{rel} → PLANILHAS")
                arquivos_processados += 1
                continue

            # --- 3) Mover imagens/prints ---
            if ext in ('.jpg', '.jpeg', '.png'):
                imagens_dir = os.path.join(diretorio, 'IMAGEM_PRINT')
                os.makedirs(imagens_dir, exist_ok=True)
                shutil.move(caminho, os.path.join(imagens_dir, os.path.basename(caminho)))
                logging.info(f"{rel} → IMAGEM_PRINT")
                arquivos_processados += 1
                continue

            # --- 4) Mover XMLs ---
            if ext == '.xml':
                xml_dir = os.path.join(diretorio, 'XML')
                os.makedirs(xml_dir, exist_ok=True)
                shutil.move(caminho, os.path.join(xml_dir, os.path.basename(caminho)))
                logging.info(f"{rel} → XML")
                arquivos_processados += 1
                continue

            # --- 5) Só trabalhamos com PDF daqui em diante ---
            if ext == '.txt':
                continue

            if ext != '.pdf':
                raise ValueError(f"Extensão não suportada: {ext}")

            # --- 6) Tenta abrir o PDF ---
            reader = PyPDF2.PdfReader(caminho)
            if getattr(reader, "is_encrypted", False):
                raise PdfReadError("PDF protegido por senha")
            paginas = len(reader.pages)

            # --- 7) PDFs muito grandes ---
            if paginas > 299:
                dest = os.path.join(diretorio, LIMITE_PAGINAS_DIR)
                os.makedirs(dest, exist_ok=True)
                shutil.move(caminho, os.path.join(dest, os.path.basename(caminho)))
                continue

            # --- 8) Classificação via Robson ---
            if paginas == 1:
                classificacao, confianca = pagina_unica(caminho)
            else:
                classificacao, confianca = varias_paginas(caminho)

            # --- 9) Decide pasta de destino ---
            if confianca > 0.99 and classificacao in PASTAS:
                pasta_dest = PASTAS[classificacao]
            else:
                pasta_dest = LOW_CONFIDENCE_DIR

            destino = os.path.join(diretorio, pasta_dest)
            os.makedirs(destino, exist_ok=True)
            shutil.move(caminho, os.path.join(destino, os.path.basename(caminho)))
            arquivos_processados += 1

        except Exception as err:
            # --- 10) Qualquer falha: move para ERRO_PROCESSAMENTO ---
            erro_dir = os.path.join(diretorio, ERRO_PROCESSAMENTO_DIR)
            os.makedirs(erro_dir, exist_ok=True)
            shutil.move(caminho, os.path.join(erro_dir, os.path.basename(caminho)))
            logging.error(f"[{rel}] não foi possível processar: {err}. "
                          f"Movido para {ERRO_PROCESSAMENTO_DIR}", exc_info=True)
            continue

    # --- 11) Limpa pastas vazias remanescentes (opcional) ---
    for root, _, _ in os.walk(diretorio, topdown=False):
        # só remove se estiver realmente vazio agora e não for a raiz
        if root != diretorio and not os.listdir(root):
            os.rmdir(root)

    # --- 12) Gera relatório final ---
    try:
        status_path = os.path.join(diretorio, 'processamento_concluido.txt')
        with open(status_path, 'w', encoding='utf-8') as f:
            f.write(f"Processamento concluído em: {datetime.datetime.now().isoformat()}\n")
            f.write(f"Total de arquivos detectados: {total_arquivos}\n")
        logging.info(f"Arquivo de status criado: {status_path}")
    except Exception as err:
        logging.error(f"Erro ao gravar status de conclusão: {err}", exc_info=True)


# ────────────────────────────────────────────────────────────────────────────
# Helpers para determinar e mover pastas de triagem
# ────────────────────────────────────────────────────────────────────────────
@log_and_handle_exceptions
def mover_cliente(folder_name: str) -> str:
    """
    Copia todo o conteúdo de BASE_TRIAGEM/folder_name para a estrutura Contábil e Fiscal
    do cliente, com base em códigos obtidos por obter_codigo_empresa().
    Retorna "Sucesso" ou mensagem de erro.
    """
    mes_comp, ano_comp = competencia_anterior()
    cliente_dir: str | None = None
    try:
        apelido = folder_name.split("-", 1)[1].strip()
        codi_emp, codi_emp_matriz = obter_codigo_empresa(apelido)
        if not codi_emp:
            return "NÃO ENVIADO PARA PASTA DO CLIENTE"

        codigo_para_busca = codi_emp_matriz or codi_emp
        cliente_dir = next(
            (nome for nome in os.listdir(BASE_CLIENTES)
             if nome.startswith(f"{codigo_para_busca}-")),
            None
        )
        if not cliente_dir:
            logging.warning("Pasta do cliente %s não encontrada.", codigo_para_busca)
            return "NÃO ENVIADO PARA PASTA DO CLIENTE"

        origem = os.path.join(BASE_TRIAGEM, folder_name)

        # Que nome de pasta “Contábil” existe?
        caminho_contabil = os.path.join(BASE_CLIENTES, cliente_dir)
        pasta_contabil = next(
            (n for n in os.listdir(caminho_contabil)
             if n.upper() in {"CONTÁBIL", "CONTABIL"}),
            "CONTÁBIL"
        )

        destino_contabil = os.path.join(
            BASE_CLIENTES, cliente_dir, pasta_contabil, "Movimento",
            f"{ano_comp}", f"{mes_comp}.{ano_comp}",
            PASTA_FINAL, folder_name
        )
        destino_fiscal = os.path.join(
            BASE_CLIENTES, cliente_dir, "FISCAL", "IMPOSTOS",
            f"{ano_comp}", f"{mes_comp}.{ano_comp}",
            "MCALC", PASTA_FINAL, folder_name
        )

        os.makedirs(destino_contabil, exist_ok=True)
        os.makedirs(destino_fiscal,  exist_ok=True)
        shutil.copytree(origem, destino_contabil, dirs_exist_ok=True)
        shutil.copytree(origem, destino_fiscal,  dirs_exist_ok=True)

        logging.info(
            "Conteúdo de %s copiado para Contábil e Fiscal do cliente %s.",
            folder_name, cliente_dir
        )
        return destino_contabil

    except Exception as err:
        logging.error(
            "Erro ao mover cliente para %s (%s): %s",
            folder_name, cliente_dir if 'cliente_dir' in locals() else 'desconhecido',
            err,
            exc_info=True
        )
        return "NÃO ENVIADO PARA PASTA DO CLIENTE"
