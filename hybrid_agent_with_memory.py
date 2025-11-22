"""
Hybrid Agent System with SQL-to-General Agent Chaining and Memory
Combines SQL query execution with general agent verification and response refinement.
Maintains conversation memory for context-aware interactions.
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
from meddata_sql_agent import MedDataSQLAgent, create_meddata_agent_from_env
from agents.general_agent import GeneralAgent
from agent_framework import ChatMessage, Role


class InteractionMemory:
    """Stores and manages conversation memory with SQL context."""
    
    def __init__(self):
        self.interactions: List[Dict[str, Any]] = []
    
    def add_interaction(
        self,
        question: str,
        sql_query: str,
        sql_results: Any,
        sql_response: str,
        final_response: str,
        timestamp: Optional[datetime] = None
    ):
        """Add a new interaction to memory."""
        interaction = {
            'timestamp': timestamp or datetime.now(),
            'question': question,
            'sql_query': sql_query,
            'sql_results': sql_results,
            'sql_response': sql_response,
            'final_response': final_response
        }
        self.interactions.append(interaction)
    
    def get_recent_context(self, n: int = 3) -> str:
        """Get recent interactions as context string."""
        if not self.interactions:
            return "No previous interactions."
        
        recent = self.interactions[-n:]
        context_parts = []
        
        for i, interaction in enumerate(recent, 1):
            context_parts.append(f"Previous Interaction {i}:")
            context_parts.append(f"  Question: {interaction['question']}")
            context_parts.append(f"  SQL: {interaction['sql_query']}")
            context_parts.append(f"  Response: {interaction['final_response'][:200]}...")
            context_parts.append("")
        
        return "\n".join(context_parts)
    
    def get_all_interactions(self) -> List[Dict[str, Any]]:
        """Get all interactions."""
        return self.interactions
    
    def clear(self):
        """Clear all memory."""
        self.interactions = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert memory to dictionary format."""
        return {
            'total_interactions': len(self.interactions),
            'interactions': [
                {
                    'timestamp': interaction['timestamp'].isoformat(),
                    'question': interaction['question'],
                    'sql_query': interaction['sql_query'],
                    'row_count': len(interaction.get('sql_results', [])),
                    'final_response': interaction['final_response']
                }
                for interaction in self.interactions
            ]
        }


