import React, { useState, useEffect, useCallback } from 'react';
import { apiFetch } from '../api';
import './Form.css';

const FRAUDE_OPTIONS = [
  { value: 'FDE', label: 'FAUSSE DECLARATION ESPECES' },
  { value: 'FDV', label: 'FAUSSE DECLARATION VALEURS' },
  { value: 'ESP', label: 'ENLEVEMENT SANS PERMIS' },
  { value: 'EXC', label: 'EXCEDENT' }
];

const ADMIN_SIGNATURES = [
  'COULIBALY KARIM',
  'COULIBALY SITA'
];

const DOSSIER_TYPES = [
  { value: 'BDAP', label: 'BDAP' },
  { value: 'DARRV', label: 'DARRV' }
];

const Form = ({ onGenerate, loading, progress = 0, currentUser }) => {
  const [formData, setFormData] = useState({
    cc: '',
    code_imp: '',
    verificateur: '',
    num_declaration: '',
    date_declaration: '',
    type_dossier: '',
    objet: '',
    signature_admin: ''
  });

  const [companies, setCompanies] = useState([]);
  const [operateurs, setOperateurs] = useState([]);
  const [selectedCompany, setSelectedCompany] = useState('');
  const [selectedOperateur, setSelectedOperateur] = useState('');
  const [isLoadingCompanies, setIsLoadingCompanies] = useState(true);
  const [isLoadingOperateurs, setIsLoadingOperateurs] = useState(true);

  // Initialize verifier name from current user (nom + prenom only, no civilite)
  useEffect(() => {
    if (currentUser) {
      // Only use nom and prenom - civilité will be looked up from DB
      const fullName = [currentUser.nom, currentUser.prenom]
        .filter(Boolean)
        .join(' ');
      setFormData(prev => ({ ...prev, verificateur: fullName }));
    }
  }, [currentUser]);

  // Load companies list
  useEffect(() => {
    const loadCompanies = async () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) {
          setIsLoadingCompanies(false);
          return;
        }

        const response = await apiFetch('/api/companies');

        if (!response.ok) {
          throw new Error(`Erreur chargement codes agréés: ${response.status}`);
        }

        const data = await response.json();
        setCompanies(data.companies || []);
      } catch (err) {
        if (err.message === 'SESSION_EXPIRED') {
          window.location.reload();
          return;
        }
        console.error('Companies load error:', err);
      } finally {
        setIsLoadingCompanies(false);
      }
    };

    loadCompanies();
  }, []);

  // Load operateurs list
  useEffect(() => {
    const loadOperateurs = async () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) {
          setIsLoadingOperateurs(false);
          return;
        }

        const response = await apiFetch('/api/operateurs');

        if (!response.ok) {
          throw new Error(`Erreur chargement opérateurs: ${response.status}`);
        }

        const data = await response.json();
        setOperateurs(data.operateurs || []);
      } catch (err) {
        if (err.message === 'SESSION_EXPIRED') {
          window.location.reload();
          return;
        }
        console.error('Operateurs load error:', err);
      } finally {
        setIsLoadingOperateurs(false);
      }
    };

    loadOperateurs();
  }, []);

  const handleChange = useCallback((e) => {
    const { name, value } = e.target;

    setFormData(prev => ({ ...prev, [name]: value }));

    if (name === 'cc') {
      const company = companies.find(c => c.cc === value);
      setSelectedCompany(company ? company.societe : '');
    }
    
    if (name === 'code_imp') {
      const operateur = operateurs.find(o => o.code_operateur === value);
      setSelectedOperateur(operateur ? operateur.nom_operateur : '');
    }
  }, [companies, operateurs]);

  const handleSubmit = useCallback((e) => {
    e.preventDefault();
    onGenerate(formData);
  }, [formData, onGenerate]);

  const isFormValid = formData.cc && formData.code_imp && formData.verificateur &&
                      formData.num_declaration && formData.date_declaration &&
                      formData.type_dossier && formData.fraude && formData.signature_admin;

  return (
    <form onSubmit={handleSubmit} className="form-container">
      <h2>Paramètres de Convocation</h2>

      <div className="form-grid">
        <div className="form-group">
          <label htmlFor="cc">Code Déclarant *</label>
          <input
            type="text"
            id="cc"
            name="cc"
            value={formData.cc}
            onChange={handleChange}
            list="cc-list"
            required
            placeholder="Ex: 00069Z"
          />
          <datalist id="cc-list">
            {companies.map((company) => (
              <option key={company.cc} value={company.cc} />
            ))}
          </datalist>
          {isLoadingCompanies && <small className="loading-text">Chargement...</small>}
          {selectedCompany && <small className="info-text">{selectedCompany}</small>}
        </div>

        <div className="form-group">
          <label htmlFor="code_imp">Code Opérateur *</label>
          <input
            type="text"
            id="code_imp"
            name="code_imp"
            value={formData.code_imp}
            onChange={handleChange}
            list="code-imp-list"
            required
            placeholder="Ex: 1222798H"
          />
          <datalist id="code-imp-list">
            {operateurs.map((operateur) => (
              <option key={operateur.code_operateur} value={operateur.code_operateur} />
            ))}
          </datalist>
          {isLoadingOperateurs && <small className="loading-text">Chargement...</small>}
          {selectedOperateur && <small className="info-text">{selectedOperateur}</small>}
        </div>

        <div className="form-group">
          <label htmlFor="num_declaration">N° Déclaration *</label>
          <input
            id="num_declaration"
            name="num_declaration"
            value={formData.num_declaration}
            onChange={handleChange}
            required
            placeholder="Ex: CIAB6C2998"
          />
        </div>

        <div className="form-group">
          <label htmlFor="date_declaration">Date Déclaration *</label>
          <input
            id="date_declaration"
            name="date_declaration"
            type="date"
            value={formData.date_declaration}
            onChange={handleChange}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="type_dossier">Type de dossier *</label>
          <select
            id="type_dossier"
            name="type_dossier"
            value={formData.type_dossier}
            onChange={handleChange}
            required
          >
            <option value="">Sélectionner un type</option>
            {DOSSIER_TYPES.map(type => (
              <option key={type.value} value={type.value}>{type.label}</option>
            ))}
          </select>
        </div>

        <div className="form-group full-width">
          <label htmlFor="fraude">Objet *</label>
          <select
            id="fraude"
            name="fraude"
            value={formData.fraude}
            onChange={handleChange}
            required
          >
            <option value="">Sélectionner un type</option>
            {FRAUDE_OPTIONS.map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
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
            <option value="">Sélectionner un admin</option>
            {ADMIN_SIGNATURES.map(name => (
              <option key={name} value={name}>{name}</option>
            ))}
          </select>
        </div>
      </div>

      {loading && (
        <div className="progress-section">
          <div className="progress-label">
            Génération en cours... {Math.round(progress)}%
          </div>
          <div className="progress-bar">
            <div
              className="progress-fill"
              style={{ width: `${progress}%` }}
              role="progressbar"
              aria-valuenow={progress}
              aria-valuemin={0}
              aria-valuemax={100}
            />
          </div>
        </div>
      )}

      <button
        type="submit"
        disabled={loading || !isFormValid}
        className="generate-btn"
      >
        {loading ? `Génération... ${Math.round(progress)}%` : '🎯 Générer Convocation'}
      </button>
    </form>
  );
};

export default React.memo(Form);
