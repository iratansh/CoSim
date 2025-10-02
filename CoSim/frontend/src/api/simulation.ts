/**
 * Simulation API Client
 * 
 * Client for interacting with the simulation agent API
 */

const SIMULATION_API_URL = import.meta.env.VITE_SIMULATION_API_URL || 'http://localhost:8005';

export interface CreateSimulationRequest {
  session_id: string;
  engine: 'mujoco' | 'pybullet';
  model_path?: string;
  width?: number;
  height?: number;
  fps?: number;
  headless?: boolean;
}

export interface SimulationControlRequest {
  action: 'play' | 'pause' | 'reset' | 'step';
  actions?: number[];
}

export interface CameraControlRequest {
  distance?: number;
  yaw?: number;
  pitch?: number;
  target?: number[];
}

export interface SimulationState {
  frame: number;
  time: number;
  is_running: boolean;
  [key: string]: any;
}

/**
 * Create a new simulation instance
 */
export async function createSimulation(request: CreateSimulationRequest): Promise<any> {
  const response = await fetch(`${SIMULATION_API_URL}/simulations/create`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to create simulation' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

/**
 * Get simulation state
 */
export async function getSimulationState(sessionId: string): Promise<SimulationState> {
  const response = await fetch(`${SIMULATION_API_URL}/simulations/${sessionId}/state`);

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to get simulation state' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

/**
 * Control simulation (play, pause, reset, step)
 */
export async function controlSimulation(
  sessionId: string,
  control: SimulationControlRequest
): Promise<any> {
  const response = await fetch(`${SIMULATION_API_URL}/simulations/${sessionId}/control`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(control),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to control simulation' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

/**
 * Update camera position (PyBullet only)
 */
export async function setCameraPosition(
  sessionId: string,
  camera: CameraControlRequest
): Promise<any> {
  const response = await fetch(`${SIMULATION_API_URL}/simulations/${sessionId}/camera`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(camera),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to set camera' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

/**
 * Delete simulation instance
 */
export async function deleteSimulation(sessionId: string): Promise<any> {
  const response = await fetch(`${SIMULATION_API_URL}/simulations/${sessionId}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to delete simulation' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

/**
 * Connect to simulation WebSocket stream
 */
export function connectSimulationStream(
  sessionId: string,
  onFrame: (frameData: ArrayBuffer) => void,
  onError?: (error: Error) => void
): WebSocket {
  const ws = new WebSocket(`${SIMULATION_API_URL.replace('http', 'ws')}/simulations/${sessionId}/stream`);

  ws.binaryType = 'arraybuffer';

  ws.onopen = () => {
    console.log('✅ Connected to simulation stream');
  };

  ws.onmessage = (event) => {
    if (event.data instanceof ArrayBuffer) {
      onFrame(event.data);
    }
  };

  ws.onerror = (error) => {
    console.error('❌ Simulation stream error:', error);
    onError?.(new Error('Simulation stream connection failed'));
  };

  ws.onclose = () => {
    console.log('❌ Simulation stream disconnected');
  };

  return ws;
}

/**
 * Send control command via WebSocket
 */
export function sendStreamControl(ws: WebSocket, command: string) {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send(command);
  } else {
    console.error('❌ WebSocket not ready');
  }
}
