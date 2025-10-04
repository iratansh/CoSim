import { useEffect, useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useParams, useNavigate } from 'react-router-dom';
import { Activity, Box, Cpu, Maximize2, Minimize2, Monitor, Play, Zap } from 'lucide-react';

import { fetchProject, fetchSessionsForWorkspace, fetchWorkspaces } from '../api/projects';
import type { Session, Workspace } from '../api/types';
import Layout from '../components/Layout';
import SessionIDE from '../components/SessionIDE';
import SimulationViewer from '../components/SimulationViewer';
import { useAuth } from '../hooks/useAuth';

const WorkspacePage = () => {
  const { projectId } = useParams();
  const { token } = useAuth();
  const navigate = useNavigate();
  const [activeWorkspaceId, setActiveWorkspaceId] = useState<string | null>(null);
  const [isSimExpanded, setIsSimExpanded] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [activeTab, setActiveTab] = useState<'simulation' | 'metrics' | 'logs'>('simulation');
  const [currentSimulationCode, setCurrentSimulationCode] = useState<string | null>(null);
  const [executionOutput, setExecutionOutput] = useState<{
    status: 'idle' | 'running' | 'success' | 'error';
    stdout?: string;
    stderr?: string;
    error?: string;
    timestamp?: string;
  }>({ status: 'idle' });

  // Handler to run code in simulator
  const handleRunSimulation = async (code: string, modelPath?: string) => {
    console.log('🎮 Running code in simulator...', { modelPath });
    setCurrentSimulationCode(code);
    setExecutionOutput({ status: 'running', timestamp: new Date().toISOString() });
    
    const simulationApiUrl = import.meta.env.VITE_SIMULATION_API_URL || 'http://localhost:8005';
    const sessionIdForSim = activeSessionId || 'default-session';
    
    try {
      // Try to create simulation (gracefully handle if already exists)
      const createResponse = await fetch(`${simulationApiUrl}/simulations/create`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { 'Authorization': `Bearer ${token}` }),
        },
        body: JSON.stringify({
          session_id: sessionIdForSim,
          engine: 'mujoco',
          model_path: modelPath || '/app/templates/mujoco/cartpole.xml',
          width: 800,
          height: 600,
          fps: 60,
          headless: true,
        }),
      });
      
      if (createResponse.ok) {
        const createData = await createResponse.json();
        console.log('✅ Simulation created:', createData);
      } else if (createResponse.status === 400) {
        console.log('ℹ️ Simulation already exists, reusing existing session');
      } else {
        console.warn('⚠️ Simulation creation returned:', createResponse.status);
      }

      // Execute code
      const response = await fetch(`${simulationApiUrl}/simulations/${sessionIdForSim}/execute`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { 'Authorization': `Bearer ${token}` }),
        },
        body: JSON.stringify({
          code,
          model_path: modelPath,
          working_dir: '/workspace',
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Simulation execution failed');
      }

      const result = await response.json();
      console.log('✓ Simulation completed:', result);
      
      if (result.stdout) console.log('stdout:', result.stdout);
      if (result.stderr) console.warn('stderr:', result.stderr);
      if (result.error) console.error('Error:', result.error);
      
      // Store execution results in state
      setExecutionOutput({
        status: result.status === 'success' ? 'success' : 'error',
        stdout: result.stdout,
        stderr: result.stderr,
        error: result.error,
        timestamp: new Date().toISOString()
      });
    } catch (error) {
      console.error('Failed to run simulation:', error);
      setExecutionOutput({
        status: 'error',
        error: error instanceof Error ? error.message : String(error),
        timestamp: new Date().toISOString()
      });
      throw error;
    }
  };

  // Redirect to login if no token
  useEffect(() => {
    if (!token) {
      console.warn('No authentication token found, redirecting to login');
      navigate('/login', { replace: true });
    }
  }, [token, navigate]);

  const { data: project } = useQuery({
    queryKey: ['project', projectId],
    queryFn: () => fetchProject(token!, projectId!),
    enabled: Boolean(projectId && token),
    retry: false
  });

  const {
    data: workspaces,
    isLoading: workspacesLoading,
    isError: workspacesError
  } = useQuery<Workspace[]>({
    queryKey: ['workspaces', projectId],
    queryFn: () => fetchWorkspaces(token!, projectId!),
    enabled: Boolean(projectId && token),
    retry: false
  });

  useEffect(() => {
    if (!workspaces || workspaces.length === 0) return;
    setActiveWorkspaceId(prev => prev ?? workspaces[0].id);
  }, [workspaces]);

  const { data: sessions } = useQuery<Session[]>({
    queryKey: ['sessions', activeWorkspaceId],
    queryFn: () => fetchSessionsForWorkspace(token!, activeWorkspaceId!),
    enabled: Boolean(token && activeWorkspaceId)
  });

  const activeWorkspace = useMemo(
    () => workspaces?.find(ws => ws.id === activeWorkspaceId) ?? null,
    [workspaces, activeWorkspaceId]
  );

  const activeSessionId = sessions && sessions.length > 0 ? sessions[0].id : undefined;
  const sessionCount = sessions?.length ?? 0;
  const sessionStatus = sessions?.[0]?.status;

  // Don't render until token is available
  if (!token) {
    return null;
  }

  return (
    <Layout title={project ? project.name : 'Workspace'}>
      <div style={{ 
        display: 'flex', 
        flexDirection: 'column', 
        gap: '1rem', 
        height: isFullscreen ? '100vh' : 'calc(100vh - 80px)',
        position: isFullscreen ? 'fixed' : 'relative',
        top: isFullscreen ? 0 : 'auto',
        left: isFullscreen ? 0 : 'auto',
        right: isFullscreen ? 0 : 'auto',
        bottom: isFullscreen ? 0 : 'auto',
        zIndex: isFullscreen ? 9999 : 'auto',
        background: isFullscreen ? '#f8fafc' : 'transparent',
        padding: isFullscreen ? '1rem' : 0
      }}>
        {/* Fullscreen Toggle Button */}
        {!isFullscreen && (
          <button
            onClick={() => setIsFullscreen(true)}
            style={{
              position: 'fixed',
              top: '100px',
              right: '20px',
              zIndex: 1000,
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              border: 'none',
              borderRadius: '12px',
              padding: '0.75rem',
              cursor: 'pointer',
              boxShadow: '0 4px 12px rgba(102, 126, 234, 0.4)',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              color: '#fff',
              fontSize: '0.9rem',
              fontWeight: 600,
              transition: 'all 0.2s'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'scale(1.05)';
              e.currentTarget.style.boxShadow = '0 6px 16px rgba(102, 126, 234, 0.5)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'scale(1)';
              e.currentTarget.style.boxShadow = '0 4px 12px rgba(102, 126, 234, 0.4)';
            }}
            title="Enter fullscreen mode"
          >
            <Maximize2 size={18} />
            Fullscreen
          </button>
        )}
        
        {isFullscreen && (
          <button
            onClick={() => setIsFullscreen(false)}
            style={{
              position: 'absolute',
              top: '20px',
              right: '20px',
              zIndex: 10000,
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              border: 'none',
              borderRadius: '12px',
              padding: '0.75rem',
              cursor: 'pointer',
              boxShadow: '0 4px 12px rgba(102, 126, 234, 0.4)',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              color: '#fff',
              fontSize: '0.9rem',
              fontWeight: 600,
              transition: 'all 0.2s'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'scale(1.05)';
              e.currentTarget.style.boxShadow = '0 6px 16px rgba(102, 126, 234, 0.5)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'scale(1)';
              e.currentTarget.style.boxShadow = '0 4px 12px rgba(102, 126, 234, 0.4)';
            }}
            title="Exit fullscreen mode"
          >
            <Minimize2 size={18} />
            Exit Fullscreen
          </button>
        )}
        
        {/* Enhanced Header Card */}
        {!isFullscreen && (
        <div style={{
          background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%)',
          borderRadius: '16px',
          padding: '1.5rem',
          border: '1px solid rgba(102, 126, 234, 0.2)',
          backdropFilter: 'blur(10px)'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
            <div style={{ flex: 1, minWidth: '280px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
                <div style={{
                  width: '42px',
                  height: '42px',
                  borderRadius: '10px',
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  boxShadow: '0 4px 12px rgba(102, 126, 234, 0.3)'
                }}>
                  <Box size={22} color="#fff" strokeWidth={2.5} />
                </div>
                <div>
                  <h1 style={{
                    margin: 0,
                    fontSize: '1.75rem',
                    fontWeight: 700,
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                    backgroundClip: 'text'
                  }}>
                    {project ? project.name : 'Loading...'}
                  </h1>
                  <p style={{ margin: '0.25rem 0 0 0', color: '#64748b', fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <Monitor size={14} />
                    {activeWorkspace ? activeWorkspace.name : 'Select workspace'}
                  </p>
                </div>
              </div>
            </div>

            <WorkspaceSelector
              workspaces={workspaces}
              isLoading={workspacesLoading}
              isError={workspacesError}
              activeWorkspaceId={activeWorkspaceId}
              onChange={setActiveWorkspaceId}
            />
          </div>

          {/* Status Cards */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
            gap: '0.75rem',
            marginTop: '1.25rem'
          }}>
            <StatusCard
              icon={<Cpu size={18} />}
              label="Status"
              value={activeWorkspace?.status ?? 'unknown'}
              color="#667eea"
            />
            <StatusCard
              icon={<Activity size={18} />}
              label="Sessions"
              value={sessionCount > 0 ? sessionCount.toString() : '0'}
              color="#0dbc79"
            />
            <StatusCard
              icon={<Zap size={18} />}
              label="State"
              value={sessionStatus ?? 'idle'}
              color="#f59e0b"
            />
            <StatusCard
              icon={<Play size={18} />}
              label="Engine"
              value="MuJoCo"
              color="#ec4899"
            />
          </div>
        </div>
        )}

        {/* Main Content Area */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: isSimExpanded ? '1fr' : 'minmax(0, 2fr) minmax(0, 1fr)',
          gap: '1rem',
          flex: 1,
          overflow: 'hidden',
          transition: 'grid-template-columns 0.3s ease'
        }}>
          {/* IDE Panel */}
          {!isSimExpanded && (
            <div style={{
              borderRadius: '16px',
              overflow: 'hidden',
              boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)',
              border: '1px solid #e2e8f0',
              background: '#fff'
            }}>
              <SessionIDE
                sessionId={activeSessionId ?? 'placeholder-session'}
                workspaceId={activeWorkspaceId ?? 'placeholder-workspace'}
                enableCollaboration={true}
                onRunSimulation={handleRunSimulation}
                onCodeChange={(code, filePath) => {
                  // Store the current code for simulation
                  setCurrentSimulationCode(code);
                  console.log('Code updated for simulation:', filePath);
                }}
              />
            </div>
          )}

          {/* Simulation Panel */}
          <div style={{
            borderRadius: '16px',
            overflow: 'hidden',
            boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)',
            border: '1px solid #e2e8f0',
            background: '#fff',
            display: 'flex',
            flexDirection: 'column'
          }}>
            {/* Simulation Header */}
            <div style={{
              padding: '1rem 1.25rem',
              borderBottom: '1px solid #e2e8f0',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              background: 'linear-gradient(135deg, #f8fafc 0%, #eef2ff 100%)'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <div style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '8px',
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  <Monitor size={16} color="#fff" />
                </div>
                <div>
                  <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: 600, color: '#1e293b' }}>
                    Simulation View
                  </h3>
                  <p style={{ margin: '0.125rem 0 0 0', fontSize: '0.75rem', color: '#64748b' }}>
                    Real-time visualization
                  </p>
                </div>
              </div>

              <button
                onClick={() => setIsSimExpanded(!isSimExpanded)}
                style={{
                  background: 'transparent',
                  border: '1px solid #cbd5e1',
                  borderRadius: '8px',
                  padding: '0.5rem',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  color: '#475569',
                  transition: 'all 0.2s'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = '#f1f5f9';
                  e.currentTarget.style.borderColor = '#94a3b8';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = 'transparent';
                  e.currentTarget.style.borderColor = '#cbd5e1';
                }}
                title={isSimExpanded ? 'Restore' : 'Expand'}
              >
                {isSimExpanded ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
              </button>
            </div>

            {/* Tabs */}
            <div style={{
              display: 'flex',
              gap: '0.25rem',
              padding: '0.75rem 1.25rem',
              borderBottom: '1px solid #e2e8f0',
              background: '#fafafa'
            }}>
              {(['simulation', 'metrics', 'logs'] as const).map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  style={{
                    background: activeTab === tab
                      ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
                      : 'transparent',
                    border: 'none',
                    borderRadius: '8px',
                    padding: '0.5rem 1rem',
                    color: activeTab === tab ? '#fff' : '#64748b',
                    cursor: 'pointer',
                    fontSize: '0.85rem',
                    fontWeight: activeTab === tab ? 600 : 500,
                    transition: 'all 0.2s',
                    textTransform: 'capitalize',
                    boxShadow: activeTab === tab ? '0 2px 8px rgba(102, 126, 234, 0.3)' : 'none'
                  }}
                  onMouseEnter={(e) => {
                    if (activeTab !== tab) {
                      e.currentTarget.style.background = '#f1f5f9';
                      e.currentTarget.style.color = '#1e293b';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (activeTab !== tab) {
                      e.currentTarget.style.background = 'transparent';
                      e.currentTarget.style.color = '#64748b';
                    }
                  }}
                >
                  {tab}
                </button>
              ))}
            </div>

            {/* Tab Content */}
            <div style={{ flex: 1, overflow: 'hidden' }}>
              {activeTab === 'simulation' && (
                <SimulationViewer
                  sessionId={activeSessionId ?? 'placeholder-session'}
                  engine="mujoco"
                  height="100%"
                  executionOutput={executionOutput}
                  onRunCode={async () => {
                    if (currentSimulationCode) {
                      await handleRunSimulation(currentSimulationCode);
                    } else {
                      console.warn('No code to run - please select a Python file in the IDE');
                    }
                  }}
                />
              )}
              {activeTab === 'metrics' && (
                <MetricsPanel />
              )}
              {activeTab === 'logs' && (
                <LogsPanel />
              )}
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
};

interface WorkspaceSelectorProps {
  workspaces: Workspace[] | undefined;
  isLoading: boolean;
  isError: boolean;
  activeWorkspaceId: string | null;
  onChange: (workspaceId: string | null) => void;
}

const WorkspaceSelector = ({ workspaces, isLoading, isError, activeWorkspaceId, onChange }: WorkspaceSelectorProps) => {
  if (isLoading) {
    return (
      <div style={{
        padding: '0.75rem 1rem',
        borderRadius: '10px',
        background: '#f1f5f9',
        color: '#64748b',
        fontSize: '0.85rem'
      }}>
        Loading workspaces…
      </div>
    );
  }

  if (isError) {
    return (
      <div style={{
        padding: '0.75rem 1rem',
        borderRadius: '10px',
        background: '#fee2e2',
        color: '#b91c1c',
        fontSize: '0.85rem'
      }}>
        Unable to load workspaces
      </div>
    );
  }

  if (!workspaces || workspaces.length === 0) {
    return (
      <div style={{
        padding: '0.75rem 1rem',
        borderRadius: '10px',
        background: '#fef3c7',
        color: '#92400e',
        fontSize: '0.85rem'
      }}>
        No workspaces yet
      </div>
    );
  }

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: '0.75rem',
      background: 'rgba(255, 255, 255, 0.8)',
      padding: '0.75rem 1.25rem',
      borderRadius: '12px',
      border: '1px solid rgba(102, 126, 234, 0.2)',
      backdropFilter: 'blur(10px)'
    }}>
      <span style={{ fontWeight: 600, color: '#475569', fontSize: '0.9rem' }}>Workspace:</span>
      <select
        value={activeWorkspaceId ?? ''}
        onChange={(event) => {
          const { value } = event.target;
          onChange(value || null);
        }}
        style={{
          borderRadius: '8px',
          border: '1px solid #cbd5e1',
          padding: '0.5rem 0.75rem',
          fontSize: '0.9rem',
          backgroundColor: '#ffffff',
          color: '#1e293b',
          fontWeight: 500,
          cursor: 'pointer',
          outline: 'none',
          transition: 'all 0.2s'
        }}
        onFocus={(e) => {
          e.currentTarget.style.borderColor = '#667eea';
          e.currentTarget.style.boxShadow = '0 0 0 3px rgba(102, 126, 234, 0.1)';
        }}
        onBlur={(e) => {
          e.currentTarget.style.borderColor = '#cbd5e1';
          e.currentTarget.style.boxShadow = 'none';
        }}
      >
        {workspaces.map(ws => (
          <option key={ws.id} value={ws.id}>
            {ws.name}
          </option>
        ))}
      </select>
    </div>
  );
};

