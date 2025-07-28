import time
import pandas as pd
from io import StringIO
import re
from utils import consulta_for

pd.set_option('display.max_columns', None)
pd.set_option('display.expand_frame_repr', False)

data = """
09.524.519/0001-43;SCRYTA ASSESSORIA CONTABIL LTDA;PR;CURITIBA;;49067;;17/09/2024;0;;;11224,00;;11224,00;11224,00;;;;0,00;;;;0,0;0,00;;;;23.880.273/0001-73
26.401.688/0001-05;SWILE DO BRASIL SA;SP;SAO PAULO;;907177;;14/10/2024;0;;;0,00;;0,00;0,00;;;;0,00;;;;0,0;0,00;;;;23.880.273/0001-73
24.440.673/0001-20;MOREIRA  NASSIF ADVOGADOS ASSOCIADOS;PR;CURITIBA;;258;;01/10/2024;0;17;;750,00;;750,00;750,00;;;;0,00;;;;0,0;0,00;;;;23.880.273/0001-73
29.954.503/0001-88;SOFTWAREIDEA DESENVOLVIMENTO DE SISTEMAS LTDA;PR;CASCAVEL;;51;;01/10/2024;0;1;;24702,79;;24702,79;24702,79;;;;0,00;;;;0,0;0,00;;;;23.880.273/0001-73
47.583.566/0001-57;SYSTEMS DEVELOPMENT AND CONSULTING LTDA;PE;RECIFE;;33;;01/10/2024;0;1;;12160,92;;12160,92;12160,92;;;;0,00;;;;0,0;0,00;;;;23.880.273/0001-73
54.773.642/0001-52;RECH SUPORTE EM TECNOLOGIA LTDA;PR;CURITIBA;;7;;01/10/2024;0;1;;29993,76;;29993,76;29993,76;;;;0,00;;;;0,0;0,00;;;;23.880.273/0001-73
30.342.266/0001-83;ONFLY TECNOLOGIA LTDA;MG;BELO HORIZONTE;;202457068;;07/10/2024;0;16;;299,99;;299,99;299,99;;;;0,00;;;;0,0;0,00;;;;23.880.273/0001-73
12.499.520/0001-70;CLICKSIGN GESTAO DE DOCUMENTOS SA;SP;BARUERI;;498610;;04/10/2024;0;1;;1464,73;;1464,73;1464,73;;;;0,00;;;;0,0;0,00;;;;23.880.273/0001-73
51.239.824/0001-50;WOLFF E SCRIPES ADVOGADOS;PR;CURITIBA;;826;;09/10/2024;0;17;;5076,90;;5076,90;5076,90;;;;0,00;;;;0,0;0,00;;;;23.880.273/0001-73
45.131.961/0001-73;CC  COACHING EMPRESARIAL E DESENVOLVIMENTO DE LIDERES LTDA;PR;CURITIBA;;643;;09/10/2024;0;22;;9000,00;;9000,00;9000,00;;;;0,00;;;;0,0;0,00;;;;23.880.273/0001-73
42.443.471/0001-14;42443471 NATANI OLIVEIRA PAZ;RS;SANTO ANGELO;;42;;30/09/2024;0;199;;1800,00;;1800,00;1800,00;;;;0,00;;;;0,0;0,00;;;;23.880.273/0001-73
10.348.318/0006-26;WINDSOR ADMINISTRACAO DE HOTEIS E SERVICOS SA;RJ;RIO DE JANEIRO;;254403;;18/10/2024;0;16;;18523,15;;18523,15;18523,15;;;;0,00;;;;0,0;0,00;;;;23.880.273/0001-73
40.803.416/0001-62;CLEVERSON AFONSO BOFF TECNOLOGIA LTDA;PR;CURITIBA;;47;;01/10/2024;0;1;;30000,00;;30000,00;30000,00;;;;0,00;;;;0,0;0,00;;;;23.880.273/0001-73
48.044.593/0001-14;MF CONSULTORIA E TECNOLOGIA DA INFORMACAO LTDA;PR;CURITIBA;;29;;01/10/2024;0;1;;21266,41;;21266,41;21266,41;;;;0,00;;;;0,0;0,00;;;;23.880.273/0001-73
05.314.972/0001-74;VTEX BRASIL TECNOLOGIA PARA ECOMMERCE LTDA;SP;SAO PAULO;;1092733;;01/10/2024;0;1;;1500,00;;1500,00;1500,00;;;;0,00;;;;0,0;0,00;;;;23.880.273/0001-73
56.114.660/0001-58;56114660 ANDRE XIMENES SANT ANNA;PR;CURITIBA;;2;;01/10/2024;0;199;;1920,00;;1920,00;1920,00;;;;0,00;;;;0,0;0,00;;;;23.880.273/0001-73
49.730.741/0001-17;KATIA MITIKO YAMAZATO;SP;SAO PAULO;;25;;01/10/2024;0;11;;24000,00;;24000,00;24000,00;;;;0,00;;;;0,0;0,00;;;;23.880.273/0001-73
55.421.442/0001-01;DIOHCHANG LTDA;SP;SAO PAULO;;20241001155421442000101;;01/10/2024;0;24;;16332,22;;16332,22;16332,22;;;;0,00;;;;0,0;0,00;;;;23.880.273/0001-73
44.616.691/0001-28;LEONARDO ALFONSO SCHMITT 10464024986;SC;GASPAR;;202400000000010;;01/10/2024;0;22;;10339,84;;10339,84;10339,84;;;;0,00;;;;0,0;0,00;;;;23.880.273/0001-73
52.642.373/0001-60;ATTOM CONSULTORIA EM TI LTDA;MG;BELO HORIZONTE;;202400000000010;;01/10/2024;0;1;;30000,00;;30000,00;30000,00;;;;0,00;;;;0,0;0,00;;;;23.880.273/0001-73
49.575.548/0001-59;49575548 ANA CAROLINA BETTIO;PR;CURITIBA;;27;;01/10/2024;0;22;;300,00;;300,00;300,00;;;;0,00;;;;0,0;0,00;;;;23.880.273/0001-73
29.095.144/0001-50;GABRIELA GIMENEZ GONCALVES;PR;CURITIBA;;88;;01/10/2024;0;;;29170,46;;29170,46;29170,46;;;;0,00;;;;0,0;0,00;;;;23.880.273/0001-73
25.285.557/0001-47;ROBOTIMIZE LTDA;PR;CURITIBA;;94;;01/10/2024;0;1;;18827,94;;18827,94;18827,94;;;;0,00;;;;0,0;0,00;;;;23.880.273/0001-73
38.310.034/0001-55;KOTINSKI CAPACITACAO EM RECURSOS HUMANOS LTDA;PR;CURITIBA;;55;;01/10/2024;0;22;;17571,06;;17571,06;17571,06;;;;0,00;;;;0,0;0,00;;;;23.880.273/0001-73
27.607.246/0001-82;NATHAN HENRIQUE DE B DIAS;GO;GOIANIA;;20;;30/09/2024;0;;;5400,00;;5400,00;5400,00;;;;0,00;;;;0,0;0,00;;;;23.880.273/0001-73
46.565.194/0001-73;KLEBER MARTINS ALBERTINI LTDA;PR;CURITIBA;;42;;01/10/2024;0;1;;22500,00;;22500,00;22500,00;;;;0,00;;;;0,0;0,00;;;;23.880.273/0001-73
15.440.485/0001-01;J ROMERO LTDA;PR;CURITIBA;;272;;03/10/2024;0;80;;56,00;;56,00;56,00;;;;0,00;;;;0,0;0,00;;;;23.880.273/0001-73
14.387.308/0002-27;GLOBAL SOLUCOES FINANCEIRAS LTDA;SC;JOINVILLE;;9242;;01/10/2024;0;199;;988,26;;988,26;988,26;;;;0,00;;;;0,0;0,00;;;;23.880.273/0001-73
55.421.442/0001-01;DIOHCHANG LTDA;SP;SAO PAULO;;20241003155421442000101;;03/10/2024;0;24;;4274,51;;4274,51;4274,51;;;;0,00;;;;0,0;0,00;;;;23.880.273/0001-73
45.391.352/0001-53;PRISCILLA NICOLODI 08829419923;SC;JOINVILLE;;33;;01/10/2024;0;199;;3500,00;;3500,00;3500,00;;;;0,00;;;;0,0;0,00;;;;23.880.273/0001-73
10.904.185/0006-27;MAIS VAGAS ESTACIONAMENTOS LTDA;PR;CURITIBA;;144;;24/09/2024;0;49;;1585,00;;1585,00;1585,00;;;;0,00;;;;0,0;0,00;;;;23.880.273/0001-73
05.653.393/0001-56;GERAR  GERACAO DE EMPREGO RENDA E APOIO AO DESENVOLVIMENTO REGIONAL;PR;CURITIBA;;223338;;23/09/2024;0;24;;223,54;;223,54;223,54;;;;0,00;;;;0,0;0,00;;;;23.880.273/0001-73
39.338.267/0001-29;MTREZUB CONSULTORIA LTDA;PR;SAO JOSE DOS PINHAIS;;19;;03/10/2024;0;24;;58107,42;;58107,42;58107,42;;;;871,61;;;;2701,9900000000002;0,00;;;;23.880.273/0001-73
34.910.347/0001-93;WANDERLAN ALECIO DE CARVALHO SISTEMAS E INTELIGENCIA COMPUTACIONAL;PR;CURITIBA;;75;;01/10/2024;0;1;;17763,91;;17763,91;17763,91;;;;0,00;;;;0,0;0,00;;;;23.880.273/0001-73
40.672.980/0001-93;APETIS CONSULTORIA LTDA;PR;SAO JOSE DOS PINHAIS;;14;;01/10/2024;0;1;;58107,42;;58107,42;58107,42;;;;0,00;;;;1830,38;0,00;;;;23.880.273/0001-73
28.745.929/0001-69;AMANDA DE MENEZES XAVIER 13010458703;RJ;RIO DE JANEIRO;;91;;02/10/2024;0;199;;16264,00;;16264,00;16264,00;;;;0,00;;;;0,0;0,00;;;;23.880.273/0001-73
39.418.423/0001-61;DOUGLAS DA SILVA GARCIA 42414065800;SP;SAO PAULO;;59;;01/10/2024;0;1;;11078,23;;11078,23;11078,23;;;;0,00;;;;0,0;0,00;;;;23.880.273/0001-73
35.584.883/0001-09;BRUNO HAULLY DE FREITAS CONSULTORIA EM TECNOLOGIA DA INFORMACAO;PR;CURITIBA;;64;;01/10/2024;0;1;;17025,63;;17025,63;17025,63;;;;0,00;;;;0,0;0,00;;;;23.880.273/0001-73
"""


