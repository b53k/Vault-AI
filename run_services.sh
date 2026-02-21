#!/bin/bash

SCRIPT_DIR="$(pwd)"

# Pretty Print
clear

# === Show System Info ===
echo "$(hostnamectl | grep -E 'hostname|Chassis|System|Kernel|Architecture|Hardware|Firmware Age')" | boxes -d boy
echo "Current Date: $(date)"

figlet "Vault AI" | boxes | lolcat -S 40
echo ""


# Function to clean up services on exit
cleanup() {
    echo ""
    echo "Stopping services..."
    # Kill all uvicorn processes
    pkill -f "uvicorn.*8000" 2>/dev/null
    pkill -f "uvicorn.*8001" 2>/dev/null
    pkill -f "uvicorn.*8002" 2>/dev/null
    
    # Kill any remaining processes
    pkill -9 -f "uvicorn.*agent" 2>/dev/null
    pkill -9 -f "uvicorn.*vectorstore" 2>/dev/null
    pkill -9 -f "uvicorn.*database" 2>/dev/null

    sleep 2

    # Force kill if its still running
    pkill -9 -f "uvicorn.*8000" 2>/dev/null
    pkill -9 -f "uvicorn.*8001" 2>/dev/null
    pkill -9 -f "uvicorn.*8002" 2>/dev/null

    echo "Services stopped"
    exit 
}

trap cleanup INT TERM

source "$SCRIPT_DIR/vault_env/bin/activate"

# === Start Services ===
# Start services in background
cd "$SCRIPT_DIR/backend/agent-service" && ./run.sh &
AGENT_PID=$!

cd "$SCRIPT_DIR/backend/vectorstore-service" && ./run.sh &       # & - run in background
VECTORSTORE_PID=$!

cd "$SCRIPT_DIR/backend/database-service" && ./run.sh &
DATABASE_PID=$!

sleep 5
echo ""
echo "Services started:"
echo "Agent service       - http://localhost:8000" | lolcat
echo "Vectorstore service - http://localhost:8001" | lolcat
echo "Database service    - http://localhost:8002" | lolcat
echo ""
echo "Press Ctrl+C to stop all services" | lolcat
echo ""


# Wait for services to be terminated
wait
