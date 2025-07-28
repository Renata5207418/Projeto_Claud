import datetime as _dt
import os
import secrets
import sqlite3
import resend
from fastapi import APIRouter, HTTPException, Depends, Cookie, Security
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm, HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from jose import JWTError
from auth_utils import (
    get_user, verify_password, hash_password,
    create_access_token, create_refresh_token, decode_token
)
from dotenv import load_dotenv
load_dotenv()


# ─── Config -------------------------------------------------------------------
resend.api_key = os.getenv("RESEND_API_KEY")
print(os.getenv("RESEND_API_KEY"))
FROM_EMAIL = "onboarding@resend.dev"
RESET_EXP_MIN = 60

router = APIRouter(prefix="/auth", tags=["auth"])
auth_scheme = HTTPBearer(auto_error=False)


# ─── Utilitário de e‑mail -----------------------------------------------------
def send_reset_email(to_email: str, token: str):
    RESET_URL = f"http://localhost:3000/reset?token={token}"
    email_html = f"""
    <div style="font-family: Verdana, Geneva, sans-serif; font-size: 10pt; color: #222;">
        <p>Você solicitou a redefinição de senha para sua conta.</p>
        <p>
            <a href="{RESET_URL}"
               style="background: #F1C40F; color: #222; font-weight: bold; padding: 10px 18px; border-radius: 5px; text-decoration: none; display: inline-block;">
               Clique aqui para redefinir sua senha
            </a>
        </p>
        <p style="font-size: 9pt; color: #888;">
            (Se não foi você, pode ignorar este e-mail)
        </p>
    </div>
    """

    payload = {
        "from": FROM_EMAIL,
        "to": [to_email],
        "subject": "Recuperar senha",
        "html": email_html,
    }

    try:
        response = resend.Emails.send(payload)
        print("Resposta do Resend:", response)
    except Exception as e:
        print(f"Erro ao enviar e-mail via Resend: {e}")
        if hasattr(e, 'response'):
            print(f"Detalhes da resposta: {e.response.text}")
        raise HTTPException(status_code=500, detail=f"Erro ao enviar e-mail: {str(e)}")


# ─── Helpers ------------------------------------------------------------------
def get_current_user(creds: HTTPAuthorizationCredentials = Security(auth_scheme)):
    if creds is None:
        raise HTTPException(status_code=401, detail="Missing token")
    try:
        payload = decode_token(creds.credentials)
        if payload.get("type") != "access":
            raise ValueError()
        return payload["sub"]
    except (JWTError, ValueError):
        raise HTTPException(status_code=401, detail="Token inválido")


# ─── Schemas ------------------------------------------------------------------
class PwChange(BaseModel):
    old_password: str
    new_password: str


class Forgot(BaseModel):
    email: str


class ResetPw(BaseModel):
    token: str
    new_password: str


class RegisterUser(BaseModel):
    username: str
    email: EmailStr
    password: str


# ─── Rotas --------------------------------------------------------------------
@router.post("/login")
def login(form: OAuth2PasswordRequestForm = Depends()):
    user = get_user(form.username)
    if not user or not verify_password(form.password, user["pwd_hash"]):
        raise HTTPException(401, "Usuário ou senha inválidos")

    access = create_access_token(form.username)
    refresh = create_refresh_token(form.username)
    resp = JSONResponse({"access_token": access, "token_type": "bearer"})
    resp.set_cookie("refresh_token", refresh,
                    httponly=True, samesite="lax", max_age=60*60*24*7)
    return resp


@router.post("/refresh")
def refresh_token(refresh_token: str | None = Cookie(None)):
    if not refresh_token:
        raise HTTPException(401, "Cookie ausente")

    try:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(401, "Token inválido")
        username = payload["sub"]
    except JWTError:
        raise HTTPException(401, "Token expirado ou inválido")

    new_access = create_access_token(username)
    new_refresh = create_refresh_token(username)
    resp = JSONResponse({"access_token": new_access, "token_type": "bearer"})
    resp.set_cookie("refresh_token", new_refresh,
                    httponly=True, samesite="lax", max_age=60*60*24*7)
    return resp


@router.post("/change_password")
def change_password(data: PwChange, username: str = Depends(get_current_user)):
    user = get_user(username)
    if not verify_password(data.old_password, user["pwd_hash"]):
        raise HTTPException(400, "Senha antiga incorreta")

    new_hash = hash_password(data.new_password)
    with sqlite3.connect("auth.db") as con:
        con.execute("UPDATE users SET pwd_hash=?, updated_at=datetime('now') "
                    "WHERE username=?", (new_hash, username))
        con.commit()
    return {"detail": "Senha alterada com sucesso"}


@router.post("/forgot-password")
def forgot_password(body: Forgot):
    token = secrets.token_urlsafe(32)
    expires = (_dt.datetime.now(_dt.UTC) +
               _dt.timedelta(minutes=RESET_EXP_MIN)).isoformat(" ", "seconds")

    with sqlite3.connect("auth.db") as con:
        cur = con.execute("SELECT username FROM users WHERE email=?", (body.email,))
        row = cur.fetchone()
        if not row:
            # não revela que o email não existe!
            return {"detail": "Se o e‑mail existir, enviaremos instruções."}
        con.execute("UPDATE users SET reset_token=?, reset_expires=? WHERE email=?",
                    (token, expires, body.email))
        con.commit()
    try:
        send_reset_email(body.email, token)
    except Exception as e:
        print("Erro Resend:", e)

    return {"detail": "Se o e‑mail existir, enviaremos instruções."}


@router.post("/reset-password")
def reset_password(body: ResetPw):
    with sqlite3.connect("auth.db") as con:
        cur = con.execute("SELECT id, reset_expires FROM users WHERE reset_token=?",
                          (body.token,))
        row = cur.fetchone()

    if not row:
        raise HTTPException(400, "Token inválido")
    if _dt.datetime.now(_dt.UTC) > _dt.datetime.fromisoformat(row[1]):
        raise HTTPException(400, "Token expirado")

    new_hash = hash_password(body.new_password)
    with sqlite3.connect("auth.db") as con:
        con.execute("""UPDATE users SET pwd_hash=?, reset_token=NULL,
                       reset_expires=NULL, updated_at=datetime('now') WHERE id=?""",
                    (new_hash, row[0]))
        con.commit()
    return {"detail": "Senha redefinida com sucesso"}


@router.post("/register")
def register_user(body: RegisterUser):
    with sqlite3.connect("auth.db") as con:
        cur = con.execute("SELECT id FROM users WHERE username=? OR email=?", (body.username, body.email))
        row = cur.fetchone()
        if row:
            raise HTTPException(400, "Usuário ou e-mail já cadastrado.")

        pwd_hash = hash_password(body.password)
        now = _dt.datetime.now(_dt.UTC).isoformat(" ", "seconds")
        con.execute(
            "INSERT INTO users (username, email, pwd_hash, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (body.username, body.email, pwd_hash, now, now)
        )
        con.commit()
    return {"detail": "Usuário cadastrado com sucesso."}
