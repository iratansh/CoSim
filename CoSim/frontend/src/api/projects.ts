import { authorizedClient } from './client';
import type { Project, Session, Workspace } from './types';

export const fetchProjects = async (token: string): Promise<Project[]> => {
  const { data } = await authorizedClient(token).get<Project[]>('/v1/projects');
  return data;
};

export const fetchWorkspaces = async (token: string, projectId: string): Promise<Workspace[]> => {
  const { data } = await authorizedClient(token).get<Workspace[]>(
    '/v1/workspaces',
    { params: { project_id: projectId } }
  );
  return data;
};

export const fetchSessionsForWorkspace = async (
  token: string,
  workspaceId: string
): Promise<Session[]> => {
  const { data } = await authorizedClient(token).get<Session[]>(
    '/v1/sessions',
    { params: { workspace_id: workspaceId } }
  );
  return data;
};
export const fetchProject = async (token: string, projectId: string): Promise<Project> => {
  const { data } = await authorizedClient(token).get<Project>(`/v1/projects/${projectId}`);
  return data;
};
