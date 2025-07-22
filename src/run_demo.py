import os
import sys
import subprocess
import threading
import time
from pathlib import Path

def setup_environment():
    """Setup the environment and create necessary directories"""
    print("🔧 Setting up environment...")
    
    # Create necessary directories
    directories = ["logs", "assets/data"]
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")
    
    # Check for .env file
    if not Path("src/.env").exists():
        print("⚠️  .env file not found. Please create one using .env.template as reference")
        return False
    
    return True

# def check_dependencies():
#     """Check if all required dependencies are installed"""
#     print("📦 Checking dependencies...")
    
#     required_packages = [
#         "fastapi", "uvicorn", "gradio", "google-generativeai",
#         "pandas", "pyjwt", "faker", "python-dotenv", "pydantic"
#     ]
    
#     missing_packages = []
#     for package in required_packages:
#         try:
#             __import__(package.replace("-", "_"))
#         except ImportError:
#             missing_packages.append(package)
    
#     if missing_packages:
#         print(f"❌ Missing packages: {', '.join(missing_packages)}")
#         print("Run: pip install -r requirements.txt")
#         return False
    
#     print("✅ All dependencies satisfied")
#     return True

def generate_databases():
    """Generate the initial databases"""
    print("🗄️  Generating databases...")
    
    try:
        from src.synthetic_clinic_cob.generate_databases import generate_databases
        generate_databases()
        print("✅ Databases generated successfully")
        return True
    except Exception as e:
        print(f"❌ Database generation failed: {e}")
        return False

def start_api_server():
    """Start the FastAPI server"""
    print("🚀 Starting API server...")
    
    try:
        cmd = [
            sys.executable, "-m", "uvicorn",
            "api_routes:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"
        ]
        return subprocess.Popen(cmd)
    except Exception as e:
        print(f"❌ Failed to start API server: {e}")
        return None

def start_gradio_interface():
    """Start the Gradio interface"""
    print("🌐 Starting Gradio interface...")
    
    try:
        cmd = [sys.executable, "src/main.py"]
        return subprocess.Popen(cmd)
    except Exception as e:
        print(f"❌ Failed to start Gradio interface: {e}")
        return None

def main():
    """Main startup function"""
    print("=" * 60)
    print("🏢 COB Company Customer Support System")
    print("=" * 60)
    
    # Setup environment
    if not setup_environment():
        sys.exit(1)
    
    # # Check dependencies
    # if not check_dependencies():
    #     sys.exit(1)
    
    # Generate databases
    if not generate_databases():
        print("⚠️  Database generation failed, but continuing...")
    
    # Start services
    print("\n🔄 Starting services...")
    
    # Start API server
    api_process = start_api_server()
    if not api_process:
        print("❌ Failed to start API server")
        sys.exit(1)
    
    # Wait a moment for API server to start
    time.sleep(3)
    
    # Start Gradio interface
    gradio_process = start_gradio_interface()
    if not gradio_process:
        print("❌ Failed to start Gradio interface")
        if api_process:
            api_process.terminate()
        sys.exit(1)
    
    print("\n✅ All services started successfully!")
    print("\n📱 Access points:")
    print("   • Gradio Interface: http://localhost:7860")
    print("   • API Documentation: http://localhost:8000/docs")
    print("   • API Health Check: http://localhost:8000/api/health")
    print("\n🛑 Press Ctrl+C to stop all services")
    
    try:
        # Wait for processes
        api_process.wait()
        gradio_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down services...")
        
        if api_process:
            api_process.terminate()
            print("✅ API server stopped")
        
        if gradio_process:
            gradio_process.terminate()
            print("✅ Gradio interface stopped")
        
        print("👋 Goodbye!")

if __name__ == "__main__":
    main()