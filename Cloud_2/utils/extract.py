import os
import logging
import zipfile
import rarfile
from pathlib import Path

ERRO_PROCESSAMENTO_DIR = 'ERRO_PROCESSAMENTO'


def scan_e_extraia_recursivo(diretorio: str | os.PathLike[str]) -> None:
    while True:
        houve_extracao = False
        for root, _, files in os.walk(diretorio):
            root_path = Path(root)
            for nome in files:
                caminho = root_path / nome
                ext = caminho.suffix.lower()
                if ext in (".zip", ".rar"):
                    sucesso = extrair_arquivos_compactados(str(caminho), str(root_path))
                    if sucesso:
                        caminho.unlink()
                        houve_extracao = True
        if not houve_extracao:
            break


def extrair_arquivos_compactados(caminho_arquivo, pasta_destino):
    """
    Extrai arquivos ZIP ou RAR individualmente:
     - arquivos válidos → pasta_destino
     - arquivos corrompidos/inválidos → pasta_destino/ERRO_PROCESSAMENTO/EXTRACAO_INTEGRIDADE
    Retorna True sempre que tentou extrair (mesmo que alguns membros falhem).
    """

    # pasta de erro geral e subpasta só de extração
    erro_root = os.path.join(pasta_destino, ERRO_PROCESSAMENTO_DIR)
    erro_extracao_dir = os.path.join(erro_root, 'EXTRACAO_INTEGRIDADE')
    os.makedirs(erro_extracao_dir, exist_ok=True)

    # lista pra gerar um log depois
    erros = []

    if caminho_arquivo.lower().endswith('.zip'):
        with zipfile.ZipFile(caminho_arquivo, 'r') as zf:
            for member in zf.infolist():
                try:
                    zf.extract(member, pasta_destino)
                    logging.info(f"[ZIP] extraído: {member.filename}")
                except Exception as e:
                    logging.error(f"[ZIP] falha ao extrair {member.filename}: {e}", exc_info=True)
                    erros.append(member.filename)
                    # cria um stub (arquivo vazio) só pra marcar que deu pau
                    stub = os.path.join(erro_extracao_dir, os.path.basename(member.filename))
                    open(stub, 'a').close()

    elif caminho_arquivo.lower().endswith('.rar'):
        with rarfile.RarFile(caminho_arquivo, 'r') as rf:
            for member in rf.infolist():
                try:
                    rf.extract(member, pasta_destino)
                    logging.info(f"[RAR] extraído: {member.filename}")
                except Exception as e:
                    logging.error(f"[RAR] falha ao extrair {member.filename}: {e}", exc_info=True)
                    erros.append(member.filename)
                    stub = os.path.join(erro_extracao_dir, os.path.basename(member.filename))
                    open(stub, 'a').close()

    else:
        logging.warning(f"Tipo de arquivo não suportado: {caminho_arquivo}")
        return False

    # opcional: grava uma lista completa dos membros que falharam
    if erros:
        lista_txt = os.path.join(erro_extracao_dir, 'lista_erros_extracao.txt')
        with open(lista_txt, 'w', encoding='utf-8') as f:
            f.write('\n'.join(erros))
        logging.info(f"[extrair_arquivos_compactados] {len(erros)} itens falharam e foram anotados em: {lista_txt}")

    return True
