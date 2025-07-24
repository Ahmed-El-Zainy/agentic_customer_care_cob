# agentic_customer_care_cob
Basic Architecure Digram for the seqenece of actions and workflow for the project
<img src="assets/architecure_diagram.png">



## DEMO


### 🚀 **Quick Setup (5 steps):**

1. **Set your environment variables:**
```bash
export GEMINI_API_KEY="your_actual_gemini_api_key_here"
export JWT_SECRET_KEY="your-secret-key"
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Make scripts executable:**
```bash
chmod +x start_system.sh stop_services.sh
```

4. **Run the verification script:**
```bash
python final_verification.py
```

5. **Start all services:**
```bash
./start_system.sh
```
6. **End all services:**
```bash
./end_services.sh
```
-------
### 🔧 **What I've provided:**

1. **Integration Test Script** - Comprehensive testing of all components
2. **Startup Script** - One-command startup of all services
3. **Stop Script** - Clean shutdown of all services  
4. **Fixed HTML Demo** - Real API integration with error handling
5. **Enhanced main.py** - Better error handling and healthcare focus
6. **Requirements.txt** - All needed dependencies
7. **Setup Guide** - Complete documentation
8. **Verification Script** - Final deployment readiness check

### 🎯 **Key Features:**

- **Real API Integration**: HTML demo connects to your FastAPI backend
- **Error Handling**: Graceful fallbacks when services are down
- **Session Management**: Proper session tracking across interfaces
- **Health Monitoring**: Connection status indicators
- **Healthcare Focus**: Updated for COB Company's medical services
- **Comprehensive Testing**: End-to-end verification

### 🔍 **Access Points After Setup:**

- **FastAPI Server**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs  
- **Gradio Interface**: http://localhost:7860
- **HTML Demo**: http://localhost:8080/gradio_demo.html
