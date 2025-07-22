
# app/services/knowledge_service.py
from typing import List, Dict, Any, Optional
import logging
from sqlalchemy.orm import Session
from src.models.database import KnowledgeBase
from src.models.schemas import KnowledgeQueryResult
from src.services.gemini_service import GeminiService
from src.core.database import get_db

import os 
import sys


# Add the parent directories to the path for custom logger import
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(os.path.dirname(SCRIPT_DIR)))
try:
    from logger.custom_logger import CustomLoggerTracker
    logger_tracker = CustomLoggerTracker()
    logger = logger_tracker.get_logger("Knowledge service")
    logger.info("Logger start at Knowledge service ")
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("Knowledge service")
    logger.info("Using standard logger - custom logger not available")


class KnowledgeService:
    def __init__(self):
        self.gemini_service = GeminiService()
        
        # Sample knowledge base - in production, this would come from database/vector store
        self.knowledge_base = [
            {
                "title": "Business Hours",
                "content": "We are open Monday through Friday from 9:00 AM to 6:00 PM, and Saturday from 10:00 AM to 4:00 PM. We are closed on Sundays and major holidays.",
                "tags": ["hours", "schedule", "availability"]
            },
            {
                "title": "Booking Policy",
                "content": "Appointments can be booked up to 30 days in advance. We require 24-hour notice for cancellations to avoid charges. Same-day appointments are subject to availability.",
                "tags": ["booking", "appointment", "cancellation"]
            },
            {
                "title": "Services Offered",
                "content": "We offer consultation services, technical support, training sessions, and custom solutions. Each service can be booked individually or as part of a package.",
                "tags": ["services", "offerings", "consultation"]
            },
            {
                "title": "Contact Information",
                "content": "You can reach us at support@example.com or call us at +1 (555) 123-4567. For urgent matters, use our 24/7 emergency hotline at +1 (555) 999-0000.",
                "tags": ["contact", "support", "phone", "email"]
            }
        ]
    
    async def search_knowledge(self, query: str) -> KnowledgeQueryResult:
        """Search knowledge base and generate answer using Gemini."""
        try:
            # Simple keyword-based search (in production, use vector similarity)
            relevant_docs = self._search_documents(query)
            
            if not relevant_docs:
                return KnowledgeQueryResult(
                    answer="I don't have specific information about that topic. Could you please rephrase your question or ask about something else?",
                    sources=[],
                    confidence=0.2
                )
            
            # Combine relevant documents as context
            context = "\n\n".join([doc["content"] for doc in relevant_docs[:3]])
            
            # Generate answer using Gemini with context
            answer = await self.gemini_service.generate_contextual_response(
                user_message=query,
                intent="knowledge_query",
                knowledge_context=context
            )
            
            sources = [doc["title"] for doc in relevant_docs[:3]]
            
            return KnowledgeQueryResult(
                answer=answer,
                sources=sources,
                confidence=0.8 if len(relevant_docs) > 0 else 0.3
            )
            
        except Exception as e:
            logger.error(f"Error searching knowledge base: {str(e)}")
            return KnowledgeQueryResult(
                answer="I'm sorry, I'm having trouble accessing information right now. Please try again later.",
                sources=[],
                confidence=0.1
            )
    
    def _search_documents(self, query: str) -> List[Dict[str, Any]]:
        """Simple keyword-based document search."""
        query_lower = query.lower()
        relevant_docs = []
        
        for doc in self.knowledge_base:
            score = 0
            
            # Check title
            if any(word in doc["title"].lower() for word in query_lower.split()):
                score += 2
            
            # Check content
            if any(word in doc["content"].lower() for word in query_lower.split()):
                score += 1
            
            # Check tags
            for tag in doc.get("tags", []):
                if any(word in tag.lower() for word in query_lower.split()):
                    score += 1.5
            
            if score > 0:
                doc_copy = doc.copy()
                doc_copy["relevance_score"] = score
                relevant_docs.append(doc_copy)
        
        # Sort by relevance score
        relevant_docs.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        return relevant_docs



if __name__=="__main__":
    logger.info(f"Starting ...")