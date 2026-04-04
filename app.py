#!/usr/bin/env python3
"""
Serveur API Flask avec auth JWT + Users CRUD + Convocation MySQL
Render-ready: PORT dynamique, secrets depuis variables d'environnement
"""
import os
import re
import subprocess
import sys
import secrets
from datetime import datetime, timedelta
import mysql.connector
from mysql.connector import Error
from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
import bcrypt
import logging
import pandas as pd

from db_config import get_db_connection, close_connection, CONFIG

app = Flask(__name__)

# ✅ JWT secret depuis variable d'environnement (obligatoire en production)
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY')
jwt = JWTManager(app)
CORS(app, origins=[
    "https://convocation-a762.onrender.com",
    "http://localhost:3000",
])
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_db():
    conn = get_db_connection()
    if not conn:
        logger.error("Cannot connect to MySQL for init_db")
        return
    cursor = conn.cursor()
    # Vérifier que les tables existent
    cursor.execute("SHOW TABLES LIKE 'users'")
    if not cursor.fetchone():
        logger.error("Tables not found - run create_remote_db.py first")
        cursor.close()
        close_connection(conn)
        return
    # Créer admin par défaut si absent
    cursor.execute("SELECT COUNT(*) as count FROM users WHERE login='admin'")
    count = cursor.fetchone()[0]
    if count == 0:
        password = 'admin123'
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor.execute(
            "INSERT INTO users (nom, prenom, grade, login, password_hash) VALUES (%s, %s, %s, %s, %s)",
            ('Admin', 'Super', 'Administrateur', 'admin', password_hash)
        )
        conn.commit()
        logger.info("Admin créé: admin/admin123")
    cursor.close()
    close_connection(conn)
    logger.info("MySQL douanesci_convocation ready")


def get_db_cursor(dictionary=False):
    conn = get_db_connection()
    if not conn:
        return None, None
    cursor = conn.cursor(dictionary=dictionary)
    return conn, cursor


@app.route('/health', methods=['GET'])
def health():
    conn = get_db_connection()
    close_connection(conn)
    return jsonify({'status': 'OK', 'db': 'MySQL douanesci_convocation'})


@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    login_ = data.get('login')
    password = data.get('password')

    conn, cursor = get_db_cursor(dictionary=True)
    if not conn:
        return jsonify({'error': 'DB connection failed'}), 500
    cursor.execute("SELECT * FROM users WHERE login=%s AND is_active=1", (login_,))
    user = cursor.fetchone()
    close_connection(conn)

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
    conn, cursor = get_db_cursor(dictionary=True)
    if not conn:
        return jsonify({'error': 'DB error'}), 500
    cursor.execute("SELECT id, login, nom, prenom, grade, civilite, created_at, CONCAT(LEFT(login,3),'***') AS plain_password FROM users WHERE is_active=1 ORDER BY nom")
    users = [dict(row) for row in cursor.fetchall()]
    close_connection(conn)
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

    conn, cursor = get_db_cursor()
    if not conn:
        return jsonify({'error': 'DB error'}), 500

    if provided_login and provided_password:
        cursor.execute("SELECT id FROM users WHERE login=%s", (provided_login,))
        if cursor.fetchone():
            close_connection(conn)
            return jsonify({'error': 'Login déjà utilisé'}), 400
        login = provided_login
        password = provided_password
    else:
        login_base = (prenom.lower()[:3] + nom.lower()[:4]).replace(' ', '')
        login = login_base
        counter = 1
        while True:
            cursor.execute("SELECT id FROM users WHERE login=%s", (login,))
            if not cursor.fetchone():
                break
            login = f"{login_base}{counter}"
            counter += 1
        password = secrets.token_urlsafe(8)

    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    civilite = data.get('civilite', '')
    cursor.execute(
        "INSERT INTO users (civilite, nom, prenom, grade, login, password_hash) VALUES (%s, %s, %s, %s, %s, %s)",
        (civilite, nom, prenom, grade, login, password_hash)
    )
    user_id = cursor.lastrowid
    conn.commit()
    close_connection(conn)

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

    conn, cursor = get_db_cursor()
    if not conn:
        return jsonify({'error': 'DB error'}), 500

    cursor.execute("SELECT id FROM users WHERE login=%s AND id != %s", (new_login, user_id))
    if cursor.fetchone():
        close_connection(conn)
        return jsonify({'error': 'Login déjà utilisé'}), 400

    password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    cursor.execute(
        "UPDATE users SET login=%s, password_hash=%s WHERE id=%s AND is_active=1",
        (new_login, password_hash, user_id)
    )
    if cursor.rowcount == 0:
        close_connection(conn)
        return jsonify({'error': 'User non trouvé'}), 404
    conn.commit()
    close_connection(conn)

    logger.info(f"Identifiants modifiés pour user_id {user_id}")
    return jsonify({'message': 'Identifiants mis à jour'})


