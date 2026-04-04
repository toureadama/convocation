import React, { useState } from 'react';
import './Login.css'; // À créer

const API_URL = process.env.REACT_APP_API_URL

const Login = ({ onLogin, error }) => {
  const [credentials, setCredentials] = useState({ login: '', password: '' });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await fetch('${API_URL}/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(credentials),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.error || 'Erreur login');
      }
      const data = await res.json();
      onLogin(data.token, data.user);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setCredentials({ ...credentials, [e.target.name]: e.target.value });
  };

  return (
    <div className="login-container">
      <form onSubmit={handleSubmit} className="login-form">
        <h2>Connexion Douanes CI</h2>
        
        <div className="form-group">
          <label>Identifiant</label>
          <input
            name="login"
            type="text"
            value={credentials.login}
            onChange={handleChange}
            required
            autoFocus
          />
        </div>
        
        <div className="form-group">
          <label>Mot de passe</label>
          <input
            name="password"
            type="password"
            value={credentials.password}
            onChange={handleChange}
            required
          />
        </div>
        
        <button type="submit" disabled={loading} className="login-btn">
          {loading ? 'Connexion...' : 'Se connecter'}
        </button>
        
        {error && <div className="error">{error}</div>}
        
        <div className="admin-note">
          Admin test: <strong>admin / admin123</strong>
        </div>
      </form>
    </div>
  );
};

export default Login;

