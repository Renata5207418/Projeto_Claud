import time
import shutil
from pathlib import Path


def espera_download(download_dir: Path, antes: set[str], timeout: int = 600) -> list[Path]:
    """
        Aguarda até que novos arquivos terminem de baixar em `download_dir`.

        Parâmetros:
          download_dir: Path — pasta monitorada (ex.: settings.download_dir)
          antes: set[str] — nomes de arquivos já presentes antes de iniciar o download
          timeout: int — tempo máximo de espera em segundos (padrão: 600)

        Comportamento:
          - Em loop, a cada 1s, compara a lista de nomes atuais com `antes`.
          - Ignora arquivos ainda em progresso (extensão “.crdownload” do Chrome).
          - Se encontrar ao menos um arquivo novo completo, retorna a lista de Paths desses arquivos.
          - Se o tempo ultrapassar `timeout`, lança TimeoutError.
        """
    limite = time.time() + timeout
    while time.time() < limite:
        agora = {p.name for p in download_dir.iterdir()}
        novos = [download_dir / n for n in (agora - antes) if not n.endswith(".crdownload")]
        if novos:
            return novos
        time.sleep(1)
    raise TimeoutError("Download não terminou no tempo limite")


def mover_arquivos(arquivos: list[Path], destino: Path):
    """
    Move cada arquivo em `arquivos` para a pasta `destino`.

    Parâmetros:
      arquivos: list[Path] — lista de arquivos a mover
      destino: Path — pasta de destino. É criada (com pais) se não existir.

    Observações:
      - Usa shutil.move, preservando nome original.
      - Se ocorrer erro de I/O, a exceção será propagada para o chamador tratar.
    """
    destino.mkdir(parents=True, exist_ok=True)
    for arq in arquivos:
        shutil.move(arq, destino / arq.name)


# Dicionário único de seletores CSS usados pela automação
CSS = {
    # campo de busca de OS
    "pesquisa": ".search__input",
    # botão de detalhes de OS
    "detalhes": ".bento-icon-info-filled",
    # filtros no grid (não usados em todos os scripts)
    "cliente": "div.filters-inline-group:nth-child(3) > span:nth-child(2)",
    "apelido": "div.filters-inline-group:nth-child(2) > span:nth-child(2)",
    "os": "div.filters-inline-group:nth-child(1) > span:nth-child(2)",
    # itens de anexo na lista
    "anexos": "[id^='a-attachment_']",
    # campos de assunto e descrição na tela de detalhes
    "assunto": "div.row:nth-child(3) > div:nth-child(2) > span:nth-child(1)",
    "descricao": "span.detail-data:nth-child(1)",
    # botão de fechar detalhes
    "fechar": "button.btn-lg:nth-child(1)",
}
