/**
 * WebRTC Signaling Server for CoSim
 * 
 * Facilitates WebRTC peer connection establishment between browser clients
 * and simulation pods for low-latency video streaming.
 */

const WebSocket = require('ws');
const { v4: uuidv4 } = require('uuid');

const PORT = process.env.PORT || 3000;

// Store active connections and rooms
const rooms = new Map(); // roomId -> Set of clients
const clients = new Map(); // ws -> { id, roomId, role }

// Create WebSocket server
const wss = new WebSocket.Server({ port: PORT });

console.log(`🚀 WebRTC Signaling Server started on port ${PORT}`);

wss.on('connection', (ws) => {
  const clientId = uuidv4();
  
  console.log(`✅ Client connected: ${clientId}`);
  
  // Initialize client metadata
  clients.set(ws, {
    id: clientId,
    roomId: null,
    role: null, // 'viewer' or 'broadcaster'
  });
  
  // Send welcome message with client ID
  send(ws, {
    type: 'welcome',
    clientId: clientId,
  });
  
  ws.on('message', (data) => {
    try {
      const message = JSON.parse(data);
      handleMessage(ws, message);
    } catch (error) {
      console.error(`❌ Failed to parse message: ${error.message}`);
      send(ws, {
        type: 'error',
        error: 'Invalid JSON message',
      });
    }
  });
  
  ws.on('close', () => {
    handleDisconnect(ws);
  });
  
  ws.on('error', (error) => {
    console.error(`❌ WebSocket error for ${clientId}:`, error.message);
  });
});

/**
 * Handle incoming messages from clients
 */
function handleMessage(ws, message) {
  const client = clients.get(ws);
  
  console.log(`📨 Message from ${client.id}: ${message.type}`);
  
  switch (message.type) {
    case 'join':
      handleJoin(ws, message);
      break;
      
    case 'offer':
      handleOffer(ws, message);
      break;
      
    case 'answer':
      handleAnswer(ws, message);
      break;
      
    case 'ice-candidate':
      handleIceCandidate(ws, message);
      break;
      
    case 'leave':
      handleLeave(ws);
      break;
      
    default:
      console.warn(`⚠️  Unknown message type: ${message.type}`);
      send(ws, {
        type: 'error',
        error: `Unknown message type: ${message.type}`,
      });
  }
}

/**
 * Handle client joining a room
 */
function handleJoin(ws, message) {
  const client = clients.get(ws);
  const { roomId, role } = message;
  
  if (!roomId || !role) {
    send(ws, {
      type: 'error',
      error: 'roomId and role are required',
    });
    return;
  }
  
  // Leave current room if any
  if (client.roomId) {
    handleLeave(ws);
  }
  
  // Join new room
  client.roomId = roomId;
  client.role = role;
  
  if (!rooms.has(roomId)) {
    rooms.set(roomId, new Set());
  }
  
  rooms.get(roomId).add(ws);
  
  console.log(`👥 Client ${client.id} joined room ${roomId} as ${role}`);
  
  // Notify client
  send(ws, {
    type: 'joined',
    roomId: roomId,
    role: role,
    participants: Array.from(rooms.get(roomId)).map(c => ({
      id: clients.get(c).id,
      role: clients.get(c).role,
    })),
  });
  
  // Notify other participants
  broadcast(ws, roomId, {
    type: 'peer-joined',
    peerId: client.id,
    role: role,
  });
}

/**
 * Handle WebRTC offer
 */
function handleOffer(ws, message) {
  const client = clients.get(ws);
  const { targetId, offer } = message;
  
  if (!targetId || !offer) {
    send(ws, {
      type: 'error',
      error: 'targetId and offer are required',
    });
    return;
  }
  
  // Find target client
  const targetWs = findClientById(targetId);
  
  if (!targetWs) {
    send(ws, {
      type: 'error',
      error: `Target client ${targetId} not found`,
    });
    return;
  }
  
  // Forward offer to target
  send(targetWs, {
    type: 'offer',
    fromId: client.id,
    offer: offer,
  });
  
  console.log(`🔄 Forwarded offer from ${client.id} to ${targetId}`);
}

