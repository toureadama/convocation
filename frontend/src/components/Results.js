import React from 'react';
import './Results.css';

const Results = ({ results }) => {
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

            <span className="status pending" title="Généré - En attente d'approbation">
              ⏳ En attente d'approbation
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default React.memo(Results);
