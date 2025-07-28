from fastapi import FastAPI
from db import db
import sqlite3


app = FastAPI()


@app.get("/overview")
def overview():
    """
        Retorna um JSON com a contagem de OS em cada status.

        Chamadas internas:
          db.list_by_status(("pendente",)) — retorna lista de OS pendentes
          db.list_by_status(("sucesso",)) — retorna lista de OS com sucesso
          db.list_by_status(("falha",)) — retorna lista de OS com falha

        Resposta:
          {
            "pendentes": <int>,
            "sucesso":   <int>,
            "falha":     <int>
          }
        """
    pend = len(db.list_by_status(("pendente",)))
    ok = len(db.list_by_status(("sucesso",)))
    falhas = len(db.list_by_status(("falha",)))
    return {"pendentes": pend, "sucesso": ok, "falha": falhas}


@app.get("/os/{os_id}")
def get_os(os_id: int):
    """
        Busca detalhes de uma ordem de serviço pelo seu ID.

        Parâmetros:
          os_id: int — identificador da OS

        Funcionamento:
          - Abre uma conexão SQLite apontando para db.DB
          - Configura row_factory para sqlite3.Row (permite dict(row))
          - Executa SELECT * FROM os_downloads WHERE os_id=?
          - Se encontrar: retorna todos os campos como dicionário
          - Se não: retorna {"erro": "não encontrada"}

        Atenção à configuração:
          * Verifique em db.DB se o caminho para o arquivo .sqlite fica num .env
            (evite ter algo como "/caminho/absoluto/qualquer.sqlite" no código).
        """
    with sqlite3.connect(db.DB) as c:
        c.row_factory = sqlite3.Row
        cur = c.execute("SELECT * FROM os_downloads WHERE os_id=?", (os_id,))
        row = cur.fetchone()
        return dict(row) if row else {"erro": "não encontrada"}
