import re


def pattern_codservico(cod: str):
    """
        Recebe um código de serviço e retorna apenas os dígitos contidos nele.

        Parâmetros:
          cod: string original do código de serviço

        Retorna:
          string contendo somente caracteres '0'-'9'

        Observação:
          • Pode ser usado para lookup em acumuladores após normalização.
    """
    cod = cod
    cod_numerico = re.sub(r'[^0-9]', '', cod)
    quantidade = len(cod_numerico)

    # df = pd.read_excel('acumuladores.xlsx', sheet_name=str(quantidade), dtype=str)
    # acumulador = df[df['cod_serv'] == cod]['acumulador']

    return cod_numerico


def pattern_valor(valor: str):
    """
        Limpa uma string de valor monetário, removendo tudo que não seja dígito ou vírgula.
        Ex.: "R$ 1.234,56" → "1234,56"

        Parâmetros:
          valor: string que pode conter símbolos, espaços, pontos, etc.

        Retorna:
          string contendo apenas dígitos e vírgulas.
    """
    valor = re.sub(r'[^0-9,]', '', valor)
    return valor


def pattern_data(data: str):
    """
    Formata/limita uma string de data no formato DD/MM/AAAA.

    - Remove caracteres que não sejam dígito ou '/'.
    - Trunca a 10 caracteres (DD/MM/AAAA).

    Parâmetros:
      data: string que pode vir com hora ou texto adicional.

    Retorna:
      até 10 primeiros caracteres após limpeza.
    """
    data = re.sub(r'[^0-9/]', '', data)
    data = data[:10]
    return data


def limpeza_cnpj(cnpj: str):
    """
    Remove tudo que não seja dígito de um CNPJ e garante 14 caracteres, preenchendo com zeros à esquerda.
    Ex.: "12.345.678/0001-99" → "12345678000199"

    Parâmetros:
      cnpj: string possivelmente formatada

    Retorna:
      string de 14 dígitos
    """
    limpeza = re.sub(r'[^0-9]', '', cnpj)
    digitos = limpeza.zfill(14)

    return digitos


def pattern_cnpj(cnpj: str):
    """
    Converte um CNPJ (qualquer formato) para a máscara padrão
    "XX.XXX.XXX/XXXX-XX".

    Ex.: "12345678000199" → "12.345.678/0001-99"

    Parâmetros:
      cnpj: string de 14 dígitos ou formatada

    Retorna:
      string formatada com pontos, barra e hífen
    """
    digitos = limpeza_cnpj(cnpj)
    pattern = f'{digitos[0:2]}.{digitos[2:5]}.{digitos[5:8]}/{digitos[8:12]}-{digitos[12:14]}'
    return pattern


def pattern_numero(numero: str):
    """
    Extrai apenas dígitos de uma string numérica e remove zeros à esquerda.

    Ex.: "0001234" → "1234"

    Parâmetros:
      numero: string com possíveis caracteres não numéricos

    Retorna:
      string com dígitos, sem zeros à esquerda
    """
    apenas_numeros = re.sub(r'[^0-9]', '', numero)
    pattern = re.sub(r'^0+', '', apenas_numeros)
    return pattern


def soma_csrf(pis='0,00', cofins='0,00', csll='0,00'):
    """
    Soma os valores de PIS, COFINS e CSLL (strings no formato "0,00"),
    retornando o total também no mesmo formato.

    Parâmetros:
      pis, cofins, csll: strings podendo ser vazias ou None

    Fluxo:
      - Substitui valores vazios por '0,00'
      - Converte "," para "." e faz float
      - Soma os três valores
      - Converte de volta para string com vírgula decimal

    Retorna:
      string como "123.45" → "123,45"
    """
    pis = pis if pis else '0,00'
    cofins = cofins if cofins else '0,00'
    csll = csll if csll else '0,00'

    pis_float = float(pis.replace(",", "."))
    cofins_float = float(cofins.replace(",", "."))
    csll_float = float(csll.replace(",", "."))

    csrf = pis_float + cofins_float + csll_float
    csrf_str = str(csrf).replace(".", ",")

    return csrf_str
