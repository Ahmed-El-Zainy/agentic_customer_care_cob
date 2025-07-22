
# app/models/schemas.py
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class IntentType(str, Enum):
    KNOWLEDGE_QUERY = "knowledge_query"
    ACTION_REQUEST = "action_request"
    BOOKING = "booking"
    CHITCHAT = "chitchat"
    COMPLAINT = "complaint"
    ESCALATION = "escalation"
    SUPPORT = "support"

class ChatMessage(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    session_id: str = Field(..., min_length=1)
    user_id: Optional[str] = "anonymous"
    metadata: Optional[Dict[str, Any]] = {}

class ChatResponse(BaseModel):
    response: str
    intent: IntentType
    confidence: float
    entities: Dict[str, Any] = {}
    suggestions: List[str] = []
    requires_escalation: bool = False
    session_id: str
    timestamp: datetime

class ConversationHistory(BaseModel):
    session_id: str
    messages: List[Dict[str, Any]]
    status: str
    created_at: datetime

class IntentResult(BaseModel):
    intent: IntentType
    confidence: float
    entities: Dict[str, Any] = {}

class KnowledgeQueryResult(BaseModel):
    answer: str
    sources: List[str] = []
    confidence: float

