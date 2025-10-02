import { Navigate, Route, Routes } from 'react-router-dom';

import { useAuth } from './hooks/useAuth';
import LoginPage from './routes/Login';
import ProjectsPage from './routes/Projects';
import WorkspacePage from './routes/Workspace';
import SessionPage from './routes/Session';
import LandingPage from './routes/Landing';
import ProfilePage from './routes/Profile';
import SettingsPage from './routes/Settings';
import PricingPage from './routes/Pricing';

const App = () => {
  const { token } = useAuth();

  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
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
