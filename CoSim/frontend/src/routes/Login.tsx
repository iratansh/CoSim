import { FormEvent, useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth0 } from '@auth0/auth0-react';
import { useMutation } from '@tanstack/react-query';
import { Loader2 } from 'lucide-react';

import { login as legacyLogin, register as legacyRegister } from '../api/auth';
import type { User } from '../api/types';
import { useAuth } from '../hooks/useAuth';

const LoginPage = () => {
  const navigate = useNavigate();
  const { loginWithRedirect, isAuthenticated, isLoading } = useAuth0();
  const { login: setAuthToken, authSource } = useAuth();
  const hasNavigated = useRef(false);
  const [legacyEmail, setLegacyEmail] = useState('');
  const [legacyPassword, setLegacyPassword] = useState('');
  const [legacyName, setLegacyName] = useState('');
  const [legacyMode, setLegacyMode] = useState<'login' | 'signup'>('login');
  const [legacyError, setLegacyError] = useState<string | null>(null);

  const legacyActionLabel = useMemo(() => (legacyMode === 'login' ? 'Sign in with email' : 'Create account'), [legacyMode]);

  const legacyMutation = useMutation({
    mutationFn: async (): Promise<{ token: string; user?: User }> => {
      setLegacyError(null);

      if (!legacyEmail.trim() || !legacyPassword.trim()) {
        throw new Error('Please enter both email and password.');
      }

      let createdUser: User | undefined;
      if (legacyMode === 'signup') {
        createdUser = await legacyRegister({
          email: legacyEmail.trim().toLowerCase(),
          password: legacyPassword,
          full_name: legacyName.trim() || undefined,
          plan: 'free',
        });
      }

      const response = await legacyLogin({
        username: legacyEmail.trim().toLowerCase(),
        password: legacyPassword,
      });

      return { token: response.access_token, user: createdUser };
    },
    onSuccess: async ({ token, user }) => {
      setAuthToken(token, { source: 'legacy', user });
      setLegacyEmail('');
      setLegacyPassword('');
      setLegacyName('');
      navigate('/projects');
    },
    onError: (error: unknown) => {
      if (error instanceof Error && error.message === 'Please enter both email and password.') {
        setLegacyError(error.message);
        return;
      }

      const axiosError = error as { response?: { data?: { detail?: string; message?: string } } };
      const detail = axiosError.response?.data?.detail ?? axiosError.response?.data?.message;
      setLegacyError(detail || 'Unable to complete the request. Please try again.');
    },
  });

  useEffect(() => {
    if ((isAuthenticated || authSource === 'legacy') && !hasNavigated.current) {
      hasNavigated.current = true;
      navigate('/projects');
    }
  }, [isAuthenticated, authSource, navigate]);

  const handleLogin = async () => {
    await loginWithRedirect({
      appState: { returnTo: '/projects' },
    });
  };

  const handleSignup = async () => {
    await loginWithRedirect({
      authorizationParams: {
        screen_hint: 'signup',
      },
      appState: { returnTo: '/projects' },
    });
  };

  const handleLegacySubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (legacyMutation.isPending) return;
    legacyMutation.mutate();
  };

  if (isLoading && authSource !== 'legacy') {
    return (
      <div className="layout">
        <div className="container" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh' }}>
          <div style={{ textAlign: 'center' }}>
            <Loader2 size={48} className="animate-spin" style={{ margin: '0 auto 1rem', color: '#667eea' }} />
            <p style={{ color: '#64748b' }}>Loading...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="layout">
      <div className="container" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh' }}>
        <div className="card" style={{ width: '100%', maxWidth: '420px', display: 'flex', flexDirection: 'column', gap: '1.5rem', textAlign: 'center' }}>
          <div>
            <h1 style={{ margin: '0 0 0.5rem', fontSize: '2rem', background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
              Welcome to CoSim
            </h1>
            <p style={{ margin: 0, color: '#64748b', fontSize: '1rem' }}>
              Cloud robotics development platform with C++ & Python
            </p>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'center' }}>
              <button
                type="button"
                onClick={() => setLegacyMode('login')}
                style={{
                  padding: '0.5rem 1rem',
                  borderRadius: '6px',
                  border: legacyMode === 'login' ? '2px solid #667eea' : '1px solid #e2e8f0',
                  background: legacyMode === 'login' ? 'rgba(102, 126, 234, 0.1)' : 'white',
                  color: legacyMode === 'login' ? '#4c51bf' : '#475569',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                Email login
              </button>
              <button
                type="button"
                onClick={() => setLegacyMode('signup')}
                style={{
                  padding: '0.5rem 1rem',
                  borderRadius: '6px',
                  border: legacyMode === 'signup' ? '2px solid #667eea' : '1px solid #e2e8f0',
                  background: legacyMode === 'signup' ? 'rgba(102, 126, 234, 0.1)' : 'white',
                  color: legacyMode === 'signup' ? '#4c51bf' : '#475569',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                Create account
              </button>
            </div>

            <form onSubmit={handleLegacySubmit} style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', textAlign: 'left' }}>
              {legacyMode === 'signup' && (
                <label style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem', fontSize: '0.875rem', color: '#475569' }}>
                  Full name (optional)
                  <input
                    type="text"
                    value={legacyName}
                    onChange={(event) => setLegacyName(event.target.value)}
                    placeholder="Ada Lovelace"
                    style={{ padding: '0.75rem', borderRadius: '8px', border: '1px solid #cbd5f5' }}
                  />
                </label>
              )}

              <label style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem', fontSize: '0.875rem', color: '#475569' }}>
                Email
                <input
                  type="email"
                  value={legacyEmail}
                  onChange={(event) => setLegacyEmail(event.target.value)}
                  placeholder="you@example.com"
                  autoComplete="email"
                  style={{ padding: '0.75rem', borderRadius: '8px', border: '1px solid #cbd5f0' }}
                  required
                />
              </label>

              <label style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem', fontSize: '0.875rem', color: '#475569' }}>
                Password
                <input
                  type="password"
                  value={legacyPassword}
                  onChange={(event) => setLegacyPassword(event.target.value)}
                  placeholder="••••••••"
                  autoComplete={legacyMode === 'login' ? 'current-password' : 'new-password'}
                  style={{ padding: '0.75rem', borderRadius: '8px', border: '1px solid #cbd5f0' }}
                  required
                />
              </label>

              {legacyError && (
                <div style={{ background: '#fef2f2', color: '#b91c1c', padding: '0.75rem', borderRadius: '8px', fontSize: '0.875rem' }}>
                  {legacyError}
                </div>
              )}

              <button
                type="submit"
                disabled={legacyMutation.isPending}
                style={{
                  padding: '0.875rem 1.5rem',
                  fontSize: '1rem',
                  fontWeight: '600',
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  border: 'none',
                  borderRadius: '8px',
                  color: 'white',
                  cursor: 'pointer',
                  opacity: legacyMutation.isPending ? 0.7 : 1,
                  transition: 'transform 0.2s, box-shadow 0.2s',
                }}
              >
                {legacyMutation.isPending ? 'Working...' : legacyActionLabel}
              </button>
            </form>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', color: '#94a3b8', fontSize: '0.75rem' }}>
              <div style={{ flexGrow: 1, height: 1, background: '#e2e8f0' }} />
              <span>or continue with</span>
              <div style={{ flexGrow: 1, height: 1, background: '#e2e8f0' }} />
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <button
                type="button"
                className="primary-button"
                onClick={handleLogin}
                style={{
                  padding: '0.875rem 1.5rem',
                  fontSize: '1rem',
                  fontWeight: '600',
                  background: '#1a73e8',
                  border: 'none',
                  borderRadius: '8px',
                  color: 'white',
                  cursor: 'pointer',
                  transition: 'transform 0.2s, box-shadow 0.2s',
                }}
              >
                Sign in with Auth0 (Google/Social)
              </button>

              <button
                type="button"
                className="secondary-button"
                onClick={handleSignup}
                style={{
                  padding: '0.875rem 1.5rem',
                  fontSize: '1rem',
                  fontWeight: '600',
                  background: 'white',
                  border: '2px solid #e2e8f0',
                  borderRadius: '8px',
                  color: '#475569',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                }}
              >
                Use Auth0 Universal Login
              </button>
            </div>
          </div>

          <div style={{ padding: '1rem', background: '#f8fafc', borderRadius: '8px', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <p style={{ margin: 0, fontSize: '0.875rem', color: '#64748b' }}>
              🔐 Secure authentication powered by Auth0 and legacy credentials
            </p>
            <p style={{ margin: 0, fontSize: '0.75rem', color: '#94a3b8' }}>
              Choose email/password or continue with Google & social providers.
            </p>
          </div>

          <div style={{ borderTop: '1px solid #e2e8f0', paddingTop: '1rem' }}>
            <p style={{ margin: 0, fontSize: '0.875rem', color: '#64748b' }}>
              By signing in, you agree to our{' '}
              <a href="/terms" style={{ color: '#667eea', textDecoration: 'none' }}>Terms of Service</a>
              {' '}and{' '}
              <a href="/privacy" style={{ color: '#667eea', textDecoration: 'none' }}>Privacy Policy</a>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
