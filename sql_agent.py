"""
SQL Agent using Microsoft Agent Framework and Azure OpenAI
This agent can query Azure SQL Database using natural language.
"""

import os
import pyodbc
from typing import List, Dict, Any, Optional
from openai import AzureOpenAI
import json
import struct
from azure.identity import DefaultAzureCredential, AzureCliCredential


class SQLAgent:
    """Agent that translates natural language to SQL queries and executes them."""
    
    def __init__(
        self,
        sql_server: str,
        sql_database: str,
        sql_username: str = None,
        sql_password: str = None,
        azure_openai_endpoint: str = None,
        azure_openai_api_key: str = None,
        azure_openai_deployment: str = None,
        azure_openai_api_version: str = "2024-08-01-preview",
        use_azure_ad: bool = True
    ):
        """Initialize the SQL Agent with database and Azure OpenAI credentials."""
        self.sql_server = sql_server
        self.sql_database = sql_database
        self.sql_username = sql_username
        self.sql_password = sql_password
        self.use_azure_ad = use_azure_ad or (sql_username is None and sql_password is None)
        
        # Initialize Azure OpenAI client
        self.client = AzureOpenAI(
            azure_endpoint=azure_openai_endpoint,
            api_key=azure_openai_api_key,
            api_version=azure_openai_api_version
        )
        self.deployment = azure_openai_deployment
        
        # Build connection string based on auth type
        if self.use_azure_ad:
            # Azure AD authentication
            self.connection_string = (
                f"Driver={{ODBC Driver 18 for SQL Server}};"
                f"Server=tcp:{sql_server},1433;"
                f"Database={sql_database};"
                f"Encrypt=yes;"
                f"TrustServerCertificate=no;"
                f"Connection Timeout=30;"
            )
            # Get Azure AD token
            try:
                credential = AzureCliCredential()
                token = credential.get_token("https://database.windows.net/.default")
                self.token_bytes = token.token.encode("utf-16-le")
                self.token_struct = struct.pack(f'<I{len(self.token_bytes)}s', len(self.token_bytes), self.token_bytes)
            except Exception as e:
                print(f"Warning: Could not get Azure AD token: {e}")
                print("Falling back to environment variables if available...")
                self.token_struct = None
        else:
            # SQL authentication
            self.connection_string = (
                f"Driver={{ODBC Driver 18 for SQL Server}};"
                f"Server=tcp:{sql_server},1433;"
                f"Database={sql_database};"
                f"Uid={sql_username};"
                f"Pwd={sql_password};"
                f"Encrypt=yes;"
                f"TrustServerCertificate=no;"
                f"Connection Timeout=30;"
            )
            self.token_struct = None
        
        # Get database schema on initialization
        self.schema_info = self._get_database_schema()
        
        # Conversation history
        self.conversation_history: List[Dict[str, str]] = []
    
    def _get_connection(self):
        """Get a database connection with appropriate authentication."""
        if self.use_azure_ad and self.token_struct:
            # Connect with Azure AD token
            SQL_COPT_SS_ACCESS_TOKEN = 1256  # Connection option for access token
            conn = pyodbc.connect(self.connection_string, attrs_before={SQL_COPT_SS_ACCESS_TOKEN: self.token_struct})
        else:
            # Connect with connection string (SQL auth or env vars)
            conn = pyodbc.connect(self.connection_string)
        return conn
    
    def _get_database_schema(self) -> str:
        """Retrieve the database schema to help with query generation."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Get tables and columns
            schema_query = """
            SELECT 
                t.TABLE_NAME,
                c.COLUMN_NAME,
                c.DATA_TYPE,
                c.IS_NULLABLE,
                CASE WHEN pk.COLUMN_NAME IS NOT NULL THEN 'YES' ELSE 'NO' END AS IS_PRIMARY_KEY
            FROM INFORMATION_SCHEMA.TABLES t
            LEFT JOIN INFORMATION_SCHEMA.COLUMNS c ON t.TABLE_NAME = c.TABLE_NAME
            LEFT JOIN (
                SELECT ku.TABLE_NAME, ku.COLUMN_NAME
                FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
                JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE ku
                    ON tc.CONSTRAINT_NAME = ku.CONSTRAINT_NAME
                WHERE tc.CONSTRAINT_TYPE = 'PRIMARY KEY'
            ) pk ON c.TABLE_NAME = pk.TABLE_NAME AND c.COLUMN_NAME = pk.COLUMN_NAME
            WHERE t.TABLE_TYPE = 'BASE TABLE'
            ORDER BY t.TABLE_NAME, c.ORDINAL_POSITION
            """
            
            cursor.execute(schema_query)
            rows = cursor.fetchall()
            
            # Build schema description
            schema_dict = {}
            for row in rows:
                table_name = row.TABLE_NAME
                if table_name not in schema_dict:
                    schema_dict[table_name] = []
                
                column_info = {
                    'name': row.COLUMN_NAME,
                    'type': row.DATA_TYPE,
                    'nullable': row.IS_NULLABLE,
                    'primary_key': row.IS_PRIMARY_KEY
                }
                schema_dict[table_name].append(column_info)
            
            # Format schema as text
            schema_text = "Database Schema:\n\n"
            for table_name, columns in schema_dict.items():
                schema_text += f"Table: {table_name}\n"
                for col in columns:
                    pk_marker = " (PRIMARY KEY)" if col['primary_key'] == 'YES' else ""
                    schema_text += f"  - {col['name']}: {col['type']}{pk_marker}\n"
                schema_text += "\n"
            
            cursor.close()
            conn.close()
            
            return schema_text
            
        except Exception as e:
            return f"Error retrieving schema: {str(e)}"
    
    def _generate_sql_query(self, user_question: str) -> Dict[str, Any]:
        """Use Azure OpenAI to generate SQL query from natural language."""
        
        system_message = f"""You are a SQL expert assistant. Your task is to convert natural language questions into SQL queries for a Microsoft SQL Server database.

