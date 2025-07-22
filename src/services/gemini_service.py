

# app/services/gemini_service.py
import google.generativeai as genai
from typing import Optional, Dict, Any, List
import logging
import json
from src.core.config import settings
import os 
import sys


# Add the parent directories to the path for custom logger import
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(os.path.dirname(SCRIPT_DIR)))
try:
    from logger.custom_logger import CustomLoggerTracker
    logger_tracker = CustomLoggerTracker()
    logger = logger_tracker.get_logger("gemini service")
    logger.info("Logger start at gemini service ")
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("gemini service")
    logger.info("Using standard logger - custom logger not available")



class GeminiService:
    def __init__(self):
        """Initialize Gemini service with API key and configuration."""
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is required")
        
        genai.configure(api_key=settings.GEMINI_API_KEY)
        
        # Configure generation settings
        self.generation_config = {
            "temperature": settings.GEMINI_TEMPERATURE,
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": settings.GEMINI_MAX_TOKENS,
        }
        
        # Safety settings
        self.safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        ]
        
        # Initialize model
        self.model = genai.GenerativeModel(
            model_name=settings.GEMINI_MODEL,
            generation_config=self.generation_config,
            safety_settings=self.safety_settings
        )
        
        logger.info(f"GeminiService initialized with model: {settings.GEMINI_MODEL}")
    
    async def generate_response(
        self, 
        prompt: str, 
        context: Optional[List[Dict[str, str]]] = None,
        system_instruction: Optional[str] = None
    ) -> str:
        """Generate response using Gemini model."""
        try:
            # Prepare conversation history
            chat_history = []
            if context:
                for msg in context:
                    chat_history.extend([
                        {"role": "user", "parts": [msg.get("user", "")]},
                        {"role": "model", "parts": [msg.get("assistant", "")]}
                    ])
            
            # Start chat session
            chat = self.model.start_chat(history=chat_history)
            
            # Add system instruction to prompt if provided
            if system_instruction:
                prompt = f"{system_instruction}\n\nUser: {prompt}"
            
            # Generate response
            response = chat.send_message(prompt)
            
            return response.text
            
        except Exception as e:
            logger.error(f"Error generating Gemini response: {str(e)}")
            return "I apologize, but I'm having trouble processing your request right now. Please try again."
    
    async def classify_intent(self, user_message: str) -> Dict[str, Any]:
        """Classify user intent using Gemini."""
        intent_prompt = f"""
Analyze this user message and classify the intent. Return a JSON response with the following structure:
{{
    "intent": "one of: knowledge_query, action_request, booking, chitchat, complaint, escalation, support",
    "confidence": 0.0-1.0,
    "entities": {{
        "extracted_entities": "value"
    }}
}}

User message: "{user_message}"

Classification guidelines:
- knowledge_query: User asking for information or facts
- action_request: User wants to perform a specific action
- booking: User wants to schedule/book something
- chitchat: Casual conversation, greetings
- complaint: User expressing dissatisfaction
- escalation: User wants to speak to human agent
- support: Technical help or troubleshooting

Respond with only the JSON, no additional text.
"""
        
        try:
            response = await self.generate_response(intent_prompt)
            # Parse JSON response
            result = json.loads(response.strip())
            return result
        except Exception as e:
            logger.error(f"Error classifying intent: {str(e)}")
            return {
                "intent": "chitchat",
                "confidence": 0.3,
                "entities": {}
            }
    
    async def generate_contextual_response(
        self, 
        user_message: str,
        intent: str,
        context: Optional[List[Dict[str, str]]] = None,
        knowledge_context: Optional[str] = None
    ) -> str:
        """Generate contextual response based on intent and available context."""
        
        system_instructions = {
            "knowledge_query": "You are a helpful assistant that provides accurate, informative answers based on the knowledge context provided. If you don't have specific information, acknowledge this and offer to help in other ways.",
            "booking": "You are a booking assistant. Help users schedule appointments or reservations. Ask for necessary details like date, time, service type, and contact information.",
            "support": "You are a technical support assistant. Help users troubleshoot issues step by step. Ask clarifying questions to understand the problem better.",
            "complaint": "You are an empathetic customer service representative. Listen to concerns, apologize for issues, and work toward resolution. Escalate if necessary.",
            "chitchat": "You are a friendly conversational assistant. Engage naturally and help users feel comfortable.",
            "escalation": "Acknowledge the user's request to speak with a human agent. Explain the escalation process and gather any necessary information.",
            "action_request": "Help users accomplish specific tasks. Break down complex requests into manageable steps."
        }
        
        system_instruction = system_instructions.get(intent, system_instructions["chitchat"])
        
        # Add knowledge context if available
        enhanced_prompt = user_message
        if knowledge_context:
            enhanced_prompt = f"Context: {knowledge_context}\n\nUser question: {user_message}"
        
        return await self.generate_response(
            enhanced_prompt, 
            context=context,
            system_instruction=system_instruction
        )

