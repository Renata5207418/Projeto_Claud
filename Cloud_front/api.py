import datetime
import io
import os
import json
import tempfile
import zipfile
import sqlite3
from datetime import timezone
from pathlib import Path
import pandas as pd
from fastapi.responses import StreamingResponse
from google.cloud import storage
from pydantic import BaseModel
from fastapi import FastAPI, Response, HTTPException, Query
from fastapi.responses import HTMLResponse
from fastapi import Request
import pathlib
import aiosqlite
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Depends
from auth_routes import router as auth_router
from auth_routes import get_current_user
from fastapi.security import HTTPBearer
from dotenv import load_dotenv

auth_scheme = HTTPBearer(auto_error=False)


# Carrega variáveis de ambiente de `.env`
load_dotenv()

# ───────── Caminhos base de cada cloud ─────────
BASE1 = pathlib.Path(r"C:/Users/usuario/PycharmProjects/Cloud_1")   # Cloud_1: downloads
BASE2 = pathlib.Path(r"C:/Users/usuario/PycharmProjects/Cloud_2")   # Cloud_2: triagem
BASE3 = pathlib.Path(r"C:/Users/usuario/PycharmProjects/Cloud_3")   # Cloud_3: tomados


# Arquivos de heartbeat para cada ambiente
HEART1 = BASE1 / "heartbeat.json"
HEART2 = BASE2 / "heartbeat.json"
HEART3 = BASE3 / "heartbeat.json"

app = FastAPI()
# Configura CORS para frontend em localhost:3000/3001
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router)


