import requests
import re


def dados_fornecedor(cnpj: str):
    """
        Consulta a API ReceitaWS para obter dados de um CNPJ.

        Parâmetros:
          cnpj: string com 14 dígitos do CNPJ (pode conter pontos, barras e hífen,
                mas a API também aceita o formato limpo)

        Retorno (em caso de sucesso):
            {
                'razao_social': '<nome da empresa sem caracteres especiais>',
                'uf':           '<UF, ex.: "SP">',
                'municipio':    '<município, ex.: "São Paulo">',
                'cnae':         '<código CNAE principal, apenas dígitos>'
            }

        Em caso de falha (ex. timeout, formato inesperado):
            {
                'razao_social': '',
                'uf':           '',
                'municipio':    '',
                'cnae':         ''
            }

        Fluxo:
          1. Faz GET em https://receitaws.com.br/v1/cnpj/{cnpj}
          2. Obtém o JSON de resposta
          3. Extrai:
             - nome → limpa caracteres especiais via regex
             - uf
             - municipio
             - atividade_principal[0]['code'] → extrai dígitos apenas
          4. Retorna dicionário com os valores formatados
    """
    try:

        response = requests.get(url=rf'https://receitaws.com.br/v1/cnpj/{cnpj}')
        response_json = response.json()
        razao_social = re.sub(r'[^0-9a-zA-Z ]', '', response_json.get('nome', ''))
        uf = response_json.get('uf', '')
        municipio = response_json.get('municipio', '')
        cnae_grupo = response_json.get('atividade_principal', '')[0]
        cod_cnae = cnae_grupo['code']
        cod_cnae_limpo = re.sub(r'[^0-9]', '', cod_cnae)

        return {'razao_social': f'{razao_social}',
                'uf': f'{uf}',
                'municipio': f'{municipio}',
                'cnae': f'{cod_cnae_limpo}'}

    except Exception as e:
        print(f"Erro ao obter dados do fornecedor para o CNPJ '{cnpj}': {e}")
        return {'razao_social': '', 'uf': '', 'municipio': '', 'cnae': ''}
