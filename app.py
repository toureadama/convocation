#!/usr/bin/env python3
"""
Convocation Douanes CI - Backend API
Flask REST API with JWT authentication for generating customs convocation PDFs.
"""

import os
import re
import subprocess
import sys
import secrets
from datetime import datetime
from functools import wraps
from contextlib import contextmanager
import logging

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
import bcrypt
import pandas as pd
import mysql.connector

from db_config import get_db_connection, close_connection

# ============================================================================
# Application Configuration
# ============================================================================

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'douanes-local-jwt-super-secure-2024')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 900  # 15 minutes
jwt = JWTManager(app)
CORS(app)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# ============================================================================
# Constants
# ============================================================================

FRAUDE_MAP = {
    'FDE': 'FAUSSE DECLARATION ESPECE',
    'FDV': 'FAUSSE DECLARATION VALEUR',
    'ESP': 'ENLEVEMENT SANS PERMIS',
    'EXC': 'EXCEDENT'    
}

DEFAULT_PAGINATION = {'page': 0, 'limit': 20}
MAX_PAGINATION_LIMIT = 100

# ============================================================================
# Database Helpers
# ============================================================================

@contextmanager
def get_db_context():
    """Context manager for database connections with automatic cleanup."""
    conn = get_db_connection()
    if not conn:
        raise RuntimeError("Database connection failed")
    try:
        cursor = conn.cursor(dictionary=True)
        yield conn, cursor
    except Exception as e:
        logger.error(f"Database error: {e}")
        raise
    finally:
        close_connection(conn)

def validate_date(date_str):
    """Validate and normalize date string. Returns None if invalid."""
    if not date_str or not str(date_str).strip():
        return None
    
    date_str = str(date_str).strip()
    
    # Try ISO format
    try:
        return date_str.replace('Z', '+00:00') if 'Z' in date_str else date_str
    except Exception:
        pass
    
    # Try YYYY-MM-DD
    try:
        datetime.strptime(date_str[:10], '%Y-%m-%d')
        return date_str[:10]
    except ValueError:
        return None


