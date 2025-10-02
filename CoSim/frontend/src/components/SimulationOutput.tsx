import React from 'react';
import { Terminal, XCircle, CheckCircle, Clock } from 'lucide-react';

interface SimulationOutputProps {
  stdout?: string;
  stderr?: string;
  error?: string;
  status?: 'idle' | 'running' | 'success' | 'error';
  executionTime?: number;
}

export const SimulationOutput: React.FC<SimulationOutputProps> = ({
  stdout,
  stderr,
  error,
  status = 'idle',
  executionTime
}) => {
  const getStatusIcon = () => {
    switch (status) {
      case 'running':
        return <Clock size={16} className="animate-spin" color="#3b82f6" />;
      case 'success':
        return <CheckCircle size={16} color="#0dbc79" />;
      case 'error':
        return <XCircle size={16} color="#ef4444" />;
      default:
        return <Terminal size={16} color="#94a3b8" />;
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case 'running': return '#3b82f6';
      case 'success': return '#0dbc79';
      case 'error': return '#ef4444';
      default: return '#94a3b8';
    }
  };

  const hasOutput = stdout || stderr || error;

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      background: '#1e1e1e',
      borderTop: '1px solid rgba(102, 126, 234, 0.2)',
    }}>
      {/* Header */}
      <div style={{
        padding: '0.75rem 1rem',
        background: 'linear-gradient(135deg, #1a1a1a 0%, #2d2d30 100%)',
        borderBottom: '1px solid rgba(102, 126, 234, 0.2)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          {getStatusIcon()}
          <span style={{ 
            fontSize: '0.85rem', 
            color: '#e2e8f0',
            fontWeight: 600 
          }}>
            Simulation Output
          </span>
          {executionTime !== undefined && (
            <span style={{ 
              fontSize: '0.75rem', 
              color: '#94a3b8',
              marginLeft: '0.5rem' 
            }}>
              ({executionTime.toFixed(2)}s)
            </span>
          )}
        </div>
        <div style={{
          padding: '0.25rem 0.5rem',
          borderRadius: '4px',
          fontSize: '0.7rem',
          fontWeight: 600,
          textTransform: 'uppercase',
          background: `${getStatusColor()}20`,
          color: getStatusColor(),
          border: `1px solid ${getStatusColor()}40`
        }}>
          {status}
        </div>
      </div>

      {/* Output Content */}
      <div style={{
        flex: 1,
        overflow: 'auto',
        padding: '1rem',
        fontFamily: 'Monaco, Menlo, "Ubuntu Mono", monospace',
        fontSize: '0.85rem',
        lineHeight: '1.5',
        color: '#d4d4d4'
      }}>
        {!hasOutput && status === 'idle' && (
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            height: '100%',
            color: '#64748b',
            textAlign: 'center',
            gap: '0.5rem'
          }}>
            <Terminal size={32} color="#64748b" />
            <p style={{ margin: 0 }}>No output yet</p>
            <p style={{ margin: 0, fontSize: '0.75rem' }}>
              Click Play to run your simulation code
            </p>
          </div>
        )}

        {status === 'running' && (
          <div style={{ color: '#3b82f6' }}>
            <span className="animate-pulse">⚡ Executing simulation...</span>
          </div>
        )}

        {stdout && (
          <div style={{ marginBottom: '1rem' }}>
            <div style={{
              fontSize: '0.75rem',
              color: '#0dbc79',
              marginBottom: '0.5rem',
              fontWeight: 600
            }}>
              STDOUT:
            </div>
            <pre style={{
              margin: 0,
              color: '#d4d4d4',
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word'
            }}>
              {stdout}
            </pre>
          </div>
        )}

        {stderr && (
          <div style={{ marginBottom: '1rem' }}>
            <div style={{
              fontSize: '0.75rem',
              color: '#ce9178',
              marginBottom: '0.5rem',
              fontWeight: 600
            }}>
              STDERR:
            </div>
            <pre style={{
              margin: 0,
              color: '#ce9178',
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word'
            }}>
              {stderr}
            </pre>
          </div>
        )}

        {error && (
          <div style={{ marginBottom: '1rem' }}>
            <div style={{
              fontSize: '0.75rem',
              color: '#ef4444',
              marginBottom: '0.5rem',
              fontWeight: 600
            }}>
              ERROR:
            </div>
            <pre style={{
              margin: 0,
              color: '#ef4444',
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word',
              background: '#2d1f1f',
              padding: '0.75rem',
              borderRadius: '4px',
              border: '1px solid #ef444440'
            }}>
              {error}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
};
