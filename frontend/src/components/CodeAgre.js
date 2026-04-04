import React, { useState, useEffect } from 'react';
import './CodeAgre.css';

const CodeAgre = () => {
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [newCC, setNewCC] = useState('');
  const [newSociete, setNewSociete] = useState('');

  useEffect(() => {
    fetchCompanies();
  }, []);

  const fetchCompanies = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch('{API_URL}/api/code_agree', {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Erreur chargement');
      const data = await res.json();
      setCompanies(data.companies || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAdd = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('token');
      const res = await fetch('{API_URL}/api/code_agree', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ cc: newCC.trim(), societe: newSociete.trim() })
      });
      if (res.ok) {
        setNewCC('');
        setNewSociete('');
        fetchCompanies();
        alert('Code agréé ajouté');
      } else {
        const err = await res.json();
        alert(err.error || 'Erreur');
      }
    } catch (err) {
      alert('Erreur réseau');
    }
  };

  const handleDelete = async (cc) => {
    if (!window.confirm(`Supprimer ${cc}?`)) return;
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`{API_URL}/api/code_agree/${cc}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        fetchCompanies();
      }
    } catch (err) {
      window.alert('Erreur suppression');
    }
  };

  if (loading) return <div>Chargement codes agréés...</div>;
  if (error) return <div className="error">Erreur: {error}</div>;

  return (
    <div className="users-container">
      <h2>Codes Agréés (Admin)</h2>
      
      {/* Add Form */}
      <form onSubmit={handleAdd} className="add-form">
        <div className="form-grid">
          <input
            placeholder="Code Agréé (ex: 00231D)"
            value={newCC}
            onChange={(e) => setNewCC(e.target.value)}
            required
          />
          <input
            placeholder="Société"
            value={newSociete}
            onChange={(e) => setNewSociete(e.target.value)}
            required
          />
          <button type="submit" className="add-btn">Ajouter</button>
        </div>
      </form>

      {/* List */}
      <div className="table-container">
        <table className="users-table">
          <thead>
            <tr>
              <th>Code Agréé</th>
              <th>Société</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {companies.map((company) => (
              <tr key={company.cc}>
                <td>{company.cc}</td>
<td><input value={company.societe} onChange={(e) => {
  const newSociete = e.target.value;
  fetch(`{API_URL}/api/code_agree/${company.cc}`, {
    method: 'PUT',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({societe: newSociete})
  }).then(() => fetchCompanies());
}} className="edit-input" /></td>
                <td>
                  <button 
                    onClick={() => handleDelete(company.cc)}
                    className="delete-btn"
                  >
                    Supprimer
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {companies.length === 0 && <p>Aucun code agréé. Ajoutez-en !</p>}
      </div>

      <button onClick={fetchCompanies} className="refresh-btn">
        Rafraîchir
      </button>
    </div>
  );
};

export default CodeAgre;

