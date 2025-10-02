import { FormEvent, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { login, register } from '../api/auth';
import { useAuth } from '../hooks/useAuth';

const LoginPage = () => {
  const navigate = useNavigate();
  const { login: setToken } = useAuth();
  const demoEmail = 'admin@cosim.dev';
  const demoPassword = 'adminadmin';
  const [mode, setMode] = useState<'signin' | 'signup'>('signin');
  const [username, setUsername] = useState(demoEmail);
  const [password, setPassword] = useState(demoPassword);
  const [fullName, setFullName] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      if (mode === 'signup') {
        await register({ email: username, password, full_name: fullName || undefined });
      }
      const response = await login({ username, password });
      setToken(response.access_token);
      navigate('/projects');
    } catch (err) {
      setError(mode === 'signup' ? 'Unable to register with those details.' : 'Unable to sign in, please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleUseDemo = () => {
    setUsername(demoEmail);
    setPassword(demoPassword);
    setMode('signin');
    setError(null);
  };

  return (
    <div className="layout">
      <div className="container" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh' }}>
        <form className="card" style={{ width: '100%', maxWidth: '420px', display: 'flex', flexDirection: 'column', gap: '1rem' }} onSubmit={handleSubmit}>
          <h1 style={{ margin: 0, textAlign: 'center' }}>{mode === 'signin' ? 'Sign in to CoSim' : 'Create your CoSim account'}</h1>
          <div>
            <label htmlFor="email" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>Email</label>
            <input
              id="email"
              type="email"
              placeholder="you@example.edu"
              value={username}
              onChange={event => setUsername(event.target.value)}
              required
            />
          </div>
          {mode === 'signup' && (
            <div>
              <label htmlFor="fullName" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>Full name (optional)</label>
              <input
                id="fullName"
                type="text"
                placeholder="Ada Lovelace"
                value={fullName}
                onChange={event => setFullName(event.target.value)}
              />
            </div>
          )}
          <div>
            <label htmlFor="password" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>Password</label>
            <input
              id="password"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={event => setPassword(event.target.value)}
              required
            />
          </div>
          {error && <div style={{ color: '#b91c1c', fontSize: '0.9rem' }}>{error}</div>}
          <button className="primary-button" type="submit" disabled={loading}>
            {loading ? (mode === 'signin' ? 'Signing in…' : 'Creating account…') : mode === 'signin' ? 'Sign in' : 'Register and sign in'}
          </button>
          <button className="secondary-button" type="button" onClick={handleUseDemo}>
            Use demo admin credentials
          </button>
          <p style={{ fontSize: '0.9rem', color: '#475569', margin: 0, textAlign: 'center' }}>
            Demo login: <strong>{demoEmail}</strong> / <strong>{demoPassword}</strong>
          </p>
          <button
            type="button"
            className="secondary-button"
            onClick={() => {
              setMode(mode === 'signin' ? 'signup' : 'signin');
              setError(null);
              if (mode === 'signin') {
                setFullName('');
              }
            }}
          >
            {mode === 'signin' ? 'Need an account? Register' : 'Already have an account? Sign in'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default LoginPage;
