#!/bin/bash

# CoSim Frontend Testing Script

echo "🔧 CoSim API & Theme Testing"
echo "=============================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if containers are running
echo -e "${BLUE}1. Checking Docker containers...${NC}"
if docker-compose ps | grep -q "Up"; then
    echo -e "${GREEN}✓ Containers are running${NC}"
else
    echo -e "${YELLOW}⚠ Containers not running. Starting them...${NC}"
    docker-compose up -d
    echo "Waiting for services to be ready..."
    sleep 10
fi
echo ""

# Check API Gateway
echo -e "${BLUE}2. Testing API Gateway connection...${NC}"
if curl -s http://localhost:8080/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ API Gateway is responding (port 8080)${NC}"
else
    echo -e "${YELLOW}⚠ API Gateway not responding${NC}"
fi
echo ""

# Check Frontend
echo -e "${BLUE}3. Testing Frontend connection...${NC}"
if curl -s http://localhost:5173 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Frontend is running (port 5173)${NC}"
else
    echo -e "${YELLOW}⚠ Frontend not responding${NC}"
fi
echo ""

# Check Yjs Collaboration Server
echo -e "${BLUE}4. Testing Yjs Collaboration Server...${NC}"
if curl -s http://localhost:1234/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Yjs server is healthy (port 1234)${NC}"
else
    echo -e "${YELLOW}⚠ Yjs server not responding${NC}"
fi
echo ""

# Display environment info
echo -e "${BLUE}5. Environment Configuration:${NC}"
if [ -f frontend/.env ]; then
    echo -e "${GREEN}✓ .env file exists${NC}"
    echo "   VITE_API_BASE_URL=/api"
    echo "   VITE_COLLAB_WS_URL=ws://localhost:1234"
else
    echo -e "${YELLOW}⚠ .env file missing${NC}"
fi
echo ""

# Test theme persistence
echo -e "${BLUE}6. Theme System:${NC}"
echo "   - localStorage key: 'cosim-theme'"
echo "   - Options: light, dark, auto"
echo "   - Auto mode: detects system preference"
echo ""

# Display URLs
echo -e "${BLUE}7. Access URLs:${NC}"
echo "   Frontend:    http://localhost:5173"
echo "   API Gateway: http://localhost:8080"
echo "   API Docs:    http://localhost:8080/docs"
echo ""

# Test instructions
echo -e "${BLUE}8. Manual Testing Checklist:${NC}"
echo "   [ ] Login with demo credentials"
echo "   [ ] Navigate to Profile page"
echo "   [ ] Click Edit and change name"
echo "   [ ] Save and verify (check Network tab)"
echo "   [ ] Navigate to Settings page"
echo "   [ ] Change theme (Light/Dark/Auto)"
echo "   [ ] Verify theme persists after refresh"
echo "   [ ] Test auto mode with system theme"
echo ""

echo -e "${GREEN}Testing setup complete!${NC}"
echo ""
echo "💡 Tips:"
echo "   - Open Browser DevTools (F12) → Network tab"
echo "   - Filter by 'api' to see API requests"
echo "   - Should see 'localhost:8080' as target"
echo "   - Check Console for any errors"
echo ""
echo "🐛 Common Issues:"
echo "   - 404 errors: Restart docker-compose"
echo "   - Theme not working: Clear localStorage"
echo "   - API not found: Check vite.config.ts proxy"
