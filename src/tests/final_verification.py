#!/usr/bin/env python3
"""
Final Integration Verification Script for COB Company Chatbot System
This script performs comprehensive testing to ensure all components work together properly.
"""

import os
import sys
import requests
import json
import time
import subprocess
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional

class COBSystemVerifier:
    def __init__(self):
        self.api_base_url = "http://localhost:8000"
        self.gradio_url = "http://localhost:7860"
        self.html_demo_url = "http://localhost:8080"
        self.test_results = {}
        self.critical_failures = []
        
    def print_header(self, title: str):
        """Print formatted header"""
        print(f"\n{'='*60}")
        print(f"🔍 {title}")
        print(f"{'='*60}")
    
    def print_step(self, step: str):
        """Print test step"""
        print(f"\n📋 {step}")
        print("-" * 40)
    
    def print_result(self, test_name: str, passed: bool, message: str = ""):
        """Print test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:<35} {status}")
        if message:
            print(f"    💬 {message}")
        
        self.test_results[test_name] = passed
        if not passed:
            self.critical_failures.append(f"{test_name}: {message}")
    
    def check_environment(self) -> bool:
        """Verify environment setup"""
        self.print_step("Environment Setup Verification")
        
        # Check Python version
        python_version = sys.version_info
        if python_version.major >= 3 and python_version.minor >= 8:
            self.print_result("Python Version", True, f"Python {python_version.major}.{python_version.minor}")
        else:
            self.print_result("Python Version", False, f"Python {python_version.major}.{python_version.minor} - Need 3.8+")
            return False
        
        # Check required environment variables
        required_vars = {
            "GEMINI_API_KEY": "Gemini API key for AI functionality",
            "JWT_SECRET_KEY": "JWT secret for authentication (optional)"
        }
        
        env_ok = True
        for var, description in required_vars.items():
            if os.getenv(var):
                self.print_result(f"Env Var: {var}", True, "Set")
            else:
                is_critical = var == "GEMINI_API_KEY"
                self.print_result(f"Env Var: {var}", not is_critical, f"Not set - {description}")
                if is_critical:
                    env_ok = False
        
        # Check project structure
        required_files = [
            "src/main.py",
            "src/api/chat.py", 
            "src/gradio_demo.html",
            "requirements.txt"
        ]
        
        for file_path in required_files:
            if os.path.exists(file_path):
                self.print_result(f"File: {file_path}", True, "Found")
            else:
                self.print_result(f"File: {file_path}", False, "Missing")
                env_ok = False
        
        return env_ok
    
    def check_dependencies(self) -> bool:
        """Check if all required dependencies are installed"""
        self.print_step("Dependencies Verification")
        
        required_packages = [
            "fastapi",
            "uvicorn", 
            "gradio",
            "google.generativeai",
            "pydantic",
            "sqlalchemy",
            "requests"
        ]
        
        deps_ok = True
        for package in required_packages:
            try:
                __import__(package.replace("-", "_"))
                self.print_result(f"Package: {package}", True, "Installed")
            except ImportError:
                self.print_result(f"Package: {package}", False, "Not installed")
                deps_ok = False
        
        return deps_ok
    
    def check_database(self) -> bool:
        """Check database connectivity and setup"""
        self.print_step("Database Verification")
        
        try:
            # Test SQLite connection
            db_path = "cob_system_2.db"
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Test basic query
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            
            conn.close()
            
            self.print_result("Database Connection", True, f"SQLite connected: {db_path}")
            return True
            
        except Exception as e:
            self.print_result("Database Connection", False, f"Error: {str(e)}")
            return False
    
    def test_api_server(self) -> bool:
        """Test FastAPI server functionality"""
        self.print_step("API Server Testing")
        
        # Test health endpoint
        try:
            response = requests.get(f"{self.api_base_url}/api/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                self.print_result("API Health Check", True, f"Status: {health_data.get('status', 'unknown')}")
            else:
                self.print_result("API Health Check", False, f"HTTP {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            self.print_result("API Health Check", False, f"Connection failed: {str(e)}")
            return False
        
        # Test chat endpoint
        try:
            chat_payload = {
                "message": "Hello, I need information about your services",
                "session_id": "test_verification_001"
            }
            
            response = requests.post(
                f"{self.api_base_url}/api/chat",
                json=chat_payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.print_result("Chat Endpoint", True, f"Response received, Intent: {data.get('intent', 'N/A')}")
            else:
                error_detail = response.json().get('detail', 'Unknown error') if response.content else 'No response'
                self.print_result("Chat Endpoint", False, f"HTTP {response.status_code}: {error_detail}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.print_result("Chat Endpoint", False, f"Request failed: {str(e)}")
            return False
        
        # Test appointment booking
        try:
            appointment_data = {
                "name": "Test Verification User",
                "email": "test@verification.com",
                "phone": "+1234567890",
                "service_type": "Product Demo",
                "preferred_date": "2024-12-15",
                "preferred_time": "14:00",
                "requirements": "System verification test"
            }
            
            response = requests.post(
                f"{self.api_base_url}/api/appointments",
                json=appointment_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.print_result("Appointment Booking", True, f"Appointment ID: {data.get('appointment_id', 'N/A')}")
            else:
                self.print_result("Appointment Booking", False, f"HTTP {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            self.print_result("Appointment Booking", False, f"Request failed: {str(e)}")
        
        return True
    
    def test_gradio_interface(self) -> bool:
        """Test Gradio interface accessibility"""
        self.print_step("Gradio Interface Testing")
        
        try:
            response = requests.get(self.gradio_url, timeout=10)
            if response.status_code == 200:
                # Check if it's actually Gradio by looking for specific content
                if "gradio" in response.text.lower() or "interface" in response.text.lower():
                    self.print_result("Gradio Accessibility", True, "Interface loaded successfully")
                    return True
                else:
                    self.print_result("Gradio Accessibility", False, "Page loaded but may not be Gradio")
                    return False
            else:
                self.print_result("Gradio Accessibility", False, f"HTTP {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.print_result("Gradio Accessibility", False, f"Connection failed: {str(e)}")
            return False
    
    def test_html_demo(self) -> bool:
        """Test HTML demo functionality"""
        self.print_step("HTML Demo Testing")
        
        # Check if HTML file exists and is valid
        html_file = "src/gradio_demo.html"
        if os.path.exists(html_file):
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Basic HTML validation
            if "<html" in content and "</html>" in content:
                self.print_result("HTML File Structure", True, "Valid HTML structure")
            else:
                self.print_result("HTML File Structure", False, "Invalid HTML structure")
                return False
            
            # Check for API integration
            if "localhost:8000" in content or "API_BASE_URL" in content:
                self.print_result("API Integration", True, "API endpoints configured")
            else:
                self.print_result("API Integration", False, "API integration not found")
                
            # Test HTTP server accessibility (if running)
            try:
                response = requests.get(f"{self.html_demo_url}/gradio_demo.html", timeout=5)
                if response.status_code == 200:
                    self.print_result("HTML Server", True, "Accessible via HTTP server")
                else:
                    self.print_result("HTML Server", False, f"HTTP {response.status_code}")
            except requests.exceptions.RequestException:
                self.print_result("HTML Server", False, "HTTP server not running (optional)")
                
        else:
            self.print_result("HTML File", False, f"File not found: {html_file}")
            return False
        
        return True
    
    def test_end_to_end_integration(self) -> bool:
        """Test complete end-to-end functionality"""
        self.print_step("End-to-End Integration Testing")
        
        # Test conversation flow through API
        test_messages = [
            ("Hello", "greeting"),
            ("What services do you offer?", "kb_query"),
            ("I want to schedule a demo", "action_request"),
            ("My name is John Test", "confirmation"),
        ]
        
        session_id = f"e2e_test_{int(time.time())}"
        conversation_success = True
        
        for i, (message, expected_intent) in enumerate(test_messages):
            try:
                payload = {
                    "message": message,
                    "session_id": session_id
                }
                
                response = requests.post(
                    f"{self.api_base_url}/api/chat",
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    intent = data.get('intent', '').lower()
                    self.print_result(f"E2E Step {i+1}: {message[:20]}...", True, f"Intent: {intent}")
                else:
                    self.print_result(f"E2E Step {i+1}: {message[:20]}...", False, f"HTTP {response.status_code}")
                    conversation_success = False
                    
            except requests.exceptions.RequestException as e:
                self.print_result(f"E2E Step {i+1}: {message[:20]}...", False, f"Request failed: {str(e)}")
                conversation_success = False
        
        return conversation_success
    
    def generate_deployment_report(self):
        """Generate a comprehensive deployment report"""
        self.print_header("DEPLOYMENT READINESS REPORT")
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)
        
        print(f"📊 Overall Status: {passed_tests}/{total_tests} tests passed")
        print(f"📈 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if passed_tests == total_tests:
            print("\n🎉 SYSTEM READY FOR DEPLOYMENT!")
            print("✅ All critical components are working correctly")
            print("✅ API integration is functional")
            print("✅ All interfaces are accessible")
        elif len(self.critical_failures) == 0:
            print("\n⚠️  SYSTEM MOSTLY READY")
            print("✅ Core functionality works")
            print("⚠️  Some minor issues detected (see above)")
        else:
            print("\n❌ SYSTEM NOT READY FOR DEPLOYMENT")
            print("❌ Critical issues need to be resolved:")
            for failure in self.critical_failures:
                print(f"   • {failure}")
        
        print(f"\n📝 Next Steps:")
        if passed_tests == total_tests:
            print("1. ✅ Start all services: ./start_system.sh")
            print("2. ✅ Access Gradio at: http://localhost:7860")
            print("3. ✅ Access HTML demo at: http://localhost:8080/gradio_demo.html")
            print("4. ✅ Monitor logs in the logs/ directory")
        else:
            print("1. 🔧 Fix the failing tests shown above")
            print("2. 📦 Install missing dependencies: pip install -r requirements.txt")
            print("3. 🔑 Set environment variables in .env file")
            print("4. 🔄 Run this verification script again")
    
    def run_full_verification(self):
        """Run complete system verification"""
        self.print_header("COB COMPANY CHATBOT SYSTEM VERIFICATION")
        print("🏥 Healthcare Technology Solutions - Integration Test")
        print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Run all verification steps
        verification_steps = [
            ("Environment Setup", self.check_environment),
            ("Dependencies", self.check_dependencies),
            ("Database", self.check_database),
            ("API Server", self.test_api_server),
            ("Gradio Interface", self.test_gradio_interface),
            ("HTML Demo", self.test_html_demo),
            ("End-to-End Integration", self.test_end_to_end_integration),
        ]
        
        for step_name, step_function in verification_steps:
            try:
                step_function()
            except Exception as e:
                self.print_result(f"{step_name} - Critical Error", False, str(e))
                
            time.sleep(1)  # Brief pause between steps
        
        # Generate final report
        self.generate_deployment_report()

def main():
    """Main verification runner"""
    print("🔍 COB Company Chatbot System Verifier")
    print("=" * 50)
    
    verifier = COBSystemVerifier()
    
    # Check if we should test running services
    if len(sys.argv) > 1 and sys.argv[1] == "--services-only":
        print("🔧 Testing only running services...")
        verifier.test_api_server()
        verifier.test_gradio_interface()
        verifier.test_html_demo()
        verifier.test_end_to_end_integration()
    else:
        # Run full verification
        verifier.run_full_verification()
    
    # Exit with appropriate code
    total_tests = len(verifier.test_results)
    passed_tests = sum(1 for result in verifier.test_results.values() if result)
    
    if passed_tests == total_tests:
        print(f"\n🎊 All systems go! Ready for deployment.")
        sys.exit(0)
    else:
        print(f"\n🔧 {total_tests - passed_tests} issues need attention.")
        sys.exit(1)

if __name__ == "__main__":
    main()