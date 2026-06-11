import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()   # lee el archivo .env automáticamente

def conectar():
    return mysql.connector.connect(
        host     = os.getenv("DB_HOST",     "localhost"),
        user     = os.getenv("DB_USER",     "root"),
        password = os.getenv("DB_PASSWORD", ""),
        database = os.getenv("DB_NAME",     "canchas_db")
    )

