import React, { useState, useCallback } from 'react';
import './Login.css';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

const Login = ({ onLogin }) => {
  const [credentials, setCredentials] = useState({ login: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = useCallback((e) => {
    const { name, value } = e.target;
    setCredentials(prev => ({ ...prev, [name]: value }));
    setError('');
  }, []);

  const handleSubmit = useCallback(async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await fetch(`${API_BASE_URL}/api/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(credentials)
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || 'Identifiants invalides');
      }

      const data = await response.json().catch(() => null);
      if (!data?.token) {
        throw new Error('Réponse serveur invalide');
      }
      onLogin(data.token, data.user);
    } catch (err) {
      setError(err.message);
      console.error('Login error:', err);
    } finally {
      setLoading(false);
    }
  }, [credentials, onLogin]);

  return (
    <div className="login-container">
      <form onSubmit={handleSubmit} className="login-form" noValidate>
        <h2>Connexion Douanes CI</h2>
        <p className="subtitle">Système de génération de convocations</p>

        <div className="form-group">
          <label htmlFor="login">Identifiant</label>
          <input
            id="login"
            name="login"
            type="text"
            value={credentials.login}
            onChange={handleChange}
            required
            autoFocus
            autoComplete="username"
            placeholder="Votre identifiant"
          />
        </div>

        <div className="form-group">
          <label htmlFor="password">Mot de passe</label>
          <input
            id="password"
            name="password"
            type="password"
            value={credentials.password}
            onChange={handleChange}
            required
            autoComplete="current-password"
            placeholder="Votre mot de passe"
          />
        </div>

        {error && <div className="error-message" role="alert">{error}</div>}

        <button
          type="submit"
          disabled={loading || !credentials.login || !credentials.password}
          className="login-btn"
        >
          {loading ? 'Connexion...' : 'Se connecter'}
        </button>

        <div className="login-hint">
          Admin: <strong>admin</strong> / <strong>admin123</strong>
        </div>
      </form>
    </div>
  );
};

export default React.memo(Login);