# ───────── Endpoint: exportar relatório Excel ─────────
@app.get("/export")
def export_report(month: str = Query(..., regex=r"^\d{4}\-\d{2}$")):
    """
        Gera um arquivo Excel consolidado para o mês informado (YYYY-MM),
        contendo três abas: Downloads, Triagem e Mensagens.
        - Lê os bancos sqlite de Cloud_1 (os_downloads) e Cloud_2 (os_triagem).
        - Filtra por created_at/updated_at no mês especificado.
        - Formata colunas de data e renomeia cabeçalhos.
        - Aplica styling no cabeçalho e autofiltro.
        - Retorna StreamingResponse com `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`.
    """
    try:
        # ── 1) Carrega dados ────────────────────────────────────────────────────
        conn1 = sqlite3.connect(str(BASE1 / "os_status.db"))
        conn2 = sqlite3.connect(str(BASE2 / "triage_status.db"))

        df_dl = (
            pd.read_sql_query(
                "SELECT * FROM os_downloads WHERE substr(created_at,1,7)=?",
                conn1,
                params=[month]
            )
            .drop(columns=[
                "assunto",
                "descricao",
                "created_at",
                "lido",
                "updated_at",
                "last_try"
            ])
        )

        df_tri = pd.read_sql_query(
            "SELECT * FROM os_triagem WHERE substr(updated_at,1,7)=?",
            conn2,
            params=[month]
        )
        if "pasta_cliente" in df_tri.columns:
            df_tri["Copiado p/ Cliente"] = df_tri["pasta_cliente"].apply(
                lambda x: "SIM" if isinstance(x, str) and x and "NÃO ENVIADO" not in x else "NÃO"
            )

        # AJUSTE: Remove colunas desnecessárias, incluindo "updated_at"
        for col in ["pasta_cliente", "pubsub_ok", "updated_at"]:
            if col in df_tri.columns:
                df_tri = df_tri.drop(columns=[col])

        df_msg = pd.read_sql_query(
            """
            SELECT
              os_id   AS OS,
              apelido AS Empresa,
              assunto AS Assunto,
              descricao AS Descrição
            FROM os_downloads
            WHERE substr(updated_at,1,7)=?
            """,
            conn1,
            params=[month]
        )

        conn1.close()
        conn2.close()

        # ── 2) Renomeia colunas de Downloads e Triagem ────────────────────────
        df_dl = df_dl.rename(columns={
            "os_id": "OS",
            "status": "Status Download",
            "tentativas": "Tentativas",
            "apelido": "Empresa",
            "anexos_total": "Total Anexos"
        })
        df_tri = df_tri.rename(columns={
            "os_id": "OS",
            "pasta": "Pasta",
            "triagem_status": "Status Triagem",
            "tomados_status": "Status Tomados",
            "gerou_tomados": "Gerou Tomados",
            "gerou_extrato": "Gerou Extrato"
        })

        # ── 4) Gera o Excel com styling ───────────────────────────────────────
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df_dl.to_excel(writer, sheet_name="Downloads", index=False)
            df_tri.to_excel(writer, sheet_name="Triagem", index=False)
            df_msg.to_excel(writer, sheet_name="Mensagens", index=False)

            wb = writer.book
            ws_dl = writer.sheets["Downloads"]
            ws_tri = writer.sheets["Triagem"]
            ws_msg = writer.sheets["Mensagens"]

            header_fmt = wb.add_format({
                "bold": True, "bg_color": "#fbba00", "font_color": "#FFFFFF",
                "border": 1, "align": "center", "valign": "vcenter"
            })
            fmt_bom = wb.add_format({"bg_color": "#C6EFCE", "font_color": "#006100"})
            fmt_ruim = wb.add_format({"bg_color": "#FFC7CE", "font_color": "#9C0006"})

            # Aplica formatação condicional na aba "Triagem"
            num_rows = len(df_tri)
            if num_rows > 0:
                for col_name, values in {
                    "Gerou Tomados": ("SIM", "NÃO"),
                    "Gerou Extrato": ("SIM", "NÃO"),
                    "Copiado p/ Cliente": ("SIM", "NÃO"),
                }.items():
                    if col_name in df_tri.columns:
                        col_idx = df_tri.columns.get_loc(col_name)
                        ws_tri.conditional_format(1, col_idx, num_rows, col_idx,
                                                  {"type": "cell", "criteria": "==", "value": f'"{values[0]}"',
                                                   "format": fmt_bom})
                        ws_tri.conditional_format(1, col_idx, num_rows, col_idx,
                                                  {"type": "cell", "criteria": "==", "value": f'"{values[1]}"',
                                                   "format": fmt_ruim})

            # Aplica styling geral
            for ws, df in ((ws_dl, df_dl), (ws_tri, df_tri), (ws_msg, df_msg)):
                ws.freeze_panes(1, 0)
                ws.autofilter(0, 0, len(df) - 1 if len(df) > 0 else 0, len(df.columns) - 1)
                for idx, col in enumerate(df.columns):
                    ws.write(0, idx, col, header_fmt)
                    max_len = max(df[col].astype(str).map(len).max(), len(col)) if len(df) > 0 else len(col)
                    ws.set_column(idx, idx, max_len + 3)

        output.seek(0)
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=relatorio_{month}.xlsx"}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar export: {e}")


# ───────── helper para mensagens dos clientes ─────────
class LidoUpdate(BaseModel):
    lido: bool


@app.post("/mark_lido/{os_id}")
async def mark_lido(os_id: int, payload: LidoUpdate):
    """
       Atualiza o campo `lido` na tabela os_downloads (Cloud_1) para ON/OFF.
       Recebe JSON: { "lido": true/false }.
    """
    try:
        db_path = r"C:\Users\usuario\PycharmProjects\Cloud_1\os_status.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        lido_int = 1 if payload.lido else 0

        cursor.execute(
            """
            UPDATE os_downloads
            SET lido = ?, updated_at = datetime('now')
            WHERE os_id = ?
            """,
            (lido_int, os_id)
        )
        conn.commit()
        conn.close()
        return {"message": "Status de leitura atualizado com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar o status: {e}")


