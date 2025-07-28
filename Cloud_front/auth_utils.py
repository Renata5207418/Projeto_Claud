import datetime as _dt
import os
import sqlite3
from typing import Optional
from jose import jwt
from passlib.hash import bcrypt
from dotenv import load_dotenv
load_dotenv()


# ───── Configurações ────────────────────────────────────────────────
DB = "auth.db"

SECRET_KEY: str = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MIN = 5   # minutos
REFRESH_TOKEN_EXPIRE_DAYS = 7  # dias


# ───── Helpers de banco de dados ────────────────────────────────────
def get_user(username: str) -> Optional[dict]:
    """Busca usuário por username (ou e‑mail). Retorna dict ou None."""
    with sqlite3.connect(DB) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()
    return dict(row) if row else None


# ───── Helpers de senha ─────────────────────────────────────────────
def verify_password(plain: str, pwd_hash: str) -> bool:
    return bcrypt.verify(plain, pwd_hash)


def hash_password(plain: str) -> str:
    """Gera hash Bcrypt para armazenar no BD."""
    return bcrypt.hash(plain)


# ───── Helpers de JWT ───────────────────────────────────────────────
def _create_token(data: dict, expires_delta: _dt.timedelta) -> str:
    to_encode = data.copy()
    # datetime.UTC existe a partir do Python 3.11
    exp = _dt.datetime.now(_dt.UTC) + expires_delta
    to_encode["exp"] = exp
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_access_token(sub: str) -> str:
    return _create_token(
        {"sub": sub, "type": "access"},
        _dt.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MIN),
    )


def create_refresh_token(sub: str) -> str:
    return _create_token(
        {"sub": sub, "type": "refresh"},
        _dt.timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    )


def decode_token(token: str) -> dict:
    """Decodifica JWT e lança jose.JWTError em caso de falha."""
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
