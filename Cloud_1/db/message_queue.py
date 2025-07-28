import sqlite3
import contextlib
import datetime
from datetime import timezone
from config.settings import settings

_QDB = settings.root_dir / "queue.db"


@contextlib.contextmanager
def _conn():
    """
    Context manager para conexão com o banco da fila.
    Abre e fecha a conexão automaticamente.
    """
    conn = sqlite3.connect(_QDB)
    try:
        yield conn
    finally:
        conn.close()


def _init():
    """
    Inicializa a tabela `queue` caso não exista.
    Executa no carregamento do módulo.
    """
    with _conn() as c:
        c.execute("""
          CREATE TABLE IF NOT EXISTS queue (
              id     INTEGER PRIMARY KEY AUTOINCREMENT,
              os_id  INTEGER,
              enqueued_at TEXT
          )
        """)
        c.commit()


# Cria a tabela na importação do módulo
_init()


def publish(os_id: int):
    """
    Adiciona um item à fila.

    Parâmetro:
      os_id: identificador da OS a enfileirar

    Ação:
      - Insere registro (os_id, timestamp UTC) na tabela.
    """
    with _conn() as c:
        c.execute("INSERT INTO queue (os_id, enqueued_at) VALUES (?, ?)",
                  (os_id, datetime.datetime.now(timezone.utc).isoformat()))
        c.commit()


def pull() -> int | None:
    """
    Remove e retorna o próximo `os_id` da fila, seguindo ordem FIFO.

    Retorno:
      - o `os_id` do item removido, ou
      - None se a fila estiver vazia
    """
    with _conn() as c:
        cur = c.execute("SELECT id, os_id FROM queue ORDER BY id LIMIT 1")
        row = cur.fetchone()
        if not row:
            return None
        qid, os_id = row
        c.execute("DELETE FROM queue WHERE id=?", (qid,))
        c.commit()
        return os_id
