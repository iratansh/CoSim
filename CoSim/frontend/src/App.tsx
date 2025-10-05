import { Navigate, Route, Routes } from 'react-router-dom';

import { useAuth } from './hooks/useAuth';
import LoginPage from './routes/Login';
import CallbackPage from './routes/Callback';
import ProjectsPage from './routes/Projects';
import WorkspacePage from './routes/Workspace';
import SessionPage from './routes/Session';
import LandingPage from './routes/Landing';
import ProfilePage from './routes/Profile';
import SettingsPage from './routes/Settings';
import PricingPage from './routes/Pricing';

const App = () => {
  const { token, isLoading } = useAuth();

  // Show loading screen while Auth0 is initializing
  if (isLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>🤖</div>
          <p style={{ color: '#64748b' }}>Loading CoSim...</p>
        </div>
      </div>
    );
  }

  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/callback" element={<CallbackPage />} />
      <Route path="/pricing" element={<PricingPage />} />
      <Route
        path="/projects"
        element={token ? <ProjectsPage /> : <Navigate to="/login" replace />}
      />
      <Route
        path="/projects/:projectId"
        element={token ? <WorkspacePage /> : <Navigate to="/login" replace />}
      />
      <Route
        path="/sessions/:sessionId"
        element={token ? <SessionPage /> : <Navigate to="/login" replace />}
      />
      <Route
        path="/profile"
        element={token ? <ProfilePage /> : <Navigate to="/login" replace />}
      />
      <Route
        path="/settings"
        element={token ? <SettingsPage /> : <Navigate to="/login" replace />}
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};

export default App;
