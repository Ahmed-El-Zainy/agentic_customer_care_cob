
from sqlalchemy import Column, String, DateTime, Text, Float, JSON, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.core.database import Base
import uuid

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(255), unique=True, index=True)
    user_id = Column(String(255), index=True)
    status = Column(String(50), default="active")  # active, escalated, closed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    messages = relationship("Message", back_populates="conversation")
    workflows = relationship("Workflow", back_populates="conversation")

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_metadata = Column(JSON)  # ✅ Safe name
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"))
    role = Column(String(20))  # user, assistant, system
    content = Column(Text)
    intent = Column(String(100))
    confidence = Column(Float)
    entities = Column(JSON)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

class Workflow(Base):
    __tablename__ = "workflows"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"))
    workflow_type = Column(String(100))  # booking, support, escalation
    state = Column(String(50))  # initiated, in_progress, completed, failed
    data = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    
    # Relationships
    conversation = relationship("Conversation", back_populates="workflows")

class KnowledgeBase(Base):
    __tablename__ = "knowledge_base"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500))
    content = Column(Text)
    document_type = Column(String(100))  # faq, guide, policy
    tags = Column(JSON)
    embedding_vector = Column(JSON)  # Store as JSON for simplicity
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
