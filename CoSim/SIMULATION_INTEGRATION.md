# MuJoCo/PyBullet Simulation Integration

## Overview

Complete WebRTC-based simulation streaming integration for MuJoCo and PyBullet physics engines.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Browser Client                                  │
│  ┌────────────────┐        ┌──────────────────┐      ┌──────────────────┐ │
│  │ SimulationViewer│◄──────►│  useWebRTC Hook  │◄────►│  WebRTC PeerConn│ │
│  │   Component    │        │                  │      │                  │ │
│  └────────────────┘        └──────────────────┘      └──────────────────┘ │
│           │                         │                          │            │
└───────────┼─────────────────────────┼──────────────────────────┼────────────┘
            │                         │                          │
            │ HTTP API                │ WebSocket                │ WebRTC
            │ (Control)               │ (Signaling)              │ (Media)
            ▼                         ▼                          ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                            Cloud Services                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────┐   │
│  │ Simulation Agent │  │ WebRTC Signaling │  │                      │   │
│  │  (FastAPI)       │  │    Server        │  │                      │   │
│  │  - MuJoCo Env    │  │  (Node.js)       │  │                      │   │
│  │  - PyBullet Env  │  │  - Rooms         │  │                      │   │
│  │  - WebSocket     │  │  - ICE Exchange  │  │                      │   │
│  └──────────────────┘  └──────────────────┘  └──────────────────────┘   │
└───────────────────────────────────────────────────────────────────────────┘
```

## Components

### Backend

#### 1. Simulation Agent (`backend/src/co_sim/agents/simulation/`)

**Main Service** (`main.py`):
- FastAPI application
- REST API for simulation control
- WebSocket endpoint for frame streaming
- Manages simulation lifecycle

**Endpoints**:
```
POST   /simulations/create          - Create simulation instance
GET    /simulations/{id}/state      - Get current state
POST   /simulations/{id}/control    - Control (play/pause/reset/step)
POST   /simulations/{id}/camera     - Update camera (PyBullet)
DELETE /simulations/{id}            - Delete simulation
WS     /simulations/{id}/stream     - WebSocket frame stream
```

**MuJoCo Environment** (`mujoco_env.py`):
- `MuJoCoEnvironment`: Core MuJoCo simulation wrapper
- `MuJoCoStreamManager`: Manages streaming lifecycle
- Features:
  - XML model loading
  - Headless rendering (offscreen)
  - JPEG frame encoding
  - Target FPS control
  - State introspection

**PyBullet Environment** (`pybullet_env.py`):
- `PyBulletEnvironment`: Core PyBullet simulation wrapper
- `PyBulletStreamManager`: Manages streaming lifecycle
- Features:
  - URDF model loading
  - Camera control
  - Built-in model support
  - Hardware OpenGL rendering

#### 2. WebRTC Signaling Server (`webrtc-signaling/`)

**Node.js WebSocket Server** (`server.js`):
- Room-based signaling
- Peer-to-peer connection establishment
- ICE candidate exchange
- Health check endpoint

**Protocol**:
```javascript
// Join room
{ type: 'join', roomId: 'session-123', role: 'viewer' }

// WebRTC offer/answer/ICE
{ type: 'offer', targetId: 'uuid', offer: {...} }
{ type: 'answer', targetId: 'uuid', answer: {...} }
{ type: 'ice-candidate', targetId: 'uuid', candidate: {...} }
```

### Frontend

#### 1. useWebRTC Hook (`frontend/src/hooks/useWebRTC.ts`)

**Features**:
- WebRTC peer connection management
- Signaling protocol implementation
- Automatic reconnection
- Error handling

**Usage**:
```typescript
const { videoRef, isConnected, connectionState } = useWebRTC({
  signalingUrl: 'ws://localhost:3000',
  sessionId: 'session-123',
  role: 'viewer',
  onError: (error) => console.error(error),
});
```

#### 2. Simulation API Client (`frontend/src/api/simulation.ts`)

**Functions**:
```typescript
// Create simulation
await createSimulation({
  session_id: 'session-123',
  engine: 'mujoco',
  model_path: '/models/cartpole.xml',
  width: 640,
  height: 480,
  fps: 60,
});

