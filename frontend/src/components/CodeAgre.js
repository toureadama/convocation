import React, { useState, useEffect, useCallback } from 'react';
import { apiFetch, handleResponse } from '../api';
import './CodeAgre.css';

const CodeAgre = () => {
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [newCC, setNewCC] = useState('');
  const [newSociete, setNewSociete] = useState('');
  const [editingCC, setEditingCC] = useState(null);

  const fetchCompanies = useCallback(async () => {
    try {
      const response = await apiFetch('/api/code_agree');
      const data = await handleResponse(response);
      setCompanies(data.companies || []);
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
    fetchCompanies();
  }, [fetchCompanies]);

  const handleAdd = async (e) => {
    e.preventDefault();

    if (!newCC.trim() || !newSociete.trim()) {
      alert('Code et société requis');
      return;
    }

    try {
      const response = await apiFetch('/api/code_agree', {
        method: 'POST',
        body: JSON.stringify({ cc: newCC.trim(), societe: newSociete.trim() })
      });

      await handleResponse(response);
      setNewCC('');
      setNewSociete('');
      fetchCompanies();
    } catch (err) {
      if (err.message === 'SESSION_EXPIRED') {
        alert('⚠️ Session expirée. Veuillez vous reconnecter.');
      } else {
        alert('❌ ' + err.message);
      }
    }
  };

  const handleUpdate = async (cc, newSociete) => {
    try {
      const response = await apiFetch(`/api/code_agree/${cc}`, {
        method: 'PUT',
        body: JSON.stringify({ societe: newSociete })
      });
      await handleResponse(response);
      setEditingCC(null);
      fetchCompanies();
    } catch (err) {
      if (err.message === 'SESSION_EXPIRED') {
        alert('⚠️ Session expirée. Veuillez vous reconnecter.');
      } else {
        alert('❌ ' + err.message);
      }
    }
  };

  const handleDelete = async (cc) => {
    if (!window.confirm(`Supprimer le code ${cc}?`)) return;

    try {
      const response = await apiFetch(`/api/code_agree/${cc}`, {
        method: 'DELETE'
      });
      await handleResponse(response);
      fetchCompanies();
    } catch (err) {
      if (err.message === 'SESSION_EXPIRED') {
        alert('⚠️ Session expirée. Veuillez vous reconnecter.');
      } else {
        alert('❌ ' + err.message);
      }
    }
  };

  if (loading) return <div className="loading">Chargement des codes agréés...</div>;

  return (
    <div className="code-agre-container">
      <header className="code-agre-header">
        <h2>Gestion des Codes Agréés</h2>
      </header>

      {error && <div className="error" role="alert">{error}</div>}

      <form onSubmit={handleAdd} className="add-form">
        <h3>Ajouter un code agréé</h3>
        <div className="form-grid">
          <div className="form-group">
            <label htmlFor="cc">Code Agréé *</label>
            <input
              id="cc"
              type="text"
              placeholder="Ex: 00231D"
              value={newCC}
              onChange={(e) => setNewCC(e.target.value)}
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="societe">Société *</label>
            <input
              id="societe"
              type="text"
              placeholder="Nom de la société"
              value={newSociete}
              onChange={(e) => setNewSociete(e.target.value)}
              required
            />
          </div>
          <button type="submit" className="add-btn">
            ➕ Ajouter
          </button>
        </div>
      </form>

      {companies.length === 0 ? (
        <p className="no-data">Aucun code agréé enregistré.</p>
      ) : (
        <div className="table-container">
          <table className="companies-table">
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
                  <td><code>{company.cc}</code></td>
                  <td>
                    {editingCC === company.cc ? (
                      <div className="edit-inline">
                        <input
                          type="text"
                          value={company.societe}
                          onChange={(e) => {
                            setCompanies(prev =>
                              prev.map(c => c.cc === company.cc ? { ...c, societe: e.target.value } : c)
                            );
                          }}
                          autoFocus
                        />
                        <button onClick={() => handleUpdate(company.cc, company.societe)} className="save-btn">
                          ✓
                        </button>
                        <button onClick={() => {
                          setEditingCC(null);
                          fetchCompanies();
                        }} className="cancel-btn">
                          ✗
                        </button>
                      </div>
                    ) : (
                      <span
                        className="editable"
                        onClick={() => setEditingCC(company.cc)}
                        title="Cliquer pour modifier"
                      >
                        {company.societe}
                      </span>
                    )}
                  </td>
                  <td>
                    <button
                      onClick={() => handleDelete(company.cc)}
                      className="delete-btn"
                      title="Supprimer"
                    >
                      🗑️
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="table-footer">{companies.length} code(s) agré(s) enregistré(s)</p>
        </div>
      )}

      <button onClick={fetchCompanies} className="refresh-btn">
        🔄 Rafraîchir
      </button>
    </div>
  );
};

export default React.memo(CodeAgre);
