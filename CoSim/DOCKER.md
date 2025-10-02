# CoSim Docker Setup

Complete Docker-based development environment for the CoSim platform with all microservices, databases, and the web IDE.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Docker Compose Stack                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ Postgres │  │  Redis   │  │   NATS   │  │  Yjs WS  │    │
│  │  :5433   │  │  :6380   │  │  :4222   │  │  :1234   │    │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘    │
│       │             │              │              │          │
│  ┌────┴─────────────┴──────────────┴──────────────┴────┐    │
│  │                                                       │    │
│  │             Backend Microservices                    │    │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐    │    │
│  │  │  Auth      │  │  Project   │  │  Session   │    │    │
│  │  │  :8001     │  │  :8002     │  │  :8003     │    │    │
│  │  └────────────┘  └────────────┘  └────────────┘    │    │
│  │                                                       │    │
│  │  ┌────────────┐  ┌────────────────────────────┐    │    │
│  │  │  Collab    │  │     API Gateway            │    │    │
│  │  │  :8004     │  │     :8080                  │    │    │
│  │  └────────────┘  └────────────────────────────┘    │    │
│  └───────────────────────────┬───────────────────────┘    │
│                               │                             │
│  ┌────────────────────────────┴───────────────────────┐    │
│  │              Frontend (Web IDE)                    │    │
│  │              :5173                                 │    │
│  │  • Monaco Editor (Python & C++)                   │    │
│  │  • Yjs Real-time Collaboration                    │    │
│  │  • xterm.js Terminal                              │    │
│  │  • WebRTC Simulation Viewer                       │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Services

### Infrastructure
- **Postgres** (`:5433`) - Main database for all agents
- **Redis** (`:6380`) - Job queues and caching
- **NATS** (`:4222`, `:8222`) - Event bus for inter-agent communication
- **Yjs WebSocket** (`:1234`) - Real-time collaboration server (CRDT sync)

### Backend Agents
- **API Gateway** (`:8080`) - Single entry point for all API requests
- **Auth Agent** (`:8001`) - Authentication, JWT, RBAC
- **Project/Workspace Agent** (`:8002`) - Project and workspace management
- **Session Orchestrator** (`:8003`) - Session lifecycle, pod management
- **Collab Agent** (`:8004`) - Document collaboration, participants

### Frontend
- **Web IDE** (`:5173`) - React app with Monaco Editor, terminal, sim viewer

## Quick Start

### 1. Start All Services

```bash
# From repository root
docker-compose up -d

# Watch logs
docker-compose logs -f

# Watch specific service
docker-compose logs -f web
docker-compose logs -f yjs-collab-server
```

### 2. Access the Application

- **Web IDE**: http://localhost:5173
- **API Gateway**: http://localhost:8080
- **API Docs**: http://localhost:8080/docs
- **NATS Monitoring**: http://localhost:8222
- **Yjs Health**: http://localhost:1234/health

### 3. Stop Services

```bash
# Stop all
docker-compose down

# Stop and remove volumes (reset database)
docker-compose down -v
```

## Development Workflow

### Hot Reload Development

The frontend container is configured with volume mounts for hot reload:

```yaml
volumes:
  - ./frontend:/app
  - /app/node_modules  # Preserve node_modules
```

Changes to frontend files will automatically reload in the browser.

### Installing New Dependencies

**Frontend:**
```bash
# Option 1: Install inside container
docker-compose exec web npm install <package>

# Option 2: Install locally and rebuild
cd frontend
npm install <package>
docker-compose up -d --build web
```

**Backend:**
```bash
# Add to requirements.txt, then rebuild
docker-compose up -d --build auth-agent
```

### Database Migrations

```bash
# Run migrations
docker-compose exec api-gateway python -m alembic upgrade head

# Create new migration
docker-compose exec api-gateway python -m alembic revision --autogenerate -m "description"
```

### Accessing Services

```bash
# Execute command in container
docker-compose exec web sh
docker-compose exec postgres psql -U cosim -d cosim

# View service logs
docker-compose logs -f web
docker-compose logs -f api-gateway
```

## Environment Variables

### Frontend (.env)

Create `frontend/.env` from `frontend/.env.example`:

