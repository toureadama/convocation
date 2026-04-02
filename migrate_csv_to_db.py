#!/usr/bin/env python3
'''
Migration CODE_AGREE.csv → history.db table 'code_agree'
Zéro downtime - dual read support
'''
import sqlite3
import pandas as pd
import os

def migrate():
    conn = sqlite3.connect('history.db')
    
    # Create table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS code_agree (
            cc TEXT PRIMARY KEY,
            societe TEXT NOT NULL,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Import CSV if empty
    count = conn.execute('SELECT COUNT(*) FROM code_agree').fetchone()[0]
    if count == 0:
        if os.path.exists('CODE_AGREE.csv'):
            df = pd.read_csv('CODE_AGREE.csv', sep=';', encoding='utf-8-sig')
            df = df.iloc[:,:2]
            df.columns = ['cc', 'societe']
            df.to_sql('code_agree', conn, if_exists='append', index=False)
            print(f"✅ Imported {len(df)} rows")
        else:
            print("❌ CODE_AGREE.csv missing")
    
    conn.commit()
    conn.close()
    print("✅ Migration complete")

if __name__ == '__main__':
    migrate()

