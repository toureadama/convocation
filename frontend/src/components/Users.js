import React, { useState, useEffect } from 'react';
import './Users.css';

const Users = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [formData, setFormData] = useState({ civilite: '', nom: '', prenom: '', grade: '', login: '', password: '' });
  const [editingId, setEditingId] = useState(null);
  const [showForm, setShowForm] = useState(false);

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch('/api/users', {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Erreur chargement');
      const data = await res.json();
      setUsers(data.users || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

      const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const method = editingId ? 'PUT' : 'POST';
      const url = editingId ? `/api/users/${editingId}` : '/api/users';
      const token = localStorage.getItem('token');
      const res = await fetch(url, {
        method,
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}` 
        },
        body: JSON.stringify({
          ...formData,
          civilite: formData.civilite || ''
        }),
      });
      const result = await res.json();
      if (!res.ok) throw new Error(result.error || 'Erreur sauvegarde');
      
      if (method === 'POST' && result.password) {
        alert(`Utilisateur créé ! Login: ${result.login} Password: ${result.password}`);
      }
    setFormData({ civilite: '', nom: '', prenom: '', grade: '', login: '', password: '' });
      setEditingId(null);
      setShowForm(false);
      fetchUsers();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleEdit = (user) => {
    setFormData({ civilite: user.civilite || '', nom: user.nom, prenom: user.prenom, grade: user.grade, login: '', password: '' });
    setEditingId(user.id);
    setShowForm(true);
  };

  const handleEditCredentials = async (user) => {
    const newLogin = prompt('Nouveau login:', user.login);
    if (newLogin === null) return;
    const newPassword = prompt('Nouveau mot de passe:', '');
    if (newPassword === null) return;
    if (!newLogin || !newPassword) {
      alert('Login et mot de passe requis');
      return;
    }
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`/api/users/${user.id}/credentials`, {
        method: 'PUT',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}` 
        },
        body: JSON.stringify({ login: newLogin, password: newPassword }),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.error || 'Erreur');
      }
      alert('Identifiants mis à jour');
      fetchUsers();
    } catch (err) {
      alert(err.message);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Supprimer utilisateur ?')) return;
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`/api/users/${id}`, { 
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Erreur suppression');
      fetchUsers();
    } catch (err) {
      setError(err.message);
    }
  };

  if (loading) return <div>Chargement utilisateurs...</div>;
  if (error) return <div className="error">Erreur: {error}</div>;

  return (
    <div className="users-container">
      <h2>Administration Utilisateurs</h2>
      <button onClick={() => setShowForm(true)} className="add-btn">
        + Nouvel utilisateur
      </button>
      
      {showForm && (
        <form onSubmit={handleSubmit} className="user-form">
          <h3>{editingId ? 'Modifier' : 'Créer'} utilisateur</h3>
          <div className="form-group">
            <label>Echelon</label>
            <input
              type="text"
              value={formData.civilite}
              onChange={(e) => setFormData({...formData, civilite: e.target.value})}
              maxlength="30"
            />
          </div>
          <div className="form-group">
            <label>Nom *</label>
            <input
              value={formData.nom}
              onChange={(e) => setFormData({...formData, nom: e.target.value})}
              required
            />
          </div>
          <div className="form-group">
            <label>Prénom *</label>
            <input
              value={formData.prenom}
              onChange={(e) => setFormData({...formData, prenom: e.target.value})}
              required
            />
          </div>
          {!editingId && (
            <>
              <div className="form-group">
                <label>Login (optionnel)</label>
                <input
                  type="text"
                  value={formData.login}
                  onChange={(e) => setFormData({...formData, login: e.target.value})}
                />
              </div>
              <div className="form-group">
                <label>Mot de passe (optionnel)</label>
                <input
                  type="password"
                  value={formData.password}
                  onChange={(e) => setFormData({...formData, password: e.target.value})}
                />
              </div>
            </>
          )}
          <div className="form-group">
            <label>Niveau *</label>
            <select
              value={formData.grade}
              onChange={(e) => setFormData({...formData, grade: e.target.value})}
              required
            >
              <option value="">Sélectionner grade</option>
              <option value="Administrateur">Administrateur</option>
              <option value="Vérificateur">Vérificateur</option>
            </select>
          </div>
          <div className="form-buttons">
            <button type="submit">Sauvegarder</button>
            <button type="button" onClick={() => {setShowForm(false); setEditingId(null); setFormData({});}}>
              Annuler
            </button>
          </div>
        </form>
      )}

      <table className="users-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Echelon</th>
            <th>Login</th>
            <th>Mot de passe</th>
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
              <td>{user.civilite || ''}</td>
              <td>{user.login}</td>
              <td>{user.plain_password || '***'}</td>
              <td>{user.nom}</td>
              <td>{user.prenom}</td>
              <td>{user.grade}</td>
              <td>{new Date(user.created_at).toLocaleDateString('fr-FR')}</td>
              <td>
                <button onClick={() => handleEdit(user)} className="edit-btn" title="Modifier profil">✏️</button>
                <button onClick={() => handleEditCredentials(user)} className="credentials-btn" title="Modifier identifiants">🔑</button>
                <button onClick={() => handleDelete(user.id)} className="delete-btn">🗑️</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default Users;

