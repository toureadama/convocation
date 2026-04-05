#!/usr/bin/env python3
import bcrypt
from db_config import get_db_connection, close_connection, CONFIG
from mysql.connector import Error
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def ensure_admin():
    conn = get_db_connection()
    if not conn:
        logger.error('DB connection failed - check .env')
        return False
    
    cursor = conn.cursor()
    
    # Create tables if missing
    tables = [
        """CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            civilite VARCHAR(10),
            nom VARCHAR(100),
            prenom VARCHAR(100),
            grade VARCHAR(50),
            login VARCHAR(50) UNIQUE,
            password_hash TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        """CREATE TABLE IF NOT EXISTS history (
            id INT AUTO_INCREMENT PRIMARY KEY,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            verificateur TEXT,
            num_declaration VARCHAR(50),
            date_declaration DATE,
            fraude VARCHAR(10),
            signature_admin VARCHAR(100),
            cc VARCHAR(20),
            num_generated INT,
            filenames TEXT,
            user_login VARCHAR(50),
            statut VARCHAR(20) DEFAULT 'EN_COURS'
        )""",
        """CREATE TABLE IF NOT EXISTS code_agree (
            cc VARCHAR(20) PRIMARY KEY,
            societe VARCHAR(255)
        )"""
    ]
    
    for sql in tables:
        cursor.execute(sql)
    
    # Create admin if missing
    cursor.execute("SELECT COUNT(*) FROM users WHERE login='admin'")
    count = cursor.fetchone()[0]
    if count == 0:
        password = 'admin123'
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor.execute(
            "INSERT INTO users (nom, prenom, grade, login, password_hash) VALUES ('Admin', 'Super', 'Administrateur', 'admin', %s)",
            (password_hash,)
        )
        conn.commit()
        logger.info("✅ Admin créé: login='admin', password='admin123'")
    else:
        logger.info("✅ Admin existe déjà")
    
    cursor.close()
    close_connection(conn)
    logger.info("DB ready!")
    return True

if __name__ == '__main__':
    ensure_admin()

