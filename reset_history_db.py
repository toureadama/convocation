import sqlite3
import os

# Supprimer ancien DB
if os.path.exists('history.db'):
    os.remove('history.db')
    print("history.db supprimé")

# Créer nouvelle DB avec VARCHAR(50) syntax (SQLite = TEXT)
conn = sqlite3.connect('history.db')
cursor = conn.cursor()

# Recréer users (admin par défaut)
cursor.execute('''
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        civilite TEXT,
        nom TEXT NOT NULL,
        prenom TEXT NOT NULL,
        grade TEXT NOT NULL,
        login TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        is_active BOOLEAN DEFAULT 1
    )
''')

# Admin par défaut (admin/admin123)
import bcrypt
pwd_hash = bcrypt.hashpw(b'admin123', bcrypt.gensalt()).decode()
cursor.execute("INSERT INTO users (nom, prenom, grade, login, password_hash) VALUES (?, ?, ?, ?, ?)",
               ('Admin', 'Super', 'Administrateur', 'admin', pwd_hash))

# History avec filenames VARCHAR(50) explicite (SQLite ignore limite)
cursor.execute('''
    CREATE TABLE history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        verificateur TEXT,
        num_declaration TEXT,
        date_declaration TEXT,
        fraude TEXT,
        signature_admin TEXT,
        csv TEXT DEFAULT 'CODE_AGREE.csv',
        cc TEXT,
        num_generated INTEGER,
        filenames VARCHAR(50),
        user_login TEXT,
        statut TEXT DEFAULT 'Non répondue'
    )
''')

conn.commit()
conn.close()
print("Nouvelle history.db créée:")
print("- users: admin/admin123")
print("- history.filenames = VARCHAR(50) explicite")
print("- Prêt pour l'app")
