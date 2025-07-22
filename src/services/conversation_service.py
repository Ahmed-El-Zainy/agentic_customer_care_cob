
# app/services/conversation_service.py
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from src.models.database import Conversation, Message, Workflow
from src.models.schemas import ChatResponse, IntentType
from src.services.gemini_service import GeminiService
from src.services.intent_service import IntentService
from src.services.knowledge_service import KnowledgeService
from src.core.database import SessionLocal
from src.core.config import settings
import sys
import os 



# Add the parent directories to the path for custom logger import
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(os.path.dirname(SCRIPT_DIR)))
try:
    from logger.custom_logger import CustomLoggerTracker
    logger_tracker = CustomLoggerTracker()
    logger = logger_tracker.get_logger("websocker_manager")
    logger.info("Logger start at websocker_manager")
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("clinic_data")
    logger.info("Using standard logger - custom logger not available")





class ConversationService:
    def __init__(self):
        self.gemini_service = GeminiService()
        self.intent_service = IntentService()
        self.knowledge_service = KnowledgeService()
    
    async def process_message(
        self, 
        session_id: str, 
        user_message: str, 
        user_id: str = "anonymous"
    ) -> Dict[str, Any]:
        """Process user message through the complete chatbot pipeline."""
        
        db = SessionLocal()
        try:
            # Get or create conversation
            conversation = self._get_or_create_conversation(db, session_id, user_id)
            
            # Classify intent
            intent_result = await self.intent_service.classify_intent(user_message)
            
            # Save user message
            self._save_message(
                db, conversation.id, "user", user_message,
                intent_result.intent.value, intent_result.confidence, intent_result.entities
            )
            
            # Check if escalation is needed
            requires_escalation = self.intent_service.should_escalate(
                intent_result.confidence, user_message
            )
            
            if requires_escalation:
                response_text = await self._handle_escalation(db, conversation)
            else:
                # Route to appropriate handler based on intent
                response_text = await self._route_intent(
                    db, conversation, user_message, intent_result
                )
            
            # Save assistant response
            self._save_message(db, conversation.id, "assistant", response_text)
            
            # Generate suggestions
            suggestions = await self._generate_suggestions(intent_result.intent)
            
            return {
                "response": response_text,
                "intent": intent_result.intent.value,
                "confidence": intent_result.confidence,
                "entities": intent_result.entities,
                "suggestions": suggestions,
                "requires_escalation": requires_escalation,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return {
                "response": "I apologize, but I'm experiencing some technical difficulties. Please try again in a moment.",
                "intent": "error",
                "confidence": 0.0,
                "entities": {},
                "suggestions": ["Try again", "Contact support"],
                "requires_escalation": True,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }
        finally:
            db.close()
    
    def _get_or_create_conversation(self, db: Session, session_id: str, user_id: str) -> Conversation:
        """Get existing conversation or create new one."""
        conversation = db.query(Conversation).filter(
            Conversation.session_id == session_id
        ).first()
        
        if not conversation:
            conversation = Conversation(
                session_id=session_id,
                user_id=user_id,
                status="active"
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
        
        return conversation
    
    def _save_message(
        self, db: Session, conversation_id, role: str, content: str,
        intent: str = None, confidence: float = None, entities: Dict = None
    ):
        """Save message to database."""
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            intent=intent,
            confidence=confidence,
            entities=entities or {}
        )
        db.add(message)
        db.commit()
    
    async def _route_intent(
        self, db: Session, conversation: Conversation, user_message: str, intent_result
    ) -> str:
        """Route message to appropriate handler based on intent."""
        
        # Get conversation history for context
        context = self._get_conversation_context(db, conversation.id)
        
        if intent_result.intent == IntentType.KNOWLEDGE_QUERY:
            knowledge_result = await self.knowledge_service.search_knowledge(user_message)
            return knowledge_result.answer
        
        elif intent_result.intent == IntentType.BOOKING:
            return await self._handle_booking(db, conversation, user_message, intent_result.entities)
        
        elif intent_result.intent == IntentType.SUPPORT:
            return await self.gemini_service.generate_contextual_response(
                user_message, "support", context
            )
        
        elif intent_result.intent == IntentType.COMPLAINT:
            return await self._handle_complaint(user_message, context)
        
        else:  # CHITCHAT or other
            return await self.gemini_service.generate_contextual_response(
                user_message, "chitchat", context
            )
    
    async def _handle_booking(
        self, db: Session, conversation: Conversation, user_message: str, entities: Dict
    ) -> str:
        """Handle booking-related requests."""
        
        # Check if workflow already exists
        existing_workflow = db.query(Workflow).filter(
            Workflow.conversation_id == conversation.id,
            Workflow.workflow_type == "booking",
            Workflow.state.in_(["initiated", "in_progress"])
        ).first()
        
        if not existing_workflow:
            # Create new booking workflow
            workflow = Workflow(
                conversation_id=conversation.id,
                workflow_type="booking",
                state="initiated",
                data={"entities"})
            