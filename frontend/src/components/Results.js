import React, { useCallback } from 'react';
import './Results.css';

// Use backend URL directly for PDF links
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

const Results = ({ results }) => {
  const handlePreview = useCallback((result) => {
    const url = `${API_BASE_URL}/output/${result.filename}`;
    window.open(url, '_blank');
  }, []);

  const handleDownload = useCallback((result) => {
    const url = `${API_BASE_URL}/output/${result.filename}`;
    
    fetch(url)
      .then(response => {
        if (!response.ok) throw new Error('File not found');
        return response.blob();
      })
      .then(blob => {
        const blobUrl = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = blobUrl;
        link.download = result.filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(blobUrl);
      })
      .catch(err => {
        console.error('Download error:', err);
        window.open(url, '_blank');
      });
  }, []);

  if (!results || results.length === 0) return null;

  return (
    <div className="results-container">
      <header className="results-header">
        <h2>Résultats</h2>
        <span className="badge">{results.length} fichier(s) généré(s)</span>
      </header>

      <div className="results-list">
        {results.map((result, index) => (
          <div key={index} className="result-item">
            <div className="file-info">
              <span className="file-icon">📄</span>
              <span className="file-name">{result.filename}</span>
            </div>

            <div className="result-actions">
              <button
                onClick={() => handlePreview(result)}
                className="preview-btn"
                title="Aperçu dans un nouvel onglet"
              >
                👁️ Aperçu
              </button>
              <button
                onClick={() => handleDownload(result)}
                className="download-btn"
                title="Télécharger le PDF"
              >
                📥 PDF
              </button>
            </div>

            <span className="status success" title="Généré avec succès">
              ✅
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default React.memo(Results);
