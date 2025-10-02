import { authorizedClient } from './client';
import type { Organization } from './types';

export const fetchOrganizations = async (token: string): Promise<Organization[]> => {
  const { data } = await authorizedClient(token).get<Organization[]>('/v1/organizations');
  return data;
};

interface CreateOrganizationPayload {
  name: string;
  slug: string;
  description?: string;
}

export const createOrganization = async (
  token: string,
  payload: CreateOrganizationPayload
): Promise<Organization> => {
  const { data } = await authorizedClient(token).post<Organization>('/v1/organizations', payload);
  return data;
};
