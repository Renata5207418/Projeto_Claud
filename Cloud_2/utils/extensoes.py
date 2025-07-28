import os


def organiza_extensao():
    """
        Varre o diretório de trabalho (o cwd) e move cada arquivo para a pasta
        correspondente à sua extensão. Cria a pasta se não existir.

        Atualmente agrupa:
          - '.csv', '.xls', '.xlsx'   → 'PLANILHA'
          - '.txt'                    → 'TXT'
          - '.png', '.jpg', '.jpeg'   → 'IMAGEM_PRINT'
          - '.zip', '.rar'            → 'ZIP'
          - '.xml'                    → 'XML'

        Observações e sugestões de melhoria:
          1. Usa `os.listdir()` repetidamente — pode ser otimizado lendo a lista
             uma única vez e mapeando extensões para destino.
          2. Depende do cwd atual; em contextos maiores, prefira receber um Path
             como parâmetro para maior clareza e testabilidade.
          3. Move com `os.replace()`, que pode falhar em sistemas de arquivos
             diferentes. Para maior robustez, considere `shutil.move()`.
    """

    arquivos_xml = [f for f in os.listdir() if f.lower().endswith('.xml')]
    arquivos_xlsx = [f for f in os.listdir() if f.lower().endswith('.xlsx')]
    arquivos_rar = [f for f in os.listdir() if f.lower().endswith('.rar')]
    arquivos_zip = [f for f in os.listdir() if f.lower().endswith('.zip')]
    arquivos_jpeg = [f for f in os.listdir() if f.lower().endswith('.jpeg')]
    arquivos_jpg = [f for f in os.listdir() if f.lower().endswith('.jpg')]
    arquivos_png = [f for f in os.listdir() if f.lower().endswith('.png')]
    arquivos_xls = [f for f in os.listdir() if f.lower().endswith('.xls')]
    arquivos_csv = [f for f in os.listdir() if f.lower().endswith('.csv')]
    arquivos_txt = [f for f in os.listdir() if f.lower().endswith('.txt')]

    for csv in arquivos_csv:
        os.makedirs(f'PLANILHA', exist_ok=True)

        caminho_atual = os.path.join(csv)
        caminho_destino = os.path.join('PLANILHA', csv)
        os.replace(caminho_atual, caminho_destino)

    for txt in arquivos_txt:
        os.makedirs(f'TXT', exist_ok=True)

        caminho_atual = os.path.join(txt)
        caminho_destino = os.path.join('TXT', txt)
        os.replace(caminho_atual, caminho_destino)

    for xls in arquivos_xls:
        os.makedirs(f'PLANILHA', exist_ok=True)

        caminho_atual = os.path.join(xls)
        caminho_destino = os.path.join('PLANILHA', xls)
        os.replace(caminho_atual, caminho_destino)

    for png in arquivos_png:
        os.makedirs(f'IMAGEM_PRINT', exist_ok=True)

        caminho_atual = os.path.join(png)
        caminho_destino = os.path.join('IMAGEM_PRINT', png)
        os.replace(caminho_atual, caminho_destino)

    for jpg in arquivos_jpg:
        os.makedirs(f'IMAGEM_PRINT', exist_ok=True)

        caminho_atual = os.path.join(jpg)
        caminho_destino = os.path.join('IMAGEM_PRINT', jpg)
        os.replace(caminho_atual, caminho_destino)

    for jpeg in arquivos_jpeg:
        os.makedirs(f'IMAGEM_PRINT', exist_ok=True)

        caminho_atual = os.path.join(jpeg)
        caminho_destino = os.path.join('IMAGEM_PRINT', jpeg)
        os.replace(caminho_atual, caminho_destino)

    for arquivo_zip in arquivos_zip:
        os.makedirs("ZIP", exist_ok=True)

        caminho_atual = os.path.join(arquivo_zip)
        caminho_destino = os.path.join("ZIP", arquivo_zip)
        os.replace(caminho_atual, caminho_destino)

    for rar in arquivos_rar:
        os.makedirs(f'ZIP', exist_ok=True)

        caminho_atual = os.path.join(rar)
        caminho_destino = os.path.join('ZIP', rar)
        os.replace(caminho_atual, caminho_destino)

    for xml in arquivos_xml:
        os.makedirs(f'XML', exist_ok=True)

        caminho_atual = os.path.join(xml)
        caminho_destino = os.path.join('XML', xml)
        os.replace(caminho_atual, caminho_destino)

    for xlsx in arquivos_xlsx:
        os.makedirs(f'PLANILHA', exist_ok=True)

        caminho_atual = os.path.join(xlsx)
        caminho_destino = os.path.join('PLANILHA', xlsx)
        os.replace(caminho_atual, caminho_destino)
