# CoSim Web IDE - Quick Start with Docker

Get the complete CoSim development environment running in under 5 minutes!

## Prerequisites

- Docker Desktop installed ([download](https://www.docker.com/products/docker-desktop))
- 8GB+ RAM available
- 10GB+ disk space

## 🚀 Quick Start

### 1. Clone and Start

```bash
# Clone the repository
git clone <your-repo-url>
cd CoSim

# Start all services (first time will take a few minutes to build)
./docker-manager.sh start

# Or manually with docker-compose
docker-compose up -d
```

### 2. Wait for Services

```bash
# Check status
./docker-manager.sh health

# Watch logs
./docker-manager.sh logs
```

### 3. Access the IDE

Open your browser to: **http://localhost:5173**

You should see the CoSim web IDE with:
- ✅ File tree on the left
- ✅ Monaco editor in the center
- ✅ Terminal at the bottom
- ✅ Simulation viewer on the right

## 🎯 What's Running?

| Service | Port | Description |
|---------|------|-------------|
| Web IDE | 5173 | Main application |
| API Gateway | 8080 | Backend API |
| Yjs Collab | 1234 | Real-time collaboration |
| PostgreSQL | 5433 | Database |
| Redis | 6380 | Cache & queues |
| NATS | 4222 | Event bus |

## 🛠️ Common Operations

### View Logs
```bash
# All services
./docker-manager.sh logs

# Specific service
./docker-manager.sh logs web
./docker-manager.sh logs api-gateway
```

### Restart Services
```bash
./docker-manager.sh restart
```

### Stop Services
```bash
./docker-manager.sh stop
```

### Check Health
```bash
./docker-manager.sh health
```

### Access Container Shell
```bash
# Frontend container
./docker-manager.sh shell web

# Backend container
./docker-manager.sh shell api-gateway

# Database
./docker-manager.sh shell postgres
```

## 💻 Using the IDE

### 1. Select a File
Click on any file in the left sidebar (e.g., `src/main.py`)

### 2. Edit Code
The Monaco editor provides:
- Syntax highlighting
- Auto-completion
- Error checking
- Multiple cursors (Alt + Click)

### 3. Save Changes
Press `Ctrl+S` (or `Cmd+S` on Mac)

### 4. Run Code in Terminal

**Python:**
```bash
python src/main.py
```

**C++:**
```bash
g++ src/main.cpp -o build/main && ./build/main
```

### 5. Switch Layouts

Use the layout buttons at the top-right:
- **Editor Only** - Focus on code
- **With Terminal** - Code + terminal
- **With Sim** - Code + simulation
- **Full** - Everything (default)

## 👥 Collaboration (Real-time Multi-user Editing)

### Enable Collaboration
The IDE has real-time collaboration enabled by default using Yjs CRDT.

### How It Works
1. Multiple users open the same session
2. Each user sees others' cursors and selections
3. Changes sync instantly
4. Conflicts resolve automatically (CRDT magic!)

### Try It
1. Open http://localhost:5173 in two different browsers
2. Navigate to the same file
3. Edit simultaneously - see changes in real-time!

## 🎮 Simulation Viewer

The simulation viewer streams video from MuJoCo or PyBullet:

### Controls
- **Play/Pause** - Start/stop simulation
- **Reset** - Reset to initial state
- **Settings** - Adjust FPS

### Note
WebRTC streaming requires a signaling server (coming in next phase).
Currently displays connection placeholder.

## 📦 Installing New Packages

### Frontend Dependencies
```bash
# Inside container
./docker-manager.sh shell web
npm install <package-name>

# Or from host
docker-compose exec web npm install <package-name>
```

### Backend Dependencies
```bash
# Add to backend/requirements.txt
# Then rebuild
./docker-manager.sh rebuild api-gateway
```

## 🐛 Troubleshooting

### Web IDE Not Loading

```bash
# Check if running
docker-compose ps web

# View logs
./docker-manager.sh logs web

# Rebuild
./docker-manager.sh rebuild web
```

### Port Already in Use

Edit `docker-compose.yml` and change port mappings:
```yaml
ports:
  - "5174:5173"  # Changed from 5173
```

### Database Connection Errors

```bash
# Check Postgres
docker-compose ps postgres

# View logs
./docker-manager.sh logs postgres

# Reset database (WARNING: deletes data!)
./docker-manager.sh reset
```

### Collaboration Not Working

```bash
# Check Yjs server
curl http://localhost:1234/health

# View logs
./docker-manager.sh logs yjs-collab-server

# Restart
docker-compose restart yjs-collab-server
```

## 🧹 Cleanup

### Stop Everything
```bash
./docker-manager.sh stop
```

### Remove All Data (Reset)
```bash
./docker-manager.sh reset
```

### Clean Docker Resources
```bash
./docker-manager.sh clean
```

## 📚 Next Steps

1. **Read the Full Documentation**
   - [DOCKER.md](./DOCKER.md) - Complete Docker guide
   - [AGENT.md](./AGENT.md) - Architecture overview
   - [frontend/README_IDE.md](./frontend/README_IDE.md) - IDE features

2. **Explore the Code**
   - `frontend/src/components/SessionIDE.tsx` - Main IDE
   - `frontend/src/components/FileTree.tsx` - File explorer
   - `frontend/src/components/Terminal.tsx` - Terminal
   - `frontend/src/components/SimulationViewer.tsx` - Sim viewer

3. **Customize**
   - Modify `docker-compose.yml` for your needs
   - Adjust environment variables in `.env`
   - Add new agents or services

## 🎉 You're Ready!

The CoSim web IDE is now running with:
- ✅ Multi-file editing (Python & C++)
- ✅ Real-time collaboration
- ✅ Integrated terminal
- ✅ Simulation viewer (WebRTC ready)
- ✅ All backend microservices

Start coding! 🚀

## 💡 Tips

- Use `Ctrl+S` to save files quickly
- Try collaborative editing with multiple browsers
- Check API docs at http://localhost:8080/docs
- Monitor services with `./docker-manager.sh health`
- View all logs with `./docker-manager.sh logs`

## 🆘 Need Help?

- Check [DOCKER.md](./DOCKER.md) for detailed troubleshooting
- View service logs: `./docker-manager.sh logs <service>`
- Check service health: `./docker-manager.sh health`
- Open an issue on GitHub

Happy coding! 🎈
