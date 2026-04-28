import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { apiFetch, handleResponse } from '../api';
import './CodeAgre.css';

const CodeAgre = () => {
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [newCC, setNewCC] = useState('');
  const [newSociete, setNewSociete] = useState('');
  const [editingCC, setEditingCC] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [isAdding, setIsAdding] = useState(false);
  const debounceRef = useRef(null);

  // Debounced search
  useEffect(() => {
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }
    debounceRef.current = setTimeout(() => {
      // Debounced search logic would go here if needed
    }, 300);
    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, [searchQuery]);

  const fetchCompanies = useCallback(async () => {
    setLoading(true);
    setError('');

    // Check cache first
    const cached = localStorage.getItem('code_agree_cache');
    if (cached) {
      try {
        const { data, timestamp } = JSON.parse(cached);
        if (Date.now() - timestamp < 5 * 60 * 1000) { // 5 minutes
          setCompanies(data);
          setLoading(false);
          return;
        }
      } catch (e) {
        console.warn('Cache read error:', e);
      }
    }

    try {
      const response = await apiFetch('/api/code_agree');
      const data = await handleResponse(response);
      const companiesData = data.companies || [];
      setCompanies(companiesData);

      // Cache the data
      localStorage.setItem('code_agree_cache', JSON.stringify({
        data: companiesData,
        timestamp: Date.now()
      }));
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

  // Filter companies based on search query (optimized)
  const filteredCompanies = useMemo(() => {
    if (!searchQuery.trim()) return companies;
    const query = searchQuery.toLowerCase().trim();
    if (query.length < 2) return companies; // Don't filter for very short queries

    return companies.filter(company =>
      company.cc.toLowerCase().includes(query) ||
      company.societe.toLowerCase().includes(query)
    );
  }, [companies, searchQuery]);

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
      setIsAdding(false);
      await fetchCompanies();
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
        <h2>📋 Gestion des Codes Agréés</h2>
        <button className="btn-add" onClick={() => setIsAdding(!isAdding)}>
          {isAdding ? '✕ Annuler' : '➕ Ajouter un code agréé'}
        </button>
      </header>

      {error && <div className="error" role="alert">{error}</div>}

      {/* Stats Banner */}
      <div className="stats-banner">
        <div>
          <div className="stat-number">{companies.length}</div>
          <div className="stat-label">Code(s) Agréé(s) enregistré(s)</div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div className="stat-number">
            {searchQuery ? filteredCompanies.length : companies.length}
          </div>
          <div className="stat-label">Affiché(s)</div>
        </div>
      </div>

      {/* Add Form */}
      {isAdding && (
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
      )}

      {/* Toolbar with Search */}
      {companies.length > 0 && (
        <div className="toolbar">
          <input
            type="text"
            className="search-input"
            placeholder="🔍 Rechercher un code ou une société..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          <button className="btn-refresh" onClick={() => fetchCompanies()}>
            🔄 Rafraîchir
          </button>
        </div>
      )}

      {filteredCompanies.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">📦</div>
          <div className="empty-state-text">
            {searchQuery
              ? 'Aucun résultat pour cette recherche.'
              : 'Aucun code agréé enregistré.'}
          </div>
          {!searchQuery && (
            <div className="empty-state-subtext">
              Cliquez sur "Ajouter un code agréé" pour commencer.
            </div>
          )}
        </div>
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
              {filteredCompanies.map((company) => (
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
                    <div className="actions-cell">
                      <button
                        className="btn-icon edit"
                        onClick={() => setEditingCC(company.cc)}
                        title="Modifier"
                      >
                        ✏️
                      </button>
                      <button
                        onClick={() => handleDelete(company.cc)}
                        className="delete-btn"
                        title="Supprimer"
                      >
                        🗑️
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* Table Footer */}
          <div className="table-footer">
            <span className="record-count">
              {filteredCompanies.length} sur {companies.length} code(s) agréé(s)
            </span>
            <span style={{ fontSize: '0.85rem', color: '#6c757d' }}>
              💡 Astuce: Cliquez sur une société pour la modifier
            </span>
          </div>
        </div>
      )}

      <button onClick={fetchCompanies} className="refresh-btn">
        🔄 Rafraîchir
      </button>
    </div>
  );
};

export default React.memo(CodeAgre);
