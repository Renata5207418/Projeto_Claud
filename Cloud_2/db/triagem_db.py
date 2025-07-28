import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from contextlib import contextmanager
from config.settings import settings

# Caminho para o arquivo SQLite de triagem (padrão: ROOT_DIR/triage_status.db
DB_PATH: Path = settings.triage_db_path


@contextmanager
def _c():
    """
    Context manager para conexão SQLite com o banco de triagem.
    Garante fechamento da conexão após uso.
    """
    conn = sqlite3.connect(str(DB_PATH))
    try:
        yield conn
    finally:
        conn.close()


def init():
    """
    Inicializa a tabela `os_triagem` se não existir.
    Campos:
      - os_id           INTEGER PRIMARY KEY
      - pasta           TEXT (nome da pasta separada, ex. "12345-APELIDO")
      - triagem_status TEXT ("Pendente" | "Triada")
      - tomados_status TEXT ("Nenhum" | "Pendente" | "Concluído")
      - tentativas     INTEGER DEFAULT 0
      - pasta_cliente   TEXT (caminho de destino no cliente)
      - gerou_tomados   INTEGER (0/1)
      - gerou_extrato   INTEGER (0/1)
      - updated_at      TEXT (timestamp ISO UTC)
    """
    with _c() as c:
        c.execute("""
        CREATE TABLE IF NOT EXISTS os_triagem (
            os_id           INTEGER PRIMARY KEY,
            pasta           TEXT,
            triagem_status  TEXT,      -- Pendente | Triada
            tomados_status  TEXT,      -- Nenhum | Pendente | Concluído
            tentativas      INTEGER DEFAULT 0,
            pasta_cliente   TEXT,
            gerou_tomados   INTEGER,   -- 0/1
            gerou_extrato   INTEGER,   -- 0/1
            pubsub_ok       INTEGER DEFAULT 0,
            updated_at      TEXT
        )""")
        c.commit()


def set_pubsub_ok(os_id: int) -> None:
    """Marca pubsub_ok =1 e atualiza updated_at."""
    with _c() as c:
        c.execute("""
            UPDATE os_triagem
               SET pubsub_ok = 1,
                   updated_at = datetime('now')
             WHERE os_id = ?
        """, (os_id,))
        c.commit()


def get_pubsub_status(os_id: int) -> bool:
    """
    Verifica se a notificação Pub/Sub para uma OS já foi enviada.
    Retorna True se pubsub_ok = 1, caso contrário False.
    """
    with _c() as c:
        cur = c.execute("SELECT pubsub_ok FROM os_triagem WHERE os_id=?", (os_id,))
        row = cur.fetchone()
        # Retorna True se row não for None e o primeiro campo (pubsub_ok) for 1
        return bool(row and row[0] == 1)


def extrair_apelido(nome_pasta: str) -> str:
    """
    Extrai o apelido da pasta no formato "12345-APELIDO":
      - entrada: "26686-B&F GESTAO DE ATIVOS"
      - saída: "B&F GESTAO DE ATIVOS"
    Se não houver "-", retorna o nome inteiro.
    """
    return nome_pasta.split('-', 1)[1].strip() if '-' in nome_pasta else nome_pasta


def get_max_downloaded_id() -> int:
    """
    Retorna o maior `os_id` já presente em settings.separados_dir,
    analisando nomes de pasta com prefixo numérico antes de "-".
    Útil para determinar até onde já fizeram download.
    """
    return max((int(p.name.split('-')[0])
                for p in settings.separados_dir.iterdir()
                if '-' in p.name and p.name.split('-')[0].isdigit()),
               default=0)


def list_download_ids():
    """
    Lista todos os `os_id` presentes em settings.separados_dir,
    conforme a convenção de nomes "ID-...".
    """
    return [int(p.name.split('-')[0])
            for p in settings.separados_dir.iterdir()
            if '-' in p.name and p.name.split('-')[0].isdigit()]


def list_separacao_ids():
    """
    Retorna todos os `os_id` cujo `triagem_status` é 'Triada' na tabela `os_triagem`.
    """
    with _c() as c:
        cur = c.execute("SELECT os_id FROM os_triagem WHERE triagem_status = 'Triada'")
        return [r[0] for r in cur.fetchall()]


def list_tomados_pendentes():
    """
    Retorna os `os_id` com `tomados_status` = 'Pendente', indicando
    que ainda faltam processar os documentos 'tomados'.
    """
    with _c() as c:
        cur = c.execute("SELECT os_id FROM os_triagem WHERE tomados_status = 'Pendente'")
        return [r[0] for r in cur.fetchall()]


