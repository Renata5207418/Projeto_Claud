import sqlite3
from pathlib import Path
from contextlib import contextmanager
from config.settings import settings

TRIAGE_DB: Path = settings.triage_db_path


@contextmanager
def db_conn():
    """
    Context manager para conexão com o banco de triagem.
    Garante que conn.close() seja chamado após uso.
    """
    conn = sqlite3.connect(str(TRIAGE_DB))
    try:
        yield conn
    finally:
        conn.close()


def get_tomados_status(os_id: int) -> str | None:
    """
    Consulta o campo `tomados_status` para a OS especificada.

    Parâmetros:
      os_id: identificador da ordem de serviço

    Retorna:
      - 'Nenhum', 'Pendente' ou 'Concluído', se existir registro
      - None, se não houver registro para esse os_id
    """
    with db_conn() as c:
        cur = c.execute(
            "SELECT tomados_status FROM os_triagem WHERE os_id=?", (os_id,)
        )
        row = cur.fetchone()
        return row[0] if row else None


def set_tomados_concluido(os_id: int) -> None:
    """
    Atualiza o status de `tomados_status` para 'Concluído' para a OS indicada.

    Parâmetros:
      os_id: identificador da ordem de serviço

    Nota:
      - Também atualiza o campo `updated_at` usando datetime('now') do SQLite.
    """
    with db_conn() as c:
        c.execute(
            """
            UPDATE os_triagem
               SET tomados_status = 'Concluído',
                   updated_at     = datetime('now')
             WHERE os_id = ?
            """,
            (os_id,),
        )
        c.commit()


def list_pendentes() -> list[int]:
    """
    Retorna OS cujo `tomados_status` está 'Pendente'
    **e** que não foram tocadas há, p.ex., > 2 h.

    Isso evita reenfileirar imediatamente algo que o Pub/Sub
    ainda pode estar processando.
    """
    with db_conn() as c:
        cur = c.execute(
            """
            SELECT os_id
              FROM os_triagem
             WHERE tomados_status = 'Pendente'
               AND (updated_at IS NULL
                    OR updated_at < datetime('now','-1 minute'))
            """
        )
        return [r[0] for r in cur.fetchall()]


def claim_pendentes(limite: int = 20) -> list[int]:
    """
    Marca até `limite` OS com tomados_status='Pendente' como 'Processando'
    e devolve a lista de ids. Evita que dois workers peguem a mesma OS.
    """
    ids: list[int] = []
    with db_conn() as c:
        for _ in range(limite):
            cur = c.execute("""
                UPDATE os_triagem
                   SET tomados_status = 'Processando',
                       updated_at     = datetime('now')
                 WHERE os_id = (
                       SELECT os_id
                         FROM os_triagem
                        WHERE tomados_status = 'Pendente'
                        ORDER BY updated_at
                        LIMIT 1
                   )
             RETURNING os_id""")
            row = cur.fetchone()
            if not row:
                break
            ids.append(row[0])
        c.commit()
    return ids
