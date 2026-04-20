#!/usr/bin/env python3
"""
Migration script to add statut_approbation column to history table.
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('secrets.env')

# Import after loading env
from db_config import get_db_connection, close_connection

def add_statut_approbation_column():
    """Add statut_approbation column to history table if it doesn't exist."""
    conn = get_db_connection()
    if not conn:
        print("Failed to connect to database")
        return False

    try:
        cursor = conn.cursor()

        # Check if column exists
        cursor.execute("""
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = 'history'
            AND COLUMN_NAME = 'statut_approbation'
            AND TABLE_SCHEMA = DATABASE()
        """)

        if cursor.fetchone():
            print("Column statut_approbation already exists")
            return True

        # Add the column
        cursor.execute("""
            ALTER TABLE history
            ADD COLUMN statut_approbation ENUM('EN_ATTENTE_APPROBATION', 'APPROUVEE', 'REJETEE') DEFAULT 'EN_ATTENTE_APPROBATION'
        """)

        conn.commit()
        print("Successfully added statut_approbation column to history table")
        return True

    except Exception as e:
        print(f"Error adding column: {e}")
        conn.rollback()
        return False
    finally:
        close_connection(conn)

if __name__ == "__main__":
    success = add_statut_approbation_column()
    sys.exit(0 if success else 1)