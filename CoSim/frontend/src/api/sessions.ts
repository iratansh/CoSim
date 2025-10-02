import { authorizedClient } from './client';
import type { Session } from './types';

export const getSession = async (token: string, sessionId: string): Promise<Session> => {
  const { data } = await authorizedClient(token).get<Session>(`/v1/sessions/${sessionId}`);
  return data;
};

export const pauseSession = async (token: string, sessionId: string): Promise<Session> => {
  const { data } = await authorizedClient(token).post<Session>(`/v1/sessions/${sessionId}/pause`);
  return data;
};

export const resumeSession = async (token: string, sessionId: string): Promise<Session> => {
  const { data } = await authorizedClient(token).post<Session>(`/v1/sessions/${sessionId}/resume`);
  return data;
};

export const terminateSession = async (token: string, sessionId: string): Promise<Session> => {
  const { data } = await authorizedClient(token).post<Session>(`/v1/sessions/${sessionId}/terminate`);
  return data;
};
