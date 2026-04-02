import sqlite3

conn = sqlite3.connect('history.db')
cursor = conn.cursor()

print("=== TOUS LES FILENAMES (ID + filename) ===")
cursor.execute('SELECT id, filenames FROM history WHERE filenames IS NOT NULL AND filenames != "" ORDER BY id DESC')
rows = cursor.fetchall()

if rows:
    for row in rows:
        id_val, filenames = row
        print(f"ID {id_val}: {repr(filenames)} ({len(filenames)} chars)")
else:
    print("Aucune donnée dans filenames (générez une convocation d'abord)")

print("\n=== COMPTE ===")
cursor.execute('SELECT COUNT(*) FROM history WHERE filenames IS NOT NULL AND filenames != ""')
count = cursor.fetchone()[0]
print(f"{count} entrées avec filenames")

conn.close()
