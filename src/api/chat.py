from fastapi import FastAPI, HTTPException, Depends, status, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List, Dict, Any, Optional
import sqlite3
import json
import os
from datetime import datetime, timedelta
import jwt
import uuid
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the parent directories to the path for imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.append(PROJECT_ROOT)

# Import the chatbot - with error handling
try:
    from main import GeminiChatbot
    logger.info("Successfully imported GeminiChatbot")
except ImportError as e:
    logger.error(f"Failed to import GeminiChatbot: {e}")
    GeminiChatbot = None

# Initialize FastAPI app
app = FastAPI(title="COB Company API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"

# Initialize chatbot with better error handling
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
chatbot = None

if GEMINI_API_KEY and GeminiChatbot:
    try:
        chatbot = GeminiChatbot(GEMINI_API_KEY)
        logger.info("Chatbot initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize chatbot: {e}")
        chatbot = None
else:
    logger.warning("Chatbot not initialized - missing API key or import failed")

# Pydantic Models
class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    intent: Optional[str] = None
    timestamp: datetime

class AppointmentRequest(BaseModel):
    name: str
    email: EmailStr
    phone: str
    service_type: str
    preferred_date: str
    preferred_time: str
    requirements: Optional[str] = None

class AppointmentResponse(BaseModel):
    appointment_id: str
    status: str
    message: str

class AdminLogin(BaseModel):
    username: str
    password: str

class AdminResponse(BaseModel):
    access_token: str
    token_type: str

class DashboardStats(BaseModel):
    total_conversations: int
    active_sessions: int
    appointments_today: int
    top_intents: List[Dict[str, Any]]

# Database helper functions
def get_db_connection():
    """Get database connection with better path handling"""
    try:
        # Try multiple possible database paths
        possible_paths = [
            "cob_system_2.db",
            "assets/data/cob_system_2.db",
            os.path.join(PROJECT_ROOT, "cob_system_2.db"),
            os.path.join(PROJECT_ROOT, "assets", "data", "cob_system_2.db")
        ]
        
        db_path = None
        for path in possible_paths:
            if os.path.exists(path):
                db_path = path
                break
        
        if not db_path:
            # Create database in current directory
            db_path = "cob_system_2.db"
            logger.info(f"Creating new database at: {db_path}")
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_admin_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify admin JWT token"""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None or username != "admin":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return username
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Chat API Endpoints
@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(message: ChatMessage):
    """Main chat endpoint for processing user messages"""
    try:
        logger.info(f"Received chat message: {message.message[:50]}...")
        
        if not chatbot:
            logger.error("Chatbot not initialized")
            # Provide fallback response when chatbot is not available
            return ChatResponse(
                response="I'm currently experiencing technical difficulties. Please try again later or contact our support team at (929) 229-7209 or support@cobcompany.com for immediate assistance.",
                session_id=message.session_id or str(uuid.uuid4())[:8],
                intent="system_error",
                timestamp=datetime.now()
            )
        
        # Generate session ID if not provided
        session_id = message.session_id or str(uuid.uuid4())[:8]
        
        # Process message
        response = chatbot.process_message(message.message, session_id)
        
        # Get user context for intent
        context = chatbot.get_or_create_session(session_id)
        intent = context.current_intent.value if context.current_intent else None
        
        # Log conversation to database
        await log_conversation(session_id, message.message, response, intent)
        
        logger.info(f"Processed message successfully for session: {session_id}")
        
        return ChatResponse(
            response=response,
            session_id=session_id,
            intent=intent,
            timestamp=datetime.now()
        )
    
    except Exception as e:
        logger.error(f"Chat processing failed: {e}", exc_info=True)
        # Return a user-friendly error message instead of raising HTTP exception
        return ChatResponse(
            response="I apologize, but I'm experiencing technical difficulties right now. Please try again in a moment, or contact our support team directly at (929) 229-7209 for immediate assistance.",
            session_id=message.session_id or str(uuid.uuid4())[:8],
            intent="error",
            timestamp=datetime.now()
        )

@app.get("/api/chat/sessions")
async def get_active_sessions():
    """Get all active chat sessions"""
    try:
        if not chatbot:
            return {"active_sessions": [], "message": "Chatbot not available"}
        
        sessions = []
        for session_id, context in chatbot.user_sessions.items():
            sessions.append({
                "session_id": session_id,
                "current_intent": context.current_intent.value if context.current_intent else None,
                "message_count": len(context.conversation_history),
                "escalation_triggers": context.escalation_triggers,
                "awaiting_confirmation": context.awaiting_confirmation
            })
        
        return {"active_sessions": sessions}
    
    except Exception as e:
        logger.error(f"Failed to get sessions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get sessions: {str(e)}")

@app.post("/api/appointments")
async def book_appointment(appointment: AppointmentRequest, background_tasks: BackgroundTasks):
    """Book an appointment"""
    try:
        appointment_id = str(uuid.uuid4())[:8].upper()
        
        # Store appointment in database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS appointments_booked (
                appointment_id TEXT PRIMARY KEY,
                name TEXT,
                email TEXT,
                phone TEXT,
                service_type TEXT,
                preferred_date TEXT,
                preferred_time TEXT,
                requirements TEXT,
                status TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            INSERT INTO appointments_booked 
            (appointment_id, name, email, phone, service_type, preferred_date, preferred_time, requirements, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'confirmed')
        """, (
            appointment_id, appointment.name, appointment.email, appointment.phone,
            appointment.service_type, appointment.preferred_date, appointment.preferred_time,
            appointment.requirements
        ))
        
        conn.commit()
        conn.close()
        
        # Add background task to send confirmation email (placeholder)
        background_tasks.add_task(send_appointment_confirmation, appointment.email, appointment_id)
        
        return AppointmentResponse(
            appointment_id=appointment_id,
            status="confirmed",
            message=f"Appointment {appointment_id} has been successfully booked. You will receive a confirmation email shortly."
        )
    
    except Exception as e:
        logger.error(f"Failed to book appointment: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to book appointment: {str(e)}")

