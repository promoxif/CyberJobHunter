
import os
import psycopg
from dotenv import load_dotenv

load_dotenv()

def conectar_db():
    url = os.getenv("DATABASE_URL")

    if not url:
        raise ValueError("DATABASE_URL no configurada")

    return psycopg.connect(url, sslmode="require")