def admin_required(f):
    """Decorator to require admin or super admin role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        current_user = get_jwt_identity()
        try:
            with get_db_context() as (conn, cursor):
                cursor.execute('SELECT role FROM users WHERE login = %s', (current_user,))
                user_row = cursor.fetchone()
                user_role = user_row['role'] if user_row else 'Vérificateur'
                
                if user_role not in ('Administrateur', 'Super Administrateur'):
                    return jsonify({'error': 'Admin access required'}), 403
        except Exception as e:
            logger.error(f"Admin check failed: {e}")
            return jsonify({'error': 'Access denied'}), 403
        
        return f(*args, **kwargs)
    return decorated_function

# ============================================================================
# Database Initialization
# ============================================================================

def init_db():
    """Initialize MySQL database tables and create admin user if missing."""
    try:
        conn = get_db_connection()
        if not conn:
            logger.error('MySQL connection failed')
            return False

        cursor = conn.cursor(dictionary=True)

        # Schema definitions (MySQL syntax)
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            civilite VARCHAR(50),
            nom VARCHAR(255) NOT NULL,
            prenom VARCHAR(255) NOT NULL,
            grade VARCHAR(255) NOT NULL,
            login VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            plain_password VARCHAR(255),
            is_active TINYINT DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            role VARCHAR(50) DEFAULT 'Vérificateur',
            signature_name TEXT
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS history (
            id INT AUTO_INCREMENT PRIMARY KEY,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            verificateur VARCHAR(255) NOT NULL,
            num_declaration VARCHAR(100) NOT NULL,
            date_declaration VARCHAR(50) NOT NULL,
            type_dossier VARCHAR(50),
            fraude VARCHAR(255) NOT NULL,
            signature_admin VARCHAR(255) NOT NULL,
            cc VARCHAR(100) NOT NULL,
            code_imp VARCHAR(100),
            date_accuse VARCHAR(50),
            retour_cda VARCHAR(10) DEFAULT 'NON',
            num_generated INT DEFAULT 0,
            filenames TEXT,
            user_login VARCHAR(255) NOT NULL,
            statut VARCHAR(50) DEFAULT 'EN_COURS',
            INDEX idx_user_login (user_login),
            INDEX idx_timestamp (timestamp),
            INDEX idx_cc (cc)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS code_agree (
            cc VARCHAR(100) PRIMARY KEY,
            societe VARCHAR(255) NOT NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS operateur (
            id INT AUTO_INCREMENT PRIMARY KEY,
            code_operateur VARCHAR(100) UNIQUE NOT NULL,
            nom_operateur VARCHAR(255) NOT NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4''')

        # Create default admin if not exists
        cursor.execute("SELECT COUNT(*) as cnt FROM users WHERE login='admin'")
        if cursor.fetchone()['cnt'] == 0:
            password = 'admin123'
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            cursor.execute(
                "INSERT INTO users (nom, prenom, grade, login, password_hash, plain_password) VALUES (%s, %s, %s, %s, %s, %s)",
                ('Admin', 'Super', 'Administrateur', 'admin', password_hash, '***')
            )
            logger.info("✅ Admin created: admin/admin123")

        conn.commit()
        logger.info("✅ MySQL database initialized successfully")
        return True

    except Exception as e:
        logger.error(f"MySQL database initialization failed: {e}")
        return False
    finally:
        close_connection(conn)

# ============================================================================
# Authentication Endpoints
# ============================================================================

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    try:
        with get_db_context() as (conn, cursor):
            return jsonify({'status': 'OK', 'db': 'MySQL douanesci_convocation'})
    except Exception:
        return jsonify({'status': 'ERROR', 'db': 'Connection failed'}), 500

@app.route('/api/login', methods=['POST'])
def login():
    """Authenticate user and return JWT token."""
    data = request.json
    
    if not data or not data.get('login') or not data.get('password'):
        return jsonify({'error': 'Login and password required'}), 400

    try:
        with get_db_context() as (conn, cursor):
            cursor.execute(
                'SELECT * FROM users WHERE login = %s AND is_active = 1',
                (data['login'],)
            )
            user = cursor.fetchone()
            
            if not user or not bcrypt.checkpw(data['password'].encode(), user['password_hash'].encode()):
                logger.warning(f"Failed login attempt for: {data['login']}")
                return jsonify({'error': 'Invalid credentials'}), 401

            token = create_access_token(identity=user['login'])
            logger.info(f"User logged in: {user['login']} ({user.get('role', 'Vérificateur')})")
            return jsonify({
                'token': token,
                'user': {
                    'id': user['id'],
                    'login': user['login'],
                    'nom': user['nom'],
                    'prenom': user['prenom'],
                    'grade': user.get('role', user['grade']),
                    'role': user.get('role', 'Vérificateur'),
                    'civilite': user.get('civilite'),
                    'signature_name': user.get('signature_name')
                }
            })
            
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/verify', methods=['GET'])
@jwt_required()
def verify():
    """Verify JWT token is valid."""
    return jsonify({'ok': True, 'user': get_jwt_identity()})

# ============================================================================
# History Endpoints
# ============================================================================

def build_history_query(current_user, filters, include_pagination=True):
    """Build SQL query for history with role-based filtering."""
    where_conditions = []
    params = []
    
    # Get user role
    try:
        with get_db_context() as (conn, cursor):
            cursor.execute(
                'SELECT role, signature_name FROM users WHERE login = %s',
                (current_user,)
            )
            user_info = cursor.fetchone()
            user_role = user_info['role'] if user_info else 'Vérificateur'
            user_signature = user_info['signature_name'] if user_info else None
    except Exception:
        user_role = 'Vérificateur'
        user_signature = None

    # Role-based filtering
    if user_role == 'Super Administrateur':
        # Super Admin sees ALL entries
        pass
    elif user_role == 'Administrateur':
        # Admin sees: own entries + entries where signature_admin matches
        if user_signature:
            where_conditions.append("(h.user_login = %s OR h.signature_admin = %s)")
            params.extend([current_user, user_signature])
        else:
            # If no signature_name, only show own entries
            where_conditions.append("h.user_login = %s")
            params.append(current_user)
    else:
        # Vérificateur sees only own entries
        where_conditions.append("h.user_login = %s")
        params.append(current_user)

    # Admin filters (for Admin and Super Admin only)
    if user_role in ('Administrateur', 'Super Administrateur') and filters:
        filter_map = [
            ('date_from', 'h.timestamp', '>='),
            ('date_to', 'h.timestamp', '<='),
            ('cc', 'h.cc', 'LIKE'),
            ('verif', 'h.verificateur', 'LIKE'),
            ('fraude', 'h.fraude', 'LIKE'),
            ('admin', 'h.signature_admin', 'LIKE'),
            ('statut', 'h.statut', '='),
        ]

        for key, col, op in filter_map:
            val = filters.get(key)
            if val and str(val).strip():
                if op == 'LIKE':
                    where_conditions.append(f"{col} LIKE %s")
                    params.append(f"%{val}%")
                elif op == '=':
                    where_conditions.append(f"{col} = %s")
                    params.append(val)
                else:
                    date_val = validate_date(val)
                    if date_val:
                        where_conditions.append(f"{col} {op} %s")
                        params.append(date_val)

    where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
    
    if include_pagination:
        query = f"""
            SELECT h.*, COALESCE(ca.societe, 'N/A') as declarant, COALESCE(o.nom_operateur, h.code_imp) as operateur
            FROM history h
            LEFT JOIN code_agree ca ON h.cc = ca.cc
            LEFT JOIN operateur o ON h.code_imp = o.code_operateur
            {where_clause}
            ORDER BY h.timestamp DESC
            LIMIT %s OFFSET %s
        """
    else:
        query = f"""
            SELECT h.*, COALESCE(ca.societe, 'N/A') as declarant, COALESCE(o.nom_operateur, h.code_imp) as operateur
            FROM history h
            LEFT JOIN code_agree ca ON h.cc = ca.cc
            LEFT JOIN operateur o ON h.code_imp = o.code_operateur
            {where_clause}
            ORDER BY h.timestamp DESC
        """
    
    return query, params

def serialize_history_rows(rows):
    """Convert database rows to JSON-serializable format."""
    serialized = []
    for row in rows:
        serialized.append({
            k: str(v) if not isinstance(v, (str, int, float, bool, type(None))) else v
            for k, v in dict(row).items()
        })
    return serialized

@app.route('/api/history', methods=['POST'])
@jwt_required()
def get_history():
    """Get convocation history with optional filters and pagination."""
    current_user = get_jwt_identity()

    try:
        data = request.json or {}
        page = max(0, int(data.get('page', DEFAULT_PAGINATION['page'])))
        limit = min(MAX_PAGINATION_LIMIT, max(1, int(data.get('limit', DEFAULT_PAGINATION['limit']))))
        filters = data.get('filters', {})
        offset = page * limit

        with get_db_context() as (conn, cursor):
            query, params = build_history_query(current_user, filters)
            params.extend([limit, offset])

            logger.info(f"Executing history query for user: {current_user}, page: {page}, limit: {limit}")
            logger.debug(f"Query params: {params}")

            cursor.execute(query, params)
            rows = serialize_history_rows(cursor.fetchall())

            logger.info(f"History retrieval successful: {len(rows)} records")
            return jsonify({'history': rows})

    except ValueError as e:
        logger.error(f"Invalid pagination parameters: {e}")
        return jsonify({'error': 'Invalid pagination parameters'}), 400
    except mysql.connector.Error as db_err:
        logger.error(f"Database error in history retrieval: {db_err}", exc_info=True)
        return jsonify({'error': f'Database error: {str(db_err)}'}), 500
    except Exception as e:
        logger.error(f"History retrieval error: {e}", exc_info=True)
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/api/history/<int:entry_id>/fields', methods=['PUT'])
@jwt_required()
def update_history_fields(entry_id):
    """Update date_accuse and/or retour_cda - only the owner can update."""
    current_user = get_jwt_identity()
    data = request.json
    
    allowed_fields = {'date_accuse', 'retour_cda'}
    updates = {k: v for k, v in data.items() if k in allowed_fields}
    
    if not updates:
        return jsonify({'error': 'No valid fields to update'}), 400

    try:
        with get_db_context() as (conn, cursor):
            # Check ownership
            cursor.execute(
                'SELECT id, user_login FROM history WHERE id = %s',
                (entry_id,)
            )
            entry = cursor.fetchone()
            
            if not entry:
                return jsonify({'error': 'Entry not found'}), 404
            
            # Only owner can update
            if entry['user_login'] != current_user:
                return jsonify({'error': 'Access denied. You can only modify your own entries.'}), 403
            
            fields = ', '.join(f'{k} = %s' for k in updates.keys())
            params = list(updates.values()) + [entry_id]

            cursor.execute(f'UPDATE history SET {fields} WHERE id = %s', params)
            conn.commit()
            
            logger.info(f"Fields updated for entry {entry_id} by {current_user}: {updates}")
            return jsonify({'success': True})
            
    except Exception as e:
        logger.error(f"Field update error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/history/export', methods=['POST'])
@jwt_required()
@admin_required
def history_export():
    """Export history to CSV format."""
    current_user = get_jwt_identity()
    try:
        data = request.json or {}
        filters = data.get('filters', {})

        with get_db_context() as (conn, cursor):
            query, params = build_history_query(current_user, filters, include_pagination=False)
            cursor.execute(query, params)
            rows = cursor.fetchall()

            if not rows:
                return jsonify({'error': 'No data to export'}), 404

            df = pd.DataFrame(rows)
            csv_data = df.to_csv(index=False)

            return csv_data, 200, {
                'Content-Type': 'text/csv',
                'Content-Disposition': 'attachment; filename=history_export.csv'
            }

    except Exception as e:
        logger.error(f"Export error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/history/<int:entry_id>/status', methods=['PUT'])
@jwt_required()
def update_history_status(entry_id):
    """Update convocation status - any user can update their own entries, admin can update all."""
    current_user = get_jwt_identity()
    data = request.json
    statut = data.get('statut')

    if not statut:
        return jsonify({'error': 'Status is required'}), 400

    try:
        with get_db_context() as (conn, cursor):
            # Check if entry exists
            cursor.execute(
                'SELECT id, user_login FROM history WHERE id = %s',
                (entry_id,)
            )
            entry = cursor.fetchone()

            if not entry:
                return jsonify({'error': 'Entry not found'}), 404

            # Check if user is admin
            cursor.execute('SELECT role FROM users WHERE login = %s', (current_user,))
            user_row = cursor.fetchone()
            user_role = user_row['role'] if user_row else 'Vérificateur'
            
            # Only owner or admin can update status
            if user_role not in ('Administrateur', 'Super Administrateur') and entry['user_login'] != current_user:
                return jsonify({'error': 'Access denied. You can only modify your own entries.'}), 403

            cursor.execute('UPDATE history SET statut = %s WHERE id = %s', (statut, entry_id))
            conn.commit()

            logger.info(f"Status updated for entry {entry_id} by {current_user}: {statut}")
            return jsonify({'success': True})

    except Exception as e:
        logger.error(f"Status update error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# ============================================================================
# User Management Endpoints
# ============================================================================

@app.route('/api/users', methods=['GET'])
@jwt_required()
def get_users():
    """List all active users."""
    try:
        with get_db_context() as (conn, cursor):
            cursor.execute(
                'SELECT id, login, nom, prenom, grade, civilite, created_at FROM users WHERE is_active = 1 ORDER BY nom'
            )
            return jsonify({'users': [dict(row) for row in cursor.fetchall()]})
    except Exception as e:
        logger.error(f"User list error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/users', methods=['POST'])
@jwt_required()
@admin_required
def create_user():
    """Create new user with manual login and password."""
    data = request.json
    current_user = get_jwt_identity()
    
    # Validate required fields
    if not data.get('nom') or not data.get('prenom') or not data.get('grade'):
        return jsonify({'error': 'Nom, prenom et grade sont requis'}), 400
    
    # Validate role based on current user's role
    try:
        with get_db_context() as (conn, cursor):
            cursor.execute('SELECT role FROM users WHERE login = %s', (current_user,))
            user_row = cursor.fetchone()
            creator_role = user_row['role'] if user_row else 'Vérificateur'
    except Exception:
        creator_role = 'Vérificateur'
    
    requested_role = data.get('role') or data.get('grade', 'Vérificateur')
    
    # Administrateur can only create Vérificateur
    if creator_role == 'Administrateur' and requested_role != 'Vérificateur':
        return jsonify({'error': 'Administrateur ne peut créer que des Vérificateurs'}), 403
    
    # Validate login if provided
    login = data.get('login', '').strip()
    password = data.get('password', '').strip()
    
    if not login:
        return jsonify({'error': 'Identifiant requis'}), 400
    
    if not password:
        return jsonify({'error': 'Mot de passe requis'}), 400
    
    # Validate login format
    if not re.match(r'^[a-zA-Z0-9._-]+$', login):
        return jsonify({'error': 'Identifiant invalide (caractères autorisés: a-z, 0-9, ., _, -)'}), 400

    try:
        with get_db_context() as (conn, cursor):
            # Check login uniqueness
            cursor.execute('SELECT COUNT(*) as cnt FROM users WHERE login = %s', (login,))
            if cursor.fetchone()['cnt'] > 0:
                return jsonify({'error': 'Cet identifiant existe déjà'}), 409

            # Build signature_name
            signature_name = f"{data['nom'].upper()} {data['prenom'].upper()}".strip()
            
            # Hash password
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

            # Insert user
            cursor.execute(
                'INSERT INTO users (civilite, nom, prenom, grade, login, password_hash, plain_password, role, signature_name) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)',
                (
                    data.get('civilite', ''),
                    data['nom'],
                    data['prenom'],
                    requested_role,
                    login,
                    password_hash,
                    password,
                    requested_role,
                    signature_name
                )
            )
            conn.commit()

            logger.info(f"User created: {login} (role: {requested_role}) by {current_user}")
            return jsonify({
                'success': True,
                'login': login,
                'message': f'Utilisateur {login} créé avec succès'
            }), 201

    except Exception as e:
        logger.error(f"User creation error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/<int:user_id>', methods=['PUT'])
@jwt_required()
@admin_required
def update_user(user_id):
    """Update user profile."""
    data = request.json
    allowed_fields = {'civilite', 'nom', 'prenom', 'grade'}
    updates = {k: v for k, v in data.items() if k in allowed_fields}

    if not updates:
        return jsonify({'error': 'No valid fields to update'}), 400

    try:
        with get_db_context() as (conn, cursor):
            fields = ', '.join(f'{k} = %s' for k in updates.keys())
            params = list(updates.values()) + [user_id]

            cursor.execute(f'UPDATE users SET {fields} WHERE id = %s', params)
            conn.commit()
            
            if cursor.rowcount == 0:
                return jsonify({'error': 'User not found'}), 404
                
            return jsonify({'success': True})
            
    except Exception as e:
        logger.error(f"User update error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_user(user_id):
    """Soft delete user (deactivate)."""
    try:
        with get_db_context() as (conn, cursor):
            cursor.execute('UPDATE users SET is_active = 0 WHERE id = %s', (user_id,))
            conn.commit()
            
            if cursor.rowcount == 0:
                return jsonify({'error': 'User not found'}), 404
                
            logger.info(f"User deactivated: {user_id}")
            return jsonify({'success': True})
            
    except Exception as e:
        logger.error(f"User deletion error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/users/<int:user_id>/credentials', methods=['PUT'])
@jwt_required()
@admin_required
def update_user_credentials(user_id):
    """Update user login and/or password."""
    data = request.json
    new_login = data.get('login', '').strip()
    new_password = data.get('password', '').strip()

    if not new_login or not new_password:
        return jsonify({'error': 'Login and password are required'}), 400

    try:
        with get_db_context() as (conn, cursor):
            # Check login uniqueness
            cursor.execute('SELECT id FROM users WHERE login = %s AND id != %s', (new_login, user_id))
            if cursor.fetchone():
                return jsonify({'error': 'Login already exists'}), 400

            # Update credentials
            password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            cursor.execute(
                'UPDATE users SET login = %s, password_hash = %s, plain_password = %s WHERE id = %s',
                (new_login, password_hash, new_password, user_id)
            )
            conn.commit()
            
            return jsonify({'success': True})

    except Exception as e:
        logger.error(f"Credentials update error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# ============================================================================
# Company Management Endpoints
# ============================================================================

@app.route('/api/companies', methods=['GET'])
@jwt_required()
def get_companies():
    """List all approved companies."""
    try:
        with get_db_context() as (conn, cursor):
            cursor.execute('SELECT cc, societe FROM code_agree ORDER BY societe')
            return jsonify({'companies': [dict(row) for row in cursor.fetchall()]})
    except Exception as e:
        logger.error(f"Company list error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/operateurs', methods=['GET'])
@jwt_required()
def get_operateurs():
    """List all operateurs."""
    try:
        with get_db_context() as (conn, cursor):
            cursor.execute('SELECT code_operateur, nom_operateur FROM operateur ORDER BY nom_operateur')
            return jsonify({'operateurs': [dict(row) for row in cursor.fetchall()]})
    except Exception as e:
        logger.error(f"Operateur list error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/code_agree', methods=['GET'])
@jwt_required()
def get_code_agree():
    """List all approved company codes (alias for /companies)."""
    return get_companies()

@app.route('/api/code_agree', methods=['POST'])
@jwt_required()
@admin_required
def add_code_agree():
    """Add new approved company."""
    data = request.json
    cc = data.get('cc', '').strip()
    societe = data.get('societe', '').strip()

    if not cc or not societe:
        return jsonify({'error': 'CC and societe are required'}), 400

    try:
        with get_db_context() as (conn, cursor):
            cursor.execute('INSERT INTO code_agree (cc, societe) VALUES (%s, %s)', (cc, societe))
            conn.commit()
            return jsonify({'success': True}), 201
    except Exception as e:
        if 'Duplicate entry' in str(e) or '1062' in str(e):
            return jsonify({'error': 'CC already exists'}), 409
        logger.error(f"Add company error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/code_agree/<cc>', methods=['PUT'])
@jwt_required()
@admin_required
def update_code_agree(cc):
    """Update company name."""
    data = request.json
    societe = data.get('societe', '').strip()

    if not societe:
        return jsonify({'error': 'Societe is required'}), 400

    try:
        with get_db_context() as (conn, cursor):
            cursor.execute('UPDATE code_agree SET societe = %s WHERE cc = %s', (societe, cc))
            conn.commit()
            
            if cursor.rowcount == 0:
                return jsonify({'error': 'Company not found'}), 404
                
            return jsonify({'success': True})
            
    except Exception as e:
        logger.error(f"Update company error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/code_agree/<cc>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_code_agree(cc):
    """Delete approved company."""
    try:
        with get_db_context() as (conn, cursor):
            cursor.execute('DELETE FROM code_agree WHERE cc = %s', (cc,))
            conn.commit()
            
            if cursor.rowcount == 0:
                return jsonify({'error': 'Company not found'}), 404
                
            return jsonify({'success': True})
            
    except Exception as e:
        logger.error(f"Delete company error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# ============================================================================
# PDF Generation Endpoint
# ============================================================================

@app.route('/api/generate', methods=['POST'])
@jwt_required()
def generate_convocation():
    """Generate convocation PDF."""
    required_fields = ['cc', 'code_imp', 'verificateur', 'num_declaration', 'date_declaration', 'type_dossier', 'fraude', 'signature_admin']

    # Validate required fields
    for field in required_fields:
        if not request.form.get(field):
            return jsonify({'error': f'Missing required field: {field}'}), 400

    user = get_jwt_identity()

    try:
        with get_db_context() as (conn, cursor):
            # Get next convocation number
            cursor.execute('SELECT COUNT(*) as cnt FROM history WHERE user_login = %s', (user,))
            count = cursor.fetchone()['cnt']
            next_num = f'{count + 1:04d}'

        # Build command
        cmd = [sys.executable, 'convocation_mysql.py', '--num_convoc', next_num]
        for field in required_fields:
            cmd.extend([f'--{field}', request.form[field]])

        # Execute generation
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60, cwd='.')

        if result.returncode != 0:
            logger.error(f"PDF generation failed: {result.stderr}")
            return jsonify({'error': f'Generation failed: {result.stderr}'}), 500

        # Parse output
        matches = re.findall(r'OK\s*:\s*([^\s\n\r]+)', result.stdout)
        results = [{'path': m, 'filename': os.path.basename(m)} for m in matches]

        # Save to history
        with get_db_context() as (conn, cursor):
            cursor.execute(
                '''INSERT INTO history (timestamp, verificateur, num_declaration, date_declaration, type_dossier, fraude, signature_admin, cc, code_imp, num_generated, filenames, user_login)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                (
                    datetime.now().isoformat(),
                    request.form['verificateur'],
                    request.form['num_declaration'],
                    request.form['date_declaration'],
                    request.form['type_dossier'],
                    request.form['fraude'],
                    request.form['signature_admin'],
                    request.form['cc'],
                    request.form['code_imp'],
                    len(results),
                    ';'.join(r['filename'] for r in results),
                    user
                )
            )
            conn.commit()

        logger.info(f"PDF generated: {len(results)} file(s) for user {user}")
        return jsonify({'success': True, 'results': results})

    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Generation timeout'}), 504
    except Exception as e:
        logger.error(f"Generation error: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# File Serving
# ============================================================================

@app.route('/output/<path:filename>')
def serve_pdf(filename):
    """Serve generated PDF files."""
    return send_from_directory('output', filename)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    """Serve React frontend in production."""
    try:
        if path != "" and os.path.exists(os.path.join('frontend', 'build', path)):
            return send_from_directory(os.path.join('frontend', 'build'), path)
        else:
            # Serve index.html for all other routes (React Router support)
            return send_from_directory(os.path.join('frontend', 'build'), 'index.html')
    except Exception:
        return jsonify({'error': 'Frontend not found'}), 404

# ============================================================================
# Application Entry Point
# ============================================================================

if __name__ == '__main__':
    if init_db():
        port = int(os.environ.get('PORT', 5000))
        is_production = os.environ.get('FLASK_ENV') == 'production'
        logger.info(f"Starting server on port {port} (production: {is_production})")
        app.run(debug=not is_production, port=port, host='0.0.0.0')
    else:
        logger.error("Failed to initialize database. Exiting.")
        sys.exit(1)
