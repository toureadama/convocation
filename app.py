#!/usr/bin/env python3
"""
Serveur API Flask avec auth JWT + Users CRUD + Convocation
Port 5000 - Frontend proxy OK
"""

import os
import re
import subprocess
import sys
import sqlite3
import secrets
from datetime import datetime, timedelta

from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
import bcrypt
import logging
import pandas as pd

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'douanes-ci-super-secret-key-2024-32bytes-minimum-for-sha256-secure!'
jwt = JWTManager(app)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    conn = sqlite3.connect('history.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
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
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
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
            filenames TEXT,
            user_login TEXT,
statut TEXT DEFAULT ''
        )
    ''')
    
    # Migration
    cursor.execute('PRAGMA table_info(history)')
    cols = [col[1] for col in cursor.fetchall()]
    if 'user_login' not in cols:
        cursor.execute('ALTER TABLE history ADD COLUMN user_login TEXT')
        logger.info('Migration user_login ajoutée')
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE login='admin'")
    if cursor.fetchone()[0] == 0:
        password = 'admin123'
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor.execute(
            "INSERT INTO users (nom, prenom, grade, login, password_hash) VALUES (?, ?, ?, ?, ?)",
            ('Admin', 'Super', 'Administrateur', 'admin', password_hash)
        )
        logger.info("Admin créé: admin/admin123")
    
    conn.commit()
    conn.close()

# ... (login, verify, users CRUD inchangés - mêmes que avant)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'OK'})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    login_ = data.get('login')
    password = data.get('password')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE login=? AND is_active=1", (login_,))
    user = cursor.fetchone()
    conn.close()
    
    if user and bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
        access_token = create_access_token(
            identity=user['login'],
            expires_delta=timedelta(hours=24)
        )
        return jsonify({
            'token': access_token,
            'user': {
                'id': user['id'],
                'login': user['login'],
                'nom': user['nom'],
                'prenom': user['prenom'],
                'grade': user['grade']
            }
        })
    return jsonify({'error': 'Identifiants invalides'}), 401

@app.route('/api/verify', methods=['GET'])
@jwt_required()
def verify_token():
    current_user = get_jwt_identity()
    logger.info(f"Verify OK for {current_user}")
    return jsonify({'ok': True, 'user': current_user})

@app.route('/api/users', methods=['GET'])
@jwt_required()
def get_users():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, login, nom, prenom, grade, civilite, created_at, substr(login,1,3)||'***' AS plain_password FROM users WHERE is_active=1 ORDER BY nom")
    users = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({'users': users})

@app.route('/api/users', methods=['POST'])
@jwt_required()
def create_user():
    data = request.get_json()
    nom = data['nom']
    prenom = data['prenom']
    grade = data['grade']
    
    provided_login = data.get('login')
    provided_password = data.get('password')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if provided_login and provided_password:
        cursor.execute("SELECT id FROM users WHERE login=?", (provided_login,))
        if cursor.fetchone():
            conn.close()
            return jsonify({'error': 'Login déjà utilisé'}), 400
        login = provided_login
        password = provided_password
    else:
        login_base = (prenom.lower()[:3] + nom.lower()[:4]).replace(' ', '')
        login = login_base
        counter = 1
        while True:
            cursor.execute("SELECT id FROM users WHERE login=?", (login,))
            if not cursor.fetchone():
                break
            login = f"{login_base}{counter}"
            counter += 1
        password = secrets.token_urlsafe(8)

    
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    civilite = data.get('civilite', '') 
    cursor.execute(
        "INSERT INTO users (civilite, nom, prenom, grade, login, password_hash) VALUES (?, ?, ?, ?, ?, ?)",
        (civilite, nom, prenom, grade, login, password_hash)
    )
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    logger.info(f"User créé: {login}/{password}")
    return jsonify({
        'id': user_id,
        'login': login,
        'password': password,
        'message': 'Utilisateur créé'
    }), 201

@app.route('/api/users/<int:user_id>/credentials', methods=['PUT'])
@jwt_required()
def update_credentials(user_id):
    data = request.get_json()
    new_login = data['login']
    new_password = data['password']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM users WHERE login=? AND id != ?", (new_login, user_id))
    if cursor.fetchone():
        conn.close()
        return jsonify({'error': 'Login déjà utilisé'}), 400
    
    password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    cursor.execute(
        "UPDATE users SET login=?, password_hash=? WHERE id=? AND is_active=1",
        (new_login, password_hash, user_id)
    )
    if cursor.rowcount == 0:
        conn.close()
        return jsonify({'error': 'User non trouvé'}), 404
    conn.commit()
    conn.close()
    
    logger.info(f"Identifiants modifiés pour user_id {user_id}")
    return jsonify({'message': 'Identifiants mis à jour'})

@app.route('/api/users/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()
    civilite = data.get('civilite', '') 
    cursor.execute(
        "UPDATE users SET civilite=?, nom=?, prenom=?, grade=? WHERE id=? AND is_active=1",
        (civilite, data['nom'], data['prenom'], data['grade'], user_id)
    )
    if cursor.rowcount == 0:
        conn.close()
        return jsonify({'error': 'User non trouvé'}), 404
    conn.commit()
    conn.close()
    return jsonify({'message': 'User mis à jour'})

@app.route('/api/history/<int:history_id>/status', methods=['PUT'])
@jwt_required()
def update_history_status(history_id):
    data = request.get_json()
    new_statut = data['statut']
    
    current_user = get_jwt_identity()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE history SET statut = ? WHERE id = ? AND user_login = ?
    """, (new_statut, history_id, current_user))
    
    if cursor.rowcount == 0:
        conn.close()
        return jsonify({'error': 'Non autorisé ou non trouvé'}), 403
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Statut mis à jour'})

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_active=0 WHERE id=?", (user_id,))
    if cursor.rowcount == 0:
        conn.close()
        return jsonify({'error': 'User non trouvé'}), 404
    conn.commit()
    conn.close()
    return jsonify({'message': 'User supprimé'})

@app.route('/api/generate', methods=['POST'])
@jwt_required()
def generate_convocation():
    try:
        data = request.form.to_dict()
        current_user = get_jwt_identity()
        logger.info(f"[{current_user}] Génération: {data}")

        # Calcul next_num dynamique par user/année
        conn = get_db_connection()
        cursor = conn.cursor()
        current_year = datetime.now().strftime('%Y')
        cursor.execute("""
            SELECT COUNT(*) FROM history 
            WHERE user_login = ? AND strftime('%Y', timestamp) = ?
        """, (current_user, current_year))
        count = cursor.fetchone()[0]
        next_num = f"{count + 1:04d}"
        logger.info(f"[{current_user}] Next num_convoc {current_year}: {next_num} (count={count})")
        conn.close()
        
        args_list = [
            sys.executable, 'convocation.py',
            '--cc', data['cc'],
            '--verificateur', data['verificateur'],
            '--num_declaration', data['num_declaration'],
            '--date_declaration', data['date_declaration'],
            '--fraude', data['fraude'],
            '--signature_admin', data['signature_admin'],
            '--num_convoc', next_num,
        ]

        result = subprocess.run(
            args_list,
            capture_output=True,
            text=True,
            cwd=os.getcwd(),
            timeout=60,
        )

        if result.returncode != 0:
            logger.error(f'Subprocess failed: {result.stderr}')
            return jsonify({'error': result.stderr}), 500
        
        
        stdout_normalized = result.stdout.replace('\\', '/')
        logger.info(f"stdout tail: {repr(stdout_normalized.splitlines()[-3:])}")  
        pdf_matches = re.findall(r'OK\s*:\s*(output/[^\s\r\n]+)', stdout_normalized)
        results = [{'path': match.strip(), 'filename': os.path.basename(match)} for match in pdf_matches]
        logger.info(f"Parsed {len(results)} files: {pdf_matches}")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO history (timestamp, verificateur, num_declaration, date_declaration, 
                               fraude, signature_admin, cc, num_generated, filenames, user_login)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            data.get('verificateur'),
            data.get('num_declaration'),
            data.get('date_declaration'),
            data.get('fraude'),
            data.get('signature_admin'),
            data.get('cc'),
            len(results),
            ';'.join([r['filename'] for r in results]),
            current_user
        ))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'results': results,
            'log': result.stdout,
        })

    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Timeout'}), 408
    except Exception as e:
        logger.error(f"Erreur: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/companies', methods=['GET'])
@jwt_required()
def get_companies():
    conn = get_db_connection()
    try:
        companies = conn.execute('SELECT cc, societe FROM code_agree ORDER BY cc LIMIT 100').fetchall()
        return jsonify({'companies': [{'cc': r['cc'], 'societe': r['societe']} for r in companies]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/history/export', methods=['GET'])
@jwt_required()
def export_history():
    current_user = get_jwt_identity()
    if current_user != 'admin':
        return jsonify({'error': 'Admin only'}), 403
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Même filtres que get_history
    where_conditions = []
    params = []
    
    filter_date_from = request.args.get('filter_date_from')
    filter_date_to = request.args.get('filter_date_to')
    filter_cc = request.args.get('filter_cc')
    filter_verif = request.args.get('filter_verif')
    filter_fraude = request.args.get('filter_fraude')
    filter_admin = request.args.get('filter_admin')
    filter_statut = request.args.get('filter_statut')
    
    if filter_date_from:
        where_conditions.append("timestamp >= ?")
        params.append(filter_date_from)
    if filter_date_to:
        where_conditions.append("timestamp <= ?")
        params.append(filter_date_to)
    if filter_cc:
        where_conditions.append("cc LIKE ?")
        params.append(f"%{filter_cc}%")
    if filter_verif:
        where_conditions.append("verificateur LIKE ?")
        params.append(f"%{filter_verif}%")
    if filter_fraude:
        where_conditions.append("fraude LIKE ?")
        params.append(f"%{filter_fraude}%")
    if filter_admin:
        where_conditions.append("signature_admin LIKE ?")
        params.append(f"%{filter_admin}%")
    if filter_statut:
        where_conditions.append("statut = ?")
        params.append(filter_statut)
    
    where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
    
    query = f"""
        SELECT id, timestamp, verificateur, num_declaration, date_declaration, 
               fraude, signature_admin, cc, num_generated, filenames, user_login, statut
        FROM history {where_clause}
        ORDER BY timestamp DESC
    """
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    columns = ['id', 'timestamp', 'verificateur', 'num_declaration', 'date_declaration', 
               'fraude', 'signature_admin', 'cc', 'num_generated', 'filenames', 'user_login', 'statut']
    
    df = pd.DataFrame([dict(zip(columns, row)) for row in rows])
    csv_buffer = df.to_csv(index=False, encoding='utf-8-sig')
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"history_{timestamp}.csv"
    
    return Response(
        csv_buffer,
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename={filename}"}
    )

@app.route('/api/history', methods=['GET'])
@jwt_required()
def get_history():
    page = int(request.args.get('page', 0))
    limit = int(request.args.get('limit', 20))
    offset = page * limit
    
    current_user = get_jwt_identity()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Filtres admin only
    where_conditions = []
    params = []
    
    if current_user != 'admin':
        where_conditions.append("user_login = ?")
        params.append(current_user)
    # Admin filtres
    else:
        filter_date_from = request.args.get('filter_date_from')
        filter_date_to = request.args.get('filter_date_to')
        filter_cc = request.args.get('filter_cc')
        filter_verif = request.args.get('filter_verif')
        filter_fraude = request.args.get('filter_fraude')
        filter_admin = request.args.get('filter_admin')
        filter_statut = request.args.get('filter_statut')
        
        if filter_date_from:
            where_conditions.append("timestamp >= ?")
            params.append(filter_date_from)
        if filter_date_to:
            where_conditions.append("timestamp <= ?")
            params.append(filter_date_to)
        if filter_cc:
            where_conditions.append("cc LIKE ?")
            params.append(f"%{filter_cc}%")
        if filter_verif:
            where_conditions.append("verificateur LIKE ?")
            params.append(f"%{filter_verif}%")
        if filter_fraude:
            where_conditions.append("fraude LIKE ?")
            params.append(f"%{filter_fraude}%")
        if filter_admin:
            where_conditions.append("signature_admin LIKE ?")
            params.append(f"%{filter_admin}%")
        if filter_statut:
            where_conditions.append("statut = ?")
            params.append(filter_statut)
    
    where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
    
    query = f"""
        SELECT id, timestamp, verificateur, num_declaration, date_declaration, 
               fraude, signature_admin, cc, num_generated, filenames, user_login, statut
        FROM history {where_clause}
        ORDER BY timestamp DESC LIMIT ? OFFSET ?
    """
    
    params.extend([limit, offset])
    cursor.execute(query, params)
    
    rows = cursor.fetchall()
    conn.close()
    
    columns = ['id', 'timestamp', 'verificateur', 'num_declaration', 'date_declaration', 
               'fraude', 'signature_admin', 'cc', 'num_generated', 'filenames', 'user_login', 'statut']
    history = [dict(zip(columns, row)) for row in rows]
    return jsonify({'history': history})

@app.route('/output/<path:filename>')
def serve_output(filename):
    return send_from_directory('output', filename)

# Admin CRUD Code Agréé
@app.route('/api/code_agree', methods=['GET'])
@jwt_required()
def get_code_agree():
    current_user = get_jwt_identity()
    if current_user != 'admin':
        return jsonify({'error': 'Admin only'}), 403
    conn = get_db_connection()
    companies = conn.execute('SELECT cc, societe FROM code_agree ORDER BY cc').fetchall()
    conn.close()
    return jsonify({'companies': [dict(r) for r in companies]})

@app.route('/api/code_agree', methods=['POST'])
@jwt_required()
def create_code_agree():
    current_user = get_jwt_identity()
    if current_user != 'admin':
        return jsonify({'error': 'Admin only'}), 403
    data = request.get_json()
    cc = data['cc'].strip()
    societe = data['societe'].strip()
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO code_agree (cc, societe) VALUES (?, ?)', (cc, societe))
        conn.commit()
        return jsonify({'message': 'Code agréé ajouté', 'cc': cc}), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': 'CC existe déjà'}), 400
    finally:
        conn.close()

@app.route('/api/code_agree/<cc>', methods=['DELETE', 'PUT'])
@jwt_required()
def update_delete_code_agree(cc):
    current_user = get_jwt_identity()
    if current_user != 'admin':
        return jsonify({'error': 'Admin only'}), 403
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == 'DELETE':
        cursor.execute('DELETE FROM code_agree WHERE cc = ?', (cc,))
        if cursor.rowcount:
            conn.commit()
            return jsonify({'message': 'Supprimé'})
    else:  # PUT
        data = request.get_json()
        societe = data['societe'].strip()
        cursor.execute('UPDATE code_agree SET societe = ? WHERE cc = ?', (societe, cc))
        if cursor.rowcount:
            conn.commit()
            return jsonify({'message': 'Mis à jour'})
    conn.close()
    return jsonify({'error': 'Non trouvé'}), 404

init_db()

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
