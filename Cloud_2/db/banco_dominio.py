import sqlanydb
import logging
import unicodedata
from dotenv import load_dotenv
import os

# -------------------------------------------------------
# Carrega .env do diretório corrente (ou raiz do projeto)
# -------------------------------------------------------
load_dotenv()
# Logging básico; em projetos maiores, use um logger configurado (e filtre dados sensíveis)
logging.basicConfig(level=logging.INFO)


class DatabaseConnection:
    """
    Wrapper para conexões SQL Anywhere (sqlanydb).

    Parâmetros de conexão esperados como dict:
      - servername: host do banco
      - port: porta TCP
      - dbn: nome do banco
      - userid: usuário
      - password: senha
      - LINKS: string de link TCP/IP

    Exemplo de conn_str:
      {
        "servername": "meu-host",
        "dbn": "bethadba",
        "userid": "usuario",
        "password": "senha",
        "LINKS": "tcpip(host=meu-host;port=2638)"
      }
    """
    def __init__(self, host, port, dbname, user, password):
        # Monta dicionário de parâmetros para sqlanydb.connect()
        self.conn_str = {
            "servername": host,
            "dbn": dbname,
            "userid": user,
            "password": password,
            "LINKS": f"tcpip(host={host};port={port})"
        }
        self.conn = None

    def connect(self):
        """
        Abre a conexão com o banco.

        Em caso de erro, registra no log e mantém `self.conn = None`.
        """
        try:
            logging.info(f"Tentando conectar com os parâmetros")
            self.conn = sqlanydb.connect(**self.conn_str)
        except sqlanydb.Error as e:
            logging.error(f"Erro ao conectar ao banco de dados: {e}")
            self.conn = None

    def close(self):
        """Fecha a conexão se ela estiver aberta."""
        if self.conn is not None:
            self.conn.close()

    def execute_query(self, query, params=None):
        """
        Executa uma consulta SQL (geralmente SELECT) e retorna todos os resultados.

        Parâmetros:
          - query: string SQL com placeholders “?”
          - params: tupla de valores para os placeholders
        Retorno:
          - lista de tuplas com os resultados, ou
          - None em caso de erro ou conexão não estabelecida
        """
        if self.conn is None:
            logging.error("Conexão ao banco não estabelecida.")
            return None
        cursor = self.conn.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            resultados = cursor.fetchall()
            return resultados
        except sqlanydb.Error as e:
            logging.error(f"Erro ao executar a consulta: {e}")
            return None
        finally:
            cursor.close()


def normalizar_string(s):
    """
    Remove acentos e caracteres especiais de uma string.

    Usa unicodedata.normalize em modo 'NFD' e filtra marcas de combinação.
    Exemplo: 'São Paulo' → 'Sao Paulo'
    """
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')


def obter_codigo_empresa(apelido_empresa):
    """
    Busca, no banco de domínio, o código da empresa dado seu apelido.

    Fluxo:
     1. Normaliza o apelido (remove acentos).
     2. Conecta ao banco usando variáveis de ambiente:
        DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
     3. Executa query em bethadba.geempre para encontrar codi_emp e apel_emp.
     4. Se apel_emp indicar 'FILIAL', busca o codi_emp da matriz (mesmo CNPJ-base).
     5. Fecha conexão e retorna (codi_emp, codi_emp_matriz) — ou (None, None) se não achar.

    Retorno:
      (codi_emp, codi_emp_matriz)
      • codi_emp: código da empresa (ou None)
      • codi_emp_matriz: se filial, código da matriz; caso contrário, None
    """
    logging.info(f"Buscando código da empresa com apelido: {apelido_empresa}")

    apelido_empresa_normalizado = normalizar_string(apelido_empresa)

    logging.info(f"Parâmetro normalizado a ser enviado para a consulta: '{apelido_empresa_normalizado}'")

    db_params = {
        "host": os.getenv("DB_HOST"),
        "port": int(os.getenv("DB_PORT")),
        "dbname": os.getenv("DB_NAME"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD")
    }

    db_conn = DatabaseConnection(**db_params)
    db_conn.connect()
    if not db_conn.conn:
        logging.error("Conexão não foi estabelecida. Encerrando a busca.")
        return None, None

    query_empresa = """
        SELECT codi_emp, apel_emp, cgce_emp, LEFT(cgce_emp, 8) AS cnpj_base
        FROM bethadba.geempre 
        WHERE apel_emp LIKE ?;
    """

    empresa = db_conn.execute_query(query_empresa, (f'%{apelido_empresa_normalizado}%',))

    if empresa:
        codi_emp = empresa[0][0]
        apel_emp = empresa[0][1]
        cnpj_base = empresa[0][3]
        logging.info(f"Código da empresa encontrado: {codi_emp}, Apelido: {apel_emp}, CNPJ Base: {cnpj_base}")

        if 'FILIAL' in apel_emp.upper():
            query_matriz = """
                SELECT codi_emp, apel_emp
                FROM bethadba.geempre
                WHERE LEFT(cgce_emp, 8) = ? AND UPPER(apel_emp) NOT LIKE '%FILIAL%';
            """

            matriz = db_conn.execute_query(query_matriz, (cnpj_base,))
            if matriz:
                codi_emp_matriz = matriz[0][0]
                apel_emp_matriz = matriz[0][1]
                logging.info(f"Empresa é uma filial. Código da matriz encontrada: {codi_emp_matriz},"
                             f" Apelido da matriz: {apel_emp_matriz}")
                db_conn.close()
                return codi_emp, codi_emp_matriz
            else:
                logging.warning("Não foi possível encontrar a matriz correspondente.")
                db_conn.close()
                return codi_emp, None
        else:
            logging.info("Empresa não é uma filial.")
            db_conn.close()
            return codi_emp, None
    else:
        logging.error(f"Empresa com apelido '{apelido_empresa}' não encontrada no banco de dados.")

        db_conn.close()
        return None, None
