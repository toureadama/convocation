import React from 'react';
import './Results.css';

const Results = ({ results }) => {
  if (!results.length) return null;

  const BASE_URL = 'http://localhost:5000';
  const token = localStorage.getItem('token');

  const handlePreview = (result) => {
    window.open(`${BASE_URL}/output/${result.filename}`, '_blank');
  };

  const handleDownload = (result) => {
    const url = `${BASE_URL}/output/${result.filename}`;
    const link = document.createElement('a');
    link.href = url;
    link.download = result.filename;
    link.type = 'application/pdf';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };


  return (
    <div className="results-container">
      <h2>Résultats Génération</h2>
      <p>{results.length} fichier(s) PDF créé(s)</p>
      
      <div className="results-list">
        {results.map((result, index) => (
          <div key={index} className="result-item">
            <div className="file-info">
              <div className="file-name">{result.filename}</div>
            </div>
            <div className="result-actions">
              <button onClick={() => handlePreview(result)} className="preview-btn" title="Aperçu">
                👁️ Aperçu
              </button>
              <button onClick={() => handleDownload(result)} className="download-btn" title="Télécharger">
                📥 PDF
              </button>
            </div>
            <span className="status success">✅ OK</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Results;