```bash
VITE_API_BASE_URL=/api
VITE_COLLAB_WS_URL=ws://localhost:1234
VITE_WEBRTC_SIGNALING_URL=ws://localhost:3000
VITE_DEBUG=false
```

### Backend

Backend services are configured via environment variables in `docker-compose.yml`:

- `COSIM_DATABASE_URI` - PostgreSQL connection
- `COSIM_JWT_SECRET_KEY` - JWT signing secret
- `COSIM_REDIS_URL` - Redis connection
- `COSIM_NATS_URL` - NATS connection
- `COSIM_SERVICE_ENDPOINTS__*` - Inter-service URLs

## Troubleshooting

### Port Conflicts

If ports are already in use, modify `docker-compose.yml`:

```yaml
ports:
  - "5174:5173"  # Changed from 5173
```

### Database Connection Issues

```bash
# Check if Postgres is healthy
docker-compose ps postgres

# View Postgres logs
docker-compose logs postgres

# Connect to Postgres directly
docker-compose exec postgres psql -U cosim -d cosim
```

### Frontend Not Loading

```bash
# Check if container is running
docker-compose ps web

# View logs
docker-compose logs web

# Rebuild if needed
docker-compose up -d --build web
```

### Yjs Collaboration Not Working

```bash
# Check Yjs server health
curl http://localhost:1234/health

# View Yjs logs
docker-compose logs yjs-collab-server

# Check WebSocket connection in browser console
# Should see: "Connected to http://localhost:1234"
```

### Terminal Not Connecting

The terminal connects to backend via WebSocket. Check:

```bash
# Verify API gateway is running
docker-compose ps api-gateway

# Check backend logs
docker-compose logs api-gateway
```

### Build Errors

```bash
# Clean build
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## Data Persistence

Data is persisted in Docker volumes:

```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect cosim_postgres_data
docker volume inspect cosim_yjs_data

# Backup database
docker-compose exec postgres pg_dump -U cosim cosim > backup.sql

# Restore database
cat backup.sql | docker-compose exec -T postgres psql -U cosim -d cosim
```

## Production Deployment

For production, create a separate `docker-compose.prod.yml`:

```yaml
version: "3.11"

services:
  web:
    build:
      context: ./frontend
      target: production
    environment:
      VITE_API_BASE_URL: https://api.cosim.example.com
      VITE_COLLAB_WS_URL: wss://collab.cosim.example.com
      VITE_WEBRTC_SIGNALING_URL: wss://signaling.cosim.example.com
    restart: always

  # Override other services with production configs
```

Deploy with:

```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## Health Checks

All services include health checks:

```bash
# Check health status
docker-compose ps

# Service health details
docker inspect <container_id> --format='{{json .State.Health}}'
```

## Scaling

Scale individual services:

```bash
# Scale session orchestrator
docker-compose up -d --scale session-orchestrator=3

# Note: Ensure stateless services for horizontal scaling
```

## Monitoring

### Resource Usage

```bash
# View resource usage
docker stats

# Specific service
docker stats cosim-web-1
```

### Logs Aggregation

```bash
# All logs
docker-compose logs -f

# Specific time range
docker-compose logs --since 30m

# Follow specific services
docker-compose logs -f web api-gateway yjs-collab-server
```

## Testing

### Run Backend Tests

```bash
docker-compose exec api-gateway pytest
```

### Run Frontend Tests

```bash
docker-compose exec web npm test
```

## CI/CD Integration

Example GitHub Actions workflow:

```yaml
name: Docker Build

on: [push]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Build images
        run: docker-compose build
      
      - name: Start services
        run: docker-compose up -d
      
      - name: Run tests
        run: docker-compose exec -T web npm test
      
      - name: Cleanup
        run: docker-compose down
```

## Security Notes

- Default credentials are for **development only**
- Change `COSIM_JWT_SECRET_KEY` in production
- Use secrets management (Docker Secrets, Vault)
- Enable HTTPS/TLS for production
- Restrict network access with Docker networks
- Run containers as non-root users
- Scan images for vulnerabilities:

```bash
docker scan cosim-web
```

## Additional Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [CoSim Architecture](../AGENT.md)
- [Frontend IDE Documentation](../frontend/README_IDE.md)
- [API Documentation](http://localhost:8080/docs)
