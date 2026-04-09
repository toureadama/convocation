import React, { useState, useEffect, Suspense, lazy } from 'react';
import './App.css';

// Lazy-loaded components for better initial load performance
const Form = lazy(() => import('./components/Form'));
const Results = lazy(() => import('./components/Results'));
const History = lazy(() => import('./components/History'));
const Users = lazy(() => import('./components/Users'));
const Login = lazy(() => import('./components/Login'));
const CodeAgre = lazy(() => import('./components/CodeAgre'));

const TABS = {
  GENERATE: 'generate',
  HISTORY: 'history',
  ADMIN: 'admin',
  CODE_AGRE: 'code_agre'
};

const ROLES = {
  VERIFICATEUR: 'Vérificateur',
  ADMINISTRATEUR: 'Administrateur',
  SUPER_ADMIN: 'Super Administrateur'
};

function App() {
  const [token, setToken] = useState(() => localStorage.getItem('token'));
  const [user, setUser] = useState(null);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState(TABS.GENERATE);

  // Verify token validity on mount
  useEffect(() => {
    if (!token) return;

    const verifyToken = async () => {
      try {
        const response = await fetch('/api/verify', {
          headers: { Authorization: `Bearer ${token}` }
        });
        
        if (!response.ok) {
          handleLogout();
        }
      } catch (error) {
        console.error('Token verification failed:', error);
        handleLogout();
      }
    };

    verifyToken();
  }, [token]);

  const handleLogin = (newToken, userData) => {
    setToken(newToken);
    setUser(userData);
    localStorage.setItem('token', newToken);
  };

  const handleLogout = () => {
    setToken(null);
    setUser(null);
    setResults([]);
    setError('');
    localStorage.removeItem('token');
  };

  const simulateProgress = () => {
    setProgress(10);
    setTimeout(() => setProgress(40), 800);
    setTimeout(() => setProgress(70), 2000);
    setTimeout(() => setProgress(100), 3500);
  };

  const handleGenerate = async (formData) => {
    setLoading(true);
    setError('');
    setResults([]);
    setProgress(0);
    simulateProgress();

    try {
      const params = new URLSearchParams(formData);
      const response = await fetch('/api/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'Authorization': `Bearer ${token}`
        },
        body: params
      });

      if (!response.ok) {
        throw new Error(`Erreur serveur: ${response.status}`);
      }

      const data = await response.json();
      setResults(data.results || []);
      setProgress(100);
    } catch (err) {
      setError(err.message || 'Erreur lors de la génération');
      setProgress(0);
    } finally {
      setLoading(false);
    }
  };

  const userRole = user?.role || user?.grade;
  const isAdmin = userRole === ROLES.ADMINISTRATEUR;
  const isSuperAdmin = userRole === ROLES.SUPER_ADMIN;
  const canManageUsers = isAdmin || isSuperAdmin;
  const canViewAllHistory = isSuperAdmin;

  // Login screen
  if (!token) {
    return (
      <Suspense fallback={<div className="loading">Chargement...</div>}>
        <Login onLogin={handleLogin} />
      </Suspense>
    );
  }

  return (
    <div className="App">
      <header className="App-header">
        <h1>Générateur Convocations Douanes CI</h1>
        <div className="user-info">
          <span>
            Bonjour, <strong>{user?.nom} {user?.prenom}</strong> ({userRole})
          </span>
          <button onClick={handleLogout} className="logout-btn">
            Déconnexion
          </button>
        </div>
      </header>

      <nav className="tabs">
        <button
          className={activeTab === TABS.GENERATE ? 'tab-active' : 'tab'}
          onClick={() => setActiveTab(TABS.GENERATE)}
        >
          Générer
        </button>
        <button
          className={activeTab === TABS.HISTORY ? 'tab-active' : 'tab'}
          onClick={() => setActiveTab(TABS.HISTORY)}
        >
          Historique
        </button>
        {canManageUsers && (
          <button
            className={activeTab === TABS.ADMIN ? 'tab-active' : 'tab'}
            onClick={() => setActiveTab(TABS.ADMIN)}
          >
            Admin Utilisateurs
          </button>
        )}
        {canManageUsers && (
          <button
            className={activeTab === TABS.CODE_AGRE ? 'tab-active' : 'tab'}
            onClick={() => setActiveTab(TABS.CODE_AGRE)}
          >
            Codes Agréés
          </button>
        )}
      </nav>

      <main>
        <Suspense fallback={<div className="loading">Chargement...</div>}>
          {activeTab === TABS.GENERATE && (
            <>
              <Form
                onGenerate={handleGenerate}
                loading={loading}
                progress={progress}
                currentUser={user}
              />
              {error && <div className="error">{error}</div>}
              <Results results={results} />
            </>
          )}

          {activeTab === TABS.HISTORY && <History user={user} canViewAll={canViewAllHistory} />}
          
          {canManageUsers && activeTab === TABS.ADMIN && <Users currentUserRole={userRole} />}
          {canManageUsers && activeTab === TABS.CODE_AGRE && <CodeAgre />}
        </Suspense>
      </main>
    </div>
  );
}

export default App;
