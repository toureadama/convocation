import React, { useState, useEffect, useCallback } from 'react';
import { apiFetch, API_BASE_URL } from '../api';
import './History.css';

const DEFAULT_FILTERS = {
  date_from: '',
  date_to: '',
  cc: '',
  verif: '',
  fraude: '',
  admin: '',
  statut: ''
};

const PENDING_FILTERS = {
  admin: '',
  statut: 'EN_COURS'
};

const PAGINATION = {
  limit: 10
};

const History = ({ user, canViewAll }) => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [page, setPage] = useState(0);
  const [filters, setFilters] = useState(DEFAULT_FILTERS);

  const isAdmin = user?.role === 'Administrateur Technique' || user?.role === 'Super Administrateur' || user?.role === 'Chrono';

  const isTechniqueAdmin = user?.grade === 'Administrateur Technique' || user?.role === 'Administrateur Technique';

  const fetchHistory = useCallback(async () => {
    setLoading(true);
    setError('');

    try {
      const response = await apiFetch('/api/history', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          page,
          limit: PAGINATION.limit,
          filters: isAdmin ? filters : {}
        })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const errorMsg = errorData.error || `Erreur serveur (${response.status})`;
        throw new Error(errorMsg);
      }

      const data = await response.json();
      setHistory(data.history || []);
    } catch (err) {
      if (err.message === 'SESSION_EXPIRED') {
        setError('Session expirée. Veuillez vous reconnecter.');
        window.location.reload();
        return;
      }
      setError(err.message);
      console.error('History fetch error:', err);
    } finally {
      setLoading(false);
    }
  }, [page, filters, isAdmin]);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  // Auto-filter for admin: show pending convocations addressed to me
  useEffect(() => {
    if (isTechniqueAdmin && user?.signature_name && filters.admin !== user.signature_name) {
      setFilters({
        ...DEFAULT_FILTERS,
        admin: user.signature_name,
        statut: 'EN_COURS'
      });
    }
  }, [user, isTechniqueAdmin]);

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const clearFilters = () => {
    setFilters(DEFAULT_FILTERS);
    setPage(0);
  };

