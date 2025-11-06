"""
General Knowledge Agent for Microsoft Agent Framework
Handles non-database queries like web searches, general questions, and conversations
"""

from typing import List, Dict, Any
from agent_framework import ChatMessage, Role, ChatAgent
from agent_framework.azure import AzureOpenAIChatClient
import os


class GeneralAgent:
    """Agent for handling general knowledge queries, web searches, and conversations."""
    
    def __init__(
        self,
        azure_openai_endpoint: str = None,
        azure_openai_api_key: str = None,
        azure_openai_deployment: str = None,
        model_id: str = "gpt-4o"
    ):
        """
        Initialize the General Agent.
        
        Args:
            azure_openai_endpoint: Azure OpenAI endpoint URL
            azure_openai_api_key: Azure OpenAI API key
            azure_openai_deployment: Azure OpenAI deployment name
            model_id: Model ID to use (default: gpt-4o)
        """
        self.name = "GeneralAgent"
        self.description = """General knowledge assistant for non-database queries.
        Use this agent when the user:
        - Asks general knowledge questions
        - Requests information from the internet
        - Wants to have a conversation
        - Asks about topics not related to the database
        - Needs help with documents or external information
        """
        
        # Initialize Azure OpenAI chat client
        # Extract the base endpoint (remove everything after and including /openai/)
        endpoint = azure_openai_endpoint
        if endpoint and '/openai/' in endpoint:
            endpoint = endpoint.split('/openai/')[0]
        
        self.chat_client = AzureOpenAIChatClient(
            endpoint=endpoint,
            deployment_name=model_id or azure_openai_deployment,
            api_key=azure_openai_api_key
        )
        
        # Create the chat agent
        self.agent = ChatAgent(
            name=self.name,
            instructions="""You are a helpful general knowledge assistant. You help users with:
            - General questions and information about concepts, definitions, explanations
            - Web searches and current events
            - Document analysis and information retrieval
            - Conversations about topics and ideas
            - Technical explanations and best practices
            
            You should NOT attempt to help with database queries or data retrieval.
            
            When you receive a question:
            1. If it's asking to retrieve, list, show, count, or analyze data from a database, respond:
               "I notice this question is about database data. I cannot access databases directly. 
               Please ask the SQL Agent instead by rephrasing your question to make it clear you want 
               to query the database (e.g., 'show me all products from the database')."
            
            2. For general knowledge questions, provide clear, accurate, and helpful responses
            3. Be conversational and friendly
            4. Be honest about what you know and don't know
            
            Remember: You handle concepts and knowledge, not data retrieval.""",
            description=self.description,
            chat_client=self.chat_client
        )
        
        self.conversation_history: List[ChatMessage] = []
    
    async def run(self, messages: List[ChatMessage]) -> List[ChatMessage]:
        """
        Run the general agent with the given conversation context.
        
        Args:
            messages: List of ChatMessage objects representing the conversation
            
        Returns:
            List of ChatMessage objects with the agent's response
        """
        # Run the agent
        response = await self.agent.run(messages)
        
        # Store in conversation history
        self.conversation_history.extend(messages)
        self.conversation_history.extend(response.messages)
        
        return response.messages
    
    async def process_query(self, question: str) -> Dict[str, Any]:
        """
        Process a general knowledge query.
        
        Args:
            question: User's question
            
        Returns:
            Dictionary containing the response
        """
        # Create a message
        user_message = ChatMessage(
            role=Role.USER,
            text=question
        )
        
        # Run the agent
        response_messages = await self.run([user_message])
        
        # Extract response text
        response_text = ""
        for msg in response_messages:
            if msg.role == Role.ASSISTANT:
                response_text += msg.text + "\n"
        
        return {
            'success': True,
            'question': question,
            'response': response_text.strip(),
            'agent': self.name
        }
    
    def clear_history(self):
        """Clear the agent's conversation history."""
        self.conversation_history = []
    
    def get_conversation_history(self) -> List[ChatMessage]:
        """Get the conversation history."""
        return self.conversation_history