/**
 * Handle WebRTC answer
 */
function handleAnswer(ws, message) {
  const client = clients.get(ws);
  const { targetId, answer } = message;
  
  if (!targetId || !answer) {
    send(ws, {
      type: 'error',
      error: 'targetId and answer are required',
    });
    return;
  }
  
  // Find target client
  const targetWs = findClientById(targetId);
  
  if (!targetWs) {
    send(ws, {
      type: 'error',
      error: `Target client ${targetId} not found`,
    });
    return;
  }
  
  // Forward answer to target
  send(targetWs, {
    type: 'answer',
    fromId: client.id,
    answer: answer,
  });
  
  console.log(`🔄 Forwarded answer from ${client.id} to ${targetId}`);
}

/**
 * Handle ICE candidate
 */
function handleIceCandidate(ws, message) {
  const client = clients.get(ws);
  const { targetId, candidate } = message;
  
  if (!targetId || !candidate) {
    send(ws, {
      type: 'error',
      error: 'targetId and candidate are required',
    });
    return;
  }
  
  // Find target client
  const targetWs = findClientById(targetId);
  
  if (!targetWs) {
    // Silently ignore if target not found (they may have disconnected)
    return;
  }
  
  // Forward ICE candidate to target
  send(targetWs, {
    type: 'ice-candidate',
    fromId: client.id,
    candidate: candidate,
  });
  
  console.log(`🧊 Forwarded ICE candidate from ${client.id} to ${targetId}`);
}

/**
 * Handle client leaving a room
 */
function handleLeave(ws) {
  const client = clients.get(ws);
  
  if (!client.roomId) {
    return;
  }
  
  const roomId = client.roomId;
  const room = rooms.get(roomId);
  
  if (room) {
    room.delete(ws);
    
    // Notify others in room
    broadcast(ws, roomId, {
      type: 'peer-left',
      peerId: client.id,
    });
    
    // Clean up empty rooms
    if (room.size === 0) {
      rooms.delete(roomId);
      console.log(`🗑️  Removed empty room ${roomId}`);
    }
  }
  
  console.log(`👋 Client ${client.id} left room ${roomId}`);
  
  client.roomId = null;
  client.role = null;
}

/**
 * Handle client disconnect
 */
function handleDisconnect(ws) {
  const client = clients.get(ws);
  
  if (!client) {
    return;
  }
  
  console.log(`❌ Client disconnected: ${client.id}`);
  
  // Leave room if joined
  handleLeave(ws);
  
  // Remove from clients map
  clients.delete(ws);
}

/**
 * Send message to a specific client
 */
function send(ws, message) {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify(message));
  }
}

/**
 * Broadcast message to all clients in a room except sender
 */
function broadcast(sender, roomId, message) {
  const room = rooms.get(roomId);
  
  if (!room) {
    return;
  }
  
  room.forEach((ws) => {
    if (ws !== sender) {
      send(ws, message);
    }
  });
}

/**
 * Find client WebSocket by ID
 */
function findClientById(clientId) {
  for (const [ws, client] of clients.entries()) {
    if (client.id === clientId) {
      return ws;
    }
  }
  return null;
}

// Health check endpoint (for Docker)
const http = require('http');
const healthServer = http.createServer((req, res) => {
  if (req.url === '/health') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      status: 'healthy',
      connections: clients.size,
      rooms: rooms.size,
    }));
  } else {
    res.writeHead(404);
    res.end();
  }
});

healthServer.listen(PORT + 1, () => {
  console.log(`❤️  Health check server on port ${PORT + 1}`);
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('📴 SIGTERM received, closing server...');
  wss.close(() => {
    healthServer.close(() => {
      console.log('👋 Server shut down gracefully');
      process.exit(0);
    });
  });
});
