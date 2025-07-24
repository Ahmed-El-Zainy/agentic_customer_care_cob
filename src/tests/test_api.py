#!/usr/bin/env python3
"""
Simple test script to verify the API is working
"""

import os
import requests
import json
import time

def test_api():
    """Test the API endpoints step by step"""
    
    api_url = "http://localhost:8000"
    
    print("🔍 Testing COB Company API")
    print("=" * 40)
    
    # Test 1: Health check
    print("\n1. Testing Health Endpoint...")
    try:
        response = requests.get(f"{api_url}/api/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ Health check passed")
            print(f"   Status: {data.get('status')}")
            print(f"   Chatbot: {data.get('chatbot_initialized')}")
            print(f"   API Key: {data.get('gemini_api_key_set')}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        print("   Make sure the API server is running on port 8000")
        return False
    
    # Test 2: Root endpoint
    print("\n2. Testing Root Endpoint...")
    try:
        response = requests.get(f"{api_url}/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ Root endpoint working")
            print(f"   Chatbot Status: {data.get('chatbot_status')}")
        else:
            print(f"❌ Root endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Root endpoint error: {e}")
    
    # Test 3: Chat endpoint
    print("\n3. Testing Chat Endpoint...")
    try:
        chat_data = {
            "message": "Hello, I need help with your services",
            "session_id": "test_session_123"
        }
        
        response = requests.post(
            f"{api_url}/api/chat",
            json=chat_data,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Chat endpoint working")
            print(f"   Response: {data.get('response', '')[:100]}...")
            print(f"   Intent: {data.get('intent')}")
            print(f"   Session: {data.get('session_id')}")
        else:
            print(f"❌ Chat endpoint failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('detail', 'Unknown error')}")
            except:
                print(f"   Raw response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Chat endpoint error: {e}")
        return False
    
    # Test 4: Another chat message
    print("\n4. Testing Follow-up Chat...")
    try:
        chat_data = {
            "message": "What are your business hours?",
            "session_id": "test_session_123"
        }
        
        response = requests.post(
            f"{api_url}/api/chat",
            json=chat_data,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Follow-up chat working")
            print(f"   Response: {data.get('response', '')[:100]}...")
        else:
            print(f"❌ Follow-up chat failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Follow-up chat error: {e}")
    
    print("\n🎉 API Testing Complete!")
    print("The API appears to be working correctly.")
    print("\nYou can now:")
    print("1. Open the HTML demo file in your browser")
    print("2. Or access the Gradio interface if running")
    print("3. Or use the API documentation at http://localhost:8000/docs")
    
    return True

def check_environment():
    """Check if environment is set up correctly"""
    print("🔧 Checking Environment...")
    print("-" * 30)
    
    # Check API key
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        print("✅ GEMINI_API_KEY is set")
    else:
        print("❌ GEMINI_API_KEY is not set")
        print("   Please set it with: export GEMINI_API_KEY=your_api_key")
        return False
    
    # Check if API server is likely running
    try:
        import requests
        print("✅ requests library available")
    except ImportError:
        print("❌ requests library not available")
        print("   Install with: pip install requests")
        return False
    
    return True


#!/usr/bin/env python3
"""
Debug script to identify issues with the COB Company API
"""

import os
import sys
import importlib.util
from pathlib import Path

def check_project_structure():
    """Check if all required files exist"""
    print("📁 Checking Project Structure...")
    print("-" * 40)
    
    required_files = [
        "src/main.py",
        "src/api/chat.py",
        "src/gradio_demo.html"
    ]
    
    missing_files = []
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - MISSING")
            missing_files.append(file_path)
    
    return len(missing_files) == 0

def check_environment_variables():
    """Check environment variables"""
    print("\n🔑 Checking Environment Variables...")
    print("-" * 40)
    
    # Check GEMINI_API_KEY
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        # Don't print the full key for security
        print(f"✅ GEMINI_API_KEY: {api_key[:10]}...{api_key[-4:]} (length: {len(api_key)})")
    else:
        print("❌ GEMINI_API_KEY: Not set")
        return False
    
    # Check other optional variables
    jwt_secret = os.getenv("JWT_SECRET_KEY")
    if jwt_secret:
        print("✅ JWT_SECRET_KEY: Set")
    else:
        print("⚠️  JWT_SECRET_KEY: Not set (will use default)")
    
    return True

def check_python_dependencies():
    """Check if required Python packages are available"""
    print("\n📦 Checking Python Dependencies...")
    print("-" * 40)
    
    required_packages = [
        "fastapi",
        "uvicorn",
        "gradio", 
        "google.generativeai",
        "pydantic",
        "requests",
        "sqlite3"  # Built-in
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            # Special handling for google.generativeai
            if package == "google.generativeai":
                import google.generativeai as genai
                print(f"✅ {package}")
            elif package == "sqlite3":
                import sqlite3
                print(f"✅ {package} (built-in)")
            else:
                __import__(package)
                print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - NOT INSTALLED")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n❌ Missing packages: {missing_packages}")
        print("Install with: pip install " + " ".join(missing_packages))
        return False
    
    return True

def test_imports():
    """Test if the main modules can be imported"""
    print("\n🔧 Testing Module Imports...")
    print("-" * 40)
    
    # Test main.py import
    try:
        sys.path.append("src")
        from main import GeminiChatbot
        print("✅ main.py - GeminiChatbot imported successfully")
        
        # Test chatbot initialization
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            try:
                chatbot = GeminiChatbot(api_key)
                print("✅ GeminiChatbot - Initialized successfully")
                
                # Test a simple message
                response = chatbot.process_message("Hello", "test_session")
                print(f"✅ Chatbot test message - Response: {response[:50]}...")
                
            except Exception as e:
                print(f"❌ GeminiChatbot initialization failed: {e}")
                return False
        else:
            print("⚠️  Cannot test chatbot without GEMINI_API_KEY")
            
    except ImportError as e:
        print(f"❌ main.py import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error with main.py: {e}")
        return False
    
    return True

def test_database():
    """Test database operations"""
    print("\n🗄️  Testing Database...")
    print("-" * 40)
    
    try:
        import sqlite3
        
        # Try to create a test database
        conn = sqlite3.connect(":memory:")  # In-memory database for testing
        cursor = conn.cursor()
        
        # Test table creation
        cursor.execute("""
            CREATE TABLE test_table (
                id INTEGER PRIMARY KEY,
                message TEXT
            )
        """)
        
        # Test insert
        cursor.execute("INSERT INTO test_table (message) VALUES (?)", ("test message",))
        
        # Test select
        cursor.execute("SELECT * FROM test_table")
        result = cursor.fetchone()
        
        conn.close()
        
        if result:
            print("✅ Database operations working")
            return True
        else:
            print("❌ Database test failed - no result")
            return False
            
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_gemini_api():
    """Test Gemini API connection"""
    print("\n🤖 Testing Gemini API...")
    print("-" * 40)
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ Cannot test Gemini API - GEMINI_API_KEY not set")
        return False
    
    try:
        import google.generativeai as genai
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Test a simple generation
        response = model.generate_content("Say hello in a professional manner")
        
        if response.text:
            print("✅ Gemini API working")
            print(f"   Test response: {response.text[:100]}...")
            return True
        else:
            print("❌ Gemini API returned empty response")
            return False
            
    except Exception as e:
        print(f"❌ Gemini API test failed: {e}")
        print("   Check if your API key is valid and has proper permissions")
        return False
    

    
if __name__ == "__main__":
    print("🚀 COB Company API Tester")
    print("=" * 40)
    
    if not check_environment():
        print("\n❌ Environment check failed. Please fix the issues above.")
        exit(1)
    
    print("\n" + "=" * 40)
    
    # Wait a moment for the user to start the server if needed
    print("Make sure the API server is running:")
    print("Run: python src/api/chat.py")
    print("Then press Enter to continue...")
    input()
    
    # Run the tests
    success = test_api()
    
    if success:
        exit(0)
    else:
        exit(1)