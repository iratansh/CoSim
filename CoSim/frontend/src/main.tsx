import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Auth0Provider } from '@auth0/auth0-react';

import App from './App';
import { AuthProvider } from './contexts/AuthContext';
import { ThemeProvider } from './contexts/ThemeContext';
import { auth0Config } from './config/auth0';
import './styles/global.css';

const authorizationParams: Record<string, string> = {
  redirect_uri: auth0Config.redirectUri,
  scope: auth0Config.scope,
};

if (auth0Config.audience) {
  authorizationParams.audience = auth0Config.audience;
}

const queryClient = new QueryClient();

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <Auth0Provider
        domain={auth0Config.domain}
        clientId={auth0Config.clientId}
        authorizationParams={authorizationParams}
        cacheLocation="localstorage"
        useRefreshTokens={true}
      >
        <ThemeProvider>
          <AuthProvider>
            <BrowserRouter
              future={{
                v7_startTransition: true,
                v7_relativeSplatPath: true
              }}
            >
              <App />
            </BrowserRouter>
          </AuthProvider>
        </ThemeProvider>
      </Auth0Provider>
    </QueryClientProvider>
  </React.StrictMode>
);
