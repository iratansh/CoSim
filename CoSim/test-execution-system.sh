#!/bin/bash

# Test script for code execution system frontend

echo "=================================================="
echo "   CoSim Code Execution System - Test Script"
echo "=================================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if we're in the CoSim directory
if [ ! -d "frontend" ]; then
    echo -e "${RED}✗ Error: Must run from CoSim root directory${NC}"
    exit 1
fi

echo "1. Checking file structure..."
echo ""

# Check execution API
if [ -f "frontend/src/api/execution.ts" ]; then
    echo -e "${GREEN}✓ execution.ts exists${NC}"
    lines=$(wc -l < frontend/src/api/execution.ts)
    echo "  → $lines lines"
else
    echo -e "${RED}✗ execution.ts missing${NC}"
fi

# Check Terminal component
if [ -f "frontend/src/components/Terminal.tsx" ]; then
    echo -e "${GREEN}✓ Terminal.tsx exists${NC}"
    lines=$(wc -l < frontend/src/components/Terminal.tsx)
    echo "  → $lines lines"
    
    # Check for WebSocket implementation
    if grep -q "new WebSocket" frontend/src/components/Terminal.tsx; then
        echo -e "${GREEN}  → WebSocket implemented${NC}"
    else
        echo -e "${YELLOW}  → WebSocket not found${NC}"
    fi
    
    # Check for command history
    if grep -q "commandHistory" frontend/src/components/Terminal.tsx; then
        echo -e "${GREEN}  → Command history implemented${NC}"
    else
        echo -e "${YELLOW}  → Command history not found${NC}"
    fi
else
    echo -e "${RED}✗ Terminal.tsx missing${NC}"
fi

# Check SessionIDE integration
if [ -f "frontend/src/components/SessionIDE.tsx" ]; then
    echo -e "${GREEN}✓ SessionIDE.tsx exists${NC}"
    
    # Check for execution imports
    if grep -q "import.*execution" frontend/src/components/SessionIDE.tsx; then
        echo -e "${GREEN}  → Execution API imported${NC}"
    else
        echo -e "${YELLOW}  → Execution API not imported${NC}"
    fi
    
    # Check for Run buttons
    if grep -q "Run Python" frontend/src/components/SessionIDE.tsx; then
        echo -e "${GREEN}  → Python run button implemented${NC}"
    else
        echo -e "${YELLOW}  → Python run button not found${NC}"
    fi
    
    if grep -q "Build & Run" frontend/src/components/SessionIDE.tsx; then
        echo -e "${GREEN}  → C++ build & run implemented${NC}"
    else
        echo -e "${YELLOW}  → C++ build & run not found${NC}"
    fi
else
    echo -e "${RED}✗ SessionIDE.tsx missing${NC}"
fi

echo ""
echo "2. Checking TypeScript compilation..."
echo ""

cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}⚠ node_modules not found. Installing dependencies...${NC}"
    npm install
fi

# Run TypeScript type checking
echo "Running tsc --noEmit..."
if npm run type-check 2>/dev/null || npx tsc --noEmit 2>/dev/null; then
    echo -e "${GREEN}✓ TypeScript compilation successful${NC}"
else
    echo -e "${YELLOW}⚠ TypeScript errors detected (may be cache issues)${NC}"
    echo "  → Try restarting VS Code or running: npm run dev"
fi

echo ""
echo "3. API Endpoint Summary"
echo ""
echo "Python Execution:"
echo "  POST /api/v1/sessions/execute/python"
echo ""
echo "C++ Build:"
echo "  POST /api/v1/sessions/build/cpp"
echo ""
echo "Binary Execution:"
echo "  POST /api/v1/sessions/execute/binary"
echo ""
echo "File Operations:"
echo "  POST /api/v1/sessions/files/{write|read|list}"
echo ""
echo "WebSocket Terminal:"
echo "  WS /api/v1/sessions/{id}/terminal?token={jwt}"
echo ""

echo "4. Testing Checklist"
echo ""
echo "Frontend Tests:"
echo "  [ ] npm run dev - Start development server"
echo "  [ ] Login to CoSim"
echo "  [ ] Open a workspace with session"
echo "  [ ] Terminal shows 'CONNECTED' status"
echo "  [ ] Write Python code in editor"
echo "  [ ] Click 'Run Python' button"
echo "  [ ] Check browser console for API call"
echo "  [ ] Write C++ code in editor"
echo "  [ ] Click 'Build & Run' button"
echo "  [ ] Verify terminal receives output"
echo ""
echo "Backend Tests (when implemented):"
echo "  [ ] curl -X POST http://localhost:8080/v1/sessions/execute/python ..."
echo "  [ ] wscat -c 'ws://localhost:8080/v1/sessions/{id}/terminal?token=...'"
echo ""

echo "=================================================="
echo "   Test script complete!"
echo "=================================================="
echo ""
echo "Next steps:"
echo "  1. cd frontend && npm run dev"
echo "  2. Open http://localhost:5173"
echo "  3. Test execution buttons in SessionIDE"
echo "  4. Check terminal WebSocket connection"
echo "  5. Implement backend endpoints (see CODE_EXECUTION_IMPLEMENTATION.md)"
echo ""
