

# app/main.py
from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
import logging
import uvicorn
from typing import List
import json

from src.core.config import settings
from src.core.database import engine, SessionLocal
from src.models.database import Base
from src.services.gemini_service import GeminiService
from src.services.intent_service import IntentService
from src.services.knowledge_service import KnowledgeService
from src.services.conversation_service import ConversationService
from src.api.chat import chat_router
from src.api.admin import admin_router
from src.core.websocket_manager import ConnectionManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Gemini Chatbot Service...")
    # Initialize database tables
    Base.metadata.create_all(bind=engine)
    # Initialize services
    app.state.gemini_service = GeminiService()
    app.state.intent_service = IntentService()
    app.state.knowledge_service = KnowledgeService()
    app.state.conversation_service = ConversationService()
    app.state.connection_manager = ConnectionManager()
    yield
    # Shutdown
    logger.info("Shutting down Gemini Chatbot Service...")

app = FastAPI(
    title="Gemini Chatbot Service",
    description="Advanced AI Chatbot powered by Google Gemini",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure based on your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Include routers
app.include_router(chat_router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(admin_router, prefix="/api/v1/admin", tags=["admin"])

@app.get("/")
async def root():
    return {"message": "Gemini Chatbot Service is running!", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "gemini-chatbot"}

# WebSocket endpoint for real-time chat
@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await app.state.connection_manager.connect(websocket, session_id)
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Process message through chatbot pipeline
            response = await app.state.conversation_service.process_message(
                session_id=session_id,
                user_message=message_data["message"],
                user_id=message_data.get("user_id", "anonymous")
            )
            
            # Send response back to client
            await app.state.connection_manager.send_message(
                session_id, json.dumps(response)
            )
    except WebSocketDisconnect:
        app.state.connection_manager.disconnect(session_id)

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if settings.ENVIRONMENT == "development" else False
    )
