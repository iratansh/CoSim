import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth0 } from '@auth0/auth0-react';
import { Loader2 } from 'lucide-react';

/**
 * Auth0 Callback Page
 * Handles the redirect after Auth0 authentication
 */
const CallbackPage = () => {
  const navigate = useNavigate();
  const { isAuthenticated, isLoading, error } = useAuth0();

  useEffect(() => {
    if (!isLoading) {
      if (isAuthenticated) {
        // Redirect to projects page after successful authentication
        navigate('/projects');
      } else if (error) {
        // Redirect to login page if there was an error
        console.error('Auth0 callback error:', error);
        navigate('/login');
      }
    }
  }, [isAuthenticated, isLoading, error, navigate]);

  return (
    <div className="layout">
      <div className="container" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh' }}>
        <div style={{ textAlign: 'center' }}>
          <Loader2 size={48} className="animate-spin" style={{ margin: '0 auto 1.5rem', color: '#667eea' }} />
          <h2 style={{ margin: '0 0 0.5rem', color: '#1e293b' }}>
            {error ? 'Authentication Error' : 'Completing sign in...'}
          </h2>
          {error && (
            <p style={{ color: '#dc2626', fontSize: '0.875rem', margin: '0.5rem 0' }}>
              {error.message}
            </p>
          )}
          <p style={{ color: '#64748b', fontSize: '0.875rem', margin: 0 }}>
            {error ? 'Redirecting to login page...' : 'Please wait while we complete your authentication.'}
          </p>
        </div>
      </div>
    </div>
  );
};

export default CallbackPage;
