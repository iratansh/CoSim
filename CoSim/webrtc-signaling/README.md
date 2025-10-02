# WebRTC Signaling Server

WebSocket-based signaling server for establishing WebRTC connections between browser clients and simulation pods.

## Features

- **Room-based signaling**: Multiple clients can join simulation rooms
- **Role-based connections**: Supports 'viewer' and 'broadcaster' roles
- **ICE candidate exchange**: Full WebRTC negotiation support
- **Health monitoring**: Built-in health check endpoint

## Message Protocol

### Client → Server

#### Join Room
```json
{
  "type": "join",
  "roomId": "session-123",
  "role": "viewer"
}
```

#### WebRTC Offer
```json
{
  "type": "offer",
  "targetId": "client-uuid",
  "offer": {
    "type": "offer",
    "sdp": "..."
  }
}
```

#### WebRTC Answer
```json
{
  "type": "answer",
  "targetId": "client-uuid",
  "answer": {
    "type": "answer",
    "sdp": "..."
  }
}
```

#### ICE Candidate
```json
{
  "type": "ice-candidate",
  "targetId": "client-uuid",
  "candidate": {
    "candidate": "...",
    "sdpMid": "...",
    "sdpMLineIndex": 0
  }
}
```

#### Leave Room
```json
{
  "type": "leave"
}
```

### Server → Client

#### Welcome
```json
{
  "type": "welcome",
  "clientId": "uuid"
}
```

#### Joined Room
```json
{
  "type": "joined",
  "roomId": "session-123",
  "role": "viewer",
  "participants": [
    { "id": "uuid", "role": "broadcaster" }
  ]
}
```

#### Peer Joined
```json
{
  "type": "peer-joined",
  "peerId": "uuid",
  "role": "broadcaster"
}
```

#### Peer Left
```json
{
  "type": "peer-left",
  "peerId": "uuid"
}
```

#### Offer Received
```json
{
  "type": "offer",
  "fromId": "uuid",
  "offer": { ... }
}
```

#### Answer Received
```json
{
  "type": "answer",
  "fromId": "uuid",
  "answer": { ... }
}
```

#### ICE Candidate Received
```json
{
  "type": "ice-candidate",
  "fromId": "uuid",
  "candidate": { ... }
}
```

## Usage

### Development
```bash
npm install
npm run dev
```

### Production
```bash
npm install --production
npm start
```

### Docker
```bash
docker build -t cosim-webrtc-signaling .
docker run -p 3000:3000 -p 3001:3001 cosim-webrtc-signaling
```

## Environment Variables

- `PORT`: WebSocket server port (default: 3000)

## Health Check

Health check endpoint available at `http://localhost:3001/health`

Response:
```json
{
  "status": "healthy",
  "connections": 5,
  "rooms": 2
}
```
