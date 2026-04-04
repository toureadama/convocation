import React, { useState, useEffect } from 'react';
import Form from './components/Form';
import Results from './components/Results';
import History from './components/History';
import Users from './components/Users';
import Login from './components/Login';
import CodeAgre from './components/CodeAgre';
import './App.css';

const API_URL = process.env.REACT_APP_API_URL

function App() {
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [user, setUser] = useState(null);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [tab, setTab] = useState('generate');
  const [loginError, setLoginError] = useState('');

  useEffect(() => {
    if (token) {
      fetch('{API_URL}/api/verify', {
        headers: { Authorization: `Bearer ${token}` },
      }).then(async res => {
        if (!res.ok) {
          console.error('Verify failed:', res.status, await res.text());
          localStorage.removeItem('token');
          setToken(null);
        }
      }).catch(err => {
        console.error('Verify error:', err);
        localStorage.removeItem('token');
        setToken(null);
      });
    }
  }, [token]);

  const handleLogin = (newToken, userData) => {
    setToken(newToken);
    setUser(userData);
    localStorage.setItem('token', newToken);
    setLoginError('');
  };

  const handleLogout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('token');
  };

  const handleGenerate = async (formData) => {
    setLoading(true);
    setError('');
    setResults([]);

    try {
      const params = new URLSearchParams(formData);
      const response = await fetch('{API_URL}/api/generate', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/x-www-form-urlencoded',
          'Authorization': `Bearer ${token}`
        },
        body: params,
      });

      if (!response.ok) throw new Error(`Erreur: ${response.status}`);
      
      const data = await response.json();
      setResults(data.results || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (!token) {
    return <Login onLogin={handleLogin} error={loginError} />;
  }

  return (
    <div className="App">
      <header className="App-header">
        <h1>Générateur Convocations Douanes CI</h1>
        <div className="user-info">
          Bonjour, <strong>{user?.nom} {user?.prenom}</strong> ({user?.grade})
          <button onClick={handleLogout} className="logout-btn">Déconnexion</button>
        </div>
      </header>
      <main>
        <div className="tabs">
          <button 
            className={tab === 'generate' ? 'tab-active' : 'tab'}
            onClick={() => setTab('generate')}
          >
            Générer
          </button>
          <button 
            className={tab === 'history' ? 'tab-active' : 'tab'}
            onClick={() => setTab('history')}
          >
            Historique
          </button>
          {user?.grade === 'Administrateur' && (
            <>
              <button 
                className={tab === 'admin' ? 'tab-active' : 'tab'}
                onClick={() => setTab('admin')}
              >
                Admin Utilisateurs
              </button>
              <button 
                className={tab === 'code_agre' ? 'tab-active' : 'tab'}
                onClick={() => setTab('code_agre')}
              >
                Codes Agréés
              </button>
            </>
          )}
        </div>
        
        {tab === 'generate' && (
          <>
<Form onGenerate={handleGenerate} loading={loading} currentUser={user} />
            {error && <div className="error">{error}</div>}
            <Results results={results} />
          </>
        )}
        
{tab === 'history' && <History user={user} />}
        
{tab === 'admin' && <Users />}
        {tab === 'code_agre' && <CodeAgre />}
      </main>
    </div>
  );
}

export default App;

