import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { apiFetch, handleResponse } from '../api';
import './CodeOperateur.css';

const CodeOperateur = () => {
  const [operateurs, setOperateurs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [newCode, setNewCode] = useState('');
  const [newNom, setNewNom] = useState('');
  const [editingId, setEditingId] = useState(null);
  const [editValue, setEditValue] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [isAdding, setIsAdding] = useState(false);

  // Fetch all operateurs
  const fetchOperateurs = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const response = await apiFetch('/api/code_operateur');
      const data = await handleResponse(response);
      setOperateurs(data.operateurs || []);
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
    fetchOperateurs();
  }, [fetchOperateurs]);

  // Filter operateurs based on search query
  const filteredOperateurs = useMemo(() => {
    if (!searchQuery.trim()) return operateurs;
    const query = searchQuery.toLowerCase();
    return operateurs.filter(
      op =>
        op.code_operateur.toLowerCase().includes(query) ||
        op.nom_operateur.toLowerCase().includes(query)
    );
  }, [operateurs, searchQuery]);

  // Add new operateur
  const handleAdd = async (e) => {
    e.preventDefault();

    if (!newCode.trim() || !newNom.trim()) {
      alert('Veuillez remplir le code et le nom de l\'opérateur.');
      return;
    }

    try {
      const response = await apiFetch('/api/code_operateur', {
        method: 'POST',
        body: JSON.stringify({
          code_operateur: newCode.trim(),
          nom_operateur: newNom.trim()
        })
      });

      await handleResponse(response);
      setNewCode('');
      setNewNom('');
      setIsAdding(false);
      await fetchOperateurs();
    } catch (err) {
      if (err.message === 'SESSION_EXPIRED') {
        alert('⚠️ Session expirée. Veuillez vous reconnecter.');
      } else {
        alert('❌ ' + err.message);
      }
    }
  };

  // Start inline editing
  const startEdit = (operateur) => {
    setEditingId(operateur.id);
    setEditValue(operateur.nom_operateur);
  };

  // Save edited value
  const handleSave = async (operateur) => {
    if (!editValue.trim()) {
      alert('Le nom ne peut pas être vide.');
      return;
    }

    try {
      const response = await apiFetch(
        `/api/code_operateur/${encodeURIComponent(operateur.code_operateur)}`,
        {
          method: 'PUT',
          body: JSON.stringify({ nom_operateur: editValue.trim() })
        }
      );
      await handleResponse(response);
      setEditingId(null);
      setEditValue('');
      await fetchOperateurs();
    } catch (err) {
      if (err.message === 'SESSION_EXPIRED') {
        alert('⚠️ Session expirée. Veuillez vous reconnecter.');
      } else {
        alert('❌ ' + err.message);
      }
    }
  };

  // Cancel editing
  const handleCancelEdit = () => {
    setEditingId(null);
    setEditValue('');
  };

  // Delete operateur
  const handleDelete = async (operateur) => {
    const confirmed = window.confirm(
      `Êtes-vous sûr de vouloir supprimer le code opérateur "${operateur.code_operateur}" ?\n\nCette action est irréversible.`
    );

    if (!confirmed) return;

    try {
      const response = await apiFetch(
        `/api/code_operateur/${encodeURIComponent(operateur.code_operateur)}`,
        { method: 'DELETE' }
      );
      await handleResponse(response);
      await fetchOperateurs();
    } catch (err) {
      if (err.message === 'SESSION_EXPIRED') {
        alert('⚠️ Session expirée. Veuillez vous reconnecter.');
      } else {
        alert('❌ ' + err.message);
      }
    }
  };

  // Loading state
  if (loading) {
    return (
      <div className="code-operateur-container">
        <div className="loading-state">
          <div className="loading-spinner"></div>
          <span>Chargement des codes opérateurs...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="code-operateur-container">
      {/* Header */}
      <header className="code-operateur-header">
        <h2>📋 Gestion des Codes Opérateurs</h2>
        <button className="btn-add" onClick={() => setIsAdding(!isAdding)}>
          {isAdding ? '✕ Annuler' : '➕ Ajouter un opérateur'}
        </button>
      </header>

      {/* Error Alert */}
      {error && (
        <div className="error-alert" role="alert">
          <span>⚠️</span>
          <span>{error}</span>
        </div>
      )}

      {/* Stats Banner */}
      <div className="stats-banner">
        <div>
          <div className="stat-number">{operateurs.length}</div>
          <div className="stat-label">Code(s) Opérateur(s) enregistré(s)</div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div className="stat-number">
            {searchQuery ? filteredOperateurs.length : operateurs.length}
          </div>
          <div className="stat-label">Affiché(s)</div>
        </div>
      </div>

      {/* Add Form */}
      {isAdding && (
        <form onSubmit={handleAdd} className="add-operateur-form">
          <h3>➕ Nouvel Opérateur</h3>
          <div className="form-row">
            <div className="form-field">
              <label htmlFor="code-operateur">Code Opérateur *</label>
              <input
                id="code-operateur"
                type="text"
                placeholder="Ex: 1222798H"
                value={newCode}
                onChange={(e) => setNewCode(e.target.value)}
                required
                autoFocus
              />
            </div>
            <div className="form-field">
              <label htmlFor="nom-operateur">Nom Opérateur *</label>
              <input
                id="nom-operateur"
                type="text"
                placeholder="Raison sociale de l'opérateur"
                value={newNom}
                onChange={(e) => setNewNom(e.target.value)}
                required
              />
            </div>
            <button type="submit" className="btn-add">
              ✓ Enregistrer
            </button>
          </div>
        </form>
      )}

      {/* Toolbar with Search */}
      {operateurs.length > 0 && (
        <div className="toolbar">
          <input
            type="text"
            className="search-input"
            placeholder="🔍 Rechercher un code ou un nom d'opérateur..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          <button className="btn-refresh" onClick={fetchOperateurs}>
            🔄 Rafraîchir
          </button>
        </div>
      )}

      {/* Table or Empty State */}
      {filteredOperateurs.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">📦</div>
          <div className="empty-state-text">
            {searchQuery
              ? 'Aucun résultat pour cette recherche.'
              : 'Aucun code opérateur enregistré.'}
          </div>
          {!searchQuery && (
            <div className="empty-state-subtext">
              Cliquez sur "Ajouter un opérateur" pour commencer.
            </div>
          )}
        </div>
      ) : (
        <div className="operateur-table-wrapper">
          <table className="operateur-table">
            <thead>
              <tr>
                <th style={{ width: '200px' }}>Code Opérateur</th>
                <th>Nom Opérateur</th>
                <th style={{ width: '120px', textAlign: 'center' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredOperateurs.map((operateur) => (
                <tr key={operateur.id}>
                  <td>
                    <span className="code-badge">{operateur.code_operateur}</span>
                  </td>
                  <td>
                    {editingId === operateur.id ? (
                      <div className="inline-edit">
                        <input
                          type="text"
                          value={editValue}
                          onChange={(e) => setEditValue(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') handleSave(operateur);
                            if (e.key === 'Escape') handleCancelEdit();
                          }}
                          autoFocus
                        />
                        <button
                          className="btn-save"
                          onClick={() => handleSave(operateur)}
                          title="Enregistrer"
                        >
                          ✓
                        </button>
                        <button
                          className="btn-cancel"
                          onClick={handleCancelEdit}
                          title="Annuler"
                        >
                          ✕
                        </button>
                      </div>
                    ) : (
                      <span
                        className="editable-field"
                        onClick={() => startEdit(operateur)}
                        title="Cliquer pour modifier"
                      >
                        {operateur.nom_operateur}
                      </span>
                    )}
                  </td>
                  <td>
                    <div className="actions-cell">
                      <button
                        className="btn-icon edit"
                        onClick={() => startEdit(operateur)}
                        title="Modifier"
                      >
                        ✏️
                      </button>
                      <button
                        className="btn-delete"
                        onClick={() => handleDelete(operateur)}
                        title="Supprimer"
                      >
                        🗑️ Supprimer
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
              {filteredOperateurs.length} sur {operateurs.length} opérateur(s)
            </span>
            <span style={{ fontSize: '0.85rem', color: '#6c757d' }}>
              💡 Astuce: Cliquez sur un nom pour le modifier
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

export default React.memo(CodeOperateur);