{self.schema_info}

Guidelines:
- Generate valid T-SQL queries for Microsoft SQL Server
- Use proper table and column names from the schema above
- Include appropriate JOINs when needed
- Use TOP instead of LIMIT for row limiting
- Format the query for readability
- If the question is ambiguous, make reasonable assumptions
- Only generate SELECT queries for safety (no INSERT, UPDATE, DELETE)
- Return your response as JSON with two fields: "sql" (the query) and "explanation" (brief explanation of what the query does)
- **IMPORTANT**: Consider the conversation history to understand context and references to previous queries
- If the user refers to "those", "them", "it", "that", etc., look at the conversation history to understand what they're referring to

Example response format:
{{
    "sql": "SELECT * FROM Products WHERE UnitPrice > 20",
    "explanation": "This query retrieves all products with a unit price greater than 20"
}}
"""
        
        try:
            # Build messages with conversation history for context
            messages = [{"role": "system", "content": system_message}]
            
            # Add recent conversation history (last 3 exchanges for context)
            for entry in self.conversation_history[-3:]:
                messages.append({"role": "user", "content": entry['question']})
                messages.append({"role": "assistant", "content": f"SQL: {entry['sql']}\n{entry['response']}"})
            
            # Add current question
            messages.append({"role": "user", "content": user_question})
            
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=messages,
                temperature=0.1,
                max_tokens=1000,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return {
                'success': True,
                'sql': result.get('sql', ''),
                'explanation': result.get('explanation', ''),
                'error': None
            }
            
        except Exception as e:
            return {
                'success': False,
                'sql': None,
                'explanation': None,
                'error': f"Error generating SQL: {str(e)}"
            }
    
    def _execute_query(self, sql_query: str) -> Dict[str, Any]:
        """Execute the SQL query and return results."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Execute the query
            cursor.execute(sql_query)
            
            # Get column names
            columns = [column[0] for column in cursor.description]
            
            # Fetch results
            rows = cursor.fetchall()
            
            # Convert to list of dictionaries
            results = []
            for row in rows:
                results.append(dict(zip(columns, row)))
            
            cursor.close()
            conn.close()
            
            return {
                'success': True,
                'data': results,
                'row_count': len(results),
                'columns': columns,
                'error': None
            }
            
        except Exception as e:
            return {
                'success': False,
                'data': None,
                'row_count': 0,
                'columns': None,
                'error': f"Error executing query: {str(e)}"
            }
    
    def _format_results_for_llm(self, results: Dict[str, Any]) -> str:
        """Format query results for LLM to generate natural language response."""
        if not results['success']:
            return f"Error: {results['error']}"
        
        if results['row_count'] == 0:
            return "No results found."
        
        # Format as text
        formatted = f"Found {results['row_count']} result(s):\n\n"
        for i, row in enumerate(results['data'][:10], 1):  # Limit to first 10 rows
            formatted += f"Row {i}:\n"
            for key, value in row.items():
                formatted += f"  {key}: {value}\n"
            formatted += "\n"
        
        if results['row_count'] > 10:
            formatted += f"... and {results['row_count'] - 10} more rows\n"
        
        return formatted
    
    def _generate_natural_language_response(
        self, 
        user_question: str, 
        sql_query: str, 
        query_results: Dict[str, Any]
    ) -> str:
        """Generate a natural language response based on query results."""
        
        results_text = self._format_results_for_llm(query_results)
        
        system_message = """You are a helpful assistant that explains database query results in natural language.
Given a user's question, the SQL query that was executed, and the results, provide a clear, concise answer in natural language.
Focus on answering the user's original question directly.
Consider the conversation history to provide contextual responses."""
        
        # Build conversation context
        context = ""
        if self.conversation_history:
            context = "\n\nRecent conversation context:\n"
            for entry in self.conversation_history[-2:]:  # Last 2 exchanges
                context += f"Q: {entry['question']}\nA: {entry['response'][:200]}...\n\n"
        
        user_message = f"""User Question: {user_question}
{context}
SQL Query Executed:
{sql_query}

Query Results:
{results_text}

Please provide a natural language answer to the user's question based on these results. If the user is asking a follow-up question, acknowledge the previous context."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error generating response: {str(e)}"
    
    def query(self, user_question: str) -> Dict[str, Any]:
        """
        Main method to process a natural language question.
        Returns SQL query, results, and natural language response.
        """
        # Step 1: Generate SQL query
        sql_generation = self._generate_sql_query(user_question)
        
        if not sql_generation['success']:
            return {
                'success': False,
                'question': user_question,
                'sql': None,
                'explanation': None,
                'results': None,
                'response': sql_generation['error'],
                'error': sql_generation['error']
            }
        
        sql_query = sql_generation['sql']
        explanation = sql_generation['explanation']
        
        # Step 2: Execute query
        query_results = self._execute_query(sql_query)
        
        # Step 3: Generate natural language response
        if query_results['success']:
            nl_response = self._generate_natural_language_response(
                user_question, 
                sql_query, 
                query_results
            )
        else:
            nl_response = f"I encountered an error executing the query: {query_results['error']}"
        
        # Add to conversation history
        self.conversation_history.append({
            'question': user_question,
            'sql': sql_query,
            'response': nl_response
        })
        
        return {
            'success': query_results['success'],
            'question': user_question,
            'sql': sql_query,
            'explanation': explanation,
            'results': query_results['data'] if query_results['success'] else None,
            'row_count': query_results['row_count'],
            'response': nl_response,
            'error': query_results.get('error')
        }
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Return the conversation history."""
        return self.conversation_history
    
    def clear_history(self):
        """Clear the conversation history."""
        self.conversation_history = []


def create_agent_from_env() -> SQLAgent:
    """Create SQLAgent instance from environment variables."""
    return SQLAgent(
        sql_server=os.getenv('SQL_SERVER'),
        sql_database=os.getenv('SQL_DATABASE'),
        sql_username=os.getenv('SQL_USERNAME'),
        sql_password=os.getenv('SQL_PASSWORD'),
        azure_openai_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT'),
        azure_openai_api_key=os.getenv('AZURE_OPENAI_API_KEY'),
        azure_openai_deployment=os.getenv('AZURE_OPENAI_DEPLOYMENT'),
        azure_openai_api_version=os.getenv('AZURE_OPENAI_API_VERSION', '2024-08-01-preview')
    )