def register_separacao(*, os_id: int, pasta: str, pasta_cliente: str, tomados: str, extrato: str) -> None:
    """
    Registra (ou atualiza) a triagem de uma OS como 'Triada'.

    Parâmetros:
      os_id         — identificador da OS
      pasta         — nome da pasta de origem (apelido)
      pasta_cliente — caminho de destino na estrutura do cliente
      tomados       — "SIM" ou "NÃO" (se gerou documentos 'tomados')
      extrato       — "SIM" ou "NÃO" (se gerou extrato)

    Lógica:
      - `gerou_tomados` = 1 se tomados == "SIM", caso contrário 0
      - `gerou_extrato` = 1 se extrato == "SIM", caso contrário 0
      - `triagem_status` sempre 'Triada'
      - `tomados_status` = 'Pendente' se gerou_tomados = 1, senão 'Nenhum'
      - Usa INSERT ... ON CONFLICT para manter histórico de status de tomados:
        se já estiver 'Concluído', não reverte; senão, atualiza conforme `excluded`.
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    gerou_tomados = 1 if tomados == "SIM" else 0
    gerou_extrato = 1 if extrato == "SIM" else 0
    triagem_status = "Triada"
    tomados_status = "Pendente" if gerou_tomados else "Nenhum"

    with _c() as c:
        c.execute("""
        INSERT INTO os_triagem (os_id, pasta, triagem_status, tomados_status,
                                pasta_cliente, gerou_tomados, gerou_extrato,
                                updated_at)
        VALUES (?,?,?,?,?,?,?,?)
        ON CONFLICT(os_id) DO UPDATE
          SET triagem_status = 'Triada',
              tomados_status = CASE
                   WHEN os_triagem.tomados_status = 'Concluído' THEN 'Concluído'
                   WHEN excluded.gerou_tomados = 1               THEN 'Pendente'
                   ELSE 'Nenhum'
              END,
              pasta         = excluded.pasta,
              pasta_cliente = excluded.pasta_cliente,
              gerou_tomados = excluded.gerou_tomados,
              gerou_extrato = excluded.gerou_extrato,
              updated_at    = excluded.updated_at
        """, (os_id, pasta, triagem_status, tomados_status,
              pasta_cliente, gerou_tomados, gerou_extrato, now_iso))
        c.commit()


def set_triagem_status(os_id: int, status: str, *, inc_try: bool = False, extra: dict | None = None) -> None:
    """
       Atualiza ou insere o status de triagem para uma OS.

       Parâmetros:
         os_id   — identificador da OS
         status — por exemplo, 'Pendente', 'processando', 'falha', 'Triada'
         inc_try — se True, incrementa o contador de tentativas
         extra   — dict com chaves opcionais:
                     - 'cliente_path' (novo valor para pasta_cliente)
                     - 'gerou_tomados' (0/1)
                     - 'gerou_extrato' (0/1)

       Comportamento:
         - Obtém tentativas atuais, soma 1 se inc_try
         - Usa INSERT ... ON CONFLICT para criar ou atualizar o registro
       """
    extra = extra or {}
    now_iso = datetime.now(timezone.utc).isoformat()

    with _c() as c:
        cur = c.execute(
            "SELECT tentativas FROM os_triagem WHERE os_id=?", (os_id,)
        )
        tent_atual = cur.fetchone()
        tentativas = (tent_atual[0] if tent_atual else 0) + (1 if inc_try else 0)

        c.execute("""
        INSERT INTO os_triagem (os_id, triagem_status, tentativas,
                                pasta_cliente, gerou_tomados, gerou_extrato,
                                updated_at)
        VALUES (?,?,?,?,?,?,?)
        ON CONFLICT(os_id) DO UPDATE
          SET triagem_status = excluded.triagem_status,
              tentativas     = excluded.tentativas,
              pasta_cliente  = excluded.pasta_cliente,
              gerou_tomados  = excluded.gerou_tomados,
              gerou_extrato  = excluded.gerou_extrato,
              updated_at     = excluded.updated_at
        """, (
            os_id,
            status,
            tentativas,
            extra.get("cliente_path"),
            extra.get("gerou_tomados", 0),
            extra.get("gerou_extrato", 0),
            now_iso,
        ))
        c.commit()


def get_tentativas(os_id: int) -> int:
    """
    Retorna o número de tentativas já registradas em `os_triagem` para a OS.
    Se não existir registro, retorna 0.
    """
    with _c() as c:
        cur = c.execute("SELECT tentativas FROM os_triagem WHERE os_id=?", (os_id,))
        row = cur.fetchone()
        return row[0] if row else 0


def get_tomados_status(os_id: int) -> str | None:
    """
     Retorna o `tomados_status` atual ('Nenhum', 'Pendente' ou 'Concluído')
     para a OS. Se não existir registro, retorna None.
     """
    with _c() as c:
        cur = c.execute("SELECT tomados_status FROM os_triagem WHERE os_id=?", (os_id,))
        row = cur.fetchone()
        return row[0] if row else None


def set_tomados_status(os_id: int, status: str) -> None:
    """
    Atualiza apenas o campo `tomados_status` de uma OS já registrada,
    além de ajustar o campo `updated_at` para o timestamp atual.
    """
    with _c() as c:
        c.execute("""
            UPDATE os_triagem
               SET tomados_status = ?,
                   updated_at     = datetime('now')
             WHERE os_id = ?""", (status, os_id))
        c.commit()
