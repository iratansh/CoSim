# Quick Start: MuJoCo/PyBullet Simulation

Get started with MuJoCo and PyBullet simulations in 5 minutes!

## Prerequisites

- Docker & Docker Compose
- (Optional) NVIDIA GPU + nvidia-docker for GPU acceleration

## 1. Start Services

```bash
# Start all services including simulation-agent and webrtc-signaling
docker-compose up -d

# Check that simulation agent is running
curl http://localhost:8005/health
# Should return: {"status":"healthy","mujoco_available":true,"pybullet_available":true}

# Check WebRTC signaling server
curl http://localhost:3001/health
# Should return: {"status":"healthy","connections":0,"rooms":0}
```

## 2. Test MuJoCo Simulation (CLI)

```bash
# Create a MuJoCo cartpole simulation
curl -X POST http://localhost:8005/simulations/create \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "quickstart-mujoco",
    "engine": "mujoco",
    "model_path": "/models/cartpole.xml",
    "width": 640,
    "height": 480,
    "fps": 60,
    "headless": true
  }'

# Check simulation state
curl http://localhost:8005/simulations/quickstart-mujoco/state

# Reset simulation
curl -X POST http://localhost:8005/simulations/quickstart-mujoco/control \
  -H "Content-Type: application/json" \
  -d '{"action": "reset"}'

# Step simulation with control action (push cart)
curl -X POST http://localhost:8005/simulations/quickstart-mujoco/control \
  -H "Content-Type: application/json" \
  -d '{"action": "step", "actions": [10.0]}'

# Clean up
curl -X DELETE http://localhost:8005/simulations/quickstart-mujoco
```

## 3. Test PyBullet Simulation (CLI)

```bash
# Create a PyBullet simulation with R2D2 robot
curl -X POST http://localhost:8005/simulations/create \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "quickstart-pybullet",
    "engine": "pybullet",
    "model_path": "r2d2.urdf",
    "width": 640,
    "height": 480,
    "fps": 60,
    "headless": true
  }'

# Get state
curl http://localhost:8005/simulations/quickstart-pybullet/state

# Update camera position
curl -X POST http://localhost:8005/simulations/quickstart-pybullet/camera \
  -H "Content-Type: application/json" \
  -d '{
    "distance": 3.0,
    "yaw": 45.0,
    "pitch": -30.0,
    "target": [0, 0, 0]
  }'

# Clean up
curl -X DELETE http://localhost:8005/simulations/quickstart-pybullet
```

## 4. Test WebSocket Frame Streaming (Python)

```python
import asyncio
import websockets
import base64
from PIL import Image
import io

async def receive_frames():
    uri = "ws://localhost:8005/simulations/quickstart-mujoco/stream"
    
    async with websockets.connect(uri) as websocket:
        print("✅ Connected to simulation stream")
        
        # Receive frames
        frame_count = 0
        while frame_count < 100:  # Receive 100 frames
            try:
                # Receive frame data
                frame_data = await websocket.recv()
                
                # frame_data is JPEG bytes
                image = Image.open(io.BytesIO(frame_data))
                
                # Save first frame
                if frame_count == 0:
                    image.save('first_frame.jpg')
                    print(f"📸 Saved first frame: {image.size}")
                
                frame_count += 1
                if frame_count % 10 == 0:
                    print(f"📦 Received {frame_count} frames")
                    
            except Exception as e:
                print(f"❌ Error: {e}")
                break
        
        print(f"✅ Received total of {frame_count} frames")

# Run
asyncio.run(receive_frames())
```

**Save as `test_stream.py` and run**:
```bash
# First, create simulation (see step 2)
# Then run streaming test
python test_stream.py
```

## 5. Test WebRTC Connection (JavaScript)

Create `test_webrtc.html`:

