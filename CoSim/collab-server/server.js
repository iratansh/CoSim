#!/usr/bin/env node

/**
 * CoSim Yjs Collaboration Server
 * Provides real-time CRDT synchronization for multi-user editing
 */

const WebSocket = require('ws');
const http = require('http');
const { setupWSConnection } = require('y-websocket/bin/utils');

const PORT = process.env.PORT || 1234;
const PERSISTENCE_DIR = process.env.PERSISTENCE_DIR || '/data';

console.log(`Starting CoSim Yjs Collaboration Server on port ${PORT}`);
console.log(`Persistence directory: ${PERSISTENCE_DIR}`);

const server = http.createServer((req, res) => {
  if (req.url === '/health') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ status: 'healthy', uptime: process.uptime() }));
    return;
  }
  res.writeHead(200, { 'Content-Type': 'text/html' });
  res.end('CoSim Yjs Collaboration Server Running');
});

const wss = new WebSocket.Server({ server });

wss.on('connection', (ws, req) => {
  const docName = req.url.slice(1); // Extract document name from URL
  console.log(`New connection for document: ${docName}`);
  
  setupWSConnection(ws, req, {
    gc: true, // Enable garbage collection
    // You can add persistence here if needed
    // persistenceDir: PERSISTENCE_DIR
  });
});

wss.on('error', (error) => {
  console.error('WebSocket server error:', error);
});

server.listen(PORT, '0.0.0.0', () => {
  console.log(`✓ Yjs collaboration server listening on ws://0.0.0.0:${PORT}`);
  console.log(`✓ Health check available at http://0.0.0.0:${PORT}/health`);
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('SIGTERM received, closing server...');
  wss.close(() => {
    server.close(() => {
      console.log('Server closed');
      process.exit(0);
    });
  });
});

process.on('SIGINT', () => {
  console.log('\nSIGINT received, closing server...');
  wss.close(() => {
    server.close(() => {
      console.log('Server closed');
      process.exit(0);
    });
  });
});
