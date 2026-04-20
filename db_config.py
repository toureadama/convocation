import mysql.connector
import os
from mysql.connector import pooling

# MySQL configuration - MUST be set via environment variables
# No defaults provided for security (will error if not set)
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT', '3306')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME', 'douanesci_convocation')

# Validate that critical env vars are set
if not all([DB_HOST, DB_USER, DB_PASSWORD]):
    raise RuntimeError(
        "Missing required environment variables:\n"
        "   - DB_HOST\n"
        "   - DB_USER\n"
        "   - DB_PASSWORD\n"
        "Set these in your .env file or Render environment variables."
    )

# Connection pool (lazy initialized)
CONNECTION_POOL = None
POOL_INITIALIZED = False

CONFIG = {
    'host': DB_HOST,
    'port': int(DB_PORT),
    'user': DB_USER,
    'password': DB_PASSWORD,
    'database': DB_NAME,
}

def _init_pool():
    """Initialize connection pool on first use"""
    global CONNECTION_POOL, POOL_INITIALIZED
    if POOL_INITIALIZED:
        return
    
    try:
        CONNECTION_POOL = pooling.MySQLConnectionPool(
            pool_name="douanes_pool",
            pool_size=5,  # Adjust based on Render plan (Starter: 5-10 connections)
            pool_reset_session=True,
            host=DB_HOST,
            port=int(DB_PORT),
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            autocommit=False,
            use_unicode=True,
            charset='utf8mb4',
            collation='utf8mb4_unicode_ci'
        )
        POOL_INITIALIZED = True
    except Exception as e:
        print(f"[WARNING] Failed to create connection pool: {e}")
        print("[INFO] Falling back to single connections (slower)")
        CONNECTION_POOL = None
        POOL_INITIALIZED = True

def get_db_connection():
    """Get a database connection from the pool (or single connection if pool unavailable)."""
    _init_pool()  # Ensure pool is initialized
    try:
        if CONNECTION_POOL:
            return CONNECTION_POOL.get_connection()
        else:
            # Fallback to single connection (slower)
            return mysql.connector.connect(**CONFIG)
    except Exception as e:
        print(f"MySQL Error: {e}")
        return None

def close_connection(conn):
    """Close a database connection (returns to pool if pooled)."""
    if conn and conn.is_connected():
        conn.close()

def get_db_cursor():
    """Get a connection and cursor (legacy helper)."""
    conn = get_db_connection()
    if not conn:
        return None, None
    cursor = conn.cursor(dictionary=True)
    return conn, cursor