const updateStatus = async (entryId, newStatus) => {
    try {
      const response = await apiFetch(`/api/history/${entryId}/status`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ statut: newStatus })
      });

      if (!response.ok) {
        throw new Error('Erreur lors de la mise à jour');
      }

      setHistory(prev => prev.map(entry =>
        entry.id === entryId ? { ...entry, statut: newStatus } : entry
      ));
    } catch (err) {
      if (err.message === 'SESSION_EXPIRED') {
        window.location.reload();
        return;
      }
      alert(err.message);
    }
  };

  const updateField = async (entryId, field, value) => {
    try {
      const response = await apiFetch(`/api/history/${entryId}/fields`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ [field]: value })
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.error || 'Erreur lors de la mise à jour');
      }

      setHistory(prev => prev.map(entry =>
        entry.id === entryId ? { ...entry, [field]: value } : entry
      ));
    } catch (err) {
      if (err.message === 'SESSION_EXPIRED') {
        window.location.reload();
        return;
      }
      alert(err.message);
    }
  };

  const handleDelete = async (entryId) => {
    if (!window.confirm('Êtes-vous sûr de vouloir supprimer cette entrée ?')) return;

    try {
      const response = await apiFetch(`/api/history/${entryId}`, {
        method: 'DELETE'
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.error || 'Erreur lors de la suppression');
      }

      setHistory(prev => prev.filter(entry => entry.id !== entryId));
    } catch (err) {
      if (err.message === 'SESSION_EXPIRED') {
        window.location.reload();
        return;
      }
      alert(err.message);
    }
  };

  const handleExport = async () => {
    try {
      const response = await apiFetch('/api/history/export', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ filters })
      });

      if (!response.ok) {
        throw new Error('Erreur lors de l\'export');
      }

      const blob = await response.blob();
      const timestamp = new Date().toISOString().slice(0, 19).replace(/[:-]/g, '');
      const filename = `history_${timestamp}.csv`;

      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      link.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      alert(err.message);
    }
  };

  const formatDate = (isoString) => {
    try {
      return new Date(isoString).toLocaleDateString('fr-FR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
      });
    } catch {
      return isoString;
    }
  };

  if (loading) return <div className="loading">Chargement de l'historique...</div>;
  if (error) return <div className="error">Erreur: {error}</div>;

  return (
    <div className="history-container">
      <h2>Historique des Convocations</h2>

      {isAdmin && (
        <div className="filters-section">
          <h3>Filtres</h3>
          <div className="filters-grid">
            <input
              type="date"
              placeholder="Date début"
              value={filters.date_from}
              onChange={(e) => handleFilterChange('date_from', e.target.value)}
            />
            <input
              type="date"
              placeholder="Date fin"
              value={filters.date_to}
              onChange={(e) => handleFilterChange('date_to', e.target.value)}
            />
            <input
              placeholder="Code Agréé"
              value={filters.cc}
              onChange={(e) => handleFilterChange('cc', e.target.value)}
            />
            <input
              placeholder="Vérificateur"
              value={filters.verif}
              onChange={(e) => handleFilterChange('verif', e.target.value)}
            />
            <input
              placeholder="Objet"
              value={filters.fraude}
              onChange={(e) => handleFilterChange('fraude', e.target.value)}
            />
            <input
              placeholder="Admin (signature)"
              value={filters.admin}
              onChange={(e) => handleFilterChange('admin', e.target.value)}
            />
            <select
              value={filters.statut}
              onChange={(e) => handleFilterChange('statut', e.target.value)}
            >
              <option value="">Tous les statuts</option>
              <option value="EN_COURS">En cours</option>
              <option value="Levé">Levé</option>
              <option value="Confirmé">Confirmé</option>
              <option value="Refusé">Refusé</option>
            </select>
            <button onClick={fetchHistory} className="filter-btn">
              Appliquer
            </button>
            <button onClick={() => {
              setFilters({ ...DEFAULT_FILTERS, ...PENDING_FILTERS, admin: user?.signature_name || '' });
              setPage(0);
            }} className="pending-btn">
              Mes En Attente
            </button>
            <button onClick={clearFilters} className="clear-btn">
              Tout Afficher
            </button>
          </div>
        </div>
      )}

      {history.length === 0 ? (
        <p className="no-data">Aucune génération trouvée.</p>
      ) : (
        <div className="table-container">
          <table className="history-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Opérateur</th>
                <th>Type de dossier</th>
                <th>Déclarant</th>
                <th>Vérificateur</th>
                <th>N° Décl.</th>
                <th>Objet</th>
                <th>Admin</th>
                <th>Date accusé</th>
                <th>Retour CDA</th>
                <th>Fichiers</th>
                <th>Statut</th>
                <th>Numéro Chrono</th>
                {isTechniqueAdmin && <th>Actions</th>}
              </tr>
            </thead>
            <tbody>
              {history.map((entry) => (
                <tr key={entry.id}>
                  <td>{formatDate(entry.timestamp)}</td>
                  <td>{entry.operateur || '-'}</td>
                  <td>{entry.type_dossier || '-'}</td>
                  <td>{entry.declarant || '-'}</td>
                  <td>{entry.verificateur}</td>
                  <td>{entry.num_declaration}</td>
                  <td>{entry.fraude}</td>
                  <td>{entry.signature_admin}</td>
                  <td>
                    {entry.user_login === user?.login ? (
                      <input
                        type="date"
                        value={entry.date_accuse || ''}
                        onChange={(e) => updateField(entry.id, 'date_accuse', e.target.value)}
                        className="date-input"
                      />
                    ) : (
                      <span className="readonly-field">{entry.date_accuse || '-'}</span>
                    )}
                  </td>
                  <td>
                    {entry.user_login === user?.login ? (
                      <select
                        value={entry.retour_cda || 'NON'}
                        onChange={(e) => updateField(entry.id, 'retour_cda', e.target.value)}
                        className="retour-select"
                      >
                        <option value="NON">NON</option>
                        <option value="OUI">OUI</option>
                      </select>
                    ) : (
                      <span className="readonly-field">{entry.retour_cda || 'NON'}</span>
                    )}
                  </td>
                  <td>
                    {(entry.filenames || '')
                      .split(';')
                      .filter(f => f)
                      .map((f, i) => (
                        <a
                          key={i}
                          href={`${API_BASE_URL}/output/${f}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="download-link"
                          download={f}
                        >
                          📄 {f}
                        </a>
                      ))}
                  </td>
                  <td>
                    {entry.user_login === user?.login ? (
                      <select
                        value={entry.statut || 'EN_COURS'}
                        onChange={(e) => updateStatus(entry.id, e.target.value)}
                      >
                        <option value="EN_COURS">En cours</option>
                        <option value="Levé">Levé</option>
                        <option value="Confirmé">Confirmé</option>
                        <option value="Refusé">Refusé</option>
                      </select>
                    ) : (
                      <span className="statut-readonly">{entry.statut || 'En cours'}</span>
                    )}
                  </td>
                  <td>
                    {user?.role === 'Chrono' ? (
                      <input
                        type="text"
                        value={entry.numero_chrono || ''}
                        onChange={(e) => updateField(entry.id, 'numero_chrono', e.target.value)}
                        className="chrono-input"
                        placeholder="N° Chrono"
                      />
                    ) : (
                      <span className="readonly-field">{entry.numero_chrono || '-'}</span>
                    )}
                  </td>
                  {isTechniqueAdmin && (
                    <td>
                      <button
                        onClick={() => handleDelete(entry.id)}
                        className="delete-entry-btn"
                        title="Supprimer cette entrée"
                      >
                        🗑️
                      </button>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>

          <div className="pagination">
            {isAdmin && (
              <button onClick={handleExport} className="export-btn">
                📥 Exporter CSV
              </button>
            )}
            <button
              disabled={page === 0}
              onClick={() => setPage(p => Math.max(0, p - 1))}
            >
              ← Préc
            </button>
            <span className="page-info">Page {page + 1}</span>
            <button
              onClick={() => setPage(p => p + 1)}
              disabled={history.length < PAGINATION.limit}
            >
              Suiv →
            </button>
            <button onClick={fetchHistory} className="refresh-btn">
              🔄 Rafraîchir
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default React.memo(History);
