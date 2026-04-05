import React, { useState, useEffect } from 'react';
import './Form.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

const Form = ({ onGenerate, loading, progress = 0, currentUser }) => { // Added progress prop
  const [formData, setFormData] = useState({
    csv: 'CODE_AGREE.csv',
    cc: '',
    verificateur: currentUser ? `${currentUser.civilite || ''} ${currentUser.nom} ${currentUser.prenom}`.trim() : '',
    num_declaration: '',
    date_declaration: '',
    fraude: '',
    signature_admin: '',
  });
  const [companies, setCompanies] = useState([]);
  const [societeDisplay, setSocieteDisplay] = useState('');
  const [companiesLoading, setCompaniesLoading] = useState(true);

  const handleChange = (e) => {
    const value = e.target.value;
    setFormData({
      ...formData,
      [e.target.name]: value,
    });
    if (e.target.name === 'cc') {
      // Opt: Simple find, no debounce needed for small list
      const company = companies.find(c => c.cc === value);
      setSocieteDisplay(company ? company.societe : '');
    }
  };

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      setCompaniesLoading(false);
      return;
    }
    fetch(`${API_URL}/api/companies`, {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then(res => {
        if (!res.ok) throw new Error(`API error: ${res.status}`);
        return res.json();
      })
      .then(data => {
        if (data.companies) {
          setCompanies(data.companies);
        }
        setCompaniesLoading(false);
      })
      .catch(err => {
        console.error('Companies load error:', err);
        setCompaniesLoading(false);
      });
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    onGenerate(formData);
  };

  return (
    <form onSubmit={handleSubmit} className="form-container">
      <h2>Saisir Paramètres</h2>
      
      <div className="form-grid">
        <div className="form-group">
          <label htmlFor="cc">Code Agréé (CA) *</label>
          <input
            type="text"
            id="cc"
            name="cc"
            value={formData.cc}
            onChange={handleChange}
            list="cc-list"
            required
          />
          <datalist id="cc-list">
            {companies.map((company) => (
              <option key={company.cc} value={company.cc} />
            ))}
          </datalist>
          {companiesLoading && <small>Chargement codes agréés...</small>}
          {societeDisplay && <small>Société: {societeDisplay}</small>}
        </div>

        <div className="form-group">
          <label htmlFor="num_declaration">N° Déclaration *</label>
          <input
            id="num_declaration"
            name="num_declaration"
            value={formData.num_declaration}
            onChange={handleChange}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="date_declaration">Date Déclaration * (dd/mm/yyyy)</label>
          <input
            id="date_declaration"
            name="date_declaration"
            type="date"
            value={formData.date_declaration}
            onChange={handleChange}
            required
          />
        </div>

        <div className="form-group full">
          <label htmlFor="fraude">Type Fraude *</label>
          <select
            id="fraude"
            name="fraude"
            value={formData.fraude}
            onChange={handleChange}
            required
          >
            <option value="">Sélectionner fraude</option>
            <option value="FDE">FAUSSE DECLARATION ESPECES</option>
            <option value="FDV">FAUSSE DECLARATION VALEURS</option>
            <option value="EXC">EXCEDENT</option>
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="signature_admin">Signature Admin *</label>
          <select
            id="signature_admin"
            name="signature_admin"
            value={formData.signature_admin}
            onChange={handleChange}
            required
          >
            <option value="">Sélectionner admin</option>
            <option value="COULIBALY KARIM">COULIBALY KARIM</option>
            <option value="COULIBALY SITA">COULIBALY SITA</option>
          </select>
        </div>
      </div>

      {/* New Progress Bar */}
      {loading && (
        <div className="progress-section">
          <div className="progress-label">
            Génération en cours... {Math.round(progress)}%
          </div>
          <div className="progress-bar">
            <div 
              className="progress-fill" 
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}

      <button type="submit" disabled={loading || !formData.cc} className="generate-btn">
        {loading ? `Génration... ${Math.round(progress)}%` : 'Générer Convocation'}
      </button>
    </form>
  );
};

export default Form;

