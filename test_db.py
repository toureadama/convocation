import os
from db_config import get_db_connection

print('DB_HOST:', os.getenv('DB_HOST'))
print('DB_USER:', os.getenv('DB_USER'))
conn = get_db_connection()
print('Connection:', 'SUCCESS' if conn else 'FAILED')
if conn:
    print('DB OK')

