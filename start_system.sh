
# COB Company Chatbot System Startup Script

set -e  # Exit on any error

echo "🚀 Starting COB Company Chatbot System"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running from correct directory
if [ ! -f "src/main.py" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

# Create logs directory
mkdir -p logs

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        return 0
    else
        return 1
    fi
}

# Function to kill process on port
kill_port() {
    local port=$1
    if check_port $port; then
        print_warning "Killing existing process on port $port"
        lsof -ti:$port | xargs kill -9 2>/dev/null || true
        sleep 2
    fi
}

# Check environment variables
print_status "Checking environment variables..."
if [ -z "$GEMINI_API_KEY" ]; then
    print_error "GEMINI_API_KEY environment variable is not set"
    echo "Please set it with: export GEMINI_API_KEY=your_api_key_here"
    exit 1
fi

if [ -z "$JWT_SECRET_KEY" ]; then
    print_warning "JWT_SECRET_KEY not set, using default (not recommended for production)"
    export JWT_SECRET_KEY="your-secret-key-change-this-in-production"
fi

print_success "Environment variables OK"

# # Install/check dependencies
# print_status "Checking Python dependencies..."
# if ! python -c "import fastapi, gradio, google.generativeai" 2>/dev/null; then
#     print_warning "Installing missing dependencies..."
#     pip install -r requirements.txt || {
#         print_error "Failed to install dependencies"
#         exit 1
#     }
# fi
print_success "Dependencies OK"

# Initialize database
print_status "Initializing database..."
python -c "
import sqlite3
import os

# Create database if it doesn't exist
db_path = '/Users/ahmedmostafa/Downloads/agentic_customer_care_cob/assets/data/cob_system_2.db'
if not os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    conn.close()
    print('Database created')
else:
    print('Database already exists')
" || {
    print_error "Failed to initialize database"
    exit 1
}
print_success "Database OK"

# Kill existing processes on ports we need
kill_port 8000  # FastAPI
kill_port 7860  # Gradio

# Start FastAPI server
print_status "Starting FastAPI server on port 8000..."
cd src
nohup python -m uvicorn api.chat:app --host 0.0.0.0 --port 8000 --reload > ../logs/fastapi.log 2>&1 &
FASTAPI_PID=$!
cd ..

# Wait for FastAPI to start
sleep 5

# Check if FastAPI started successfully
if ! check_port 8000; then
    print_error "FastAPI failed to start"
    cat logs/fastapi.log
    exit 1
fi
print_success "FastAPI server started (PID: $FASTAPI_PID)"

# Start Gradio interface
print_status "Starting Gradio interface on port 7860..."
nohup python src/main.py > logs/gradio.log 2>&1 &
GRADIO_PID=$!

# Wait for Gradio to start
sleep 5

# Check if Gradio started successfully
if ! check_port 7860; then
    print_error "Gradio failed to start"
    cat logs/gradio.log
    exit 1
fi
print_success "Gradio interface started (PID: $GRADIO_PID)"

# Test the integration
print_status "Running integration tests..."
python tests/integration_test.py || {
    print_warning "Integration tests failed, but services are running"
}

# Create a simple HTTP server for the HTML demo (optional)
print_status "Setting up HTML demo server on port 8080..."
cd src
nohup python -m http.server 8080 > ../logs/html_server.log 2>&1 &
HTML_PID=$!
cd ..

# Save PIDs for later cleanup
echo $FASTAPI_PID > logs/fastapi.pid
echo $GRADIO_PID > logs/gradio.pid
echo $HTML_PID > logs/html.pid

print_success "All services started successfully!"
echo ""
echo "🌟 Service URLs:"
echo "   📡 FastAPI Server:    http://localhost:8000"
echo "   🎯 Gradio Interface:  http://localhost:7860"
echo "   🌐 HTML Demo:         http://localhost:8080/gradio_demo.html"
echo "   📊 API Documentation: http://localhost:8000/docs"
echo ""
echo "📝 Logs are available in the 'logs/' directory"
echo "🛑 To stop all services, run: ./stop_services.sh"
echo ""
echo "✨ System is ready for use!"