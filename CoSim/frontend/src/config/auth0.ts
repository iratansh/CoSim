/**
 * Auth0 configuration for the frontend application.
 * Reads configuration from environment variables.
 */

export interface Auth0Config {
  domain: string;
  clientId: string;
  redirectUri: string;
  audience?: string;
  scope: string;
}

export const getAuth0Config = (): Auth0Config => {
  const domain = import.meta.env.VITE_AUTH0_DOMAIN;
  const clientId = import.meta.env.VITE_AUTH0_CLIENT_ID;
  const callbackUrl = import.meta.env.VITE_AUTH0_CALLBACK_URL || `${window.location.origin}/callback`;
  const audience = import.meta.env.VITE_AUTH0_AUDIENCE || undefined;
  const scope = import.meta.env.VITE_AUTH0_SCOPE || 'openid profile email';

  if (!domain || !clientId) {
    console.error('Auth0 configuration is missing! Please set VITE_AUTH0_DOMAIN and VITE_AUTH0_CLIENT_ID');
  }

  return {
    domain,
    clientId,
    redirectUri: callbackUrl,
    audience,
    scope,
  };
};

export const auth0Config = getAuth0Config();
