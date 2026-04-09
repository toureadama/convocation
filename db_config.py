import mysql.connector
import os

# MySQL configuration - values from environment or defaults
CONFIG = {
    'host': os.getenv('DB_HOST', 'mysql-a54ef6c-toureadama-2bc0.c.aivencloud.com'),
    'port': int(os.getenv('DB_PORT', '15107')),
    'user': os.getenv('DB_USER', 'avnadmin'),
    'password': os.getenv('DB_PASSWORD', 'AVNS_O9FSI98GLiPqRHk5e0H'),
    'database': os.getenv('DB_NAME', 'douanesci_convocation'),
}

def get_db_connection():
    try:
        conn = mysql.connector.connect(**CONFIG)
        return conn
    except Exception as e:
        print(f"MySQL Error: {e}")
        return None

def close_connection(conn):
    if conn and conn.is_connected():
        conn.close()

def get_db_cursor():
    conn = get_db_connection()
    if not conn:
        return None, None
    cursor = conn.cursor(dictionary=True)
    return conn, cursor
