import mysql.connector
from mysql.connector import Error

CONFIG = {
    'host': 'mysql-a54ef6c-toureadama-2bc0.c.aivencloud.com',
    'port': 15107,
    'user': 'avnadmin',
    'password': 'AVNS_O9FSI98GLiPqRHk5e0H',
    'database': 'douanesci_convocation',
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

