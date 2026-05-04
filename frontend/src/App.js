import React, { useState, useEffect, Suspense, lazy } from 'react';
import './App.css';
import { refreshToken, apiFetch, API_BASE_URL } from './api';
import ErrorBoundary from './components/ErrorBoundary';

// Lazy-loaded components for better initial load performance
const Form = lazy(() => import('./components/Form'));
const Results = lazy(() => import('./components/Results'));
const History = lazy(() => import('./components/History'));
const Users = lazy(() => import('./components/Users'));
const Login = lazy(() => import('./components/Login'));
const CodeAgre = lazy(() => import('./components/CodeAgre'));
const CodeOperateur = lazy(() => import('./components/CodeOperateur'));

const TABS = {
  GENERATE: 'generate',
  HISTORY: 'history',
  ADMIN: 'admin',
  CODE_AGRE: 'code_agre',
  CODE_OPERATEUR: 'code_operateur'
};

const ROLES = {
  VERIFICATEUR: 'Vérificateur',
  ADMINISTRATEUR: 'Administrateur',
  SUPER_ADMIN: 'Super Administrateur',
  ADMIN_TECHNIQUE: 'Administrateur Technique'
};

function App() {
  const [token, setToken] = useState(() => localStorage.getItem('token'));
  const [user, setUser] = useState(null);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState('');
  const [successfullySubmitted, setSuccessfullySubmitted] = useState(false);
  const [activeTab, setActiveTab] = useState(TABS.GENERATE);

  // Verify token validity on mount and auto-refresh if needed
  useEffect(() => {
    if (!token) return;

    const verifyAndRefresh = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/verify`, {
          headers: { Authorization: `Bearer ${token}` }
        });

        if (!response.ok) {
          // Token expired, try to refresh
          try {
            const newToken = await refreshToken();
            setToken(newToken);
          } catch {
            // Refresh failed, force login
            handleLogout();
          }
        }
      } catch (error) {
        console.error('Token verification failed:', error);
        // Try refresh as fallback
        try {
          const newToken = await refreshToken();
          setToken(newToken);
        } catch {
          handleLogout();
        }
      }
    };

    verifyAndRefresh();

    // Auto-refresh token every 10 minutes (before 15-min expiry)
    const refreshInterval = setInterval(async () => {
      try {
        const newToken = await refreshToken();
        setToken(newToken);
      } catch {
        handleLogout();
      }
    }, 10 * 60 * 1000);

    return () => clearInterval(refreshInterval);
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
    // Progressive simulation that reaches ~99% after ~90 seconds
    // (LibreOffice PDF conversion can take 30-120 seconds)
    setProgress(10);
    setTimeout(() => setProgress(25), 1000);
    setTimeout(() => setProgress(40), 3000);
    setTimeout(() => setProgress(55), 8000);
    setTimeout(() => setProgress(70), 15000);
    setTimeout(() => setProgress(80), 30000);
    setTimeout(() => setProgress(90), 60000);
    // Stop at 99% to avoid showing 100% before actual completion
  };

  const handleGenerate = async (formData) => {
    setLoading(true);
    setError('');
    setResults([]);
    setProgress(0);
    simulateProgress();

    try {
      const params = new URLSearchParams(formData);
      const response = await apiFetch('/api/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
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
      if (err.message === 'SESSION_EXPIRED') {
        window.location.reload();
        return;
      }
      setError(err.message || 'Erreur lors de la génération');
      setProgress(0);
    } finally {
      setLoading(false);
    }
  };

  const handleFormReset = () => {
    setSuccessfullySubmitted(false);
  };

  const handleSubmit = async (formData) => {
    setLoading(true);
    setError('');
    setSuccessfullySubmitted(false);

    try {
      const params = new URLSearchParams(formData);
      const response = await apiFetch('/api/submit', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: params
      });

      if (!response.ok) {
        throw new Error(`Erreur serveur: ${response.status}`);
      }

      const data = await response.json();
      alert(data.message || 'Convocation soumise pour approbation');
      setSuccessfullySubmitted(true);
    } catch (err) {
      if (err.message === 'SESSION_EXPIRED') {
        window.location.reload();
        return;
      }
      setError(err.message || 'Erreur lors de la soumission');
    } finally {
      setLoading(false);
    }
  };

  const userRole = user?.role || user?.grade;
  const isSuperAdmin = userRole === ROLES.SUPER_ADMIN;
  const isAdminTechnique = userRole === ROLES.ADMIN_TECHNIQUE;
  const isVerificateur = userRole === ROLES.VERIFICATEUR;
  const canManageUsers = isAdminTechnique;
  const canManageCodes = isAdminTechnique;
  const canGenerate = isVerificateur;
  const canViewAllHistory = isSuperAdmin || isAdminTechnique;

  // Login screen
  if (!token) {
    return (
      <Suspense fallback={<div className="loading">Chargement...</div>}>
        <Login onLogin={handleLogin} />
      </Suspense>
    );
  }

  return (
    <ErrorBoundary>
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
        {canGenerate && (
          <button
            className={activeTab === TABS.GENERATE ? 'tab-active' : 'tab'}
            onClick={() => setActiveTab(TABS.GENERATE)}
          >
            Générer
          </button>
        )}
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
        {canManageCodes && (
          <button
            className={activeTab === TABS.CODE_AGRE ? 'tab-active' : 'tab'}
            onClick={() => setActiveTab(TABS.CODE_AGRE)}
          >
            Codes Agréés
          </button>
        )}
        {canManageCodes && (
          <button
            className={activeTab === TABS.CODE_OPERATEUR ? 'tab-active' : 'tab'}
            onClick={() => setActiveTab(TABS.CODE_OPERATEUR)}
          >
            Codes Opérateurs
          </button>
        )}
      </nav>

      <main>
        <Suspense fallback={<div className="loading">Chargement...</div>}>
          {canGenerate && activeTab === TABS.GENERATE && (
            <>
               <Form
                 onGenerate={handleGenerate}
                 onSubmit={handleSubmit}
                 loading={loading}
                 progress={progress}
                 currentUser={user}
                 successfullyGenerated={results.length > 0}
                 successfullySubmitted={successfullySubmitted}
                 onFormReset={handleFormReset}
                 userRole={userRole}

              />
              {error && <div className="error">{error}</div>}
              <Results results={results} />
            </>
          )}

          {activeTab === TABS.HISTORY && <History user={user} canViewAll={canViewAllHistory} />}

          {canManageUsers && activeTab === TABS.ADMIN && <Users currentUserRole={userRole} />}
          {canManageCodes && activeTab === TABS.CODE_AGRE && <CodeAgre />}
          {canManageCodes && activeTab === TABS.CODE_OPERATEUR && <CodeOperateur />}
        </Suspense>
      </main>
      </div>
    </ErrorBoundary>
  );
}

export default App;