class HybridAgentWithMemory:
    """
    Hybrid agent that chains SQL agent output through general agent for verification.
    Maintains conversation memory for context-aware interactions.
    """
    
    def __init__(
        self,
        sql_agent: MedDataSQLAgent,
        general_agent: GeneralAgent
    ):
        """
        Initialize the hybrid agent system.
        
        Args:
            sql_agent: MedData SQL agent for database queries
            general_agent: General agent for response verification and refinement
        """
        self.sql_agent = sql_agent
        self.general_agent = general_agent
        self.memory = InteractionMemory()
        self.name = "Hybrid Medical Query Agent"
    
    async def query(self, question: str) -> Dict[str, Any]:
        """
        Process a query through SQL agent, then verify and refine with general agent.
        Includes error recovery with up to 2 retry attempts via General Agent suggestions.
        
        Flow:
        1. SQL Agent generates SQL and executes it
        2. If error: General Agent analyzes error and suggests fixes
        3. Retry with corrections (up to 2 attempts)
        4. If success: General Agent analyzes ACTUAL DATA RESULTS
        5. Memory stores the complete interaction
        
        Args:
            question: User's natural language question
            
        Returns:
            Dictionary with complete interaction details and final response
        """
        timestamp = datetime.now()
        max_retries = 2
        attempt = 0
        sql_result: Dict[str, Any] = {}  # Initialize as empty dict instead of None
        
        # Step 1: Try SQL query generation and execution (with retries)
        while attempt < max_retries:
            attempt += 1
            print(f"[{timestamp.strftime('%H:%M:%S')}] Attempt {attempt}: SQL Agent processing query...")
            sql_result = self.sql_agent.query(question)
            
            if sql_result.get('success'):
                print(f"[{timestamp.strftime('%H:%M:%S')}] Attempt {attempt}: Success! Retrieved {sql_result.get('row_count', 0)} rows")
                break
            
            # If this is the last attempt, we'll handle the error after the loop
            if attempt >= max_retries:
                print(f"[{timestamp.strftime('%H:%M:%S')}] Attempt {attempt}: Failed. Max retries reached.")
                break
            
            # Try error recovery with General Agent
            print(f"[{timestamp.strftime('%H:%M:%S')}] Attempt {attempt}: Error detected. Routing to General Agent for SQL correction suggestion...")
            
            error_str = sql_result.get('error', 'Unknown error')
            error_category = sql_result.get('error_category', 'UNKNOWN_ERROR')
            error_hint = sql_result.get('error_hint', '')
            sql_query = sql_result.get('sql', 'No query generated')
            
            # Ask General Agent to suggest SQL correction
            correction_prompt = f"""The user asked this medical database question: "{question}"

The SQL Agent generated this query:
{sql_query}

But it failed with this SQL Server error:
ERROR TYPE: {error_category}
ERROR MESSAGE: {error_str}
ERROR HINT: {error_hint}

Please analyze this error and suggest:
1. What went wrong with the SQL
2. The specific SQL issue (e.g., "LIMIT is not valid in T-SQL, use TOP instead")
3. A corrected version of the SQL query that would work for this question
4. Explain your fix briefly

Format your response to include:
- PROBLEM: [brief description of the SQL issue]
- FIX: [the corrected SQL query - this will be re-executed]
- EXPLANATION: [why this fix works]

Important: The FIX must be valid T-SQL for Microsoft SQL Server with these rules:
- Use TOP instead of LIMIT
- Use DISTINCT when needed for multiple joins
- Use MAX(CASE WHEN ...) for conditional aggregation
- Always GROUP BY when using aggregates
- Use proper table aliases (m1, m2, m3, etc.)
- No markdown, no code fences - just raw T-SQL"""
            
            general_result = await self.general_agent.process_query(correction_prompt)
            general_suggestion = general_result.get('response', '')
            
            print(f"[{timestamp.strftime('%H:%M:%S')}] General Agent suggested correction")
            
            # Extract corrected SQL from the general agent's response
            corrected_sql = self._extract_corrected_sql(general_suggestion)
            
            if corrected_sql:
                print(f"[{timestamp.strftime('%H:%M:%S')}] Retrying with corrected SQL...")
                # Execute the corrected SQL directly
                retry_result = self.sql_agent._execute_query(corrected_sql)
                
                if retry_result.get('success'):
                    # Create a modified result that tracks the retry
                    sql_result = {
                        'success': True,
                        'sql': corrected_sql,
                        'results': retry_result.get('results', []),
                        'row_count': retry_result.get('row_count', 0),
                        'columns': retry_result.get('columns', []),
                        'response': f"Query corrected and executed successfully after error recovery.",
                        'was_corrected': True,
                        'original_error': error_str,
                        'correction_applied': general_suggestion
                    }
                    print(f"[{timestamp.strftime('%H:%M:%S')}] Retry successful! Retrieved {sql_result.get('row_count', 0)} rows")
                    break
                else:
                    print(f"[{timestamp.strftime('%H:%M:%S')}] Corrected query still failed: {retry_result.get('error', 'Unknown error')}")
        
        # Handle final failure after all retries
        if not sql_result.get('success'):
            print(f"[{timestamp.strftime('%H:%M:%S')}] All retry attempts exhausted. Providing helpful error response.")
            
            error_str = sql_result.get('error', 'Unknown error')
            error_category = sql_result.get('error_category', 'UNKNOWN_ERROR')
            error_hint = sql_result.get('error_hint', '')
            sql_query = sql_result.get('sql', 'No query generated')
            
            # Build comprehensive error context for General Agent
            error_analysis = f"""A user asked this medical database question: "{question}"

The SQL Agent generated a query but encountered a SQL Server error that couldn't be automatically fixed:

ERROR TYPE: {error_category}
ERROR MESSAGE: {error_str}
LAST SQL ATTEMPTED: {sql_query}
ERROR HINT: {error_hint}

The system tried to auto-correct the SQL but was unable to fix it.

Your task is to help the user understand:
1. What went wrong in simple, non-technical language
2. Why this error occurred and why it was hard to fix
3. How they could rephrase their question to avoid this error
4. Provide 2-3 concrete alternative questions they could try instead

Be helpful, friendly, and conversational. Acknowledge that medical database queries can be complex."""
            
            general_result = await self.general_agent.process_query(error_analysis)
            
            # Return helpful error response
            return {
                'success': False,
                'error': sql_result.get('error', 'SQL query failed'),
                'question': question,
                'timestamp': timestamp.isoformat(),
                'final_response': general_result.get('response', f"I encountered a SQL error: {error_str}. The system tried to: {error_hint}"),
                'agent_chain': f'SQL (Attempt 1) -> General Agent (Correction) -> SQL (Attempt 2) -> General Agent (Explanation)',
                'original_error': error_str,
                'error_category': error_category,
                'retry_attempts': attempt
            }
        
        # At this point we have:
        # - SQL statement that was generated
        # - ACTUAL DATA RESULTS from executing that SQL
        # - SQL Agent's response text
        
        print(f"[{timestamp.strftime('%H:%M:%S')}] SQL Query Phase Complete. Analyzing results...")
        
        # Step 2: Send ACTUAL DATA to General Agent for analysis and reasoning
        print(f"[{timestamp.strftime('%H:%M:%S')}] Step 2: Sending data results to General Agent for analysis...")
        
        verification_prompt = self._build_verification_prompt(
            question=question,
            sql_query=sql_result['sql'],
            sql_results=sql_result.get('results', []),
            sql_response=sql_result.get('response', ''),
            row_count=sql_result.get('row_count', 0),
            recent_context=self.memory.get_recent_context(n=2)
        )
        
        # Step 3: Get general agent analysis of the DATA
        general_result = await self.general_agent.process_query(verification_prompt)
        
        if not general_result.get('success'):
            # Fallback to SQL response if general agent fails
            final_response = sql_result.get('response', '')
            verification_note = "\n\n⚠️ Note: General agent analysis unavailable."
        else:
            final_response = general_result['response']
            verification_note = ""
        
        # Add note if SQL was corrected
        correction_note = ""
        if sql_result.get('was_corrected'):
            correction_note = "\n\n📝 Note: This query was automatically corrected from an initial SQL error."
        
        # Step 4: Store complete interaction in memory
        self.memory.add_interaction(
            question=question,
            sql_query=sql_result['sql'],
            sql_results=sql_result.get('results', []),
            sql_response=sql_result.get('response', ''),
            final_response=final_response,
            timestamp=timestamp
        )
        
        print(f"[{timestamp.strftime('%H:%M:%S')}] Step 4: Stored {sql_result.get('row_count', 0)} data rows in memory")
        
        # Return complete result
        return {
            'success': True,
            'question': question,
            'sql_query': sql_result['sql'],
            'sql_response': sql_result.get('response', ''),
            'final_response': final_response + verification_note + correction_note,
            'results': sql_result.get('results', []),
            'row_count': sql_result.get('row_count', 0),
            'columns': sql_result.get('columns', []),
            'timestamp': timestamp.isoformat(),
            'memory_size': len(self.memory.interactions),
            'agent_chain': 'SQL (Generate + Execute) -> General Agent (Analyze Data) -> Memory',
            'was_corrected': sql_result.get('was_corrected', False),
            'retry_attempts': attempt
        }
    
    def _format_data_table(self, sql_results: List[Dict]) -> str:
        """Format query results as readable table."""
        if not sql_results:
            return "No data returned from query."
        
        # Get column names from first row
        columns = list(sql_results[0].keys())
        
        # Calculate column widths
        col_widths = {col: len(col) for col in columns}
        for row in sql_results:
            for col in columns:
                col_widths[col] = max(col_widths[col], len(str(row.get(col, ''))))
        
        # Build header
        header = " | ".join(col.ljust(col_widths[col]) for col in columns)
        separator = "-" * len(header)
        
        # Build rows (limit to first 20 for readability)
        rows_formatted = []
        for row in sql_results[:20]:
            row_str = " | ".join(str(row.get(col, '')).ljust(col_widths[col]) for col in columns)
            rows_formatted.append(row_str)
        
        result = f"{header}\n{separator}\n" + "\n".join(rows_formatted)
        
        if len(sql_results) > 20:
            result += f"\n... and {len(sql_results) - 20} more rows"
        
        return result
    
    def _build_verification_prompt(
        self,
        question: str,
        sql_query: str,
        sql_results: List[Dict],
        sql_response: str,
        row_count: int,
        recent_context: str
    ) -> str:
        """
        Build prompt for general agent to analyze ACTUAL DATA RESULTS.
        THIS PROMPT FOCUSES ON THE DATA, NOT THE SQL STATEMENT.
        """
        
        # Format the actual data results as a table
        formatted_table = self._format_data_table(sql_results)
        
        # Prepare detailed JSON representation for first few rows
        json_detail = ""
        if sql_results:
            json_detail = "\n\n**Detailed Data (JSON format):**\n"
            for i, row in enumerate(sql_results[:3]):
                json_detail += f"\nRow {i+1}:\n```json\n{json.dumps(row, indent=2, default=str)}\n```"
            if len(sql_results) > 3:
                json_detail += f"\n... and {len(sql_results)-3} more rows"
        
        prompt = f"""You are a medical data analysis expert analyzing database query results.
Your role is to interpret medical ontology data, explain relationships, and answer complex questions.

**KEY INSTRUCTION**: You are analyzing the ACTUAL DATA RESULTS from the database query execution.
Focus on the data shown in the table and JSON below - this is the real data returned from the database.

=== ORIGINAL QUESTION ===
{question}

=== ACTUAL DATA RESULTS FROM DATABASE QUERY ===
**Total rows returned: {row_count}**

**Data Table:**
```
{formatted_table}
```
{json_detail}

=== RECENT CONVERSATION CONTEXT ===
{recent_context}

=== YOUR ANALYSIS TASK ===
Based on the ACTUAL DATA RESULTS shown above, please:

1. **Analyze the Data**: What does this data tell us about the original question?
   - Identify key entities (procedures, tests, problems, codes)
   - Explain the medical significance of the findings
   - Note any relationships or patterns in the data

2. **Extract Key Findings**: What are the most important data points?
   - Highlight specific codes, names, and relationships
   - Explain LOINC, SNOMED, and other medical codes
   - Connect procedures to problems and vice versa

3. **Answer the Question**: Directly answer the user's original question using the data
   - Use complete sentences
   - Reference specific data from the results
   - Organize findings logically

4. **Provide Clinical Context**: Add relevant medical interpretation
   - Explain what procedures measure or indicate
   - Explain what problems the procedures help diagnose
   - Clarify medical terminology and relationships

5. **Format for Clarity**: Use bullet points or sections for readability
   - Structure complex information with clear headings
   - Use bullet points for lists of items
   - Create comparison tables for related items

6. **Note Data Completeness**: 
   - If results show "... and N more rows", mention that additional findings exist
   - Highlight if this is a partial result set
   - Suggest if more detailed drilling down might be helpful

**IMPORTANT GUIDELINES FOR MULTI-STEP QUERIES:**
- If the data shows relationships you need to explore further (e.g., procedures indicating problems, 
  problems indicated by procedures), explain these relationships clearly
- If you notice gaps in the data (e.g., some items lack certain codes or names), mention this
- If the current results suggest there might be related information worth exploring, you can suggest 
  it: "To get more insights, we could also look at..."
- For complex relationships, create a narrative explanation of how items are connected

**Your comprehensive analysis and answer:**"""
        
        return prompt
    
    def _extract_corrected_sql(self, general_response: str) -> Optional[str]:
        """
        Extract corrected SQL from General Agent's response.
        
        Looks for patterns like:
        - FIX: [SQL here]
        - ```sql\n[SQL here]\n```
        - Lines between markers that contain SQL keywords
        
        Args:
            general_response: Response from General Agent with suggested fix
            
        Returns:
            Extracted SQL string or None if no SQL found
        """
        import re
        
        # Try to find SQL between FIX: marker and next section
        fix_match = re.search(r'(?:FIX|Fix|FIXED|Fixed):\s*\n?\s*(SELECT.*?)(?:\n\n|EXPLANATION|Explanation|$)', general_response, re.IGNORECASE | re.DOTALL)
        if fix_match:
            sql = fix_match.group(1).strip()
            # Remove markdown code fences if present
            sql = re.sub(r'```sql\s*\n?', '', sql)
            sql = re.sub(r'\n?```', '', sql)
            if sql and sql.upper().startswith('SELECT'):
                return sql
        
        # Try to find SQL in code blocks
        code_match = re.search(r'```sql\s*\n(.*?)\n```', general_response, re.DOTALL)
        if code_match:
            sql = code_match.group(1).strip()
            if sql and sql.upper().startswith('SELECT'):
                return sql
        
        # Try to find any line that looks like complete SQL
        lines = general_response.split('\n')
        for i, line in enumerate(lines):
            line = line.strip()
            if line.upper().startswith('SELECT') and ('FROM' in line.upper() or 'WHERE' in line.upper()):
                # Collect from this line onwards until we hit a blank line or end
                sql_lines = [line]
                for next_line in lines[i+1:]:
                    next_line = next_line.strip()
                    if not next_line or next_line.startswith('EXPLANATION') or next_line.startswith('PROBLEM'):
                        break
                    sql_lines.append(next_line)
                
                sql = ' '.join(sql_lines).strip()
                if sql:
                    return sql
        
        return None
    
    def get_memory_summary(self) -> Dict[str, Any]:
        """Get summary of conversation memory."""
        return self.memory.to_dict()
    
    def get_recent_interactions(self, n: int = 5) -> List[Dict[str, Any]]:
        """Get recent interactions."""
        return self.memory.interactions[-n:] if self.memory.interactions else []
    
    def clear_memory(self):
        """Clear conversation memory."""
        self.memory.clear()
        self.sql_agent.clear_history()
        self.general_agent.clear_history()
        print("✅ Memory cleared for all agents")
    
    def export_memory(self, filepath: str):
        """Export memory to JSON file."""
        memory_dict = self.memory.to_dict()
        # Convert datetime objects to strings
        for interaction in memory_dict['interactions']:
            if isinstance(interaction.get('timestamp'), datetime):
                interaction['timestamp'] = interaction['timestamp'].isoformat()
        
        with open(filepath, 'w') as f:
            json.dump(memory_dict, f, indent=2)
        
        print(f"✅ Memory exported to {filepath}")