// Control simulation
await controlSimulation('session-123', { action: 'reset' });
await controlSimulation('session-123', { action: 'step', actions: [1.0, 0.5] });

// WebSocket stream
const ws = connectSimulationStream('session-123', (frameData) => {
  // Render frame
});
```

#### 3. SimulationViewer Component (Enhanced)

**Integration Points**:
1. **WebRTC Video**: Displays remote stream from simulation agent
2. **Control API**: Sends play/pause/reset/step commands
3. **State Polling**: Updates frame count, time, simulation metrics
4. **Camera Control**: PyBullet camera manipulation

## Simulation Models

### MuJoCo Models (`simulation-models/*.xml`)

**cartpole.xml**:
```xml
<mujoco model="cartpole">
  <!-- Cart-pole inverted pendulum -->
  <worldbody>
    <body name="cart" pos="0 0 1">
      <joint name="slider" type="slide" axis="1 0 0" range="-2 2"/>
      <geom type="box" size="0.2 0.15 0.1" mass="1"/>
      <body name="pole" pos="0 0 0">
        <joint name="hinge" type="hinge" axis="0 1 0"/>
        <geom type="capsule" fromto="0 0 0 0 0 1" size="0.045" mass="0.1"/>
      </body>
    </body>
  </worldbody>
  <actuator>
    <motor joint="slider" gear="100" ctrlrange="-50 50"/>
  </actuator>
</mujoco>
```

**pendulum.xml**:
```xml
<mujoco model="pendulum">
  <!-- Simple pendulum with torque control -->
  <worldbody>
    <body name="anchor" pos="0 0 2">
      <body name="pole" pos="0 0 0">
        <joint name="hinge" type="hinge" axis="0 1 0"/>
        <geom type="capsule" fromto="0 0 0 0 0 -1" size="0.03" mass="0.5"/>
        <body name="bob" pos="0 0 -1">
          <geom type="sphere" size="0.12" mass="1"/>
        </body>
      </body>
    </body>
  </worldbody>
  <actuator>
    <motor joint="hinge" gear="10" ctrlrange="-5 5"/>
  </actuator>
</mujoco>
```

### PyBullet Models

**Built-in**:
- `plane.urdf` - Ground plane
- `r2d2.urdf` - Wheeled robot
- `cartpole.urdf` - Cart-pole system
- `humanoid.urdf` - Humanoid character
- `kuka_iiwa/model.urdf` - Robot arm

**Custom**: Generate with `pybullet_models.py`

## Usage Guide

### 1. Start Services

```bash
# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f simulation-agent
docker-compose logs -f webrtc-signaling
```

**Services**:
- Simulation Agent: `http://localhost:8005`
- WebRTC Signaling: `ws://localhost:3000`
- Health Check: `http://localhost:3001/health`

### 2. Create Simulation (API)

```bash
# Create MuJoCo simulation
curl -X POST http://localhost:8005/simulations/create \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-session",
    "engine": "mujoco",
    "model_path": "/models/cartpole.xml",
    "width": 640,
    "height": 480,
    "fps": 60,
    "headless": true
  }'

# Create PyBullet simulation
curl -X POST http://localhost:8005/simulations/create \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-session",
    "engine": "pybullet",
    "model_path": "r2d2.urdf",
    "width": 640,
    "height": 480,
    "fps": 60,
    "headless": true
  }'
```

### 3. Control Simulation

```bash
# Reset
curl -X POST http://localhost:8005/simulations/test-session/control \
  -H "Content-Type: application/json" \
  -d '{"action": "reset"}'

# Step with actions
curl -X POST http://localhost:8005/simulations/test-session/control \
  -H "Content-Type: application/json" \
  -d '{"action": "step", "actions": [1.0, 0.5]}'
```

### 4. Frontend Integration

```typescript
import { useWebRTC } from '@/hooks/useWebRTC';
import { createSimulation, controlSimulation } from '@/api/simulation';

function MyComponent() {
  const sessionId = 'my-session';
  
  // Setup WebRTC connection
  const { videoRef, isConnected } = useWebRTC({
    signalingUrl: import.meta.env.VITE_WEBRTC_SIGNALING_URL,
    sessionId: sessionId,
    role: 'viewer',
  });
  
  // Create simulation on mount
  useEffect(() => {
    createSimulation({
      session_id: sessionId,
      engine: 'mujoco',
      model_path: '/models/cartpole.xml',
    });
  }, []);
  
  // Control handlers
  const handlePlay = () => controlSimulation(sessionId, { action: 'play' });
  const handleReset = () => controlSimulation(sessionId, { action: 'reset' });
  
  return (
    <div>
      <video ref={videoRef} autoPlay playsInline />
      <button onClick={handlePlay}>Play</button>
      <button onClick={handleReset}>Reset</button>
    </div>
  );
}
```

## GPU Support

### Enable NVIDIA GPU

**Requirements**:
- NVIDIA GPU
- NVIDIA Docker runtime
- nvidia-docker2

**Docker Compose** (uncomment in `docker-compose.yml`):
```yaml
simulation-agent:
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
```

**Test GPU**:
```bash
docker-compose exec simulation-agent nvidia-smi
```

## Performance Tuning

### MuJoCo

**CPU Mode** (fast boot, prototyping):
```python
env = MuJoCoEnvironment(
    model_path="/models/cartpole.xml",
    headless=True,  # Offscreen rendering
    fps=30,         # Lower FPS for CPU
)
```

**GPU Mode** (RL training):
```python
# Use MJX (GPU-accelerated) when available
import mujoco.mjx as mjx
# ... MJX parallel environments
```

### PyBullet

**Rendering Modes**:
```python
# Fast (DIRECT mode)
env = PyBulletEnvironment(urdf_path="r2d2.urdf", headless=True)

# Visual (GUI mode)
env = PyBulletEnvironment(urdf_path="r2d2.urdf", headless=False)
```

**Renderer Selection**:
- `ER_TINY_RENDERER`: CPU-only (headless)
- `ER_BULLET_HARDWARE_OPENGL`: Hardware-accelerated

## Troubleshooting

### Connection Issues

**Signaling fails**:
```bash
# Check signaling server
curl http://localhost:3001/health

# Check WebSocket
wscat -c ws://localhost:3000
```

**WebRTC fails**:
- Check STUN/TURN servers
- Verify firewall rules (UDP ports)
- Check browser console for ICE errors

### Simulation Issues

**MuJoCo not found**:
```bash
# Install in Docker
docker-compose exec simulation-agent pip install mujoco
```

**PyBullet rendering black screen**:
- Check OpenGL support in container
- Try `ER_TINY_RENDERER` for headless

**Model load errors**:
```bash
# Verify model path
docker-compose exec simulation-agent ls /models

# Test model
docker-compose exec simulation-agent python -c \
  "import mujoco; m = mujoco.MjModel.from_xml_path('/models/cartpole.xml'); print('OK')"
```

### Performance Issues

**Low FPS**:
- Reduce render resolution (640x480 → 320x240)
- Lower target FPS (60 → 30)
- Enable GPU if available

**High latency**:
- Use WebRTC data channels instead of WebSocket
- Optimize frame encoding (JPEG quality)
- Use local STUN/TURN servers

## Next Steps

1. **Implement in Workspace.tsx**: Replace placeholder with real WebRTC
2. **Add Session Integration**: Wire up session orchestrator
3. **RL Training**: Add parallel environment support
4. **SLAM Integration**: Add dataset loaders and trajectory visualization
5. **Metrics Dashboard**: Real-time performance monitoring

## Resources

- **MuJoCo**: https://mujoco.readthedocs.io/
- **PyBullet**: https://pybullet.org/wordpress/
- **WebRTC**: https://webrtc.org/getting-started/overview
- **Models**: `simulation-models/README.md`