interface StatusCardProps {
  icon: React.ReactNode;
  label: string;
  value: string;
  color: string;
}

const StatusCard = ({ icon, label, value, color }: StatusCardProps) => (
  <div style={{
    background: 'rgba(255, 255, 255, 0.6)',
    backdropFilter: 'blur(10px)',
    borderRadius: '12px',
    padding: '1rem',
    border: '1px solid rgba(226, 232, 240, 0.8)',
    transition: 'all 0.3s ease',
    cursor: 'default'
  }}
  onMouseEnter={(e) => {
    e.currentTarget.style.transform = 'translateY(-2px)';
    e.currentTarget.style.boxShadow = '0 8px 20px rgba(0, 0, 0, 0.1)';
  }}
  onMouseLeave={(e) => {
    e.currentTarget.style.transform = 'translateY(0)';
    e.currentTarget.style.boxShadow = 'none';
  }}
  >
    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
      <div style={{
        width: '36px',
        height: '36px',
        borderRadius: '8px',
        background: `linear-gradient(135deg, ${color}22, ${color}33)`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color
      }}>
        {icon}
      </div>
      <p style={{
        margin: 0,
        fontSize: '0.75rem',
        textTransform: 'uppercase',
        letterSpacing: '0.05em',
        color: '#64748b',
        fontWeight: 600
      }}>
        {label}
      </p>
    </div>
    <p style={{
      margin: 0,
      fontSize: '1.25rem',
      fontWeight: 700,
      color: '#1e293b',
      textTransform: 'capitalize'
    }}>
      {value}
    </p>
  </div>
);

