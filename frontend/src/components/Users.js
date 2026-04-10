import React, { useState, useEffect, useCallback } from 'react';
import { apiFetch, handleResponse } from '../api';
import './Users.css';

const GRADE_OPTIONS = ['Vérificateur', 'Administrateur', 'Super Administrateur'];

const Users = ({ currentUserRole }) => {
  const isSuperAdmin = currentUserRole === 'Super Administrateur';
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [formData, setFormData] = useState({
    civilite: '',
    nom: '',
    prenom: '',
    grade: '',
    login: '',
    password: ''
  });
  const [editingId, setEditingId] = useState(null);
  const [showForm, setShowForm] = useState(false);

  const fetchUsers = useCallback(async () => {
    try {
      const response = await apiFetch('/api/users');
      const data = await handleResponse(response);
      setUsers(data.users || []);
    } catch (err) {
      if (err.message === 'SESSION_EXPIRED') {
        setError('Session expirée. Veuillez vous reconnecter.');
      } else {
        setError(err.message);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      const method = editingId ? 'PUT' : 'POST';
      const url = editingId ? `/api/users/${editingId}` : '/api/users';

      const body = editingId
        ? { civilite: formData.civilite, nom: formData.nom, prenom: formData.prenom, grade: formData.grade }
        : {
            civilite: formData.civilite,
            nom: formData.nom,
            prenom: formData.prenom,
            grade: formData.grade,
            login: formData.login,
            password: formData.password
          };

      const response = await apiFetch(url, {
        method,
        body: JSON.stringify(body)
      });

      const result = await handleResponse(response);

      if (method === 'POST') {
        alert(`✅ Utilisateur créé avec succès!\n\nIdentifiant: ${result.login}\n\nL'utilisateur peut maintenant se connecter.`);
      } else {
        alert('✅ Utilisateur modifié avec succès');
      }

      resetForm();
      fetchUsers();
    } catch (err) {
      if (err.message === 'SESSION_EXPIRED') {
        setError('Session expirée. Veuillez vous reconnecter.');
      } else {
        setError(err.message);
      }
    }
  };

  const handleEdit = (user) => {
    setFormData({
      civilite: user.civilite || '',
      nom: user.nom,
      prenom: user.prenom,
      grade: user.grade,
      password: ''
    });
    setEditingId(user.id);
    setShowForm(true);
  };

  const handleEditCredentials = async (user) => {
    const newLogin = prompt('Nouvel identifiant:', user.login);
    if (!newLogin) return;

    const newPassword = prompt('Nouveau mot de passe:');
    if (newPassword === null) return;

    if (!newLogin.trim() || !newPassword.trim()) {
      alert('Identifiant et mot de passe requis');
      return;
    }

    try {
      const response = await apiFetch(`/api/users/${user.id}/credentials`, {
        method: 'PUT',
        body: JSON.stringify({ login: newLogin, password: newPassword })
      });

      await handleResponse(response);
      alert('✅ Identifiants mis à jour');
      fetchUsers();
    } catch (err) {
      if (err.message === 'SESSION_EXPIRED') {
        alert('⚠️ Session expirée. Veuillez vous reconnecter.');
      } else {
        alert('❌ ' + err.message);
      }
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Désactiver cet utilisateur?')) return;

    try {
      const response = await apiFetch(`/api/users/${id}`, {
        method: 'DELETE'
      });
      await handleResponse(response);
      fetchUsers();
    } catch (err) {
      if (err.message === 'SESSION_EXPIRED') {
        setError('Session expirée. Veuillez vous reconnecter.');
      } else {
        setError(err.message);
      }
    }
  };

  const resetForm = () => {
    setFormData({ civilite: '', nom: '', prenom: '', grade: '', login: '', password: '' });
    setEditingId(null);
    setShowForm(false);
    setError('');
  };

  const handleChange = (e) => {
    setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  if (loading) return <div className="loading">Chargement des utilisateurs...</div>;

  return (
    <div className="users-container">
      <header className="users-header">
        <h2>Administration des Utilisateurs</h2>
        <button onClick={() => setShowForm(true)} className="add-btn">
          + Nouvel utilisateur
        </button>
      </header>

      {error && <div className="error" role="alert">{error}</div>}

      {showForm && (
        <form onSubmit={handleSubmit} className="user-form">
          <h3>{editingId ? 'Modifier' : 'Créer'} un utilisateur</h3>

          <div className="form-grid">
            <div className="form-group">
              <label htmlFor="civilite">Échelon</label>
              <input
                id="civilite"
                name="civilite"
                type="text"
                value={formData.civilite}
                onChange={handleChange}
                maxLength={30}
                placeholder="Ex: M."
              />
            </div>

            <div className="form-group">
              <label htmlFor="nom">Nom *</label>
              <input
                id="nom"
                name="nom"
                type="text"
                value={formData.nom}
                onChange={handleChange}
                required
                placeholder="Nom de famille"
              />
            </div>

            <div className="form-group">
              <label htmlFor="prenom">Prénom *</label>
              <input
                id="prenom"
                name="prenom"
                type="text"
                value={formData.prenom}
                onChange={handleChange}
                required
                placeholder="Prénom"
              />
            </div>

            {!editingId && (
              <>
                <div className="form-group">
                  <label htmlFor="login">Identifiant *</label>
                  <input
                    id="login"
                    name="login"
                    type="text"
                    value={formData.login}
                    onChange={handleChange}
                    required
                    placeholder="Identifiant de connexion"
                    autoComplete="off"
                  />
                  <small className="help-text">L'identifiant doit être unique</small>
                </div>

                <div className="form-group">
                  <label htmlFor="password">Mot de passe *</label>
                  <div className="password-input-wrapper">
                    <input
                      id="password"
                      name="password"
                      type="password"
                      value={formData.password}
                      onChange={handleChange}
                      required
                      placeholder="Mot de passe sécurisé"
                      autoComplete="new-password"
                    />
                  </div>
                  <small className="help-text">Minimum 6 caractères recommandé</small>
                </div>
              </>
            )}

            <div className="form-group">
              <label htmlFor="grade">Niveau *</label>
              <select
                id="grade"
                name="grade"
                value={formData.grade}
                onChange={handleChange}
                required
              >
                <option value="">Sélectionner un niveau</option>
                {GRADE_OPTIONS
                  .filter(grade => isSuperAdmin || grade === 'Vérificateur')
                  .map(grade => (
                    <option key={grade} value={grade}>{grade}</option>
                  ))}
              </select>
            </div>
          </div>

          <div className="form-buttons">
            <button type="submit" className="save-btn">
              {editingId ? 'Modifier' : 'Créer'}
            </button>
            <button type="button" onClick={resetForm} className="cancel-btn">
              Annuler
            </button>
          </div>
        </form>
      )}

      {users.length === 0 ? (
        <p className="no-data">Aucun utilisateur trouvé.</p>
      ) : (
        <div className="table-container">
          <table className="users-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Échelon</th>
                <th>Identifiant</th>
                <th>Nom</th>
                <th>Prénom</th>
                <th>Niveau</th>
                <th>Créé le</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.id}>
                  <td>{user.id}</td>
                  <td>{user.civilite || '-'}</td>
                  <td><code>{user.login}</code></td>
                  <td>{user.nom}</td>
                  <td>{user.prenom}</td>
                  <td>
                    <span className={`badge badge-${user.grade === 'Administrateur' ? 'admin' : 'user'}`}>
                      {user.grade}
                    </span>
                  </td>
                  <td>{new Date(user.created_at).toLocaleDateString('fr-FR')}</td>
                  <td className="actions">
                    <button onClick={() => handleEdit(user)} className="edit-btn" title="Modifier">
                      ✏️
                    </button>
                    <button onClick={() => handleEditCredentials(user)} className="key-btn" title="Modifier identifiants">
                      🔑
                    </button>
                    <button onClick={() => handleDelete(user.id)} className="delete-btn" title="Désactiver">
                      🗑️
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default React.memo(Users);
