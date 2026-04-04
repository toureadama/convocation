import React, { useState, useEffect, useCallback } from 'react';
import './History.css';

const API_URL = process.env.REACT_APP_API_URL

const History = ({ user }) => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [page, setPage] = useState(0);
  const [filters, setFilters] = useState({
    date_from: '',
    date_to: '',
    cc: '',
    verif: '',
    fraude: '',
    admin: '',
    statut: ''
  });
  const limit = 10;
  const isAdmin = user?.grade === 'Administrateur';

  const buildQuery = () => {
    const params = new URLSearchParams({ page, limit });
    if (isAdmin) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value) {
          params.append(`filter_${key}`, value);
        }
      });
    }
    return params.toString();
  };

  const fetchHistory = useCallback(async () => {
    try {
      const token = localStorage.getItem('token');
      const query = buildQuery();
      const res = await fetch(`{API_URL}/api/history?${query}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Failed to fetch');
      const data = await res.json();
      setHistory(data.history || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [page, filters]);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  const formatDate = (iso) => {
    const date = new Date(iso);
    return date.toLocaleDateString('fr-FR');
  };

  const updateStatus = async (entryId, newStatus) => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`{API_URL}/api/history/${entryId}/status`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ statut: newStatus })
      });
      if (res.ok) {
        fetchHistory(); // Refresh
      } else {
        alert('Erreur save');
      }
    } catch (err) {
      alert('Erreur réseau');
    }
  };

  if (loading) return <div>Chargement historique...</div>;
  if (error) return <div className="error">Erreur: {error}</div>;

  return (
    <div className="history-container">
      <h2>Historique Convocations</h2>
      
      {isAdmin && (
        <div className="filters-section">
          <h3>Filtres (Admin)</h3>
          <div className="filters-grid">
            <input
              type="date"
              placeholder="Date début"
              value={filters.date_from}
              onChange={(e) => setFilters({...filters, date_from: e.target.value})}
            />
            <input
              type="date"
              placeholder="Date fin"
              value={filters.date_to}
              onChange={(e) => setFilters({...filters, date_to: e.target.value})}
            />
            <input
              placeholder="CA"
              value={filters.cc}
              onChange={(e) => setFilters({...filters, cc: e.target.value})}
            />
            <input
              placeholder="Vérificateur"
              value={filters.verif}
              onChange={(e) => setFilters({...filters, verif: e.target.value})}
            />
            <input
              placeholder="Fraude"
              value={filters.fraude}
              onChange={(e) => setFilters({...filters, fraude: e.target.value})}
            />
            <input
              placeholder="Admin (signature)"
              value={filters.admin}
              onChange={(e) => setFilters({...filters, admin: e.target.value})}
            />
            <select
              value={filters.statut}
              onChange={(e) => setFilters({...filters, statut: e.target.value})}
            >

              <option value=" ">Tous statuts</option>
              <option value=" "> </option>
              <option value="Levé">Levé</option>
              <option value="Confirmé">Confirmé</option>
              <option value="Refusé">Refusé</option>

            </select>
            <button onClick={fetchHistory} className="filter-btn">Appliquer</button>
            <button onClick={() => setFilters({date_from:'',date_to:'',cc:'',verif:'',fraude:'',admin:'',statut:''})} className="clear-btn">Effacer</button>
          </div>
        </div>
      )}
      
      {history.length === 0 ? (
        <p>Aucune génération. Faites une génération pour voir l'historique.</p>
      ) : (
        <div className="table-container">
          <table className="history-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>CA</th>
                <th>Vérificateur</th>
                <th>N° Décl.</th>
                <th>Fraude</th>
                <th>Admin</th>
                <th>Générés</th>
                <th>Statut du contentieux</th>
                <th>Fichiers</th>
              </tr>
            </thead>
            <tbody>
              {history.map((entry) => (
                <tr key={entry.id}>
                  <td>{formatDate(entry.timestamp)}</td>
                  <td>{entry.cc || ''}</td>
                  <td>{entry.verificateur}</td>
                  <td>{entry.num_declaration}</td>
                  <td>{entry.fraude}</td>
                  <td>{entry.signature_admin}</td>
                  <td>{entry.num_generated}</td>
                  <td>

                    <select 
                      value={entry.statut || ' '}
                      onChange={(e) => updateStatus(entry.id, e.target.value)}
                    >
                      <option value=" "> </option>
                      <option value="Levé">Levé</option>
                      <option value="Confirmé">Confirmé</option>
                      <option value="Refusé">Refusé</option>
                    </select>

                  </td>
                  <td>
{(entry.filenames || '').split(';').filter(f => f).map((f, i) => (
                      <a key={i} href={`{API_URL}/output/${f}`} target="_blank" rel="noopener noreferrer" className="download-link">
                        {f}
                      </a>
                    ))}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="pagination">
            {isAdmin && (
              <button 
                onClick={async () => {
                  const token = localStorage.getItem('token');
                  const query = buildQuery().replace(/page=\d+&limit=\d+/, '');
                  const url = `{API_URL}/api/history/export?${query}`;
                  const res = await fetch(url, {
                    headers: { Authorization: `Bearer ${token}` }
                  });
                  const blob = await res.blob();
                  const timestamp = new Date().toISOString().slice(0,19).replace(/[:-]/g,'');
                  const filename = `history_${timestamp}.csv`;
                  const a = document.createElement('a');
                  a.href = URL.createObjectURL(blob);
                  a.download = filename;
                  a.click();
                }}
                className="export-btn"
              >

                Télécharger
              
              </button>
            )}
            <button disabled={page === 0} onClick={() => setPage(p => p - 1)}>Préc</button>
            <span>Page {page + 1}</span>
            <button onClick={() => setPage(p => p + 1)}>Suivant</button>
            <button onClick={fetchHistory}>Rafraîchir</button>
          </div>
        </div>
      )}
    </div>
  );
};

export default History;