@app.route('/api/users/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    data = request.get_json()
    conn, cursor = get_db_cursor()
    if not conn:
        return jsonify({'error': 'DB error'}), 500
    civilite = data.get('civilite', '')
    cursor.execute(
        "UPDATE users SET civilite=%s, nom=%s, prenom=%s, grade=%s WHERE id=%s AND is_active=1",
        (civilite, data['nom'], data['prenom'], data['grade'], user_id)
    )
    if cursor.rowcount == 0:
        close_connection(conn)
        return jsonify({'error': 'User non trouvé'}), 404
    conn.commit()
    close_connection(conn)
    return jsonify({'message': 'User mis à jour'})


@app.route('/api/history/<int:history_id>/status', methods=['PUT'])
@jwt_required()
def update_history_status(history_id):
    data = request.get_json()
    new_statut = data['statut']
    current_user = get_jwt_identity()

    conn, cursor = get_db_cursor()
    if not conn:
        return jsonify({'error': 'DB error'}), 500
    cursor.execute(
        "UPDATE history SET statut = %s WHERE id = %s AND user_login = %s",
        (new_statut, history_id, current_user)
    )
    if cursor.rowcount == 0:
        close_connection(conn)
        return jsonify({'error': 'Non autorisé ou non trouvé'}), 403
    conn.commit()
    close_connection(conn)
    return jsonify({'message': 'Statut mis à jour'})


@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    conn, cursor = get_db_cursor()
    if not conn:
        return jsonify({'error': 'DB error'}), 500
    cursor.execute("UPDATE users SET is_active=0 WHERE id=%s", (user_id,))
    if cursor.rowcount == 0:
        close_connection(conn)
        return jsonify({'error': 'User non trouvé'}), 404
    conn.commit()
    close_connection(conn)
    return jsonify({'message': 'User supprimé'})


@app.route('/api/generate', methods=['POST'])
@jwt_required()
def generate_convocation():
    try:
        data = request.form.to_dict()
        current_user = get_jwt_identity()
        logger.info(f"[{current_user}] Génération: {data}")

        conn, cursor = get_db_cursor()
        if not conn:
            return jsonify({'error': 'DB error'}), 500
        current_year = datetime.now().strftime('%Y')
        cursor.execute(
            "SELECT COUNT(*) FROM history WHERE user_login = %s AND YEAR(STR_TO_DATE(timestamp, '%Y-%m-%dT%H:%i:%s')) = %s",
            (current_user, current_year)
        )
        count = cursor.fetchone()[0]
        next_num = f"{int(count) + 1:04d}"
        logger.info(f"[{current_user}] Next num_convoc {current_year}: {next_num} (count={count})")
        close_connection(conn)

        args_list = [
            sys.executable, 'convocation_mysql.py',
            '--cc', data['cc'],
            '--verificateur', data['verificateur'],
            '--num_declaration', data['num_declaration'],
            '--date_declaration', data['date_declaration'],
            '--fraude', data['fraude'],
            '--signature_admin', data['signature_admin'],
            '--num_convoc', next_num,
        ]

        # Passer les variables d'environnement DB au sous-processus
        env = os.environ.copy()

        result = subprocess.run(
            args_list,
            capture_output=True,
            text=True,
            cwd=os.getcwd(),
            timeout=60,
            env=env,
        )

        if result.returncode != 0:
            logger.error(f'Subprocess failed: {result.stderr}')
            return jsonify({'error': result.stderr}), 500

        stdout_normalized = result.stdout.replace('\\', '/')
        logger.info(f"stdout tail: {repr(stdout_normalized.splitlines()[-3:])}")
        # ✅ Correction du regex (backslash dans raw string)
        pdf_matches = re.findall(r'OK\s*:\s*(output/[^\s\r\n]+)', stdout_normalized)
        results = [{'path': match.strip(), 'filename': os.path.basename(match)} for match in pdf_matches]
        logger.info(f"Parsed {len(results)} files: {pdf_matches}")

        conn, cursor = get_db_cursor()
        if not conn:
            return jsonify({'error': 'DB error'}), 500
        cursor.execute(
            "INSERT INTO history (timestamp, verificateur, num_declaration, date_declaration, fraude, signature_admin, cc, num_generated, filenames, user_login) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (
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
            )
        )
        conn.commit()
        close_connection(conn)

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
    conn, cursor = get_db_cursor(dictionary=True)
    if not conn:
        return jsonify({'error': 'DB error'}), 500
    cursor.execute('SELECT cc, societe FROM code_agree ORDER BY cc LIMIT 100')
    companies = [dict(row) for row in cursor.fetchall()]
    close_connection(conn)
    return jsonify({'companies': companies})


