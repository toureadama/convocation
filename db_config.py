import os
import mysql.connector
from mysql.connector import Error

CONFIG = {
    'host': os.getenv('DB_HOST'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME'),
    'charset': 'utf8mb4'
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