const MetricsPanel = () => (
  <div style={{
    height: '100%',
    display: 'flex',
    flexDirection: 'column',
    padding: '1.5rem',
    background: 'linear-gradient(135deg, #f8fafc 0%, #eef2ff 100%)'
  }}>
    <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.1rem', fontWeight: 600, color: '#1e293b' }}>
      Performance Metrics
    </h3>
    <div style={{ display: 'grid', gap: '1rem', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))' }}>
      <MetricCard label="FPS" value="60" trend="+5%" trendUp={true} />
      <MetricCard label="Latency" value="12ms" trend="-3ms" trendUp={true} />
      <MetricCard label="Memory" value="1.2GB" trend="+0.1GB" trendUp={false} />
      <MetricCard label="CPU" value="45%" trend="-2%" trendUp={true} />
    </div>
    <div style={{
      marginTop: '1.5rem',
      padding: '1rem',
      background: 'rgba(102, 126, 234, 0.05)',
      borderRadius: '12px',
      border: '1px solid rgba(102, 126, 234, 0.1)'
    }}>
      <p style={{ margin: 0, fontSize: '0.85rem', color: '#64748b', lineHeight: 1.6 }}>
        📊 Real-time metrics will be displayed here once the monitoring agent is connected.
        Track simulation performance, resource usage, and execution statistics.
      </p>
    </div>
  </div>
);

