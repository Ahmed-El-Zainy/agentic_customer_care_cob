import json
import re
import datetime
import os
import uuid
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import gradio as gr
import google.generativeai as genai
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IntentType(Enum):
    KNOWLEDGE_BASE_QUERY = "kb_query"
    ACTION_REQUEST = "action_request"
    HUMAN_ESCALATION = "human_escalation"
    GREETING = "greeting"
    GOODBYE = "goodbye"
    CONFIRMATION = "confirmation"


class ActionType(Enum):
    SCHEDULE_APPOINTMENT = "schedule_appointment"
    UPDATE_PROFILE = "update_profile"
    CANCEL_APPOINTMENT = "cancel_appointment"

@dataclass
class UserContext:
    """Manages user session context and conversation state"""
    session_id: str
    current_intent: Optional[IntentType] = None
    current_action: Optional[ActionType] = None
    entities: Dict[str, Any] = field(default_factory=dict)
    conversation_history: List[Dict] = field(default_factory=list)
    escalation_triggers: int = 0
    collected_info: Dict[str, Any] = field(default_factory=dict)
    awaiting_confirmation: bool = False
    
    def add_message(self, user_msg: str, bot_response: str):
        self.conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "user": user_msg,
            "bot": bot_response
        })

class KnowledgeBase:
    """Enhanced knowledge base for COB Company with comprehensive information"""
    
    def __init__(self):
        self.knowledge_data = {
            "products_services": {
                "software_solutions": {
                    "description": "COB Company offers comprehensive enterprise software solutions including Customer Relationship Management (CRM), Enterprise Resource Planning (ERP), and advanced project management tools.",
                    "features": ["Cloud-based deployment", "24/7 support", "Custom integrations", "Mobile apps", "Analytics dashboard"],
                    "pricing": "Contact our sales team for customized pricing based on your organization's needs."
                },
                "consulting_services": {
                    "description": "Our expert consultants provide IT consulting, digital transformation strategies, and business process optimization services.",
                    "specialties": ["Digital transformation", "Cloud migration", "Process automation", "Data analytics", "Cybersecurity"],
                    "engagement_models": ["Project-based", "Retainer", "Hourly consultation"]
                },
                "support_services": {
                    "description": "Comprehensive support services including 24/7 technical support, training programs, and system maintenance.",
                    "support_levels": ["Basic (Business hours)", "Premium (24/7)", "Enterprise (Dedicated team)"],
                    "response_times": {"Critical": "1 hour", "High": "4 hours", "Medium": "24 hours", "Low": "48 hours"}
                }
            },
            "policies": {
                "refund_policy": "Full refunds available within 30 days of purchase. Partial refunds may apply for annual subscriptions after 30 days. Contact our support team to initiate the refund process.",
                "privacy_policy": "We protect customer data according to GDPR, CCPA, and industry-leading security standards. Your data is never shared with third parties without explicit consent.",
                "service_agreement": "Our Service Level Agreement guarantees 99.9% uptime, with 24-hour response time for critical issues. Compensation provided for SLA breaches.",
                "cancellation_policy": "Services can be cancelled with 30-day notice. No cancellation fees for monthly subscriptions. Annual subscriptions subject to terms."
            },
            "company_info": {
                "about": "COB Company is a leading technology solutions provider established in 2010, serving over 10,000 customers worldwide with innovative software and consulting services.",
                "contact": {
                    "email": "support@cobcompany.com",
                    "phone": "1-800-COB-HELP",
                    "address": "123 Technology Boulevard, Innovation City, IC 12345",
                    "live_chat": "Available 24/7 on our website"
                },
                "hours": {
                    "business_hours": "Monday-Friday 9:00 AM - 6:00 PM EST",
                    "support_hours": "24/7 emergency support available",
                    "sales_hours": "Monday-Friday 8:00 AM - 7:00 PM EST"
                },
                "locations": ["San Francisco, CA", "New York, NY", "Austin, TX", "London, UK", "Toronto, Canada"]
            },
            "appointments": {
                "types": [
                    {"name": "Product Demo", "duration": "30 minutes", "description": "Live demonstration of our software solutions"},
                    {"name": "Technical Consultation", "duration": "45 minutes", "description": "Technical discussion about implementation and integration"},
                    {"name": "Sales Meeting", "duration": "60 minutes", "description": "Detailed discussion about pricing and business requirements"},
                    {"name": "Support Session", "duration": "30 minutes", "description": "Technical support and troubleshooting session"}
                ],
                "availability": "Monday-Friday 9:00 AM - 5:00 PM EST",
                "booking_notice": "Please book at least 24 hours in advance",
                "cancellation_policy": "Free cancellation up to 2 hours before appointment"
            }
        }
    
    def search_knowledge(self, query: str) -> Tuple[str, float]:
        """Search knowledge base using Gemini API for intelligent retrieval"""
        try:
            # Create a comprehensive context from knowledge base
            kb_context = json.dumps(self.knowledge_data, indent=2)
            
            prompt = f"""
            Based on the following knowledge base about COB Company, provide a helpful and accurate answer to the user's question.
            
            Knowledge Base:
            {kb_context}
            
            User Question: {query}
            
            Instructions:
            1. Provide a concise but comprehensive answer
            2. Include specific details when available (prices, hours, contact info, etc.)
            3. If the question is not covered in the knowledge base, say so clearly
            4. Be helpful and professional
            5. Include relevant contact information when appropriate
            
            Answer:
            """
            
            # Use Gemini to generate intelligent response
            model = genai.GenerativeModel('gemini-2.5-flash-lite-preview-06-17')
            response = model.generate_content(prompt)
            
            if response.text:
                # Simple confidence scoring based on response quality
                confidence = 0.9 if "not covered" not in response.text.lower() else 0.3
                return response.text.strip(), confidence
            else:
                return "I don't have specific information about that.", 0.3
                
        except Exception as e:
            logger.error(f"Error in knowledge search: {e}")
            return "I'm having trouble accessing that information right now. Please try again or contact our support team.", 0.3

