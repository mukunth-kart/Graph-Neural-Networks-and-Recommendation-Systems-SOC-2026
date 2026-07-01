import React, { useState, useEffect, useRef } from 'react';
import { 
  Search, Sparkles, Star, User, Lock, Shield, LogOut, 
  RefreshCw, AlertTriangle, CheckCircle2, UserX, UserCheck, 
  Play, Mail, Phone, Film, ListFilter, Trash2 
} from 'lucide-react';

const API_BASE = ''; // proxied via vite to http://localhost:8000

export default function App() {
  // Authentication states
  const [token, setToken] = useState(localStorage.getItem('token') || '');
  const [user, setUser] = useState(null);
  
  // App views: 'login' | 'register' | 'onboarding' | 'dashboard' | 'admin'
  const [view, setView] = useState('login');
  
  // Movie catalog & search states
  const [movies, setMovies] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedGenre, setSelectedGenre] = useState('');
  const [moviePage, setMoviePage] = useState(0);
  const [hasMoreMovies, setHasMoreMovies] = useState(true);
  
  // User recommendation & ratings states
  const [recommendations, setRecommendations] = useState([]);
  const [myRatings, setMyRatings] = useState([]);
  const [seedMovies, setSeedMovies] = useState([]); // Selected during onboarding
  const [ratingLoading, setRatingLoading] = useState({}); // Movie ID -> bool
  
  // Admin dashboard states
  const [adminTab, setAdminTab] = useState('outliers'); // 'outliers' | 'retrain'
  const [usersList, setUsersList] = useState([]);
  const [outliers, setOutliers] = useState([]);
  const [trainingLogs, setTrainingLogs] = useState([]);
  const [trainingActive, setTrainingActive] = useState(false);
  const [adminStats, setAdminStats] = useState({ totalUsers: 0, totalOutliers: 0, totalBanned: 0 });
  const [toast, setToast] = useState(null);

  // Sync token and load user metadata on start
  useEffect(() => {
    if (token) {
      localStorage.setItem('token', token);
      fetchUserProfile();
    } else {
      localStorage.removeItem('token');
      setUser(null);
      setView('login');
    }
  }, [token]);

  // Set up views depending on role & ratings count
  useEffect(() => {
    if (user) {
      if (user.role === 'admin') {
        setView('admin');
      } else {
        fetchMyRatings();
      }
    }
  }, [user]);

  // Toast auto-clear
  useEffect(() => {
    if (toast) {
      const timer = setTimeout(() => setToast(null), 4000);
      return () => clearTimeout(timer);
    }
  }, [toast]);

  // Retrain log polling
  useEffect(() => {
    let interval;
    if (view === 'admin' && adminTab === 'retrain' && token) {
      fetchTrainingLogs();
      interval = setInterval(() => {
        fetchTrainingLogs();
      }, 3000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [view, adminTab, token]);

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
  };

  const fetchUserProfile = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/auth/me`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setUser(data);
      } else {
        setToken('');
      }
    } catch (err) {
      console.error(err);
      setToken('');
    }
  };

  const fetchMyRatings = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/ratings/my-ratings`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const ratings = await res.json();
        setMyRatings(ratings);
        
        // If user has rated 0 movies, show onboarding
        if (ratings.length === 0) {
          setView('onboarding');
          fetchMovies(true);
        } else {
          setView('dashboard');
          fetchRecommendations(ratings.map(r => r.movie_id));
          fetchMovies(true);
        }
      }
    } catch (err) {
      console.error(err);
    }
  };

  const fetchMovies = async (reset = false) => {
    const pageToLoad = reset ? 0 : moviePage;
    try {
      const query = searchQuery ? `&q=${encodeURIComponent(searchQuery)}` : '';
      const genre = selectedGenre ? `&genre=${encodeURIComponent(selectedGenre)}` : '';
      const offset = pageToLoad * 24;
      const res = await fetch(`${API_BASE}/api/movies?limit=24&offset=${offset}${query}${genre}`);
      if (res.ok) {
        const data = await res.json();
        if (reset) {
          setMovies(data);
          setMoviePage(1);
        } else {
          setMovies(prev => [...prev, ...data]);
          setMoviePage(prev => prev + 1);
        }
        setHasMoreMovies(data.length === 24);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const fetchRecommendations = async (seedIds = []) => {
    try {
      const res = await fetch(`${API_BASE}/api/movies/recommend`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ seed_movie_ids: seedIds })
      });
      if (res.ok) {
        const data = await res.json();
        setRecommendations(data);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const submitRating = async (movieId, rating) => {
    setRatingLoading(prev => ({ ...prev, [movieId]: true }));
    try {
      const res = await fetch(`${API_BASE}/api/ratings`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ movie_id: movieId, rating })
      });
      if (res.ok) {
        showToast("Rating saved!");
        // Refresh ratings
        const ratingsRes = await fetch(`${API_BASE}/api/ratings/my-ratings`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (ratingsRes.ok) {
          const ratings = await ratingsRes.json();
          setMyRatings(ratings);
          // Refresh recommendations using updated ratings
          fetchRecommendations(ratings.map(r => r.movie_id));
        }
      } else {
        const errData = await res.json();
        showToast(errData.detail || "Error saving rating", "error");
      }
    } catch (err) {
      showToast("Network error saving rating", "error");
    } finally {
      setRatingLoading(prev => ({ ...prev, [movieId]: false }));
    }
  };

  // Onboarding action: complete onboarding
  const handleOnboardingSubmit = async () => {
    if (seedMovies.length < 5) {
      showToast("Please select at least 5 movies to proceed.", "error");
      return;
    }
    
    // Save onboarding preferences to DB as 5.0 ratings
    for (const movieId of seedMovies) {
      await fetch(`${API_BASE}/api/ratings`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ movie_id: movieId, rating: 5.0 })
      });
    }
    
    showToast("Interests saved! Fetching GraphSAGE recommendations...");
    
    // Transition to dashboard and get recommendations
    const ratingsRes = await fetch(`${API_BASE}/api/ratings/my-ratings`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (ratingsRes.ok) {
      const ratings = await ratingsRes.json();
      setMyRatings(ratings);
      fetchRecommendations(ratings.map(r => r.movie_id));
    }
    
    setView('dashboard');
  };

  // ADMIN ACTIONS
  const fetchOutliers = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/admin/outliers`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setOutliers(data);
        
        // Compute summary metrics
        const total = data.length;
        const flagged = data.filter(u => u.anomaly_score > 30).length;
        const banned = data.filter(u => u.status === 'banned').length;
        setAdminStats({ totalUsers: total, totalOutliers: flagged, totalBanned: banned });
      }
    } catch (err) {
      console.error(err);
    }
  };

  const toggleBanUser = async (userId, currentStatus) => {
    const nextStatus = currentStatus === 'active' ? 'banned' : 'active';
    try {
      const res = await fetch(`${API_BASE}/api/admin/users/${userId}/status`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ status: nextStatus })
      });
      if (res.ok) {
        showToast(`User successfully ${nextStatus === 'banned' ? 'banned' : 'unbanned'}.`);
        fetchOutliers();
      } else {
        const data = await res.json();
        showToast(data.detail || "Action failed", "error");
      }
    } catch (err) {
      showToast("Error updating user status", "error");
    }
  };

  const fetchTrainingLogs = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/admin/training-status`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const logs = await res.json();
        setTrainingLogs(logs);
        const isRunning = logs.length > 0 && logs[0].status === 'running';
        setTrainingActive(isRunning);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const triggerModelRetrain = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/admin/train`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        showToast("Model retraining queued in background thread!");
        setTrainingActive(true);
        fetchTrainingLogs();
      } else {
        const err = await res.json();
        showToast(err.detail || "Failed to trigger training", "error");
      }
    } catch (err) {
      showToast("Error triggering model training", "error");
    }
  };

  // Auth Submit Handlers
  const [loginUsername, setLoginUsername] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  
  const [regUsername, setRegUsername] = useState('');
  const [regEmail, setRegEmail] = useState('');
  const [regPhone, setRegPhone] = useState('');
  const [regPassword, setRegPassword] = useState('');
  
  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const params = new URLSearchParams();
      params.append('username', loginUsername);
      params.append('password', loginPassword);
      
      const res = await fetch(`${API_BASE}/api/auth/token`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: params
      });
      
      if (res.ok) {
        const data = await res.json();
        setToken(data.access_token);
        showToast("Login successful!");
      } else {
        const errData = await res.json();
        showToast(errData.detail || "Authentication failed", "error");
      }
    } catch (err) {
      showToast("Network error. Is backend running?", "error");
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch(`${API_BASE}/api/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: regUsername,
          email: regEmail,
          phone: regPhone,
          password: regPassword
        })
      });
      
      if (res.ok) {
        showToast("Account created successfully! Please log in.");
        setView('login');
        setLoginUsername(regUsername);
        // Clear registration
        setRegUsername('');
        setRegEmail('');
        setRegPhone('');
        setRegPassword('');
      } else {
        const errData = await res.json();
        showToast(errData.detail || "Registration failed", "error");
      }
    } catch (err) {
      showToast("Network error registering user", "error");
    }
  };

  const handleLogout = () => {
    setToken('');
    setUser(null);
    setMyRatings([]);
    setRecommendations([]);
    setSeedMovies([]);
    setView('login');
    showToast("Logged out successfully.");
  };

  // Genre Options helper
  const genresList = [
    "Action", "Adventure", "Animation", "Children's", "Comedy", "Crime", 
    "Documentary", "Drama", "Fantasy", "Film-Noir", "Horror", "Musical", 
    "Mystery", "Romance", "Sci-Fi", "Thriller", "War", "Western"
  ];

  // Helper: toggle seed selection
  const handleToggleSeed = (movieId) => {
    setSeedMovies(prev => {
      if (prev.includes(movieId)) {
        return prev.filter(id => id !== movieId);
      } else {
        return [...prev, movieId];
      }
    });
  };

  // Helper: check if movie is liked
  const getMovieUserRating = (movieId) => {
    const found = myRatings.find(r => r.movie_id === movieId);
    return found ? found.rating : 0;
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      
      {/* Toast Alert */}
      {toast && (
        <div style={{
          position: 'fixed',
          bottom: '24px',
          right: '24px',
          padding: '16px 24px',
          borderRadius: '12px',
          backgroundColor: toast.type === 'error' ? 'var(--accent-danger)' : 'var(--accent-success)',
          color: '#fff',
          boxShadow: 'var(--shadow-lg)',
          zIndex: 1000,
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          animation: 'fadeIn var(--transition-fast) forwards',
          fontFamily: 'var(--font-display)',
          fontWeight: 600
        }}>
          {toast.type === 'error' ? <AlertTriangle size={20} /> : <CheckCircle2 size={20} />}
          {toast.message}
        </div>
      )}

      {/* Navigation Header */}
      {user && (
        <header className="navbar">
          <div className="nav-brand">
            <Film size={26} style={{ color: 'var(--accent-secondary)' }} />
            <span>GNN Recommender</span>
          </div>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <span style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <User size={16} /> {user.username} 
              <span style={{
                fontSize: '0.75rem',
                padding: '2px 8px',
                borderRadius: '12px',
                background: user.role === 'admin' ? 'rgba(99,102,241,0.2)' : 'rgba(255,255,255,0.06)',
                color: user.role === 'admin' ? '#818cf8' : 'var(--text-secondary)',
                border: '1px solid ' + (user.role === 'admin' ? '#4f46e5' : 'var(--border-color)')
              }}>
                {user.role}
              </span>
            </span>

            {user.role === 'admin' && (
              <button 
                onClick={() => {
                  if (view === 'admin') {
                    // Preview recommendation engine
                    fetchMyRatings();
                  } else {
                    setView('admin');
                    fetchOutliers();
                  }
                }}
                className="btn btn-secondary"
                style={{ padding: '8px 16px', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '8px' }}
              >
                <Shield size={14} />
                {view === 'admin' ? "Recommendation View" : "Admin Panel"}
              </button>
            )}

            <button 
              onClick={handleLogout}
              className="btn btn-secondary"
              style={{ padding: '8px 16px', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '8px', color: '#fca5a5' }}
            >
              <LogOut size={14} />
              Logout
            </button>
          </div>
        </header>
      )}

      {/* Main Content Area */}
      <main style={{ flex: 1, padding: user ? '40px' : '0px', display: 'flex', flexDirection: 'column' }}>
        
        {/* LOGIN SCREEN */}
        {view === 'login' && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flex: 1,
            padding: '20px',
            minHeight: '100vh',
            background: 'radial-gradient(circle at center, #1e1e38 0%, #0a0b10 100%)'
          }}>
            <div className="glass-panel" style={{
              width: '100%',
              maxWidth: '420px',
              padding: '40px',
              animation: 'fadeIn var(--transition-normal) forwards'
            }}>
              <div style={{ textAlign: 'center', marginBottom: '32px' }}>
                <div style={{
                  width: '64px',
                  height: '64px',
                  borderRadius: '16px',
                  background: 'linear-gradient(135deg, var(--accent-primary) 0%, var(--accent-secondary) 100%)',
                  display: 'inline-flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginBottom: '16px',
                  boxShadow: '0 8px 24px rgba(99, 102, 241, 0.4)'
                }}>
                  <Film size={32} color="#fff" />
                </div>
                <h2 style={{ fontSize: '2rem', marginBottom: '8px' }}>Sign In</h2>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Welcome to GNN Recommendations</p>
              </div>

              <form onSubmit={handleLogin}>
                <div className="form-group">
                  <label className="form-label">Username</label>
                  <div style={{ position: 'relative' }}>
                    <User size={18} style={{ position: 'absolute', left: '16px', top: '15px', color: 'var(--text-muted)' }} />
                    <input 
                      type="text" 
                      required
                      placeholder="Enter username" 
                      className="form-input" 
                      style={{ paddingLeft: '48px' }}
                      value={loginUsername}
                      onChange={(e) => setLoginUsername(e.target.value)}
                    />
                  </div>
                </div>

                <div className="form-group" style={{ marginBottom: '30px' }}>
                  <label className="form-label">Password</label>
                  <div style={{ position: 'relative' }}>
                    <Lock size={18} style={{ position: 'absolute', left: '16px', top: '15px', color: 'var(--text-muted)' }} />
                    <input 
                      type="password" 
                      required
                      placeholder="••••••••" 
                      className="form-input" 
                      style={{ paddingLeft: '48px' }}
                      value={loginPassword}
                      onChange={(e) => setLoginPassword(e.target.value)}
                    />
                  </div>
                </div>

                <button type="submit" className="btn btn-primary" style={{ width: '100%', padding: '14px', marginBottom: '24px' }}>
                  Authenticate Account
                </button>
              </form>

              <div style={{ textAlign: 'center', fontSize: '0.85rem' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Don't have an account? </span>
                <button 
                  onClick={() => setView('register')} 
                  style={{ background: 'none', border: 'none', color: 'var(--accent-secondary)', fontWeight: 600, cursor: 'pointer', outline: 'none' }}
                >
                  Create One Now
                </button>
              </div>
            </div>
          </div>
        )}

        {/* REGISTER SCREEN */}
        {view === 'register' && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flex: 1,
            padding: '20px',
            minHeight: '100vh',
            background: 'radial-gradient(circle at center, #1e1e38 0%, #0a0b10 100%)'
          }}>
            <div className="glass-panel" style={{
              width: '100%',
              maxWidth: '460px',
              padding: '40px',
              animation: 'fadeIn var(--transition-normal) forwards'
            }}>
              <div style={{ textAlign: 'center', marginBottom: '28px' }}>
                <h2 style={{ fontSize: '1.8rem', marginBottom: '8px' }}>Register Account</h2>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Join to receive custom GNN recommendations</p>
              </div>

              <form onSubmit={handleRegister}>
                <div className="form-group">
                  <label className="form-label">Username</label>
                  <div style={{ position: 'relative' }}>
                    <User size={16} style={{ position: 'absolute', left: '16px', top: '14px', color: 'var(--text-muted)' }} />
                    <input 
                      type="text" 
                      required
                      placeholder="Choose a username" 
                      className="form-input" 
                      style={{ paddingLeft: '44px', padding: '10px 16px 10px 44px' }}
                      value={regUsername}
                      onChange={(e) => setRegUsername(e.target.value)}
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label className="form-label">Email Address</label>
                  <div style={{ position: 'relative' }}>
                    <Mail size={16} style={{ position: 'absolute', left: '16px', top: '14px', color: 'var(--text-muted)' }} />
                    <input 
                      type="email" 
                      required
                      placeholder="you@example.com" 
                      className="form-input" 
                      style={{ paddingLeft: '44px', padding: '10px 16px 10px 44px' }}
                      value={regEmail}
                      onChange={(e) => setRegEmail(e.target.value)}
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label className="form-label">Mobile Number</label>
                  <div style={{ position: 'relative' }}>
                    <Phone size={16} style={{ position: 'absolute', left: '16px', top: '14px', color: 'var(--text-muted)' }} />
                    <input 
                      type="tel" 
                      required
                      placeholder="+1 (555) 000-0000" 
                      className="form-input" 
                      style={{ paddingLeft: '44px', padding: '10px 16px 10px 44px' }}
                      value={regPhone}
                      onChange={(e) => setRegPhone(e.target.value)}
                    />
                  </div>
                </div>

                <div className="form-group" style={{ marginBottom: '24px' }}>
                  <label className="form-label">Password</label>
                  <div style={{ position: 'relative' }}>
                    <Lock size={16} style={{ position: 'absolute', left: '16px', top: '14px', color: 'var(--text-muted)' }} />
                    <input 
                      type="password" 
                      required
                      placeholder="••••••••" 
                      className="form-input" 
                      style={{ paddingLeft: '44px', padding: '10px 16px 10px 44px' }}
                      value={regPassword}
                      onChange={(e) => setRegPassword(e.target.value)}
                    />
                  </div>
                </div>

                <button type="submit" className="btn btn-primary" style={{ width: '100%', padding: '12px', marginBottom: '20px' }}>
                  Create Account
                </button>
              </form>

              <div style={{ textAlign: 'center', fontSize: '0.85rem' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Already have an account? </span>
                <button 
                  onClick={() => setView('login')} 
                  style={{ background: 'none', border: 'none', color: 'var(--accent-secondary)', fontWeight: 600, cursor: 'pointer', outline: 'none' }}
                >
                  Sign In
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ONBOARDING USER PROFILE SELECTOR */}
        {view === 'onboarding' && (
          <div style={{ display: 'flex', flexDirection: 'column', flex: 1, animation: 'fadeIn var(--transition-normal) forwards' }}>
            <div style={{ maxWidth: '800px', margin: '0 auto 40px auto', textAlign: 'center' }}>
              <div style={{ display: 'inline-flex', padding: '12px', borderRadius: '50%', background: 'rgba(99,102,241,0.1)', color: 'var(--accent-primary)', marginBottom: '16px' }}>
                <Sparkles size={36} />
              </div>
              <h1 style={{ fontSize: '2.5rem', marginBottom: '16px', fontFamily: 'var(--font-display)' }}>Personalize Your Recommendations</h1>
              <p style={{ color: 'var(--text-secondary)', fontSize: '1.1rem', lineHeight: '1.6' }}>
                Welcome! Since this is your first time logging in, please select at least <strong>5 movies</strong> that you enjoy. 
                Our GraphSAGE GNN model will map your interest profile in real time to recommend matches.
              </p>
              
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '16px', marginTop: '24px' }}>
                <div style={{ fontSize: '1rem', color: '#fff', background: 'rgba(255,255,255,0.04)', border: '1px solid var(--border-color)', padding: '10px 20px', borderRadius: '30px' }}>
                  Selected: <strong>{seedMovies.length}</strong> / 5 movies
                </div>
                <button 
                  onClick={handleOnboardingSubmit}
                  disabled={seedMovies.length < 5}
                  className="btn btn-primary"
                  style={{ padding: '12px 28px', opacity: seedMovies.length < 5 ? 0.5 : 1, cursor: seedMovies.length < 5 ? 'not-allowed' : 'pointer' }}
                >
                  Generate My Recommendations
                </button>
              </div>
            </div>

            {/* Catalog Selector */}
            <div className="glass-panel" style={{ padding: '32px', flex: 1 }}>
              <div style={{ display: 'flex', gap: '16px', marginBottom: '24px', flexWrap: 'wrap' }}>
                <div style={{ position: 'relative', flex: 1, minWidth: '260px' }}>
                  <Search size={18} style={{ position: 'absolute', left: '16px', top: '13px', color: 'var(--text-muted)' }} />
                  <input 
                    type="text" 
                    placeholder="Search movies..." 
                    className="form-input" 
                    style={{ paddingLeft: '48px' }}
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyDown={(e) => { if (e.key === 'Enter') fetchMovies(true); }}
                  />
                </div>
                <div style={{ position: 'relative', width: '200px' }}>
                  <ListFilter size={18} style={{ position: 'absolute', left: '16px', top: '13px', color: 'var(--text-muted)' }} />
                  <select 
                    className="form-input" 
                    style={{ paddingLeft: '44px', appearance: 'none', background: 'rgba(255,255,255,0.03)' }}
                    value={selectedGenre}
                    onChange={(e) => setSelectedGenre(e.target.value)}
                  >
                    <option value="" style={{ background: 'var(--bg-secondary)' }}>All Genres</option>
                    {genresList.map(g => (
                      <option key={g} value={g} style={{ background: 'var(--bg-secondary)' }}>{g}</option>
                    ))}
                  </select>
                </div>
                <button className="btn btn-secondary" onClick={() => fetchMovies(true)}>
                  Search
                </button>
              </div>

              <div className="grid-container">
                {movies.map(movie => {
                  const isSelected = seedMovies.includes(movie.id);
                  return (
                    <div 
                      key={movie.id} 
                      onClick={() => handleToggleSeed(movie.id)}
                      className="glass-card" 
                      style={{ 
                        padding: '20px', 
                        cursor: 'pointer',
                        borderColor: isSelected ? 'var(--accent-secondary)' : 'var(--border-color)',
                        background: isSelected ? 'rgba(6, 182, 212, 0.08)' : 'var(--bg-glass-card)',
                        boxShadow: isSelected ? '0 0 15px rgba(6, 182, 212, 0.2)' : 'none',
                        display: 'flex',
                        flexDirection: 'column',
                        justifyContent: 'space-between',
                        height: '140px'
                      }}
                    >
                      <div>
                        <h4 style={{ fontSize: '1rem', color: '#fff', marginBottom: '6px', overflow: 'hidden', textOverflow: 'ellipsis', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' }}>
                          {movie.title}
                        </h4>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginTop: '4px' }}>
                          {movie.genres && movie.genres.split(',').slice(0, 2).map(g => (
                            <span key={g} style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', background: 'rgba(255,255,255,0.04)', padding: '2px 6px', borderRadius: '4px' }}>
                              {g}
                            </span>
                          ))}
                        </div>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{movie.release_year}</span>
                        <div style={{
                          width: '20px',
                          height: '20px',
                          borderRadius: '50%',
                          border: '2px solid ' + (isSelected ? 'var(--accent-secondary)' : 'var(--text-muted)'),
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          background: isSelected ? 'var(--accent-secondary)' : 'transparent',
                          color: '#000',
                          fontSize: '0.65rem',
                          fontWeight: 'bold'
                        }}>
                          {isSelected ? "✓" : ""}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>

              {hasMoreMovies && (
                <div style={{ textAlign: 'center', marginTop: '30px' }}>
                  <button className="btn btn-secondary" onClick={() => fetchMovies(false)}>
                    Load More Options
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        {/* USER RECOMMENDATIONS DASHBOARD */}
        {view === 'dashboard' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '40px', animation: 'fadeIn var(--transition-normal) forwards' }}>
            
            {/* Header Metrics */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
              <div>
                <h1 style={{ fontSize: '2.2rem', display: 'flex', alignItems: 'center', gap: '12px' }}>
                  Welcome back, {user.username} <Sparkles style={{ color: 'var(--accent-secondary)' }} />
                </h1>
                <p style={{ color: 'var(--text-secondary)' }}>Dynamically computed embeddings recommending matched movies.</p>
              </div>
              
              <div style={{ display: 'flex', gap: '16px' }}>
                <div className="glass-panel" style={{ padding: '16px 24px', display: 'flex', alignItems: 'center', gap: '16px' }}>
                  <Film size={24} style={{ color: 'var(--accent-primary)' }} />
                  <div>
                    <div style={{ fontSize: '1.2rem', fontWeight: 'bold' }}>{myRatings.length}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>Movies Rated</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Recommendations Grid */}
            <div className="glass-panel" style={{ padding: '32px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', flexWrap: 'wrap', gap: '12px' }}>
                <h2 style={{ fontSize: '1.5rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Sparkles size={20} style={{ color: 'var(--accent-secondary)' }} />
                  GraphSAGE Recommended For You
                </h2>
                <button 
                  className="btn btn-secondary" 
                  style={{ padding: '8px 16px', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '8px' }}
                  onClick={() => fetchRecommendations(myRatings.map(r => r.movie_id))}
                >
                  <RefreshCw size={12} /> Refresh Engine
                </button>
              </div>

              {recommendations.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '40px 0', color: 'var(--text-secondary)' }}>
                  <Film size={48} style={{ opacity: 0.3, marginBottom: '16px' }} />
                  <p>Calculating node representations... Choose more seed movies below to feed recommendations.</p>
                </div>
              ) : (
                <div className="grid-container">
                  {recommendations.map(movie => {
                    const similarityPct = Math.round(movie.similarity_score * 100);
                    return (
                      <div key={movie.id} className="glass-card" style={{ padding: '20px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', minHeight: '220px' }}>
                        <div>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '8px', marginBottom: '8px' }}>
                            <span style={{ 
                              fontSize: '0.7rem', 
                              fontWeight: 'bold', 
                              padding: '2px 8px', 
                              borderRadius: '12px',
                              background: 'rgba(6,182,212,0.1)', 
                              color: 'var(--accent-secondary)',
                              border: '1px solid rgba(6,182,212,0.2)'
                            }}>
                              {similarityPct}% Match
                            </span>
                            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{movie.release_year}</span>
                          </div>
                          
                          <h4 style={{ fontSize: '1.1rem', color: '#fff', marginBottom: '8px', overflow: 'hidden', textOverflow: 'ellipsis', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' }}>
                            {movie.title}
                          </h4>
                          
                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                            {movie.genres && movie.genres.split(',').slice(0, 3).map(g => (
                              <span key={g} style={{ fontSize: '0.65rem', color: 'var(--text-secondary)', background: 'rgba(255,255,255,0.04)', padding: '2px 6px', borderRadius: '4px' }}>
                                {g}
                              </span>
                            ))}
                          </div>
                        </div>

                        {/* Star feedback selection */}
                        <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '12px', marginTop: '12px' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Provide Feedback:</span>
                            {ratingLoading[movie.id] ? (
                              <RefreshCw size={14} className="animate-spin" style={{ color: 'var(--accent-primary)' }} />
                            ) : (
                              <div className="star-rating">
                                {[5, 4, 3, 2, 1].map(star => (
                                  <React.Fragment key={star}>
                                    <input 
                                      type="radio" 
                                      id={`star-${movie.id}-${star}`} 
                                      name={`rating-${movie.id}`} 
                                      value={star} 
                                      checked={getMovieUserRating(movie.id) === star}
                                      onChange={() => submitRating(movie.id, star)}
                                    />
                                    <label htmlFor={`star-${movie.id}-${star}`}>
                                      <Star size={16} fill={getMovieUserRating(movie.id) >= star ? 'var(--accent-warning)' : 'none'} />
                                    </label>
                                  </React.Fragment>
                                ))}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Split layout: Search & Rate Catalog vs My Ratings */}
            <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 0.8fr', gap: '40px', alignItems: 'start' }}>
              
              {/* Catalog Rate Panel */}
              <div className="glass-panel" style={{ padding: '32px' }}>
                <h3 style={{ fontSize: '1.3rem', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <ListFilter size={18} style={{ color: 'var(--accent-primary)' }} /> Browse and Rate Movies
                </h3>

                <div style={{ display: 'flex', gap: '12px', marginBottom: '20px', flexWrap: 'wrap' }}>
                  <div style={{ position: 'relative', flex: 1, minWidth: '200px' }}>
                    <Search size={16} style={{ position: 'absolute', left: '16px', top: '11px', color: 'var(--text-muted)' }} />
                    <input 
                      type="text" 
                      placeholder="Search title..." 
                      className="form-input" 
                      style={{ paddingLeft: '44px', padding: '8px 16px 8px 44px', fontSize: '0.85rem' }}
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      onKeyDown={(e) => { if (e.key === 'Enter') fetchMovies(true); }}
                    />
                  </div>
                  <div style={{ position: 'relative', width: '150px' }}>
                    <select 
                      className="form-input" 
                      style={{ padding: '8px 16px', fontSize: '0.85rem', appearance: 'none', background: 'rgba(255,255,255,0.03)' }}
                      value={selectedGenre}
                      onChange={(e) => { setSelectedGenre(e.target.value); }}
                    >
                      <option value="" style={{ background: 'var(--bg-secondary)' }}>All Genres</option>
                      {genresList.map(g => (
                        <option key={g} value={g} style={{ background: 'var(--bg-secondary)' }}>{g}</option>
                      ))}
                    </select>
                  </div>
                  <button className="btn btn-secondary" style={{ padding: '8px 16px', fontSize: '0.85rem' }} onClick={() => fetchMovies(true)}>
                    Search
                  </button>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  {movies.map(movie => {
                    const currentRating = getMovieUserRating(movie.id);
                    return (
                      <div key={movie.id} className="glass-card" style={{ padding: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '16px' }}>
                        <div style={{ overflow: 'hidden' }}>
                          <h4 style={{ fontSize: '0.95rem', color: '#fff', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{movie.title}</h4>
                          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{movie.release_year} • {movie.genres}</span>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexShrink: 0 }}>
                          {ratingLoading[movie.id] ? (
                            <RefreshCw size={14} className="animate-spin" style={{ color: 'var(--accent-primary)' }} />
                          ) : (
                            <div className="star-rating">
                              {[5, 4, 3, 2, 1].map(star => (
                                <React.Fragment key={star}>
                                  <input 
                                    type="radio" 
                                    id={`catalog-star-${movie.id}-${star}`} 
                                    name={`catalog-rating-${movie.id}`} 
                                    value={star} 
                                    checked={currentRating === star}
                                    onChange={() => submitRating(movie.id, star)}
                                  />
                                  <label htmlFor={`catalog-star-${movie.id}-${star}`}>
                                    <Star size={14} fill={currentRating >= star ? 'var(--accent-warning)' : 'none'} />
                                  </label>
                                </React.Fragment>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>

                {hasMoreMovies && (
                  <div style={{ textAlign: 'center', marginTop: '20px' }}>
                    <button className="btn btn-secondary" style={{ padding: '8px 16px', fontSize: '0.8rem' }} onClick={() => fetchMovies(false)}>
                      Load More
                    </button>
                  </div>
                )}
              </div>

              {/* My Ratings panel */}
              <div className="glass-panel" style={{ padding: '32px' }}>
                <h3 style={{ fontSize: '1.3rem', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Star size={18} style={{ color: 'var(--accent-warning)' }} /> My Rating History
                </h3>
                
                {myRatings.length === 0 ? (
                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>No ratings yet. Rate movies in the catalog to get started!</p>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', maxHeight: '500px', overflowY: 'auto' }}>
                    {myRatings.map(r => (
                      <div key={r.movie_id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px', borderBottom: '1px solid var(--border-color)' }}>
                        <div style={{ overflow: 'hidden', paddingRight: '12px' }}>
                          <h4 style={{ fontSize: '0.9rem', color: '#fff', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{r.title}</h4>
                          <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>{r.genres}</span>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '4px', flexShrink: 0 }}>
                          <Star size={12} fill="var(--accent-warning)" color="var(--accent-warning)" />
                          <span style={{ fontSize: '0.9rem', fontWeight: 'bold' }}>{r.rating.toFixed(1)}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* ADMIN CONTROL PANEL */}
        {view === 'admin' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '30px', animation: 'fadeIn var(--transition-normal) forwards' }}>
            <div>
              <h1 style={{ fontSize: '2.2rem', fontFamily: 'var(--font-display)', display: 'flex', alignItems: 'center', gap: '12px' }}>
                <Shield style={{ color: 'var(--accent-primary)' }} /> Admin Control Center
              </h1>
              <p style={{ color: 'var(--text-secondary)' }}>Monitor user behaviors, inspect outliers, and retrain the GraphSAGE architecture.</p>
            </div>

            {/* Admin Stats Row */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '20px' }}>
              <div className="glass-panel" style={{ padding: '24px', display: 'flex', alignItems: 'center', gap: '20px' }}>
                <div style={{ background: 'rgba(99,102,241,0.1)', color: 'var(--accent-primary)', padding: '12px', borderRadius: '12px' }}>
                  <User size={30} />
                </div>
                <div>
                  <h3 style={{ fontSize: '1.8rem', fontWeight: 800 }}>{adminStats.totalUsers}</h3>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', textTransform: 'uppercase' }}>Monitored Users</p>
                </div>
              </div>
              <div className="glass-panel" style={{ padding: '24px', display: 'flex', alignItems: 'center', gap: '20px' }}>
                <div style={{ background: 'rgba(245,158,11,0.1)', color: 'var(--accent-warning)', padding: '12px', borderRadius: '12px' }}>
                  <AlertTriangle size={30} />
                </div>
                <div>
                  <h3 style={{ fontSize: '1.8rem', fontWeight: 800 }}>{adminStats.totalOutliers}</h3>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', textTransform: 'uppercase' }}>Anomalous Users</p>
                </div>
              </div>
              <div className="glass-panel" style={{ padding: '24px', display: 'flex', alignItems: 'center', gap: '20px' }}>
                <div style={{ background: 'rgba(239,68,68,0.1)', color: 'var(--accent-danger)', padding: '12px', borderRadius: '12px' }}>
                  <UserX size={30} />
                </div>
                <div>
                  <h3 style={{ fontSize: '1.8rem', fontWeight: 800 }}>{adminStats.totalBanned}</h3>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', textTransform: 'uppercase' }}>Banned Accounts</p>
                </div>
              </div>
            </div>

            {/* Admin Tabs */}
            <div style={{ display: 'flex', borderBottom: '1px solid var(--border-color)', gap: '24px' }}>
              <button 
                onClick={() => { setAdminTab('outliers'); fetchOutliers(); }}
                style={{
                  background: 'none', border: 'none',
                  padding: '12px 8px', fontSize: '1.05rem', fontFamily: 'var(--font-display)', fontWeight: 600,
                  color: adminTab === 'outliers' ? 'var(--accent-primary)' : 'var(--text-secondary)',
                  borderBottom: '2px solid ' + (adminTab === 'outliers' ? 'var(--accent-primary)' : 'transparent'),
                  cursor: 'pointer', outline: 'none'
                }}
              >
                Outlier & Anomaly Detection
              </button>
              <button 
                onClick={() => { setAdminTab('retrain'); fetchTrainingLogs(); }}
                style={{
                  background: 'none', border: 'none',
                  padding: '12px 8px', fontSize: '1.05rem', fontFamily: 'var(--font-display)', fontWeight: 600,
                  color: adminTab === 'retrain' ? 'var(--accent-primary)' : 'var(--text-secondary)',
                  borderBottom: '2px solid ' + (adminTab === 'retrain' ? 'var(--accent-primary)' : 'transparent'),
                  cursor: 'pointer', outline: 'none'
                }}
              >
                GraphSAGE Model Retraining
              </button>
            </div>

            {/* TAB 1: OUTLIERS DETECTOR */}
            {adminTab === 'outliers' && (
              <div className="glass-panel" style={{ padding: '32px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
                  <h2>Suspicious User Activity Analysis</h2>
                  <button className="btn btn-secondary" onClick={fetchOutliers} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <RefreshCw size={14} /> Calculate Anomalies
                  </button>
                </div>

                <div style={{ overflowX: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                    <thead>
                      <tr style={{ borderBottom: '2px solid var(--border-color)', paddingBottom: '12px' }}>
                        <th style={{ padding: '12px 8px', color: 'var(--text-secondary)', fontSize: '0.85rem', textTransform: 'uppercase' }}>Username</th>
                        <th style={{ padding: '12px 8px', color: 'var(--text-secondary)', fontSize: '0.85rem', textTransform: 'uppercase' }}>Contact details</th>
                        <th style={{ padding: '12px 8px', color: 'var(--text-secondary)', fontSize: '0.85rem', textTransform: 'uppercase', textAlign: 'center' }}>Total Ratings</th>
                        <th style={{ padding: '12px 8px', color: 'var(--text-secondary)', fontSize: '0.85rem', textTransform: 'uppercase', textAlign: 'center' }}>Avg Rating</th>
                        <th style={{ padding: '12px 8px', color: 'var(--text-secondary)', fontSize: '0.85rem', textTransform: 'uppercase', textAlign: 'center' }}>Variance</th>
                        <th style={{ padding: '12px 8px', color: 'var(--text-secondary)', fontSize: '0.85rem', textTransform: 'uppercase', textAlign: 'center' }}>Anomaly Score</th>
                        <th style={{ padding: '12px 8px', color: 'var(--text-secondary)', fontSize: '0.85rem', textTransform: 'uppercase' }}>Flagged Reasons</th>
                        <th style={{ padding: '12px 8px', color: 'var(--text-secondary)', fontSize: '0.85rem', textTransform: 'uppercase', textAlign: 'right' }}>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {outliers.map(item => {
                        let scoreColor = '#10b981'; // Green
                        if (item.anomaly_score > 60) scoreColor = 'var(--accent-danger)'; // Red
                        else if (item.anomaly_score > 30) scoreColor = 'var(--accent-warning)'; // Amber

                        return (
                          <tr key={item.user_id} style={{ 
                            borderBottom: '1px solid var(--border-color)', 
                            opacity: item.status === 'banned' ? 0.5 : 1,
                            backgroundColor: item.anomaly_score > 40 ? 'rgba(239, 68, 68, 0.02)' : 'transparent'
                          }}>
                            <td style={{ padding: '16px 8px', fontWeight: 600 }}>{item.username}</td>
                            <td style={{ padding: '16px 8px', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                              <div>{item.email}</div>
                              <div>{item.phone}</div>
                            </td>
                            <td style={{ padding: '16px 8px', textAlign: 'center' }}>{item.rating_count}</td>
                            <td style={{ padding: '16px 8px', textAlign: 'center' }}>{item.avg_rating.toFixed(2)}</td>
                            <td style={{ padding: '16px 8px', textAlign: 'center' }}>{item.rating_variance.toFixed(2)}</td>
                            <td style={{ padding: '16px 8px', textAlign: 'center' }}>
                              <span style={{ 
                                color: scoreColor, 
                                fontWeight: 'bold', 
                                background: scoreColor + '15',
                                padding: '4px 10px',
                                borderRadius: '12px',
                                border: '1px solid ' + scoreColor + '30'
                              }}>
                                {item.anomaly_score.toFixed(0)} / 100
                              </span>
                            </td>
                            <td style={{ padding: '16px 8px', fontSize: '0.8rem', maxWidth: '300px' }}>
                              {item.reasons.length === 0 ? (
                                <span style={{ color: 'var(--text-muted)' }}>Healthy activity</span>
                              ) : (
                                <ul style={{ listStyleType: 'square', paddingLeft: '16px', color: 'var(--text-secondary)' }}>
                                  {item.reasons.map((r, i) => <li key={i}>{r}</li>)}
                                </ul>
                              )}
                            </td>
                            <td style={{ padding: '16px 8px', textAlign: 'right' }}>
                              <button 
                                onClick={() => toggleBanUser(item.user_id, item.status)}
                                className={`btn ${item.status === 'banned' ? 'btn-success' : 'btn-danger'}`}
                                style={{ padding: '6px 12px', fontSize: '0.75rem', display: 'inline-flex', alignItems: 'center', gap: '6px' }}
                              >
                                {item.status === 'banned' ? (
                                  <>
                                    <UserCheck size={12} /> Unban User
                                  </>
                                ) : (
                                  <>
                                    <UserX size={12} /> Ban User
                                  </>
                                )}
                              </button>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* TAB 2: RETRAINING LOOPS */}
            {adminTab === 'retrain' && (
              <div style={{ display: 'grid', gridTemplateColumns: '0.8fr 1.2fr', gap: '30px', alignItems: 'start' }}>
                
                {/* Control Panel */}
                <div className="glass-panel" style={{ padding: '32px' }}>
                  <h2 style={{ fontSize: '1.4rem', marginBottom: '16px' }}>Training Controls</h2>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '24px', lineHeight: '1.6' }}>
                    This triggers a GraphSAGE bipartite network retraining loop. 
                    It compiles all active user ratings (excluding banned users) alongside the MovieLens 100k base records, 
                    recomputes node representations on GPU (if CUDA is enabled), and saves updated embeddings.
                  </p>

                  <button 
                    disabled={trainingActive}
                    onClick={triggerModelRetrain}
                    className="btn btn-primary"
                    style={{ width: '100%', padding: '14px', fontSize: '1rem', display: 'flex', alignItems: 'center', gap: '10px', opacity: trainingActive ? 0.6 : 1 }}
                  >
                    {trainingActive ? (
                      <>
                        <RefreshCw className="animate-spin" size={18} />
                        Training in Progress...
                      </>
                    ) : (
                      <>
                        <Play size={18} />
                        Trigger GraphSAGE Train Run
                      </>
                    )}
                  </button>
                </div>

                {/* Console Log Output */}
                <div className="glass-panel" style={{ padding: '32px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                    <h2 style={{ fontSize: '1.4rem' }}>Training Console Logs</h2>
                    <span style={{ 
                      fontSize: '0.75rem', 
                      padding: '4px 10px', 
                      borderRadius: '12px', 
                      background: trainingActive ? 'rgba(99,102,241,0.2)' : 'rgba(255,255,255,0.06)',
                      color: trainingActive ? '#818cf8' : 'var(--text-secondary)'
                    }}>
                      Status: {trainingActive ? "ACTIVE" : "IDLE"}
                    </span>
                  </div>

                  <div className="terminal-window">
                    {trainingLogs.length === 0 ? (
                      <div>No training runs recorded.</div>
                    ) : (
                      trainingLogs.map(log => {
                        let statusColor = '#10b981'; // completed
                        if (log.status === 'running') statusColor = '#3b82f6';
                        if (log.status === 'failed') statusColor = '#ef4444';

                        return (
                          <div key={log.id} style={{ borderBottom: '1px solid rgba(0,255,0,0.1)', paddingBottom: '10px', marginBottom: '10px' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', color: '#fff', fontSize: '0.8rem' }}>
                              <span>[{log.timestamp}]</span>
                              <span style={{ color: statusColor, fontWeight: 'bold' }}>{log.status.toUpperCase()}</span>
                            </div>
                            <div style={{ paddingLeft: '10px', marginTop: '4px', wordBreak: 'break-all' }}>
                              {log.status === 'completed' && log.loss ? `Loss: ${log.loss.toFixed(4)}` : ''}
                              <div style={{ color: 'rgba(0, 255, 0, 0.7)' }}>{log.metrics}</div>
                            </div>
                          </div>
                        );
                      })
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