interface MetricCardProps {
  label: string;
  value: string;
  trend: string;
  trendUp: boolean;
}

const MetricCard = ({ label, value, trend, trendUp }: MetricCardProps) => (
  <div style={{
    padding: '1rem',
    background: '#fff',
    borderRadius: '10px',
    border: '1px solid #e2e8f0',
    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.04)'
  }}>
    <p style={{ margin: '0 0 0.5rem 0', fontSize: '0.8rem', color: '#64748b', fontWeight: 500 }}>
      {label}
    </p>
    <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem' }}>
      <span style={{ fontSize: '1.5rem', fontWeight: 700, color: '#1e293b' }}>{value}</span>
      <span style={{
        fontSize: '0.75rem',
        fontWeight: 600,
        color: trendUp ? '#0dbc79' : '#ef4444'
      }}>
        {trend}
      </span>
    </div>
  </div>
);

const LogsPanel = () => (
  <div style={{
    height: '100%',
    display: 'flex',
    flexDirection: 'column',
    background: '#1e1e1e',
    padding: '1rem',
    fontFamily: 'monospace',
    fontSize: '0.85rem',
    color: '#d4d4d4',
    overflow: 'auto'
  }}>
    <div style={{ marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
      <span style={{ color: '#4ec9b0' }}>[09:45:23]</span>
      <span style={{ color: '#ce9178' }}>INFO</span>
      <span>Session initialized successfully</span>
    </div>
    <div style={{ marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
      <span style={{ color: '#4ec9b0' }}>[09:45:24]</span>
      <span style={{ color: '#ce9178' }}>INFO</span>
      <span>Connected to collaboration server</span>
    </div>
    <div style={{ marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
      <span style={{ color: '#4ec9b0' }}>[09:45:25]</span>
      <span style={{ color: '#dcdcaa' }}>WARN</span>
      <span>Simulation stream not available</span>
    </div>
    <div style={{ marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
      <span style={{ color: '#4ec9b0' }}>[09:45:26]</span>
      <span style={{ color: '#ce9178' }}>INFO</span>
      <span>Workspace ready for editing</span>
    </div>
    <div style={{
      marginTop: '1rem',
      padding: '0.75rem',
      background: '#252526',
      borderRadius: '8px',
      border: '1px solid #3e3e42'
    }}>
      <p style={{ margin: 0, fontSize: '0.8rem', color: '#858585' }}>
        📝 System logs and execution output will appear here in real-time.
      </p>
    </div>
  </div>
);

export default WorkspacePage;