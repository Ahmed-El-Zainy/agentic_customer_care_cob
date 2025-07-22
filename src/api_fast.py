from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, List, Any
import uvicorn
import os
import sys
import sqlite3
import json
from datetime import datetime
from contextlib import contextmanager

# Add the current directory to Python path for imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(SCRIPT_DIR)

# Import your existing modules
try:
    from main import GeminiChatbot, UserContext
    from synthetic_clinic_cob.generate_databases import generate_databases
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure all required modules are available")
    sys.exit(1)

# Pydantic models for API
class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    intent: Optional[str] = None
    entities: Optional[Dict[str, Any]] = None

class AppointmentRequest(BaseModel):
    customer_name: str
    email: str
    phone: str
    appointment_type: str
    preferred_date: str
    preferred_time: str
    notes: Optional[str] = None

class AppointmentResponse(BaseModel):
    appointment_id: str
    status: str
    message: str

class AvailabilityQuery(BaseModel):
    date: Optional[str] = None
    service_type: Optional[str] = None

# Initialize FastAPI app
app = FastAPI(
    title="COB Company API",
    description="Customer support chatbot and appointment booking API",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global chatbot instance
chatbot = None

@contextmanager
def get_db_connection(db_path: str):
    """Context manager for database connections"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def initialize_chatbot():
    """Initialize the chatbot with API key"""
    global chatbot
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is required")
    chatbot = GeminiChatbot(api_key)
    return chatbot

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    try:
        # Generate databases if they don't exist
        clinic_db_path = os.getenv("CLINIC_DB_PATH", "clinic_appointments_2.db")
        cob_db_path = os.getenv("COB_DB_PATH", "cob_system_2.db")
        
        if not os.path.exists(clinic_db_path) or not os.path.exists(cob_db_path):
            print("Generating databases...")
            generate_databases()
        
        # Initialize chatbot
        initialize_chatbot()
        print("✅ FastAPI server initialized successfully")
        
    except Exception as e:
        print(f"❌ Startup error: {e}")
        raise

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "COB Company API is running",
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(chat_request: ChatMessage):
    """Main chat endpoint"""
    try:
        if not chatbot:
            raise HTTPException(status_code=500, detail="Chatbot not initialized")
        
        session_id = chat_request.session_id or f"session_{datetime.now().timestamp()}"
        
        # Process message through chatbot
        response = chatbot.process_message(chat_request.message, session_id)
        
        # Get session context for additional info
        context = chatbot.get_or_create_session(session_id)
        
        return ChatResponse(
            response=response,
            session_id=session_id,
            intent=context.current_intent.value if context.current_intent else None,
            entities=context.entities
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat processing error: {str(e)}")

@app.get("/availability")
async def get_availability(date: Optional[str] = None, service_type: Optional[str] = None):
    """Get available appointment slots"""
    try:
        cob_db_path = os.getenv("COB_DB_PATH", "cob_system_2.db")
        
        with get_db_connection(cob_db_path) as conn:
            query = """
            SELECT marketer_id, marketer_name, slot_datetime, available 
            FROM marketing_availability 
            WHERE available = '1' OR available = 'True'
            """
            params = []
            
            if date:
                query += " AND DATE(slot_datetime) = ?"
                params.append(date)
            
            query += " ORDER BY slot_datetime LIMIT 50"
            
            cursor = conn.execute(query, params)
            slots = [dict(row) for row in cursor.fetchall()]
            
            return {
                "available_slots": slots,
                "count": len(slots)
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Availability query error: {str(e)}")

@app.post("/appointment", response_model=AppointmentResponse)
async def book_appointment(appointment: AppointmentRequest):
    """Book an appointment"""
    try:
        import uuid
        appointment_id = str(uuid.uuid4())[:8].upper()
        
        # Here you would typically:
        # 1. Check availability
        # 2. Update database
        # 3. Send confirmation email
        
        # For now, return success response
        return AppointmentResponse(
            appointment_id=appointment_id,
            status="confirmed",
            message=f"Appointment {appointment_id} booked successfully for {appointment.customer_name}"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Appointment booking error: {str(e)}")

@app.get("/products")
async def get_products():
    """Get available products/services"""
    try:
        cob_db_path = os.getenv("COB_DB_PATH", "cob_system_2.db")
        
        with get_db_connection(cob_db_path) as conn:
            cursor = conn.execute("SELECT * FROM products")
            products = [dict(row) for row in cursor.fetchall()]
            
            return {"products": products}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Products query error: {str(e)}")

@app.get("/session/{session_id}")
async def get_session_info(session_id: str):
    """Get session information"""
    try:
        if not chatbot or session_id not in chatbot.user_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        context = chatbot.user_sessions[session_id]
        
        return {
            "session_id": session_id,
            "current_intent": context.current_intent.value if context.current_intent else None,
            "current_action": context.current_action.value if context.current_action else None,
            "conversation_length": len(context.conversation_history),
            "collected_info": context.collected_info,
            "awaiting_confirmation": context.awaiting_confirmation
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Session query error: {str(e)}")

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Run the server
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )