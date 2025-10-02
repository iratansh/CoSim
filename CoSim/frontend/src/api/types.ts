export interface User {
  id: string;
  email: string;
  full_name?: string | null;
  plan: 'free' | 'student' | 'pro' | 'team' | 'enterprise';
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
  updated_at: string;
}

export interface Project {
  id: string;
  name: string;
  slug: string;
  description?: string | null;
  organization_id: string;
  template_id?: string | null;
  created_by_id?: string | null;
  created_at: string;
  updated_at: string;
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
  description?: string | null;
  created_at: string;
  updated_at: string;
}

export interface Workspace {
  id: string;
  name: string;
  slug: string;
  status: 'provisioning' | 'active' | 'paused' | 'hibernated' | 'deleted';
  project_id: string;
  template_id?: string | null;
  requested_gpu?: number | null;
  created_at: string;
  updated_at: string;
}

export interface SessionParticipant {
  id: string;
  user_id: string;
  role: string;
  created_at: string;
  updated_at: string;
}

export interface Session {
  id: string;
  workspace_id: string;
  session_type: 'ide' | 'simulator';
  status: 'pending' | 'starting' | 'running' | 'paused' | 'terminating' | 'terminated';
  requested_gpu?: number | null;
  details: Record<string, unknown>;
  started_at?: string | null;
  ended_at?: string | null;
  created_at: string;
  updated_at: string;
  participants: SessionParticipant[];
}

export interface AuthTokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface LoginPayload {
  username: string;
  password: string;
}

export interface RegisterPayload {
  email: string;
  password: string;
  full_name?: string;
  plan?: User['plan'];
}
