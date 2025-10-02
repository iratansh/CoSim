# CoSim Web IDE

Browser-based collaborative IDE for robotics development with C++ and Python support, integrated simulation viewer, and real-time collaboration.

## Features

### 🎨 Monaco Editor Integration
- Full-featured code editor (same as VS Code)
- Syntax highlighting for Python and C++
- IntelliSense and code completion
- Multi-file support with file tree navigation
- Keyboard shortcuts (Ctrl+S to save)

### 👥 Real-time Collaboration
- **Yjs CRDT** for conflict-free collaborative editing
- WebSocket-based synchronization
- Presence awareness (see who's editing)
- Per-file collaboration rooms

### 🖥️ Integrated Terminal
- **xterm.js** terminal emulator
- Execute Python scripts
- Compile and build C++ projects (g++, clang++, cmake)
- Full terminal command support
- Persistent session connection

### 🤖 Simulation Viewer
- WebRTC-based video streaming
- Support for MuJoCo and PyBullet simulators
- Real-time simulation control (play, pause, reset, step)
- Adjustable FPS settings
- Low-latency rendering

### 📁 File Management
- Hierarchical file tree
- Navigate between Python and C++ projects
- Support for configuration files (sim-control.json)
- Real-time file synchronization

### 🎯 Layout Flexibility
- **Editor Only**: Focus on code
- **With Terminal**: Code + terminal split
- **With Simulation**: Code + simulation viewer
- **Full Layout**: Code + terminal + simulation (default)

## Installation

\`\`\`bash
cd frontend
npm install
\`\`\`

## Dependencies

### Core
- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **React Router** - Navigation

### Editor
- **@monaco-editor/react** - Monaco editor React wrapper
- **monaco-editor** - Core editor engine

### Collaboration
- **yjs** - CRDT for real-time sync
- **y-websocket** - WebSocket provider for Yjs
- **y-monaco** - Monaco editor binding for Yjs

### Terminal
- **@xterm/xterm** - Terminal emulator
- **@xterm/addon-fit** - Auto-sizing addon
- **@xterm/addon-web-links** - Clickable links

### State & API
- **zustand** - State management
- **@tanstack/react-query** - Data fetching
- **axios** - HTTP client

### UI
- **lucide-react** - Icon library
- **clsx** - Conditional styling

## Development

\`\`\`bash
# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
\`\`\`

## Project Structure

\`\`\`
frontend/
├── src/
│   ├── components/
│   │   ├── SessionIDE.tsx          # Main IDE container
│   │   ├── FileTree.tsx            # File explorer sidebar
│   │   ├── Terminal.tsx            # Terminal emulator
│   │   ├── SimulationViewer.tsx    # Simulation canvas
│   │   ├── Layout.tsx              # Page layout wrapper
│   │   └── TopNav.tsx              # Navigation header
│   ├── routes/
│   │   ├── Login.tsx               # Authentication
│   │   ├── Projects.tsx            # Project list
│   │   ├── Workspace.tsx           # Workspace management
│   │   └── Session.tsx             # Active session with IDE
│   ├── api/
│   │   ├── sessions.ts             # Session API calls
│   │   ├── collab.ts               # Collaboration API
│   │   └── types.ts                # TypeScript types
│   ├── hooks/
│   │   └── useAuth.ts              # Authentication hook
│   ├── contexts/
│   └── styles/
├── public/
├── package.json
├── tsconfig.json
├── vite.config.ts
└── README.md
\`\`\`

## Usage

### Basic Editing
1. Select a file from the file tree
2. Edit code in Monaco editor
3. Press `Ctrl+S` (or `Cmd+S` on Mac) to save
4. Changes sync automatically in collaborative mode

### Running Code

**Python:**
\`\`\`bash
# In terminal
python src/main.py
python3 src/utils.py
\`\`\`

**C++:**
\`\`\`bash
# Compile single file
g++ src/main.cpp -o build/main

# Using CMake
cmake -B build
cmake --build build
./build/main
\`\`\`

### Simulation Control
1. Select layout: "Full" or "With Simulation"
2. Use control buttons:
   - **Play/Pause**: Start/stop simulation
   - **Reset**: Reset to initial state
   - **Settings**: Adjust FPS and rendering options

### Collaboration
- Multiple users can edit the same file simultaneously
- Changes appear in real-time
- Each file has its own collaboration room
- Presence indicators show active editors

## Environment Variables

Create a `.env` file:

\`\`\`env
VITE_API_URL=http://localhost:8000
VITE_COLLAB_WS_URL=ws://localhost:1234
VITE_WEBRTC_SIGNALING_URL=ws://localhost:3000
\`\`\`

## Architecture Integration

This web IDE integrates with the CoSim platform architecture:

- **API Gateway**: `/sessions`, `/workspaces`, `/runs/*`
- **Collab Server**: Yjs document sync via WebSocket
- **Build Agent**: C++ compilation requests
- **Python Agent**: Script execution
- **Simulation Agent**: WebRTC stream + control
- **Stream Agent**: WebRTC SFU for video

## Keyboard Shortcuts

- `Ctrl+S` / `Cmd+S`: Save current file
- `Ctrl+F` / `Cmd+F`: Find in file
- `Ctrl+H` / `Cmd+H`: Find and replace
- `Ctrl+/` / `Cmd+/`: Toggle comment
- `Alt+Up/Down`: Move line up/down
- `Shift+Alt+F`: Format document

## Browser Support

- Chrome/Edge: ✅ Full support
- Firefox: ✅ Full support
- Safari: ✅ Full support (WebRTC may need TURN)

## Performance

- Monaco lazy loads language features
- xterm.js renders up to 10k lines efficiently
- WebRTC video uses hardware acceleration
- Yjs CRDT handles conflicts without server round-trips

## Security

- JWT authentication for all API calls
- Signed WebSocket connections for collaboration
- WebRTC with TURN server for NAT traversal
- CSP headers for XSS protection

## Troubleshooting

**Editor not loading:**
- Check browser console for Monaco loader errors
- Ensure `monaco-editor` is properly installed

**Terminal not connecting:**
- Verify backend WebSocket endpoint
- Check network tab for connection errors

**Collaboration not working:**
- Ensure Yjs WebSocket server is running
- Check WebSocket URL in environment config

**Simulation video not showing:**
- Verify WebRTC signaling server
- Check browser WebRTC support
- May need TURN server for restrictive networks

## Future Enhancements

- [ ] Diff viewer for collaboration conflicts
- [ ] Integrated debugger (lldb/gdb for C++, debugpy for Python)
- [ ] Git integration
- [ ] Notebook support (.ipynb files)
- [ ] Extensions marketplace
- [ ] Custom themes
- [ ] Voice chat for collaborators
- [ ] Screen sharing

## Contributing

See main CoSim repository for contribution guidelines.

## License

See main CoSim repository for license information.