def instancia_df(data):
    """
        Converte texto CSV delimitado por ponto-e-vírgula em DataFrame.

        Parâmetros:
          data: string contendo múltiplas linhas CSV, sem cabeçalho.

        Colunas definidas:
          ['CPF/CNPJ', 'Razão Social', 'UF', 'Município', 'Endereço',
           'Número Documento', 'Série', 'Data',
           'Situação (0- Regular / 2- Cancelada)', 'Acumulador', 'CFOP',
           'Valor Serviços', 'Valor Descontos', 'Valor Contábil',
           'Base de Calculo', 'Alíquota ISS', 'Valor ISS Normal',
           'Valor ISS Retido', 'Valor IRRF', 'Valor PIS', 'Valor COFINS',
           'Valor CSLL', 'Valo CRF', 'Valor INSS', 'Código do Item',
           'Quantidade', 'Valor Unitário', 'tomador']

        Retorna:
          DataFrame com dtype object e valores NaN substituídos por ''.
    """
    col_names = ['CPF/CNPJ', 'Razão Social', 'UF', 'Município', 'Endereço',
                 'Número Documento', 'Série', 'Data', 'Situação (0- Regular / 2- Cancelada)', 'Acumulador', 'CFOP',
                 'Valor Serviços', 'Valor Descontos', 'Valor Contábil', 'Base de Calculo', 'Alíquota ISS',
                 'Valor ISS Normal', 'Valor ISS Retido', 'Valor IRRF', 'Valor PIS', 'Valor COFINS', 'Valor CSLL',
                 'Valo CRF', 'Valor INSS', 'Código do Item', 'Quantidade', 'Valor Unitário', 'tomador']

    df = pd.read_csv(StringIO(data), delimiter=';', names=col_names, dtype={'Acumulador': str, 'Número Documento': str})
    df = df.astype(object)
    df.fillna('', inplace=True)

    return df