# ───────── Helpers genéricos para leitura de DB ─────────
async def fetch_rows(db: pathlib.Path, query: str):
    """
    Conecta via aiosqlite e executa SELECT.
    Retorna lista de dicts, renomeando `os_id` para `id` no JSON.
    """
    async with aiosqlite.connect(db) as conn:
        conn.row_factory = aiosqlite.Row
        rows = await conn.execute_fetchall(query)

    # ---------- DEBUG ----------
    if rows:
        print(">>> DEBUG keys:", list(rows[0].keys()))
        print(">>> DEBUG row :", dict(rows[0]))
    # ---------------------------

    return [
        {**dict(r), "id": r["os_id"] if "os_id" in r.keys() else r["os"]}
        for r in rows
    ]


def read_hb(path: pathlib.Path):
    """
    Lê heartbeat.json e devolve:
      { state: running/idle/down, age: seg, msg: str }
    Considera running  <120 s, idle <600 s, down >=600 s.
    """
    try:
        data = json.loads(path.read_text())

        # converte "2025-07-17T16:32:10Z" →  datetime com tz UTC
        ts = datetime.datetime.fromisoformat(
            data["ts"].replace("Z", "+00:00")
        )

        age_sec = (datetime.datetime.now(datetime.timezone.utc) - ts).total_seconds()

        if age_sec < 120:
            state = "running"
        elif age_sec < 600:
            state = "idle"
        else:
            state = "down"

        return {"state": state, "age": int(age_sec), "msg": data.get("msg", "")}

    except Exception as e:
        # log opcional: print(f"read_hb erro: {e}")
        return {"state": "unknown", "age": None, "msg": ""}


# ───────── Endpoint: lista downloads (Cloud_1) ─────────
@app.get("/downloads")
async def get_downloads(_: str = Depends(get_current_user)):
    """
    Retorna os últimos 200 registros de os_downloads:
      os_id, status, tentativas, created_at (ISO), updated_at (ISO), apelido, anexos_total
    """
    sql = """
    SELECT
        os_id,               
        status,
        tentativas,        
        REPLACE(substr(created_at, 1, 19), ' ', 'T') || 'Z'  AS created_at,
        REPLACE(substr(updated_at, 1, 19), ' ', 'T') || 'Z'  AS updated_at,
        apelido,
        anexos_total
    FROM os_downloads
    ORDER BY os_id DESC
    LIMIT 200
    """
    db = BASE1 / "os_status.db"
    return await fetch_rows(db, sql)


# ───────── Endpoint: lista triagem (Cloud_2) ─────────
@app.get("/triagem")
async def get_triagem(_: str = Depends(get_current_user)):
    """
    Retorna todos os registros de os_triagem:
      os_id, pasta, triagem_status, tomados_status, gerou_tomados, gerou_extrato, updated_at
    """
    sql = """
    SELECT
        os_id,
        pasta,
        triagem_status,
        tomados_status,
        gerou_tomados,
        gerou_extrato,
        updated_at
    FROM os_triagem
    ORDER BY updated_at DESC
    """
    db = BASE2 / "triage_status.db"
    return await fetch_rows(db, sql)


