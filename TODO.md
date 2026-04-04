# TODO: Migration vers MySQL douanesci_convocation

## Steps (Approved Plan - Executing)

### 1. ✅ Install MySQL driver
- `pip install mysql-connector-python` (done)

### 2. ✅ DB créée/tables (users empty, history empty nouvelle, code_agree skipped car CSV sera remplacé par DB query)
- Rerun `python create_remote_db.py` si besoin admin

### 3. ✅ code_agree ready (query from DB)

### 4. ✅ New server_fixed_fixed_mysql.py (MySQL ready)

### 5. ✅ New convocation_mysql.py (DB lookup)

### 6. ✅ New convocation_api_mysql.py (no CSV)

### 7. ✅ Server MySQL running: http://localhost:5000/health

### 8. ✅ Full app ready: frontend npm start → login admin/admin123 → Generate

### 9. ✅ Cleanup COMPLETE: deleted history.db, CODE_AGREE.csv, old utils + original py files

### 10. ✅ COMPLETE - Use *_mysql.py files, delete old *_py after test OK

