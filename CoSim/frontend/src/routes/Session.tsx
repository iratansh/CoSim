import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useEffect, useMemo, useState } from 'react';
import { useParams } from 'react-router-dom';

import { getSession, pauseSession, resumeSession, terminateSession } from '../api/sessions';
import { createDocument, addParticipantToDocument } from '../api/collab';
import type { Session } from '../api/types';
import Layout from '../components/Layout';
import SessionIDE from '../components/SessionIDE';
import { useAuth } from '../hooks/useAuth';

const SessionPage = () => {
  const { sessionId } = useParams();
  const { token, user } = useAuth();
  const queryClient = useQueryClient();
  const [lastSavedSnippet, setLastSavedSnippet] = useState<string>('');
  const [documentId, setDocumentId] = useState<string | null>(null);

  const { data: session, isLoading, isError } = useQuery<Session>({
    queryKey: ['session', sessionId],
    queryFn: () => getSession(token!, sessionId!),
    enabled: Boolean(sessionId)
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['session', sessionId] });

  const pause = useMutation({
    mutationFn: () => pauseSession(token!, sessionId!),
    onSuccess: invalidate
  });

  const resume = useMutation({
    mutationFn: () => resumeSession(token!, sessionId!),
    onSuccess: invalidate
  });

  const terminate = useMutation({
    mutationFn: () => terminateSession(token!, sessionId!),
    onSuccess: invalidate
  });

  useEffect(() => {
    if (!session || !token) return;
    if (documentId) return;
    createDocument(token, {
      workspace_id: session.workspace_id,
      name: `Session ${session.id}`
    })
      .then(doc => {
        setDocumentId(doc.document_id);
        if (user) {
          return addParticipantToDocument(token, doc.document_id, { user_id: user.id, role: 'editor' });
        }
        return undefined;
      })
      .catch(() => {
        /* best-effort stub for now */
      });
  }, [session, token, user, documentId]);

  const statusActions = useMemo(() => {
    if (!session) return null;
    switch (session.status) {
      case 'paused':
        return (
          <button className="primary-button" onClick={() => resume.mutate()} disabled={resume.isPending}>
            Resume session
          </button>
        );
      case 'running':
      case 'starting':
        return (
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button className="secondary-button" onClick={() => pause.mutate()} disabled={pause.isPending}>
              Pause
            </button>
            <button className="primary-button" onClick={() => terminate.mutate()} disabled={terminate.isPending}>
              Terminate
            </button>
          </div>
        );
      default:
        return null;
    }
  }, [session, pause, resume, terminate]);

  return (
    <Layout
      title={session ? `Session • ${session.session_type.toUpperCase()}` : 'Session'}
      actions={statusActions}
    >
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        {isLoading && <p>Loading session…</p>}
        {isError && <p style={{ color: '#b91c1c' }}>Unable to load session.</p>}
        {session && (
          <dl style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem', margin: 0 }}>
            <InfoItem label="Status" value={<span className="badge">{session.status}</span>} />
            <InfoItem label="Workspace" value={session.workspace_id} />
            <InfoItem label="GPU" value={session.requested_gpu ?? 'CPU only'} />
            <InfoItem label="Started" value={session.started_at ? new Date(session.started_at).toLocaleString() : '—'} />
          </dl>
        )}
      </div>

      <section style={{ display: 'flex', gap: '1.5rem', flexDirection: 'column' }}>
        <div style={{ height: '700px', border: '1px solid #e2e8f0', borderRadius: '8px', overflow: 'hidden' }}>
          <SessionIDE
            sessionId={sessionId}
            workspaceId={session?.workspace_id}
            enableCollaboration={true}
            onSave={({ path, content }) => {
              setLastSavedSnippet(`Saved ${path} (${content.length} chars)`);
            }}
          />
        </div>
        <TelemetryCard session={session} lastSavedSnippet={lastSavedSnippet} />
      </section>
    </Layout>
  );
};

interface InfoItemProps {
  label: string;
  value: React.ReactNode;
}

const InfoItem = ({ label, value }: InfoItemProps) => (
  <div>
    <dt style={{ fontSize: '0.85rem', textTransform: 'uppercase', color: '#64748b', marginBottom: '0.25rem' }}>{label}</dt>
    <dd style={{ margin: 0, fontWeight: 600 }}>{value}</dd>
  </div>
);

interface TelemetryProps {
  session?: Session;
  lastSavedSnippet: string;
}

const TelemetryCard = ({ session, lastSavedSnippet }: TelemetryProps) => (
  <div className="card">
    <h2 style={{ marginTop: 0 }}>Live telemetry</h2>
    <p style={{ color: '#475569', marginTop: 0 }}>
      Real-time metrics and simulator streams will display here once the simulation plane is connected.
    </p>
    <ul style={{ paddingLeft: '1.2rem', color: '#1e293b' }}>
      <li>Session status: {session?.status ?? 'unknown'}</li>
      <li>Last saved snippet: {lastSavedSnippet || 'No snippets saved yet'}</li>
      <li>Participants: {session ? session.participants.length : 0}</li>
    </ul>
  </div>
);

export default SessionPage;