```html
<!DOCTYPE html>
<html>
<head>
  <title>WebRTC Simulation Test</title>
</head>
<body>
  <h1>WebRTC Simulation Stream</h1>
  <video id="video" autoplay playsinline style="width: 640px; height: 480px; background: #000;"></video>
  <div id="status">Connecting...</div>

  <script>
    const signalingUrl = 'ws://localhost:3000';
    const sessionId = 'quickstart-webrtc';
    let ws, pc, clientId;

    // Connect to signaling server
    ws = new WebSocket(signalingUrl);

    ws.onopen = () => {
      console.log('✅ Connected to signaling server');
    };

    ws.onmessage = async (event) => {
      const message = JSON.parse(event.data);

      switch (message.type) {
        case 'welcome':
          clientId = message.clientId;
          console.log('👋 Client ID:', clientId);
          // Join room
          ws.send(JSON.stringify({
            type: 'join',
            roomId: sessionId,
            role: 'viewer'
          }));
          break;

        case 'joined':
          console.log('✅ Joined room');
          document.getElementById('status').textContent = 'Joined room, waiting for stream...';
          break;

        case 'offer':
          console.log('📨 Received offer');
          await handleOffer(message.fromId, message.offer);
          break;

        case 'ice-candidate':
          console.log('🧊 Received ICE candidate');
          if (pc) {
            await pc.addIceCandidate(new RTCIceCandidate(message.candidate));
          }
          break;
      }
    };

    async function handleOffer(fromId, offer) {
      pc = new RTCPeerConnection({
        iceServers: [{ urls: 'stun:stun.l.google.com:19302' }]
      });

      pc.ontrack = (event) => {
        console.log('🎥 Received video track');
        document.getElementById('video').srcObject = event.streams[0];
        document.getElementById('status').textContent = '✅ Streaming!';
      };

      pc.onicecandidate = (event) => {
        if (event.candidate) {
          ws.send(JSON.stringify({
            type: 'ice-candidate',
            targetId: fromId,
            candidate: event.candidate
          }));
        }
      };

      await pc.setRemoteDescription(new RTCSessionDescription(offer));
      const answer = await pc.createAnswer();
      await pc.setLocalDescription(answer);

      ws.send(JSON.stringify({
        type: 'answer',
        targetId: fromId,
        answer: pc.localDescription
      }));
    }
  </script>
</body>
</html>
```

**Open in browser**: `file:///path/to/test_webrtc.html`

## 6. Use in Frontend (React)

```typescript
import { useWebRTC } from '@/hooks/useWebRTC';
import { createSimulation } from '@/api/simulation';

function SimulationDemo() {
  const sessionId = 'my-simulation';

  // Setup WebRTC
  const { videoRef, isConnected } = useWebRTC({
    signalingUrl: 'ws://localhost:3000',
    sessionId,
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

  return (
    <div>
      <h1>Simulation Stream</h1>
      <video ref={videoRef} autoPlay playsInline />
      <p>Status: {isConnected ? 'Connected' : 'Connecting...'}</p>
    </div>
  );
}
```

## 7. Available Models

### MuJoCo (in `/models`)
- `cartpole.xml` - Cart-pole inverted pendulum
- `pendulum.xml` - Simple pendulum with torque control

### PyBullet (built-in)
- `r2d2.urdf` - Wheeled robot
- `cartpole.urdf` - Cart-pole
- `humanoid.urdf` - Humanoid character
- `kuka_iiwa/model.urdf` - Robot arm

## 8. GPU Acceleration (Optional)

Uncomment GPU settings in `docker-compose.yml`:

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

Restart:
```bash
docker-compose down
docker-compose up -d
```

Test GPU:
```bash
docker-compose exec simulation-agent nvidia-smi
```

## Troubleshooting

### Simulation agent not starting
```bash
# Check logs
docker-compose logs simulation-agent

# Common issue: MuJoCo/PyBullet not installed
docker-compose exec simulation-agent pip install mujoco pybullet
```

### WebRTC connection fails
```bash
# Check signaling server
curl http://localhost:3001/health

# Check browser console for errors
# Most common: CORS or firewall blocking WebSocket
```

### No video stream
```bash
# Ensure simulation is created first
curl http://localhost:8005/simulations/{session_id}/state

# Check WebSocket connection
# Browser DevTools > Network > WS tab
```

## Next Steps

- Read full documentation: `SIMULATION_INTEGRATION.md`
- Add custom models: `simulation-models/README.md`
- Integrate into workspace: Update `SimulationViewer.tsx`
- Enable GPU: See Docker Compose GPU configuration

## Resources

- **API Docs**: http://localhost:8005/docs (when running)
- **MuJoCo Docs**: https://mujoco.readthedocs.io/
- **PyBullet Docs**: https://pybullet.org/wordpress/
- **WebRTC Guide**: https://webrtc.org/getting-started/overview
