import sqlite3
from contextlib import contextmanager
from config.settings import settings

# Caminho para o banco SQLite da fila, definido em QUEUE_DB_PATH no .env
_QDB = settings.queue_db_path


@contextmanager
def _conn():
    """
    Context manager para conexão com o SQLite.
    Garante fechamento da conexão mesmo se ocorrerem erros.
    """
    conn = sqlite3.connect(str(_QDB))
    try:
        yield conn
    finally:
        conn.close()


def _init():
    """
    Cria a tabela `queue` se não existir.
    Executado automaticamente ao importar o módulo.
    """
    with _conn() as c:
        c.execute("""
          CREATE TABLE IF NOT EXISTS queue (
              id          INTEGER PRIMARY KEY AUTOINCREMENT,
              os_id       INTEGER UNIQUE,
              enqueued_at TEXT DEFAULT CURRENT_TIMESTAMP
          )
        """)
        c.commit()


_init()


def pull_one() -> int | None:
    """
    Remove e retorna o próximo `os_id` da fila (FIFO).

    Retorno:
      - o `os_id` do item mais antigo, ou
      - None se a fila estiver vazia
    """
    with _conn() as c:
        row = c.execute(
            "SELECT id, os_id FROM queue ORDER BY id LIMIT 1"
        ).fetchone()
        if not row:
            return None
        qid, os_id = row
        c.execute("DELETE FROM queue WHERE id=?", (qid,))
        c.commit()
        return os_id


def requeue(os_id: int) -> None:
    """
    Reinsere um `os_id` na fila, mas somente se ainda não estiver presente
    (evita duplicatas via UNIQUE constraint em os_id).

    Parâmetro:
      os_id: identificador da OS a re‐enfileirar
    """
    with _conn() as c:
        c.execute(
            "INSERT OR IGNORE INTO queue (os_id) VALUES (?)",
            (os_id,),
        )
        c.commit()
