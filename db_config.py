import os
import mysql.connector
from mysql.connector import Error

# ============================================================
# Les credentials sont lus depuis les variables d'environnement
# Définies dans secrets.env (local) ou dans Render > Environment
# ============================================================

CONFIG = {
    'host':     os.environ.get('DB_HOST', 'mysql-a54ef6c-toureadama-2bc0.c.aivencloud.com'),
    'port':     int(os.environ.get('DB_PORT', 15107)),
    'user':     os.environ.get('DB_USER', 'avnadmin'),
    'password': os.environ.get('DB_PASSWORD', ''),
    'database': os.environ.get('DB_NAME', 'douanesci_convocation'),
    'charset':  'utf8mb4',
    # SSL requis par Aiven Cloud MySQL
    'ssl_disabled': False,
}

def get_db_connection():
    try:
        conn = mysql.connector.connect(**CONFIG)
        if conn.is_connected():
            return conn
    except Error as e:
        print(f"DB Error: {e}")
        return None
    return None

def close_connection(conn):
    if conn and conn.is_connected():
        conn.close()
