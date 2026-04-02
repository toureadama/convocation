import sqlite3
conn = sqlite3.connect('history.db')
c = conn.cursor()

print('=== TABLES ===')
print([row[0] for row in c.execute('SELECT name FROM sqlite_master WHERE type="table";').fetchall()])

print('\n=== HISTORY SCHEMA ===')
for line in c.execute('PRAGMA table_info(history);').fetchall():
    print(line)

print('\n=== USERS SCHEMA ===')
for line in c.execute('PRAGMA table_info(users);').fetchall():
    print(line)
    
print('\n=== CODES AGREES SCHEMA ===')
for line in c.execute('PRAGMA table_info(code_agree);').fetchall():
    print(line)

print('\n=== SAMPLE DATA HISTORY ===')
print(c.execute('SELECT * FROM history LIMIT 3;').fetchall())

print('\n=== SAMPLE DATA USERS ===')
print(c.execute('SELECT id, login, nom, prenom, grade, civilite FROM users LIMIT 3;').fetchall())

print('\n=== SAMPLE DATA CODE AGREE ===')
print(c.execute('SELECT * FROM code_agree LIMIT 3;').fetchall())

conn.close()
print('DB info complete.')

