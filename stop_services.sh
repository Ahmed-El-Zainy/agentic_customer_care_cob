#!/bin/bash

# COB Company Chatbot System Shutdown Script

echo "🛑 Stopping COB Company Chatbot System"
echo "====================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Function to safely kill process
kill_process() {
    local pid=$1
    local name=$2
    
    if [ -n "$pid" ] && kill -0 $pid 2>/dev/null; then
        print_status "Stopping $name (PID: $pid)..."
        kill $pid
        sleep 2
        
        # Force kill if still running
        if kill -0 $pid 2>/dev/null; then
            print_warning "Force killing $name..."
            kill -9 $pid 2>/dev/null
        fi
        print_success "$name stopped"
    else
        print_warning "$name was not running"
    fi
}

# Stop services using saved PIDs
if [ -f "logs/fastapi.pid" ]; then
    FASTAPI_PID=$(cat logs/fastapi.pid)
    kill_process $FASTAPI_PID "FastAPI Server"
    rm -f logs/fastapi.pid
fi

if [ -f "logs/gradio.pid" ]; then
    GRADIO_PID=$(cat logs/gradio.pid)
    kill_process $GRADIO_PID "Gradio Interface"
    rm -f logs/gradio.pid
fi

if [ -f "logs/html.pid" ]; then
    HTML_PID=$(cat logs/html.pid)
    kill_process $HTML_PID "HTML Server"
    rm -f logs/html.pid
fi

# Kill any remaining processes on the ports
print_status "Cleaning up any remaining processes..."

for port in 8000 7860 8080; do
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_warning "Killing remaining process on port $port"
        lsof -ti:$port | xargs kill -9 2>/dev/null || true
    fi
done

print_success "All services stopped successfully!"
echo ""
echo "📝 Log files are preserved in the 'logs/' directory"
echo "🚀 To restart the system, run: ./start_system.sh"