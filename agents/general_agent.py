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
            instructions="""You are a helpful analysis and reasoning assistant. You help users with:
            - Analyzing and interpreting data results from database queries
            - Drawing insights from presented data
            - General questions and information about concepts, definitions, explanations
            - Web searches and current events
            - Document analysis and information retrieval
            - Conversations about topics and ideas
            - Technical explanations and best practices
            - Medical data interpretation and clinical significance
            
            IMPORTANT: When you receive a prompt that contains:
            - A question at the top (marked as "ORIGINAL QUESTION")
            - Actual data results shown in tables or JSON format (marked as "ACTUAL DATA RESULTS")
            This is a DATA ANALYSIS prompt. Your job is to analyze and interpret the provided data.
            DO NOT reject these prompts. Instead, analyze the data and provide insights.
            
            You should ONLY reject database queries when:
            - The user is asking you to perform the database query yourself
            - There is NO actual data provided for analysis
            - The request is asking you to access databases directly
            
            When you receive a direct database query request (without data):
            1. If it's asking to retrieve, list, show, count data from a database directly, respond:
               "I notice this question is about database data. I cannot access databases directly. 
               Please ask the SQL Agent instead by rephrasing your question to make it clear you want 
               to query the database (e.g., 'show me all products from the database')."
            
            2. For data analysis prompts containing actual results, analyze and interpret them
            3. For general knowledge questions, provide clear, accurate, and helpful responses
            4. Be conversational and friendly
            5. Be honest about what you know and don't know
            
            Remember: You handle data analysis, concepts, and knowledge interpretation, not direct data retrieval.""",
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
        # Combine conversation history with new messages for full context
        full_context = self.conversation_history + messages
        
        # Run the agent with full conversation context
        response = await self.agent.run(full_context)
        
        # Store in conversation history (only new messages)
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
        
        # Run the agent with conversation history
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
