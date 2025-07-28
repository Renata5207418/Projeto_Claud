import sqlite3
import datetime
from datetime import timezone
from contextlib import contextmanager
from config.settings import settings

# arquivo SQLite
DB = settings.db_path


# ────────────────────────────────────────────────
# utilitários
# ────────────────────────────────────────────────
@contextmanager
def _conn():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def _now_iso() -> str:
    """Retorna timestamp UTC em ISO‑8601 (segundos)."""
    return datetime.datetime.now(timezone.utc).isoformat(timespec="seconds")


# ────────────────────────────────────────────────
# schema
# ────────────────────────────────────────────────
def init_db():
    """
    Cria (se faltar) a tabela `os_downloads`:

      os_id       PK
      status      pendente | aguardando | sucesso | falha
      tentativas quantas vezes falhou
      last_try   última vez que tentamos abrir (UTC)
      created_at inclusão
      updated_at última alteração
      (demais colunas: dados da OS)
    """
    with _conn() as c:
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS os_downloads (
                os_id         INTEGER PRIMARY KEY,
                status        TEXT,
                tentativas    INTEGER DEFAULT 0,
                last_try      TEXT,
                created_at    TEXT,
                updated_at    TEXT,

                apelido       TEXT,
                assunto       TEXT,
                descricao     TEXT,
                anexos_total  INTEGER,
                lido          INTEGER DEFAULT 0
            )
            """
        )
        c.commit()


# ────────────────────────────────────────────────
# helpers de acesso
# ────────────────────────────────────────────────
def exists(os_id: int) -> bool:
    """True se o registro já existe."""
    with _conn() as c:
        cur = c.execute("SELECT 1 FROM os_downloads WHERE os_id = ?", (os_id,))
        return cur.fetchone() is not None


def upsert_os(
    os_id: int,
    status: str = "pendente",
    *,
    last_try: str | datetime.datetime | None = None,
):
    """
    Insere nova OS OU atualiza status quando já existir.
    Não altera `tentativas`.

    last_try:
        • None  → timestamp agora
        • str   → usa como está
        • datetime → convertido p/ ISO
    """
    now = _now_iso()
    lt = (
        last_try.isoformat(timespec="seconds")
        if isinstance(last_try, datetime.datetime)
        else (last_try or now)
    )

    with _conn() as c:
        c.execute(
            """
            INSERT INTO os_downloads
                (os_id, status, tentativas, last_try, created_at, updated_at)
            VALUES (?,     ?,      0,          ?,       ?,          ?)
            ON CONFLICT(os_id)
            DO UPDATE SET
                status     = excluded.status,
                last_try   = excluded.last_try,
                updated_at = excluded.updated_at
            """,
            (os_id, status, lt, now, now),
        )
        c.commit()


def mark_status(
    os_id: int,
    status: str,
    *,
    inc_try: bool = False,
    extra: dict | None = None,
):
    """
    Atualiza status + updated_at + last_try.
    Se `inc_try=True`, incrementa `tentativas`.
    Aceita colunas extras via dicionário.
    """
    now = _now_iso()
    sets = ["status = ?", "updated_at = ?", "last_try = ?"]
    params: list = [status, now, now]

    if inc_try:
        sets.insert(1, "tentativas = tentativas + 1")

    if extra:
        for k, v in extra.items():
            sets.append(f"{k} = ?")
            params.append(v)

    params.append(os_id)
    with _conn() as c:
        c.execute(f"UPDATE os_downloads SET {', '.join(sets)} WHERE os_id = ?", params)
        c.commit()


def list_by_status(statuses: tuple[str, ...], max_try: int | None = None) -> list[int]:
    """
    Lista IDs cujo `status` esteja em `statuses`.
    Se max_try ≠ None, filtra tentativas < max_try.
    """
    placeholders = ",".join("?" * len(statuses))
    params: list = list(statuses)
    cond_try = ""

    if max_try is not None:
        cond_try = "AND tentativas < ?"
        params.append(max_try)

    sql = (
        f"SELECT os_id FROM os_downloads "
        f"WHERE status IN ({placeholders}) {cond_try} "
        f"ORDER BY created_at"
    )
    with _conn() as c:
        cur = c.execute(sql, params)
        return [row["os_id"] for row in cur.fetchall()]


def list_for_retry(status: str, max_try: int, cooldown_minutes: int) -> list[int]:
    """
    IDs nesse `status` que:
      • tentativas < max_try
      • last_try <= agora - cooldown_minutes
    """
    sql = """
        SELECT os_id
        FROM os_downloads
        WHERE status = ?
          AND tentativas < ?
          AND datetime(last_try) <= datetime('now', ?)
        ORDER BY created_at
    """
    offset = f"-{cooldown_minutes} minutes"
    with _conn() as c:
        cur = c.execute(sql, (status, max_try, offset))
        return [row["os_id"] for row in cur.fetchall()]
