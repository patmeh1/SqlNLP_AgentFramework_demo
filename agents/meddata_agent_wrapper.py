"""
MedData SQL Agent Wrapper for Microsoft Agent Framework
Specialized agent for querying the MedData Azure SQL Database
Handles medical slot and code queries
"""

import asyncio
from typing import Dict, Any, List
from agent_framework import ChatMessage, Role
from sql_agent import SQLAgent


class MedDataAgentWrapper:
    """Wrapper that adapts SQLAgent to work with MedData medical database."""
    
    def __init__(self, sql_agent: SQLAgent):
        """
        Initialize the MedData Agent Wrapper.
        
        Args:
            sql_agent: Instance of SQLAgent configured for MedData database
        """
        self.sql_agent = sql_agent
        self.name = "MedDataAgent"
        self.description = """Specialist in querying the MedData Azure SQL Database for medical information.
        Use this agent when the user asks questions about:
        - Medical codes and their properties
        - Slot definitions (LOINC codes, SNOMED codes, etc.)
        - Medical test information (sodium tests, lab procedures, etc.)
        - Relationships between medical codes and slots
        - CPMC Laboratory Tests, procedures, and measurements
        - Medical terminology and coding systems
        - Questions containing terms like: medical code, LOINC, SNOMED, slot, test, procedure, measurement
        
        Database contains:
        - MED_SLOTS table: Slot definitions (LOINC-CODE, SNOMED-CODE, EPIC-COMPONENT-ID, etc.)
        - MED table: Medical codes with their slot values (155 medical records)
        """
    
    async def process_query(self, question: str) -> Dict[str, Any]:
        """
        Process a medical database query asynchronously.
        
        Args:
            question: Natural language question about the MedData database
            
        Returns:
            Dictionary containing query results and response
        """
        # Run synchronous SQLAgent.query in thread pool
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, 
            self.sql_agent.query, 
            question
        )
        
        # Enhance the response with medical context
        if result.get('success') and result.get('results'):
            result['medical_context'] = self._add_medical_context(result)
        
        return result
    
    def _add_medical_context(self, result: Dict[str, Any]) -> str:
        """
        Add medical context to the query results.
        
        Args:
            result: Query result dictionary
            
        Returns:
            Additional context string
        """
        context_hints = []
        
        # Check if query involves LOINC codes
        if 'LOINC' in result.get('sql', '').upper():
            context_hints.append("💡 LOINC codes are standardized codes for laboratory tests and observations.")
        
        # Check if query involves SNOMED codes
        if 'SNOMED' in result.get('sql', '').upper():
            context_hints.append("💡 SNOMED codes are standardized medical terminology for diseases and procedures.")
        
        # Check if query involves print names
        if 'PRINT-NAME' in result.get('sql', '').upper() or 'PRINT_NAME' in result.get('sql', '').upper():
            context_hints.append("💡 Print names are human-readable descriptions of medical codes.")
        
        return " ".join(context_hints) if context_hints else ""
    
    async def run(self, messages: List[ChatMessage]) -> List[ChatMessage]:
        """
        Run the MedData agent with the given conversation context.
        
        Args:
            messages: List of ChatMessage objects representing the conversation
            
        Returns:
            List of ChatMessage objects with the agent's response
        """
        # Extract the last user message
        user_messages = [msg for msg in messages if msg.role == Role.USER]
        if not user_messages:
            return [ChatMessage(
                role=Role.ASSISTANT,
                text="I need a question to query the MedData medical database.",
                author_name=self.name
            )]
        
        last_question = user_messages[-1].text
        
        # Process the query
        result = await self.process_query(last_question)
        
        # Format response as ChatMessage
        if result['success']:
            response_text = f"{result['response']}\n\n"
            
            # Add medical context if available
            if result.get('medical_context'):
                response_text += f"{result['medical_context']}\n\n"
            
            response_text += f"**SQL Query Executed:**\n```sql\n{result['sql']}\n```\n\n"
            
            if result['results']:
                response_text += f"**Results:** {result['row_count']} medical record(s) found"
        else:
            response_text = f"Error processing MedData query: {result.get('error', 'Unknown error')}"
        
        return [ChatMessage(
            role=Role.ASSISTANT,
            text=response_text,
            author_name=self.name
        )]
    
    def get_schema_info(self) -> str:
        """Get MedData database schema information."""
        return self.sql_agent.schema_info
    
    def clear_history(self):
        """Clear the agent's conversation history."""
        self.sql_agent.clear_history()
    
    def get_available_slots(self) -> str:
        """
        Get a summary of available medical slots in the database.
        
        Returns:
            String describing available slot types
        """
        return """Available Medical Slots:
        - Slot 3: DESCENDANT-OF (Semantic relationships)
        - Slot 4: SUBCLASS-OF (Hierarchical relationships)
        - Slot 6: PRINT-NAME (Human-readable names)
        - Slot 9: CPMC-LAB-PROC-CODE (Lab procedure codes)
        - Slot 15: MEASURED-BY-PROCEDURE (Measurement procedures)
        - Slot 16: ENTITY-MEASURED (Measured entities)
        - Slot 20: CPMC-LAB-TEST-CODE (Lab test codes)
        - Slot 149: PT-PROBLEM-(INDICATED-BY)->PROCEDURE (Problem indicators)
        - Slot 150: PROCEDURE-(INDICATES)->PT-PROBLEM (Procedure indicators)
        - Slot 212: LOINC-CODE (LOINC standard codes)
        - Slot 264: MILLENNIUM-LAB-CODE (Millennium codes)
        - Slot 266: SNOMED-CODE (SNOMED standard codes)
        - Slot 277: EPIC-COMPONENT-ID (Epic component IDs)
        """
