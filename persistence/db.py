import os
import pymysql
from dotenv import load_dotenv


load_dotenv()

def get_connection():
    return pymysql.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", 24316)), # Si no lee el puerto, usa 24316 por defecto
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        ssl={'ssl': {}}
    )