@app.route('/api/history/export', methods=['GET'])
@jwt_required()
def export_history():
    current_user = get_jwt_identity()
    if current_user != 'admin':
        return jsonify({'error': 'Admin only'}), 403

    conn, cursor = get_db_cursor(dictionary=True)
    if not conn:
        return jsonify({'error': 'DB error'}), 500

    where_conditions = []
    params = []

    for arg, col, op in [
        ('filter_date_from', 'timestamp', '>='),
        ('filter_date_to',   'timestamp', '<='),
        ('filter_cc',        'cc',        'LIKE'),
        ('filter_verif',     'verificateur', 'LIKE'),
        ('filter_fraude',    'fraude',    'LIKE'),
        ('filter_admin',     'signature_admin', 'LIKE'),
    ]:
        val = request.args.get(arg)
        if val:
            if op == 'LIKE':
                where_conditions.append(f"{col} LIKE %s")
                params.append(f"%{val}%")
            else:
                where_conditions.append(f"{col} {op} %s")
                params.append(val)

    filter_statut = request.args.get('filter_statut')
    if filter_statut:
        where_conditions.append("statut = %s")
        params.append(filter_statut)

    where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
    query = f"""
        SELECT id, timestamp, verificateur, num_declaration, date_declaration,
               fraude, signature_admin, cc, num_generated, filenames, user_login, statut
        FROM history {where_clause}
        ORDER BY timestamp DESC
    """
    cursor.execute(query, params)
    rows = [dict(row) for row in cursor.fetchall()]
    close_connection(conn)

    df = pd.DataFrame(rows)
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
    conn, cursor = get_db_cursor(dictionary=True)
    if not conn:
        return jsonify({'history': []}), 200

    where_conditions = []
    params = []

    if current_user != 'admin':
        where_conditions.append("user_login = %s")
        params.append(current_user)
    else:
        for arg, col, op in [
            ('filter_date_from', 'timestamp', '>='),
            ('filter_date_to',   'timestamp', '<='),
            ('filter_cc',        'cc',        'LIKE'),
            ('filter_verif',     'verificateur', 'LIKE'),
            ('filter_fraude',    'fraude',    'LIKE'),
            ('filter_admin',     'signature_admin', 'LIKE'),
        ]:
            val = request.args.get(arg)
            if val:
                if op == 'LIKE':
                    where_conditions.append(f"{col} LIKE %s")
                    params.append(f"%{val}%")
                else:
                    where_conditions.append(f"{col} {op} %s")
                    params.append(val)

        filter_statut = request.args.get('filter_statut')
        if filter_statut:
            where_conditions.append("statut = %s")
            params.append(filter_statut)

    where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
    query = f"""
        SELECT id, timestamp, verificateur, num_declaration, date_declaration,
               fraude, signature_admin, cc, num_generated, filenames, user_login, statut
        FROM history {where_clause}
        ORDER BY timestamp DESC LIMIT %s OFFSET %s
    """
    params.extend([limit, offset])
    cursor.execute(query, params)
    rows = [dict(row) for row in cursor.fetchall()]
    close_connection(conn)

    return jsonify({'history': rows})


@app.route('/output/<path:filename>')
def serve_output(filename):
    return send_from_directory('output', filename)


# Admin CRUD Code Agréé MySQL
@app.route('/api/code_agree', methods=['GET'])
@jwt_required()
def get_code_agree():
    current_user = get_jwt_identity()
    if current_user != 'admin':
        return jsonify({'error': 'Admin only'}), 403
    conn, cursor = get_db_cursor(dictionary=True)
    if not conn:
        return jsonify({'error': 'DB error'}), 500
    cursor.execute('SELECT cc, societe FROM code_agree ORDER BY cc')
    companies = [dict(row) for row in cursor.fetchall()]
    close_connection(conn)
    return jsonify({'companies': companies})


@app.route('/api/code_agree', methods=['POST'])
@jwt_required()
def create_code_agree():
    current_user = get_jwt_identity()
    if current_user != 'admin':
        return jsonify({'error': 'Admin only'}), 403
    data = request.get_json()
    cc = data['cc'].strip()
    societe = data['societe'].strip()
    conn, cursor = get_db_cursor()
    if not conn:
        return jsonify({'error': 'DB error'}), 500
    try:
        cursor.execute('INSERT INTO code_agree (cc, societe) VALUES (%s, %s)', (cc, societe))
        conn.commit()
        return jsonify({'message': 'Code agréé ajouté', 'cc': cc}), 201
    except Error as e:
        if 'Duplicate entry' in str(e):
            return jsonify({'error': 'CC existe déjà'}), 400
        return jsonify({'error': str(e)}), 500
    finally:
        close_connection(conn)


@app.route('/api/code_agree/<cc>', methods=['DELETE', 'PUT'])
@jwt_required()
def update_delete_code_agree(cc):
    current_user = get_jwt_identity()
    if current_user != 'admin':
        return jsonify({'error': 'Admin only'}), 403
    conn, cursor = get_db_cursor()
    if not conn:
        return jsonify({'error': 'DB error'}), 500
    try:
        if request.method == 'DELETE':
            cursor.execute('DELETE FROM code_agree WHERE cc = %s', (cc,))
            if cursor.rowcount:
                conn.commit()
                return jsonify({'message': 'Supprimé'})
        else:
            data = request.get_json()
            societe = data['societe'].strip()
            cursor.execute('UPDATE code_agree SET societe = %s WHERE cc = %s', (societe, cc))
            if cursor.rowcount:
                conn.commit()
                return jsonify({'message': 'Mis à jour'})
        return jsonify({'error': 'Non trouvé'}), 404
    finally:
        close_connection(conn)


if __name__ == '__main__':
    init_db()
    # ✅ PORT dynamique pour Render (Render injecte la variable PORT)
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, port=port, host='0.0.0.0')
