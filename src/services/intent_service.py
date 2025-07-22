
# app/services/intent_service.py
from typing import Dict, Any
import logging
from src.models.schemas import IntentType, IntentResult
from src.services.gemini_service import GeminiService
import os 
import sys


# Add the parent directories to the path for custom logger import
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(os.path.dirname(SCRIPT_DIR)))
try:
    from logger.custom_logger import CustomLoggerTracker
    logger_tracker = CustomLoggerTracker()
    logger = logger_tracker.get_logger("intent service")
    logger.info("Logger start at intent service ")
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("intent service")
    logger.info("Using standard logger - custom logger not available")

class IntentService:
    def __init__(self):
        self.gemini_service = GeminiService()
    
    async def classify_intent(self, user_message: str) -> IntentResult:
        """Classify user intent using Gemini AI."""
        try:
            # Use Gemini for intent classification
            classification_result = await self.gemini_service.classify_intent(user_message)
            
            # Map to our intent types
            intent_mapping = {
                "knowledge_query": IntentType.KNOWLEDGE_QUERY,
                "action_request": IntentType.ACTION_REQUEST,
                "booking": IntentType.BOOKING,
                "chitchat": IntentType.CHITCHAT,
                "complaint": IntentType.COMPLAINT,
                "escalation": IntentType.ESCALATION,
                "support": IntentType.SUPPORT
            }
            
            intent_str = classification_result.get("intent", "chitchat")
            intent = intent_mapping.get(intent_str, IntentType.CHITCHAT)
            confidence = classification_result.get("confidence", 0.5)
            entities = classification_result.get("entities", {})
            
            logger.info(f"Intent classified: {intent} (confidence: {confidence})")
            
            return IntentResult(
                intent=intent,
                confidence=confidence,
                entities=entities
            )
            
        except Exception as e:
            logger.error(f"Error classifying intent: {str(e)}")
            # Fallback to chitchat with low confidence
            return IntentResult(
                intent=IntentType.CHITCHAT,
                confidence=0.3,
                entities={}
            )
    
    def should_escalate(self, confidence: float, user_message: str) -> bool:
        """Determine if conversation should be escalated to human."""
        # Escalate if confidence is too low
        if confidence < 0.4:
            return True
        
        # Check for escalation keywords
        escalation_keywords = [
            "human", "agent", "representative", "manager", "supervisor",
            "person", "talk to someone", "speak to", "frustrated", "angry"
        ]
        
        message_lower = user_message.lower()
        for keyword in escalation_keywords:
            if keyword in message_lower:
                return True
        
        return False