def elimina_duplicidade(df):
    """
    Remove linhas duplicadas com base em 'CPF/CNPJ' e 'Número Documento'.

    Parâmetros:
      df: DataFrame original

    Retorna:
      DataFrame sem duplicatas nesses campos.
    """
    df_unique = df.drop_duplicates(subset=['CPF/CNPJ', 'Número Documento'])
    return df_unique


def split_tomador(df, tomados_dir):
    """
        Gera um arquivo por tomador (coluna 'tomador') contendo apenas as linhas
        daquele tomador, ajustando o CFOP conforme o estado.

        Parâmetros:
          df: DataFrame já limpo e sem duplicatas
          tomados_dir: Path da pasta onde escrever os arquivos de saída

        Fluxo:
          1. Identifica cada tomador único em df['tomador']
          2. Para cada tomador:
             a. Limpa CNPJ (remove não-dígitos) e consulta `dados_fornecedor`
             b. Ajusta `CFOP`:
                - se df['UF'] == uf_fornecedor → 1933
                - caso contrário                 → 2933
             c. Gera filename: "TOMADOS <razao_social> - <cnpj>.txt"
             d. Exporta CSV separado por ';', sem índice, encoding latin-1
             e. Aguarda `time.sleep(18)` para não estourar rate-limit
    """
    unico = df['tomador'].unique()
    for i in unico:
        dados_tomador = consulta_for.dados_fornecedor(re.sub("[^0-9]", "", i))
        uf = dados_tomador.get('uf')
        tomador = df[df['tomador'] == i].copy()

        tomador.loc[tomador['UF'] == uf, 'CFOP'] = 1933
        tomador.loc[tomador['UF'] != uf, 'CFOP'] = 2933

        filename = f"TOMADOS {dados_tomador['razao_social']} - {re.sub('[^0-9]', '', i)}.txt"
        full_path = tomados_dir / filename
        tomador.to_csv(full_path, index=False, sep=";", encoding='latin-1')
        time.sleep(18)


def exe(csv, tomados_dir):
    """
    Pipeline completo de tratamento de CSV:
      1. Cria DataFrame com `instancia_df`
      2. Remove duplicados com `elimina_duplicidade`
      3. Gera arquivos de tomadores com `split_tomador`

    Parâmetros:
      data_csv: string contendo o CSV bruto
      tomados_dir: Path da pasta de saída para arquivos "TOMADOS"
    """
    df = instancia_df(csv)
    df = elimina_duplicidade(df)
    split_tomador(df, tomados_dir)
