import { apiClient } from './client';
import type { AuthTokenResponse, LoginPayload, RegisterPayload, User } from './types';

export const login = async (payload: LoginPayload): Promise<AuthTokenResponse> => {
  const params = new URLSearchParams();
  params.append('username', payload.username);
  params.append('password', payload.password);

  const { data } = await apiClient.post<AuthTokenResponse>('/v1/auth/token', params, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
  });

  return data;
};

export const me = async (token: string): Promise<User> => {
  const { data } = await apiClient.get<User>('/v1/auth/me', {
    headers: { Authorization: `Bearer ${token}` }
  });
  return data;
};

export const register = async (payload: RegisterPayload): Promise<User> => {
  const { data } = await apiClient.post<User>('/v1/auth/register', payload);
  return data;
};

export const exchangeAuth0Token = async (auth0Token: string): Promise<AuthTokenResponse> => {
  const { data } = await apiClient.post<AuthTokenResponse>('/v1/auth/auth0/exchange', {}, {
    headers: { Authorization: `Bearer ${auth0Token}` }
  });
  return data;
};
