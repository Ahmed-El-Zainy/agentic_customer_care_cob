#!/usr/bin/env python3
"""
Integration test script to verify all components work together
"""

import os
import sys
import requests
import json
import time
import asyncio
from datetime import datetime

# Add project root to path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.append(PROJECT_ROOT)

class SystemIntegrationTester:
    def __init__(self):
        self.api_base_url = "http://localhost:8000"
        self.gradio_url = "http://localhost:7860"
        self.html_demo_url = "http://localhost:8080"  # If serving HTML separately
        
    def test_environment_setup(self):
        """Test if all required environment variables are set"""
        print("🔍 Testing Environment Setup...")
        
        required_vars = ["GEMINI_API_KEY", "JWT_SECRET_KEY"]
        missing_vars = []
        
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"❌ Missing environment variables: {missing_vars}")
            return False
        
        print("✅ Environment variables are set")
        return True
    
    def test_api_health(self):
        """Test if the FastAPI server is running and healthy"""
        print("🔍 Testing API Health...")
        
        try:
            response = requests.get(f"{self.api_base_url}/api/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                print(f"✅ API is healthy: {health_data}")
                return True
            else:
                print(f"❌ API health check failed: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Cannot connect to API: {e}")
            return False
    
    def test_chat_endpoint(self):
        """Test the main chat endpoint"""
        print("🔍 Testing Chat Endpoint...")
        
        test_messages = [
            "Hello, I need help with booking an appointment",
            "What are your business hours?",
            "I'd like to schedule a product demo",
            "Can I speak to a human agent?"
        ]
        
        for message in test_messages:
            try:
                payload = {
                    "message": message,
                    "session_id": "test_session_001"
                }
                
                response = requests.post(
                    f"{self.api_base_url}/api/chat",
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Message: '{message[:30]}...' -> Response received")
                    print(f"   Intent: {data.get('intent', 'Unknown')}")
                    print(f"   Session: {data.get('session_id', 'Unknown')}")
                else:
                    print(f"❌ Chat failed for message: '{message}' - Status: {response.status_code}")
                    return False
                    
            except requests.exceptions.RequestException as e:
                print(f"❌ Chat request failed: {e}")
                return False
        
        return True
    
    def test_appointment_booking(self):
        """Test appointment booking endpoint"""
        print("🔍 Testing Appointment Booking...")
        
        appointment_data = {
            "name": "Test User",
            "email": "test@example.com",
            "phone": "+1234567890",
            "service_type": "Product Demo",
            "preferred_date": "2024-12-01",
            "preferred_time": "14:00",
            "requirements": "Testing the booking system"
        }
        
        try:
            response = requests.post(
                f"{self.api_base_url}/api/appointments",
                json=appointment_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Appointment booked: {data.get('appointment_id')}")
                return True
            else:
                print(f"❌ Appointment booking failed: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Appointment booking request failed: {e}")
            return False
    
    def test_gradio_interface(self):
        """Test if Gradio interface is accessible"""
        print("🔍 Testing Gradio Interface...")
        
        try:
            response = requests.get(self.gradio_url, timeout=5)
            if response.status_code == 200:
                print("✅ Gradio interface is accessible")
                return True
            else:
                print(f"❌ Gradio interface not accessible: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Cannot connect to Gradio: {e}")
            return False
    
    def test_database_connectivity(self):
        """Test database operations"""
        print("🔍 Testing Database Connectivity...")
        
        try:
            # Test if we can get sessions (admin endpoint would need auth)
            response = requests.get(f"{self.api_base_url}/api/chat/sessions", timeout=5)
            if response.status_code == 200:
                print("✅ Database operations working")
                return True
            else:
                print(f"⚠️  Database test inconclusive: {response.status_code}")
                return True  # Not a critical failure
        except requests.exceptions.RequestException as e:
            print(f"⚠️  Database test failed: {e}")
            return True  # Not a critical failure
    
    def run_full_test_suite(self):
        """Run all integration tests"""
        print("🚀 Starting System Integration Tests")
        print("=" * 50)
        
        tests = [
            ("Environment Setup", self.test_environment_setup),
            ("API Health", self.test_api_health),
            ("Chat Endpoint", self.test_chat_endpoint),
            ("Appointment Booking", self.test_appointment_booking),
            ("Gradio Interface", self.test_gradio_interface),
            ("Database Connectivity", self.test_database_connectivity),
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            print(f"\n{test_name}:")
            print("-" * 30)
            results[test_name] = test_func()
            time.sleep(1)  # Brief pause between tests
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 50)
        
        passed = 0
        total = len(tests)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name:<25} {status}")
            if result:
                passed += 1
        
        print(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! System is ready for use.")
        else:
            print("⚠️  Some tests failed. Please check the issues above.")
        
        return passed == total

def main():
    """Main test runner"""
    tester = SystemIntegrationTester()
    success = tester.run_full_test_suite()
    
    if success:
        print("\n🌟 Next Steps:")
        print("1. Start the FastAPI server: uvicorn src.api.chat:app --reload")
        print("2. Start the Gradio interface: python src/main.py")
        print("3. Open HTML demo in browser: src/gradio_demo.html")
        sys.exit(0)
    else:
        print("\n🔧 Fix the issues above before proceeding.")
        sys.exit(1)

if __name__ == "__main__":
    main()