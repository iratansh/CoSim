import { authorizedClient } from './client';

export interface WorkspaceFile {
  id: string;
  workspace_id: string;
  path: string;
  content: string;
  language?: string | null;
  created_at: string;
  updated_at: string;
}

export interface WorkspaceFilePayload {
  path: string;
  content: string;
  language?: string | null;
}

export const listWorkspaceFiles = async (token: string, workspaceId: string): Promise<WorkspaceFile[]> => {
  const { data } = await authorizedClient(token).get<WorkspaceFile[]>(`/v1/workspaces/${workspaceId}/files`);
  return data;
};

export const upsertWorkspaceFile = async (
  token: string,
  workspaceId: string,
  payload: WorkspaceFilePayload
): Promise<WorkspaceFile> => {
  const { data } = await authorizedClient(token).put<WorkspaceFile>(
    `/v1/workspaces/${workspaceId}/files`,
    payload
  );
  return data;
};