class GeminiChatbot:
    """Main chatbot class using Gemini API for intelligent conversation"""
    
    def __init__(self, api_key: str):
        """Initialize chatbot with Gemini API"""
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash-lite-preview-06-17')
        self.knowledge_base = KnowledgeBase()
        self.user_sessions = {}
        
        # System prompt for the chatbot
        self.system_prompt = """
        You are a professional customer service AI assistant for COB Company, a technology solutions provider.
        
        Your responsibilities:
        1. Answer questions about COB Company's products, services, and policies
        2. Help schedule appointments by collecting necessary information
        3. Handle customer requests professionally and efficiently
        4. Escalate to human agents when appropriate
        5. Maintain conversation context and provide personalized assistance
        
        Guidelines:
        - Be professional, helpful, and friendly
        - Ask clarifying questions when needed
        - Provide specific information when available
        - Offer to escalate complex issues to human agents
        - Always confirm important details before taking actions
        
        Available appointment types:
        - Product Demo (30 min)
        - Technical Consultation (45 min)
        - Sales Meeting (60 min)
        - Support Session (30 min)
        
        For appointment scheduling, collect:
        - Full name
        - Email address
        - Phone number
        - Preferred appointment type
        - Preferred date and time
        - Any specific requirements or questions
        """
    
    def get_or_create_session(self, session_id: str) -> UserContext:
        """Get or create user session"""
        if session_id not in self.user_sessions:
            self.user_sessions[session_id] = UserContext(session_id=session_id)
        return self.user_sessions[session_id]
    
    def classify_intent(self, message: str, context: UserContext) -> IntentType:
        """Use Gemini to classify user intent"""
        try:
            prompt = f"""
            Analyze the following user message and classify it into one of these intents:
            
            1. greeting - User is saying hello, starting conversation
            2. goodbye - User is ending conversation, saying goodbye
            3. kb_query - User is asking for information about products, services, policies, company info
            4. action_request - User wants to schedule appointment, update profile, or take specific action
            5. human_escalation - User is frustrated, needs complex help, or specifically requests human agent
            6. confirmation - User is confirming or providing requested information
            
            Message: "{message}"
            
            Consider the conversation context: Current intent: {context.current_intent}, Escalation triggers: {context.escalation_triggers}
            
            Respond with just the intent name (e.g., "greeting", "kb_query", etc.)
            """
            
            response = self.model.generate_content(prompt)
            intent_text = response.text.strip().lower()
            
            # Map response to IntentType
            intent_mapping = {
                "greeting": IntentType.GREETING,
                "goodbye": IntentType.GOODBYE,
                "kb_query": IntentType.KNOWLEDGE_BASE_QUERY,
                "action_request": IntentType.ACTION_REQUEST,
                "human_escalation": IntentType.HUMAN_ESCALATION,
                "confirmation": IntentType.CONFIRMATION
            }
            
            return intent_mapping.get(intent_text, IntentType.KNOWLEDGE_BASE_QUERY)
            
        except Exception as e:
            logger.error(f"Error in intent classification: {e}")
            return IntentType.KNOWLEDGE_BASE_QUERY
    
    def extract_entities(self, message: str) -> Dict[str, Any]:
        """Extract entities from user message using Gemini"""
        try:
            prompt = f"""
            Extract structured information from the following message. Look for:
            
            1. Name (full name of person)
            2. Email address
            3. Phone number
            4. Date preferences (specific dates or relative dates like "next Tuesday")
            5. Time preferences (specific times or general times like "afternoon")
            6. Service type (Product Demo, Technical Consultation, Sales Meeting, Support Session)
            7. Any specific requirements or questions
            
            Message: "{message}"
            
            Return the information in JSON format with keys: name, email, phone, date, time, service_type, requirements
            Only include fields that are clearly mentioned. Use null for missing information.
            
            Example: {{"name": "John Smith", "email": "john@email.com", "phone": null, "date": "next Tuesday", "time": "2 PM", "service_type": "Product Demo", "requirements": null}}
            """
            
            response = self.model.generate_content(prompt)
            try:
                entities = json.loads(response.text.strip())
                return {k: v for k, v in entities.items() if v is not None}
            except json.JSONDecodeError:
                return {}
                
        except Exception as e:
            logger.error(f"Error in entity extraction: {e}")
            return {}
    
    def handle_appointment_scheduling(self, message: str, context: UserContext) -> str:
        """Handle appointment scheduling with Gemini AI"""
        try:
            # Extract entities from current message
            entities = self.extract_entities(message)
            context.collected_info.update(entities)
            
            # Required fields for appointment
            required_fields = ["name", "email", "phone", "service_type", "date", "time"]
            missing_fields = [field for field in required_fields if field not in context.collected_info]
            
            if missing_fields:
                # Ask for missing information
                prompt = f"""
                You are helping a customer schedule an appointment. They have provided some information but we need more details.
                
                Already collected:
                {json.dumps(context.collected_info, indent=2)}
                
                Still need: {', '.join(missing_fields)}
                
                Available appointment types:
                - Product Demo (30 min): Live demonstration of our software solutions
                - Technical Consultation (45 min): Technical discussion about implementation
                - Sales Meeting (60 min): Detailed discussion about pricing and requirements
                - Support Session (30 min): Technical support and troubleshooting
                
                Write a friendly message asking for the missing information. Be specific about what you need and provide options when helpful.
                """
                
                response = self.model.generate_content(prompt)
                return response.text.strip()
            
            else:
                # All information collected, generate confirmation
                context.awaiting_confirmation = True
                appointment_id = str(uuid.uuid4())[:8].upper()
                
                confirmation_prompt = f"""
                Generate a professional appointment confirmation message with the following details:
                
                Customer Information:
                - Name: {context.collected_info.get('name')}
                - Email: {context.collected_info.get('email')}
                - Phone: {context.collected_info.get('phone')}
                
                Appointment Details:
                - Service: {context.collected_info.get('service_type')}
                - Date: {context.collected_info.get('date')}
                - Time: {context.collected_info.get('time')}
                - Requirements: {context.collected_info.get('requirements', 'None specified')}
                
                Appointment ID: {appointment_id}
                
                Include:
                1. Professional confirmation of the appointment
                2. All the details in a clear format
                3. Next steps (confirmation email, calendar invite)
                4. Contact information for changes
                5. Ask for final confirmation
                """
                
                response = self.model.generate_content(confirmation_prompt)
                return response.text.strip()
                
        except Exception as e:
            logger.error(f"Error in appointment scheduling: {e}")
            return "I'm having trouble processing your appointment request. Let me connect you with a human agent who can help you schedule your appointment."
    
    def process_message(self, message: str, session_id: str = "default") -> str:
        """Process incoming message and generate intelligent response"""
        try:
            context = self.get_or_create_session(session_id)
            
            # Classify intent
            intent = self.classify_intent(message, context)
            context.current_intent = intent
            
            # Generate response based on intent
            if intent == IntentType.GREETING:
                response = self.handle_greeting()
            
            elif intent == IntentType.GOODBYE:
                response = self.handle_goodbye()
            
            elif intent == IntentType.KNOWLEDGE_BASE_QUERY:
                response = self.handle_knowledge_query(message, context)
            
            elif intent == IntentType.ACTION_REQUEST:
                response = self.handle_action_request(message, context)
            
            elif intent == IntentType.HUMAN_ESCALATION:
                response = self.handle_human_escalation(context)
            
            elif intent == IntentType.CONFIRMATION:
                response = self.handle_confirmation(message, context)
            
            else:
                response = self.generate_fallback_response(message)
            
            # Update conversation history
            context.add_message(message, response)
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return "I'm experiencing technical difficulties. Please try again or contact our support team at support@cobcompany.com"
    
    def handle_greeting(self) -> str:
        """Handle greeting with dynamic response"""
        try:
            prompt = """
            Generate a warm, professional greeting for COB Company's customer service chatbot.
            
            Include:
            1. Friendly welcome
            2. Brief mention of what you can help with
            3. Invitation to ask questions
            
            Keep it concise but welcoming.
            """
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Error in greeting: {e}")
            return "Hello! Welcome to COB Company Customer Support. How can I help you today?"
    
    def handle_goodbye(self) -> str:
        """Handle goodbye with helpful closing"""
        try:
            prompt = """
            Generate a professional goodbye message for COB Company's customer service.
            
            Include:
            1. Thank you message
            2. Contact information for future needs
            3. Warm closing
            
            Keep it helpful and professional.
            """
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Error in goodbye: {e}")
            return "Thank you for contacting COB Company! If you need further assistance, please don't hesitate to reach out. Have a great day!"
    
    def handle_knowledge_query(self, message: str, context: UserContext) -> str:
        """Handle knowledge base queries"""
        answer, confidence = self.knowledge_base.search_knowledge(message)
        
        if confidence < 0.5:
            context.escalation_triggers += 1
            if context.escalation_triggers >= 2:
                return self.handle_human_escalation(context)
        
        return answer
    
    def handle_action_request(self, message: str, context: UserContext) -> str:
        """Handle action requests"""
        # Check if it's appointment related
        if any(word in message.lower() for word in ['appointment', 'schedule', 'book', 'meeting']):
            context.current_action = ActionType.SCHEDULE_APPOINTMENT
            return self.handle_appointment_scheduling(message, context)
        
        # Handle other actions with Gemini
        try:
            prompt = f"""
            The user is requesting an action. Based on their message: "{message}"
            
            Available actions:
            1. Schedule appointment
            2. Update profile/account information
            3. Cancel/reschedule appointment
            4. General account management
            
            Provide a helpful response that:
            1. Acknowledges their request
            2. Explains what you can help with
            3. Asks for any additional information needed
            4. Provides clear next steps
            """
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Error in action request: {e}")
            return "I can help you with scheduling appointments, updating your profile, or other account-related tasks. What would you like to do?"
    
    def handle_human_escalation(self, context: UserContext) -> str:
        """Handle escalation to human agent"""
        try:
            prompt = """
            Generate a professional escalation message for transferring to a human agent.
            
            Include:
            1. Understanding acknowledgment
            2. Transfer explanation
            3. Contact information alternatives
            4. What to expect next
            
            Be reassuring and helpful.
            """
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Error in escalation: {e}")
            return "I'll connect you with one of our human agents who can provide more specialized assistance. Please hold while I transfer you, or you can reach us directly at support@cobcompany.com or 1-800-COB-HELP."
    
    def handle_confirmation(self, message: str, context: UserContext) -> str:
        """Handle confirmation responses"""
        if context.awaiting_confirmation and context.current_action == ActionType.SCHEDULE_APPOINTMENT:
            if any(word in message.lower() for word in ['yes', 'correct', 'confirm', 'good', 'right']):
                context.awaiting_confirmation = False
                return """
                Perfect! ✅ Your appointment has been successfully scheduled.
                
                📧 You'll receive a confirmation email shortly with:
                - Calendar invite
                - Meeting details
                - Preparation instructions
                
                📞 If you need to make any changes, please contact us at:
                - Email: support@cobcompany.com
                - Phone: 1-800-COB-HELP
                
                Thank you for choosing COB Company! We look forward to meeting with you.
                """
            else:
                context.awaiting_confirmation = False
                context.collected_info = {}
                return "No problem! Let's start over with your appointment scheduling. What type of appointment would you like to schedule?"
        
        return "Thank you for the confirmation. Is there anything else I can help you with today?"
    
    def generate_fallback_response(self, message: str) -> str:
        """Generate fallback response using Gemini"""
        try:
            prompt = f"""
            A customer said: "{message}"
            
            As a COB Company customer service AI, provide a helpful response that:
            1. Acknowledges their message
            2. Offers assistance
            3. Suggests what you can help with
            4. Asks clarifying questions if needed
            
            Be professional and helpful.
            """
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Error in fallback: {e}")
            return "I want to make sure I understand how to help you. Could you please provide more details about what you're looking for?"

