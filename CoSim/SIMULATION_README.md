# 🤖 CoSim Simulation System

WebRTC-based real-time physics simulation streaming for robotics development.

## Overview

Stream **MuJoCo** and **PyBullet** simulations to your browser with low-latency WebRTC, giving you the power of cloud-based physics engines with local responsiveness.

### Key Features

- 🎮 **Dual Engine Support**: MuJoCo 3 + PyBullet
- 📹 **WebRTC Streaming**: Sub-100ms latency
- 🎛️ **Full Control API**: Play, pause, reset, step, camera control
- 🐳 **Docker Ready**: One-command deployment
- 🚀 **GPU Accelerated**: Optional NVIDIA GPU support
- 🔄 **Real-time Collaboration**: Multi-user simulation viewing
- 📊 **State Introspection**: Live physics data streams

## Quick Start

### 1. Start Services

```bash
docker-compose up -d
```

That's it! Services running:
- Simulation Agent: http://localhost:8005
- WebRTC Signaling: ws://localhost:3000
- Frontend: http://localhost:5173

### 2. Create Your First Simulation

**MuJoCo Cart-Pole**:
```bash
curl -X POST http://localhost:8005/simulations/create \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "my-sim",
    "engine": "mujoco",
    "model_path": "/models/cartpole.xml",
    "width": 640,
    "height": 480,
    "fps": 60
  }'
```

**PyBullet R2D2**:
```bash
curl -X POST http://localhost:8005/simulations/create \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "my-sim",
    "engine": "pybullet",
    "model_path": "r2d2.urdf"
  }'
```

### 3. View in Browser

Open your workspace at http://localhost:5173 and see your simulation streaming live!

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                        Browser                                │
│  ┌──────────────┐         ┌─────────────────────────┐       │
│  │ React App    │◄───────►│  WebRTC Video Stream   │       │
│  │ + useWebRTC  │         │  (H.264 @ 60 FPS)      │       │
│  └──────────────┘         └─────────────────────────┘       │
│         │                            │                        │
└─────────┼────────────────────────────┼────────────────────────┘
          │ HTTP/WS                    │ WebRTC (SRTP)
          ▼                            ▼
┌──────────────────────────────────────────────────────────────┐
│                     Cloud Services                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Simulation   │  │   WebRTC     │  │   STUN/TURN      │  │
│  │   Agent      │  │  Signaling   │  │   Servers        │  │
│  │  (FastAPI)   │  │  (Node.js)   │  │                  │  │
│  │              │  │              │  │                  │  │
│  │ ┌──────────┐ │  │ • Rooms     │  │ NAT Traversal   │  │
│  │ │ MuJoCo   │ │  │ • ICE       │  │                  │  │
│  │ │ PyBullet │ │  │ • Offer/Ans │  │                  │  │
│  │ └──────────┘ │  └──────────────┘  └──────────────────┘  │
│  └──────────────┘                                           │
└──────────────────────────────────────────────────────────────┘
```

## Supported Engines

### MuJoCo 3

**Best for**: Robotics, manipulation, contact-rich tasks

**Features**:
- XML model format
- High-fidelity contact dynamics
- Fast inverse kinematics
- MJX GPU acceleration (coming soon)

**Example Models**:
- `cartpole.xml` - Inverted pendulum
- `pendulum.xml` - Simple pendulum

### PyBullet

**Best for**: Locomotion, multi-body dynamics, URDF compatibility

**Features**:
- URDF model format
- Extensive built-in library
- Hardware OpenGL rendering
- Easy camera control

**Example Models**:
- `r2d2.urdf` - Wheeled robot
- `humanoid.urdf` - Bipedal walker
- `kuka_iiwa/model.urdf` - Robot arm

## API Reference

### Create Simulation

```http
POST /simulations/create
Content-Type: application/json

{
  "session_id": "unique-id",
  "engine": "mujoco" | "pybullet",
  "model_path": "/models/cartpole.xml",
  "width": 640,
  "height": 480,
  "fps": 60,
  "headless": true
}
```

### Control Simulation

```http
POST /simulations/{session_id}/control
Content-Type: application/json

{
  "action": "play" | "pause" | "reset" | "step",
  "actions": [1.0, 0.5]  // Optional control inputs
}
```

### Get State

```http
GET /simulations/{session_id}/state
```

Response:
```json
{
  "frame": 1234,
  "time": 20.567,
  "is_running": true,
  "qpos": [0.1, 0.2, ...],
  "qvel": [0.01, 0.02, ...]
}
```

### WebSocket Stream

```javascript
const ws = new WebSocket('ws://localhost:8005/simulations/my-sim/stream');
ws.binaryType = 'arraybuffer';

ws.onmessage = (event) => {
  const frameData = event.data; // JPEG bytes
  // Render frame
};
```

## React Integration

### Using the Hook

```typescript
import { useWebRTC } from '@/hooks/useWebRTC';

function SimViewer({ sessionId }) {
  const { videoRef, isConnected, connectionState } = useWebRTC({
    signalingUrl: import.meta.env.VITE_WEBRTC_SIGNALING_URL,
    sessionId,
    role: 'viewer',
  });

  return (
    <div>
      <video ref={videoRef} autoPlay playsInline />
      <p>Status: {isConnected ? '✅ Connected' : '🔄 Connecting...'}</p>
    </div>
  );
}
```

### Control API

```typescript
import { createSimulation, controlSimulation } from '@/api/simulation';

