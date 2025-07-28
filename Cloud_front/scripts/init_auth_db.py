import sqlite3
import getpass
import datetime
from passlib.hash import bcrypt

DB = "auth.db"

username = input("Usuário inicial: ").strip()
email = input("E-mail para recuperação: ").strip()
pwd_plain = getpass.getpass("Senha inicial: ")

conn = sqlite3.connect(DB)
conn.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    pwd_hash TEXT NOT NULL,
    reset_token TEXT,
    reset_expires TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
""")

now = datetime.datetime.now(datetime.timezone.utc).isoformat(" ", "seconds")
conn.execute(
    "INSERT OR REPLACE INTO users (username, email, pwd_hash, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
    (username, email, bcrypt.hash(pwd_plain), now, now)
)
conn.commit()
conn.close()
print(f"Usuário '{username}' criado em {DB}.")