def create_gradio_interface(api_key: str):
    """Create Gradio interface for the chatbot"""
    
    # Initialize chatbot
    chatbot = GeminiChatbot(api_key)
    
    # Session management
    session_store = {}
    
    def chat_function(message, history, session_id):
        """Main chat function for Gradio interface"""
        try:
            # Generate unique session ID if not provided
            if not session_id:
                session_id = str(uuid.uuid4())[:8]
            
            # Process message
            response = chatbot.process_message(message, session_id)
            
            # Update history
            history.append((message, response))
            
            return history, "", session_id
            
        except Exception as e:
            logger.error(f"Error in chat function: {e}")
            error_response = "I'm experiencing technical difficulties. Please try again or contact support@cobcompany.com"
            history.append((message, error_response))
            return history, "", session_id
    
    def clear_chat():
        """Clear chat history"""
        return [], ""
    
    # Create Gradio interface
    with gr.Blocks(title="COB Company Customer Support", theme=gr.themes.Soft()) as demo:
        gr.Markdown("""
        # 🏢 COB Company Customer Support Chatbot
        
        Welcome to COB Company's AI-powered customer support! I can help you with:
        
        - 📋 **Product & Service Information** - Learn about our solutions
        - 📅 **Appointment Scheduling** - Book demos, consultations, and meetings  
        - 🔧 **Technical Support** - Get help with our products
        - 📞 **Contact Information** - Find the right department
        - 👥 **Human Agent Transfer** - Connect with our support team
        
        Just type your question or request below to get started!
        """)
        
        with gr.Row():
            with gr.Column(scale=4):
                chatbot_interface = gr.Chatbot(
                    height=500,
                    label="Customer Support Chat",
                    avatar_images=["👤", "🤖"]
                )
                
                with gr.Row():
                    msg = gr.Textbox(
                        placeholder="Type your message here...",
                        label="Message",
                        lines=2,
                        max_lines=5
                    )
                    
                with gr.Row():
                    send_btn = gr.Button("Send 📤", variant="primary")
                    clear_btn = gr.Button("Clear Chat 🗑️", variant="secondary")
            
            with gr.Column(scale=1):
                gr.Markdown("### Quick Actions")
                
                with gr.Group():
                    gr.Markdown("**Common Requests:**")
                    demo_btn = gr.Button("📋 Product Demo", size="sm")
                    consultation_btn = gr.Button("🔧 Technical Consultation", size="sm")
                    hours_btn = gr.Button("🕐 Business Hours", size="sm")
                    contact_btn = gr.Button("📞 Contact Info", size="sm")
                    human_btn = gr.Button("👥 Human Agent", size="sm")
                
                gr.Markdown("### Session Info")
                session_id = gr.Textbox(
                    label="Session ID",
                    interactive=False,
                    value=""
                )
                
                gr.Markdown("### 📞 Direct Contact")
                gr.Markdown("""
                **Phone:** 1-800-COB-HELP  
                **Email:** support@cobcompany.com  
                **Hours:** Mon-Fri 9AM-6PM EST
                """)
        
        # Event handlers
        def send_message(message, history, session_id):
            return chat_function(message, history, session_id)
        
        def quick_action(action_text, history, session_id):
            return chat_function(action_text, history, session_id)
        
        # Button events
        send_btn.click(
            send_message,
            inputs=[msg, chatbot_interface, session_id],
            outputs=[chatbot_interface, msg, session_id]
        )
        
        msg.submit(
            send_message,
            inputs=[msg, chatbot_interface, session_id],
            outputs=[chatbot_interface, msg, session_id]
        )
        
        clear_btn.click(
            clear_chat,
            outputs=[chatbot_interface, msg]
        )
        
        # Quick action buttons
        demo_btn.click(
            lambda h, s: quick_action("I'd like to schedule a product demo", h, s),
            inputs=[chatbot_interface, session_id],
            outputs=[chatbot_interface, msg, session_id]
        )
        
        consultation_btn.click(
            lambda h, s: quick_action("I need a technical consultation", h, s),
            inputs=[chatbot_interface, session_id],
            outputs=[chatbot_interface, msg, session_id]
        )
        
        hours_btn.click(
            lambda h, s: quick_action("What are your business hours?", h, s),
            inputs=[chatbot_interface, session_id],
            outputs=[chatbot_interface, msg, session_id]
        )
        
        contact_btn.click(
            lambda h, s: quick_action("How can I contact you?", h, s),
            inputs=[chatbot_interface, session_id],
            outputs=[chatbot_interface, msg, session_id]
        )
        
        human_btn.click(
            lambda h, s: quick_action("I need to speak with a human agent", h, s),
            inputs=[chatbot_interface, session_id],
            outputs=[chatbot_interface, msg, session_id]
        )
    
    return demo

if __name__ == "__main__":
    # Get API key from environment or user input
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        print("Please set your Gemini API key:")
        print("1. Set environment variable: GEMINI_API_KEY=your_api_key_here")
        print("2. Or enter it now:")
        api_key = input("Enter your Gemini API key: ").strip()
    
    if not api_key:
        print("Error: Gemini API key is required!")
        exit(1)
    
    try:
        # Create and launch Gradio interface
        demo = create_gradio_interface(api_key)
        
        print("🚀 Starting COB Company Customer Support Chatbot...")
        print("📱 Access the chatbot at: http://localhost:7860")
        print("🛑 Press Ctrl+C to stop the server")
        
        # Launch with public sharing option
        demo.launch(
            server_name="0.0.0.0",
            server_port=7860,
            share=False,  # Set to True for public sharing
            debug=False
        )
        
    except Exception as e:
        print(f"Error starting the application: {e}")
        print("Please check your API key and internet connection.")