// Create
await createSimulation({
  session_id: 'my-sim',
  engine: 'mujoco',
  model_path: '/models/cartpole.xml',
});

// Control
await controlSimulation('my-sim', { action: 'reset' });
await controlSimulation('my-sim', { action: 'step', actions: [1.0] });
```

## Available Models

### MuJoCo (`/models/*.xml`)

| Model | Description | DOFs | Actuators |
|-------|-------------|------|-----------|
| `cartpole.xml` | Cart-pole (inverted pendulum) | 2 | 1 motor |
| `pendulum.xml` | Simple pendulum | 1 | 1 motor |

### PyBullet (built-in)

| Model | Description | Type |
|-------|-------------|------|
| `r2d2.urdf` | Wheeled robot | Mobile |
| `cartpole.urdf` | Cart-pole | Control |
| `humanoid.urdf` | Humanoid character | Locomotion |
| `kuka_iiwa/model.urdf` | 7-DOF robot arm | Manipulation |
| `quadruped/quadruped.urdf` | Quadruped robot | Locomotion |

## GPU Acceleration

### Enable NVIDIA GPU

**Requirements**:
- NVIDIA GPU (Tesla, RTX, etc.)
- nvidia-docker2
- CUDA drivers

**Enable in docker-compose.yml**:
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

**Test**:
```bash
docker-compose exec simulation-agent nvidia-smi
```

**Performance Boost**:
- 5-10x faster rendering
- Parallel environment support (RL)
- MJX GPU acceleration (future)

## Configuration

### Frontend `.env`

```env
VITE_API_BASE_URL=/api
VITE_COLLAB_WS_URL=ws://localhost:1234
VITE_WEBRTC_SIGNALING_URL=ws://localhost:3000
VITE_SIMULATION_API_URL=http://localhost:8005
```

### Simulation Agent

| Variable | Default | Description |
|----------|---------|-------------|
| `COSIM_PORT` | 8005 | API port |
| `COSIM_DEBUG` | false | Debug logging |

### WebRTC Signaling

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | 3000 | WebSocket port |

## Performance Tuning

### CPU Mode (Fast Boot)
```json
{
  "fps": 30,
  "width": 320,
  "height": 240,
  "headless": true
}
```

**Best for**: Prototyping, SLAM, CPU-only instances

### GPU Mode (High Quality)
```json
{
  "fps": 60,
  "width": 1280,
  "height": 720,
  "headless": true
}
```

**Best for**: RL training, visual tasks, demos

## Use Cases

### 1. Reinforcement Learning

```python
# Parallel environment training
for episode in range(1000):
    obs = env.reset()
    for step in range(max_steps):
        action = policy(obs)
        obs, reward, done = env.step(action)
        # Save checkpoint every 100 episodes
```

### 2. SLAM Development

```python
# Load SLAM dataset
env = create_simulation(dataset='kitti-00')
for frame in dataset:
    env.step()
    trajectory = env.get_trajectory()
    metrics = compute_ate_rpe(trajectory, ground_truth)
```

### 3. Robot Testing

```python
# Test manipulation task
env = create_simulation(model='kuka_iiwa')
for waypoint in trajectory:
    env.set_joint_positions(waypoint)
    if detect_collision():
        break
```

## Troubleshooting

### Connection Issues

**Problem**: WebRTC connection fails

**Solutions**:
1. Check signaling server: `curl http://localhost:3001/health`
2. Verify firewall allows UDP (WebRTC)
3. Use TURN server for strict NAT
4. Check browser console for ICE errors

### Rendering Issues

**Problem**: Black screen or slow rendering

**Solutions**:
1. Lower FPS: 60 → 30
2. Reduce resolution: 640x480 → 320x240
3. Use `ER_TINY_RENDERER` for PyBullet headless
4. Enable GPU if available

### Model Loading Errors

**Problem**: "Model not found" or load fails

**Solutions**:
1. Check model path: `docker-compose exec simulation-agent ls /models`
2. Test model: `python -c "import mujoco; mujoco.MjModel.from_xml_path('...')"`
3. Verify URDF syntax for PyBullet
4. Check file permissions

## Documentation

| Guide | Description |
|-------|-------------|
| [SIMULATION_INTEGRATION.md](./SIMULATION_INTEGRATION.md) | Complete architecture & API |
| [SIMULATION_QUICKSTART.md](./SIMULATION_QUICKSTART.md) | 5-minute tutorial |
| [simulation-models/README.md](./simulation-models/README.md) | Model reference |
| [webrtc-signaling/README.md](./webrtc-signaling/README.md) | Signaling protocol |

## Resources

- **MuJoCo**: https://mujoco.readthedocs.io/
- **PyBullet**: https://pybullet.org/wordpress/
- **WebRTC**: https://webrtc.org/
- **Model Zoo**: https://github.com/google-deepmind/mujoco_menagerie

## License

MIT - See LICENSE file

## Contributing

We welcome contributions! Areas of interest:
- New simulation models
- Performance optimizations
- Additional physics engines
- Testing and documentation

---

**Built with** ❤️ **for robotics developers**
