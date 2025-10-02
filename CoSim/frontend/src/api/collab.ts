import { authorizedClient } from './client';

interface CollabDocumentPayload {
  workspace_id: string;
  name: string;
  description?: string;
  template_path?: string;
}

interface CollabDocumentResponse {
  document_id: string;
}

export const createDocument = async (token: string, payload: CollabDocumentPayload) => {
  const { data } = await authorizedClient(token).post<CollabDocumentResponse>('/v1/collab/documents', payload);
  return data;
};

export const addParticipantToDocument = async (
  token: string,
  documentId: string,
  payload: { user_id: string; role?: string }
) => {
  await authorizedClient(token).post(`/v1/collab/documents/${documentId}/participants`, payload);
};