async def create_hybrid_agent_from_env() -> HybridAgentWithMemory:
    """
    Create a HybridAgentWithMemory from environment variables.
    
    Returns:
        HybridAgentWithMemory instance
    """
    import os
    
    # Create SQL agent
    sql_agent = create_meddata_agent_from_env()
    
    # Create general agent
    general_agent = GeneralAgent(
        azure_openai_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT') or '',
        azure_openai_api_key=os.getenv('AZURE_OPENAI_API_KEY') or '',
        azure_openai_deployment=os.getenv('AZURE_OPENAI_DEPLOYMENT') or ''
    )
    
    return HybridAgentWithMemory(sql_agent, general_agent)


# Test function
async def test_hybrid_agent():
    """Test the hybrid agent system."""
    print("=" * 80)
    print("HYBRID AGENT WITH MEMORY - TEST")
    print("=" * 80)
    print()
    
    # Create hybrid agent
    agent = await create_hybrid_agent_from_env()
    
    # Test queries
    test_questions = [
        "Show me all tests with LOINC code 2947-0",
        "What patient problems do those tests indicate?",
        "Give me the SNOMED codes for those problems"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n{'=' * 80}")
        print(f"QUERY {i}: {question}")
        print('=' * 80)
        
        result = await agent.query(question)
        
        if result['success']:
            print(f"\n✅ Success!")
            print(f"SQL: {result['sql_query']}")
            print(f"\nFinal Response:\n{result['final_response']}")
            print(f"\nMemory Size: {result['memory_size']} interactions")
        else:
            print(f"\n❌ Error: {result.get('error')}")
        
        print()
    
    # Show memory summary
    print("=" * 80)
    print("MEMORY SUMMARY")
    print("=" * 80)
    memory_summary = agent.get_memory_summary()
    print(f"Total Interactions: {memory_summary['total_interactions']}")
    print()
    
    # Export memory
    agent.export_memory('memory_export.json')


if __name__ == "__main__":
    asyncio.run(test_hybrid_agent())