@app.get("/api/appointments")
async def get_appointments(admin: str = Depends(verify_admin_token)):
    """Get all appointments (admin only)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM appointments_booked 
            ORDER BY created_at DESC
        """)
        
        appointments = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return {"appointments": appointments}
    
    except Exception as e:
        logger.error(f"Failed to get appointments: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get appointments: {str(e)}")

# Admin API Endpoints
@app.post("/api/admin/login", response_model=AdminResponse)
async def admin_login(credentials: AdminLogin):
    """Admin login endpoint"""
    # Simple admin authentication (replace with proper authentication)
    if credentials.username == "admin" and credentials.password == os.getenv("ADMIN_PASSWORD", "admin123"):
        access_token_expires = timedelta(hours=24)
        access_token = create_access_token(
            data={"sub": credentials.username}, expires_delta=access_token_expires
        )
        return AdminResponse(access_token=access_token, token_type="bearer")
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

@app.get("/api/admin/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(admin: str = Depends(verify_admin_token)):
    """Get dashboard statistics (admin only)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get total conversations
        cursor.execute("SELECT COUNT(*) as count FROM conversation_logs")
        result = cursor.fetchone()
        total_conversations = result["count"] if result else 0
        
        # Get active sessions
        active_sessions = len(chatbot.user_sessions) if chatbot else 0
        
        # Get appointments today
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute("""
            SELECT COUNT(*) as count FROM appointments_booked 
            WHERE DATE(created_at) = ?
        """, (today,))
        result = cursor.fetchone()
        appointments_today = result["count"] if result else 0
        
        # Get top intents
        cursor.execute("""
            SELECT intent, COUNT(*) as count FROM conversation_logs 
            WHERE intent IS NOT NULL
            GROUP BY intent 
            ORDER BY count DESC 
            LIMIT 5
        """)
        top_intents = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return DashboardStats(
            total_conversations=total_conversations,
            active_sessions=active_sessions,
            appointments_today=appointments_today,
            top_intents=top_intents
        )
    
    except Exception as e:
        logger.error(f"Failed to get dashboard stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard stats: {str(e)}")

@app.get("/api/admin/conversations")
async def get_conversations(admin: str = Depends(verify_admin_token), limit: int = 100):
    """Get conversation logs (admin only)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM conversation_logs 
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (limit,))
        
        conversations = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return {"conversations": conversations}
    
    except Exception as e:
        logger.error(f"Failed to get conversations: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get conversations: {str(e)}")

@app.delete("/api/admin/sessions/{session_id}")
async def clear_session(session_id: str, admin: str = Depends(verify_admin_token)):
    """Clear a specific session (admin only)"""
    try:
        if chatbot and session_id in chatbot.user_sessions:
            del chatbot.user_sessions[session_id]
            return {"message": f"Session {session_id} cleared successfully"}
        else:
            raise HTTPException(status_code=404, detail="Session not found")
    
    except Exception as e:
        logger.error(f"Failed to clear session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear session: {str(e)}")

# Utility Functions
async def log_conversation(session_id: str, user_message: str, bot_response: str, intent: str = None):
    """Log conversation to database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversation_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                user_message TEXT,
                bot_response TEXT,
                intent TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            INSERT INTO conversation_logs (session_id, user_message, bot_response, intent)
            VALUES (?, ?, ?, ?)
        """, (session_id, user_message, bot_response, intent))
        
        conn.commit()
        conn.close()
    
    except Exception as e:
        logger.error(f"Failed to log conversation: {e}")

async def send_appointment_confirmation(email: str, appointment_id: str):
    """Background task to send appointment confirmation email"""
    # Placeholder for email sending logic
    logger.info(f"Sending confirmation email to {email} for appointment {appointment_id}")

# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "chatbot_initialized": chatbot is not None,
        "gemini_api_key_set": bool(GEMINI_API_KEY)
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "COB Company Customer Support API",
        "version": "1.0.0",
        "status": "running",
        "chatbot_status": "initialized" if chatbot else "not_initialized",
        "endpoints": {
            "chat": "/api/chat",
            "appointments": "/api/appointments",
            "admin": "/api/admin/login",
            "health": "/api/health",
            "docs": "/docs"
        }
    }

if __name__ == "__main__":
    import uvicorn
    
    # Print startup information
    print("🚀 Starting COB Company API Server")
    print("=" * 40)
    print(f"🔑 Gemini API Key: {'✅ Set' if GEMINI_API_KEY else '❌ Not Set'}")
    print(f"🤖 Chatbot Status: {'✅ Ready' if chatbot else '❌ Not Ready'}")
    print("📡 Server will start on: http://0.0.0.0:8000")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("=" * 40)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)