@app.get("/tomados/{pasta:path}")
def baixar_zip_txt(pasta: str):
    """
    Converte os TXT gerados no Cloud 3 para uma planilha XLSX formatada
    e devolve tudo em um ZIP (um XLSX por TXT).

    Bucket: gs://claudio-tomados
    Prefixo: tomados_saida/{pasta}/
    """
    print("Recebeu pasta:", repr(pasta))
    if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = (
            r"C:/Users/usuario/PycharmProjects/Cloud_front/keys/credenciais_Cloud.json"
        )

    client = storage.Client()
    bucket = client.bucket("claudio-tomados")
    prefix = f"tomados_saida/{pasta}/"
    blobs = list(bucket.list_blobs(prefix=prefix))

    if not blobs:
        return Response(content=b"Nenhum arquivo encontrado!", status_code=404)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        zip_path = tmpdir / f"{pasta}_planilhas.zip"

        with zipfile.ZipFile(zip_path, "w") as zipf:
            for blob in blobs:
                local_txt = tmpdir / Path(blob.name).name
                blob.download_to_filename(str(local_txt))
                print(f"Baixou TXT: {local_txt.name}")

                if local_txt.suffix.lower() != ".txt":
                    print(f"Ignorando (não é TXT): {local_txt.name}")
                    continue

                # ── 1) Lê o TXT (UTF-8 ou Latin-1) ────────────────────────────
                with open(local_txt, "rb") as fb:
                    raw = fb.read()
                try:
                    text = raw.decode("utf-8")
                except UnicodeDecodeError:
                    text = raw.decode("latin-1")

                # ── 2) Carrega em DataFrame diretamente ──────────────────────
                df = pd.read_csv(
                    io.StringIO(text),
                    sep=";",
                    header=None,        # TXT não traz “header oficial”
                    dtype=str,
                    keep_default_na=False
                )

                # Se o primeiro registro for cabeçalho, use-o:
                if all(cell.isalpha() for cell in df.iloc[0].fillna("")):
                    df.columns = df.iloc[0]
                    df = df.drop(index=0).reset_index(drop=True)

                # ── 3) Gera XLSX formatado ───────────────────────────────────
                xlsx_file = local_txt.with_suffix(".xlsx")
                with pd.ExcelWriter(xlsx_file, engine="xlsxwriter") as writer:
                    df.to_excel(writer, sheet_name="Tomados", index=False)
                    wb = writer.book
                    ws = writer.sheets["Tomados"]

                    header_fmt = wb.add_format(
                        {"bold": True, "bg_color": "#F1C40F", "border": 1}
                    )
                    ws.freeze_panes(1, 0)
                    ws.autofilter(0, 0, 0, len(df.columns)-1)

                    for col_idx, col_name in enumerate(df.columns):
                        ws.write(0, col_idx, col_name, header_fmt)
                        largura = max(
                            df[col_name].astype(str).map(len).max(),
                            len(str(col_name))
                        )
                        ws.set_column(col_idx, col_idx, largura + 2)

                zipf.write(xlsx_file, arcname=xlsx_file.name)
                print(f"Adicionado XLSX: {xlsx_file.name}")

        return Response(
            content=zip_path.read_bytes(),
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={pasta}_planilhas.zip"}
        )


# ───────── Endpoint: lista mensagens (Cloud_1) ─────────
@app.get("/mensagens")
async def get_mensagens(_: str = Depends(get_current_user)):
    """
    Retorna os registros de mensagens de clientes:
      os_id, apelido, assunto, descricao, lido
    """
    sql = """
    SELECT
        os_id,            
        apelido,                    
        assunto,                    
        descricao,                   
        lido
    FROM os_downloads
    ORDER BY os_id DESC
    """
    db = BASE1 / "os_status.db"
    return await fetch_rows(db, sql)


# ───────── Endpoint: health check dos 3 clouds ─────────
@app.get("/status")
async def get_status(_: str = Depends(get_current_user)):
    """
    Retorna o estado de cada ambiente (cloud1, cloud2, cloud3)
    com base nos respectivos heartbeat.json, mais timestamp do servidor.
    """
    return {
        "cloud1": read_hb(HEART1),
        "cloud2": read_hb(HEART2),
        "cloud3": read_hb(HEART3),
        "server_time": datetime.datetime.now(timezone.utc).isoformat(timespec="seconds") + "Z",
    }


# ───────── Helper para erro ─────────
@app.exception_handler(404)
async def custom_404_handler(request: Request, exc):
    return HTMLResponse(
        '''
        <div style="font-family: Verdana, Geneva, sans-serif; font-size: 10pt; color: #222; background: #111; padding: 24px;">
          <h2 style="color: #F1C40F;">Página não encontrada</h2>
          <p>O link acessado não existe ou expirou.</p>
          <a href="http://localhost:3000/" style="color: #F1C40F; text-decoration: underline;">Voltar para o início</a>
        </div>
        ''',
        status_code=404
    )

# Inicie a API com:
#   uvicorn api:app --reload
