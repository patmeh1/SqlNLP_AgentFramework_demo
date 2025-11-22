"""
MedData SQL Agent using Microsoft Agent Framework, Azure OpenAI, and POML
This agent queries the medical ontology database using slot-based structure.
Integrates POML (Prompt Optimization Markup Language) for advanced prompt engineering.
"""

import os
import pyodbc
from typing import List, Dict, Any, Optional
from openai import AzureOpenAI
import json
import struct
from azure.identity import DefaultAzureCredential, AzureCliCredential


# POML System Prompt for Medical Ontology
MEDICAL_ONTOLOGY_SYSTEM_PROMPT = """
<system>
<role>Medical Ontology SQL Query Expert for Multi-Step Analysis</role>
<context>
You are an expert system for querying a medical ontology knowledge base using a slot-based architecture.
You understand complex multi-step queries that require:
1. Finding initial entities (procedures, tests, problems) by various criteria
2. Traversing relationships between entities (indicated by, measures, related to)
3. Enriching results with semantic codes and descriptive information
4. Aggregating results across multiple relationship paths

<knowledge_base_structure>
**Database Schema:**
- **MED Table**: Contains medical concepts (codes) with attributes stored as slot-value pairs
  - CODE (NVARCHAR 50): Unique identifier for medical concepts (e.g., '1302', '3668', '19928')
  - SLOT_NUMBER (INT): References the type of attribute (see MED_SLOTS)
  - SLOT_VALUE (NVARCHAR 200): The actual value for this attribute or reference to another CODE

- **MED_SLOTS Table**: Defines the semantic meaning of each slot number
  - SLOT_NUMBER (INT): Unique identifier for the slot type
  - SLOT_NAME (NVARCHAR 100): Name and type of the slot (format: "SLOT-NAME,TYPE")

**Understanding the Data Model:**
The MED table represents a SEMANTIC NETWORK where:
- Each CODE is a unique medical concept (test, problem, procedure, measurement, etc.)
- Each CODE can have MULTIPLE ROWS (one per attribute/slot)
- SLOT_NUMBER indicates WHAT the attribute is
- SLOT_VALUE indicates the VALUE or REFERENCE to another CODE
- This creates a GRAPH of relationships between concepts

**Key Slot Types (and their usage patterns):**
- Slot 3: DESCENDANT-OF (semantic hierarchy - CODE is a descendant of SLOT_VALUE)
- Slot 4: SUBCLASS-OF (semantic classification - CODE is subclass of SLOT_VALUE)
- Slot 6: PRINT-NAME (human-readable name for the concept - SLOT_VALUE is the name string)
- Slot 9: CPMC-LAB-PROC-CODE (institutional codes for procedures)
- Slot 15: MEASURED-BY-PROCEDURE (what procedure measures this - CODE is measured by SLOT_VALUE procedure)
- Slot 16: ENTITY-MEASURED (semantic meaning - what does this test/procedure measure)
- Slot 20: CPMC-LAB-TEST-CODE (institutional test codes)
- Slot 149: PT-PROBLEM-(INDICATED-BY)->PROCEDURE (inverse: problems that indicate this procedure)
- Slot 150: PROCEDURE-(INDICATES)->PT-PROBLEM (forward: problems indicated by this procedure - SLOT_VALUE is problem CODE)
- Slot 212: LOINC-CODE (standardized LOINC code - SLOT_VALUE is the LOINC code like '2947-0')
- Slot 264: MILLENNIUM-LAB-CODE (system-specific codes)
- Slot 266: SNOMED-CODE (standardized SNOMED CT codes)
- Slot 277: EPIC-COMPONENT-ID (EHR integration codes)
</knowledge_base_structure>

<query_patterns>
**Single-Step Queries:**

1. **Finding tests by LOINC code:**
   SELECT DISTINCT m1.CODE, MAX(CASE WHEN m2.SLOT_NUMBER = 6 THEN m2.SLOT_VALUE END) AS [Name], MAX(CASE WHEN m3.SLOT_NUMBER = 266 THEN m3.SLOT_VALUE END) AS [SNOMED Code] FROM MED m1 LEFT JOIN MED m2 ON m1.CODE = m2.CODE AND m2.SLOT_NUMBER = 6 LEFT JOIN MED m3 ON m1.CODE = m3.CODE AND m3.SLOT_NUMBER = 266 WHERE m1.SLOT_NUMBER = 212 AND m1.SLOT_VALUE = '2947-0' GROUP BY m1.CODE

2. **Finding Pt-Problems indicated by a procedure with LOINC code:**
   SELECT DISTINCT prob.CODE, MAX(CASE WHEN pname.SLOT_NUMBER = 6 THEN pname.SLOT_VALUE END) AS [Problem Name], MAX(CASE WHEN psnomed.SLOT_NUMBER = 266 THEN psnomed.SLOT_VALUE END) AS [Problem SNOMED Code] FROM MED loinc_ref INNER JOIN MED indicates ON loinc_ref.CODE = indicates.CODE AND indicates.SLOT_NUMBER = 150 INNER JOIN MED prob ON indicates.SLOT_VALUE = prob.CODE LEFT JOIN MED pname ON prob.CODE = pname.CODE AND pname.SLOT_NUMBER = 6 LEFT JOIN MED psnomed ON prob.CODE = psnomed.CODE AND psnomed.SLOT_NUMBER = 266 WHERE loinc_ref.SLOT_NUMBER = 212 AND loinc_ref.SLOT_VALUE = '2947-0' GROUP BY prob.CODE

3. **Finding tests by name (fuzzy search):**
   SELECT DISTINCT m1.CODE, m1.SLOT_VALUE AS [Test Name] FROM MED m1 WHERE m1.SLOT_NUMBER = 6 AND m1.SLOT_VALUE LIKE '%glucose%' ORDER BY m1.SLOT_VALUE

4. **Getting all attributes for a code:**
   SELECT m.SLOT_NUMBER, ms.SLOT_NAME, m.SLOT_VALUE FROM MED m LEFT JOIN MED_SLOTS ms ON m.SLOT_NUMBER = ms.SLOT_NUMBER WHERE m.CODE = 'CODE_VALUE' ORDER BY m.SLOT_NUMBER

**Multi-Step Query Patterns (Complex Queries):**

5. **Multi-hop relationships (e.g., procedures → problems → related tests):**
   Build queries in steps:
   - Step 1: Find starting entities (e.g., procedures with LOINC code)
   - Step 2: Traverse to related entities (e.g., problems indicated by those procedures)
   - Step 3: Enrich with additional relationships (e.g., codes, names, measurements)
   - Step 4: Aggregate all information into single result set

6. **Filtering and comparison across relationships:**
   When the query mentions multiple criteria like:
   - "Show me tests that indicate both hypernatremia AND hyponatremia"
   - "Find procedures related to LOINC 2947-0 that indicate problems with specific SNOMED codes"
   Translate to: Multi-table joins with GROUP BY and HAVING for counting related items

7. **Semantic traversal (following classification hierarchies):**
   When asked about "all types of", "subcategories of", "related to":
   - Use slot 3 (DESCENDANT-OF) or slot 4 (SUBCLASS-OF)
   - Chain multiple joins to traverse the hierarchy
   - Include all descendants or subclasses in results
</query_patterns>

<reasoning_guidelines>
**CRITICAL SQL Generation Rules:**

1. **Multiple Attributes**: Use MAX(CASE WHEN ...) or conditional aggregation to get multiple slot values in one row

2. **Group By**: Always GROUP BY when using conditional aggregation (MAX, MIN, COUNT, etc.)

3. **Join Strategy**: 
   - Use LEFT JOINs for optional attributes (like PRINT-NAME, SNOMED-CODE)
   - Use INNER JOINs for required relationships (like slot 150 relationships)

4. **DISTINCT**: Use when joining multiple times to same table to avoid duplicate rows

5. **Alias**: Always alias joined tables (m1, m2, m3, etc.) and use descriptive column aliases

6. **Fuzzy Matching**: Use LIKE '%search%' for partial text matches in SLOT_VALUE

7. **NULL Handling**: Results with NULL slot values are valid - they represent missing attributes

8. **LOINC Priority**: When user mentions LOINC code (slot 212), prioritize finding procedures by LOINC first

9. **SNOMED Association**: Always try to include SNOMED code (slot 266) in results

10. **Relationships**: CRITICAL - Understand the join pattern:
    - For slot 150 (PROCEDURE-(INDICATES)->PT-PROBLEM):
      * Join to find procedures: table1.CODE in a query where table1.SLOT_NUMBER=212
      * Join to find indicated problems: table2.CODE = table1.CODE AND table2.SLOT_NUMBER=150
      * Get problem codes: table3.CODE = table2.SLOT_VALUE (SLOT_VALUE contains the related CODE)
    - For other relationship slots: SLOT_VALUE points to the related CODE

11. **Multi-Step Queries**: 
    - Break complex queries into logical steps
    - Start with finding base entities (tests/procedures/problems)
    - Then traverse relationships to find connected entities
    - Finally enrich with names and codes
    - Return ALL relevant information in single result set

12. **Optimization**: 
    - Use TOP N when appropriate to limit results
    - Use WHERE clauses early to filter before joins
    - Avoid cross joins unless intentional

**IMPORTANT - Avoid These Mistakes:**
- DON'T use column names directly in WHERE clauses after aggregation (would cause error)
- DON'T use string literals for slot values without proper quoting
- DON'T forget to GROUP BY when using aggregate functions
- DON'T confuse SLOT_VALUE with CODE - SLOT_VALUE contains the actual data or reference to another CODE
- DON'T use ### symbols or comments in the SQL - return clean SQL only
- DON'T use undefined aliases or columns
- DON'T forget DISTINCT when doing multiple joins to avoid duplicates
- DON'T forget to include the relationship join condition (SLOT_NUMBER check) when traversing relationships
- DON'T assume a relationship exists - verify slot number matches the intended relationship
</reasoning_guidelines>

<output_format>
Return ONLY a valid T-SQL query. No explanations, no markdown, no code fences.
The query will be executed directly on Microsoft SQL Server.

For complex multi-step queries:
- Build single query that traverses all relationships in one go
- Use multiple INNER/LEFT JOINs to connect all required data
- Return a single result set with all requested information
- Do NOT return multiple queries or suggest multiple steps
</output_format>

<data_insights>
**Important Facts About This Database:**
- Test procedures with LOINC codes (like 2947-0 for sodium) often indicate multiple patient problems
- Patient problems (like Hypernatremia, Hyponatremia) can be indicated by multiple procedures
- Many procedures and problems have SNOMED codes for standardization
- Names (slot 6) are human-readable and help interpret the meaning of codes
- Each medical concept can have multiple attributes - always use DISTINCT and GROUP BY
- Relationships flow through SLOT_NUMBER/SLOT_VALUE pairs in the MED table
- When joining relationships, remember: CODE connects to next table's CODE, SLOT_VALUE points to the related CODE
</data_insights>
</context>
</system>
"""


class MedDataSQLAgent:
    """Agent that translates natural language to SQL queries for medical ontology database."""
    
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
        use_azure_ad: bool = True,
        use_poml: bool = True
    ):
        """Initialize the MedData SQL Agent with database and Azure OpenAI credentials."""
        self.sql_server = sql_server
        self.sql_database = sql_database
        self.sql_username = sql_username
        self.sql_password = sql_password
        self.use_azure_ad = use_azure_ad or (sql_username is None and sql_password is None)
        self.use_poml = use_poml
        
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
            SQL_COPT_SS_ACCESS_TOKEN = 1256
            conn = pyodbc.connect(self.connection_string, attrs_before={SQL_COPT_SS_ACCESS_TOKEN: self.token_struct})
        else:
            conn = pyodbc.connect(self.connection_string)
        return conn
    
    def _get_database_schema(self) -> str:
        """Retrieve the medical ontology database schema."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            schema_parts = []
            
            # Get table information
            schema_parts.append("=== MEDICAL ONTOLOGY DATABASE SCHEMA ===\n")
            
            # MED table
            schema_parts.append("\n--- Table: MED (Medical Concepts & Attributes) ---")
            cursor.execute("""
                SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, IS_NULLABLE
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = 'MED'
                ORDER BY ORDINAL_POSITION
            """)
            schema_parts.append("Columns:")
            for row in cursor.fetchall():
                col_name, data_type, max_len, nullable = row
                length_info = f"({max_len})" if max_len else ""
                null_info = "NULL" if nullable == "YES" else "NOT NULL"
                schema_parts.append(f"  - {col_name}: {data_type}{length_info} {null_info}")
            
            # Get sample slot distribution
            cursor.execute("""
                SELECT TOP 5 SLOT_NUMBER, COUNT(*) as count
                FROM MED
                GROUP BY SLOT_NUMBER
                ORDER BY count DESC
            """)
            schema_parts.append("\nTop Slot Usage:")
            for row in cursor.fetchall():
                schema_parts.append(f"  - Slot {row[0]}: {row[1]} entries")
            
            # MED_SLOTS table
            schema_parts.append("\n--- Table: MED_SLOTS (Slot Definitions) ---")
            cursor.execute("""
                SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, IS_NULLABLE
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = 'MED_SLOTS'
                ORDER BY ORDINAL_POSITION
            """)
            schema_parts.append("Columns:")
            for row in cursor.fetchall():
                col_name, data_type, max_len, nullable = row
                length_info = f"({max_len})" if max_len else ""
                null_info = "NULL" if nullable == "YES" else "NOT NULL"
                schema_parts.append(f"  - {col_name}: {data_type}{length_info} {null_info}")
            
            # Get all slot definitions
            cursor.execute("SELECT SLOT_NUMBER, SLOT_NAME FROM MED_SLOTS ORDER BY SLOT_NUMBER")
            schema_parts.append("\nAvailable Slots:")
            for row in cursor.fetchall():
                schema_parts.append(f"  - Slot {row[0]}: {row[1]}")
            
            # Get total counts
            cursor.execute("SELECT COUNT(DISTINCT CODE) FROM MED")
            unique_codes = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM MED")
            total_entries = cursor.fetchone()[0]
            
            schema_parts.append(f"\n=== DATABASE STATISTICS ===")
            schema_parts.append(f"Total unique medical codes: {unique_codes}")
            schema_parts.append(f"Total slot-value pairs: {total_entries}")
            schema_parts.append(f"Average attributes per code: {total_entries / unique_codes:.1f}")
            
            conn.close()
            return "\n".join(schema_parts)
            
        except Exception as e:
            return f"Error retrieving schema: {str(e)}"
    
    def _generate_sql_query(self, question: str) -> Dict[str, Any]:
        """Generate SQL query from natural language using Azure OpenAI with POML."""
        
        # Build messages with POML system prompt if enabled
        messages = []
        
        if self.use_poml:
            messages.append({
                "role": "system",
                "content": MEDICAL_ONTOLOGY_SYSTEM_PROMPT
            })
        
        # Add schema context (AFTER the POML system prompt for proper instruction order)
        messages.append({
            "role": "system",
            "content": f"""**SQL GENERATION INSTRUCTIONS:**
            
Database Schema:
{self.schema_info}

**YOUR TASK**: Generate a T-SQL query to answer the user's question.

**CRITICAL REQUIREMENTS:**
1. Return ONLY valid T-SQL - no markdown, no code fences, no explanations
2. Use MAX(CASE WHEN slot = X THEN value END) for multiple attributes per row
3. Always GROUP BY when using aggregate functions
4. Use DISTINCT when joining multiple times to avoid duplicates
5. Use LEFT JOIN for optional attributes, INNER JOIN for required relationships
6. For Pt-Problems queries: Use slot 150 (PROCEDURE-(INDICATES)->PT-PROBLEM) to link procedures to problems
7. Always include slot 6 (PRINT-NAME) for human-readable names
8. Always try to include slot 266 (SNOMED-CODE) for standard terminology
9. Use TOP 100 to limit results for performance

**EXAMPLE - Pt-Problems for LOINC code:**
SELECT DISTINCT prob.CODE, MAX(CASE WHEN n.SLOT_NUMBER=6 THEN n.SLOT_VALUE END) AS Name, MAX(CASE WHEN s.SLOT_NUMBER=266 THEN s.SLOT_VALUE END) AS SNOMEDCode FROM MED loinc_ref INNER JOIN MED indicates ON loinc_ref.CODE = indicates.CODE AND indicates.SLOT_NUMBER = 150 INNER JOIN MED prob ON indicates.SLOT_VALUE = prob.CODE LEFT JOIN MED n ON prob.CODE = n.CODE AND n.SLOT_NUMBER = 6 LEFT JOIN MED s ON prob.CODE = s.CODE AND s.SLOT_NUMBER = 266 WHERE loinc_ref.SLOT_NUMBER = 212 AND loinc_ref.SLOT_VALUE = '2947-0' GROUP BY prob.CODE
"""
        })
        
        # Add conversation history
        for msg in self.conversation_history[-6:]:  # Last 3 exchanges
            messages.append(msg)
        
        # Add current question
        messages.append({
            "role": "user",
            "content": question
        })
        
        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=messages,
                temperature=0.1,
                max_tokens=1000
            )
            
            sql_query = response.choices[0].message.content.strip()
            
            # Clean up the SQL query
            sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
            
            return {
                "success": True,
                "sql": sql_query,
                "question": question
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error generating SQL: {str(e)}",
                "question": question
            }
    
    def _execute_query(self, sql_query: str) -> Dict[str, Any]:
        """Execute SQL query and return results with detailed error information."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(sql_query)
            
            # Get column names
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            
            # Fetch results
            rows = cursor.fetchall()
            
            # Convert to list of dictionaries
            results = []
            for row in rows:
                results.append({columns[i]: str(row[i]) if row[i] is not None else None 
                               for i in range(len(columns))})
            
            conn.close()
            
            return {
                "success": True,
                "results": results,
                "row_count": len(results),
                "columns": columns
            }
            
        except Exception as e:
            # Extract detailed error information for better debugging
            error_str = str(e)
            error_details = {
                "success": False,
                "error": error_str,
                "sql_query": sql_query,
                "error_type": type(e).__name__
            }
            
            # Parse common SQL Server errors to provide helpful context
            if "Incorrect syntax" in error_str:
                error_details["error_category"] = "SYNTAX_ERROR"
                # Provide specific hints for common syntax errors
                if "LIMIT" in error_str:
                    error_details["hint"] = "T-SQL doesn't support LIMIT. Use TOP instead (e.g., SELECT TOP 10 instead of LIMIT 10)"
                elif "The" in error_str and "keyword" in error_str:
                    error_details["hint"] = "A SQL keyword is missing or incorrect. Check the query syntax carefully."
                else:
                    error_details["hint"] = "The generated SQL has a syntax error. Check for missing keywords, unmatched parentheses, or incorrect table/column names."
            elif "Invalid column name" in error_str or "Column name" in error_str:
                error_details["error_category"] = "COLUMN_ERROR"
                error_details["hint"] = "The SQL references a column that doesn't exist. Verify slot numbers and column names match the schema."
            elif "Invalid table name" in error_str or "Table name" in error_str:
                error_details["error_category"] = "TABLE_ERROR"
                error_details["hint"] = "The SQL references a table that doesn't exist. Valid tables are: MED, MED_SLOTS"
            elif "Ambiguous column" in error_str:
                error_details["error_category"] = "AMBIGUOUS_REFERENCE"
                error_details["hint"] = "Multiple tables have a column with this name. Use aliases (e.g., m1.CODE vs m2.CODE)"
            elif "Conversion failed" in error_str or "Cannot convert" in error_str:
                error_details["error_category"] = "TYPE_ERROR"
                error_details["hint"] = "There's a data type mismatch. Verify that JOIN conditions compare compatible types."
            elif "An expression of non-boolean" in error_str or "specified in a context where a condition" in error_str:
                error_details["error_category"] = "BOOLEAN_ERROR"
                error_details["hint"] = "A WHERE or JOIN condition is invalid. Make sure comparisons return true/false values."
            elif "GROUP BY" in error_str or "aggregate" in error_str:
                error_details["error_category"] = "AGGREGATE_ERROR"
                error_details["hint"] = "Check that all non-aggregated columns in SELECT are in the GROUP BY clause."
            else:
                error_details["error_category"] = "UNKNOWN_ERROR"
                error_details["hint"] = "An unexpected database error occurred. Check the SQL syntax and database connectivity."
            
            return error_details
    
    def _format_response(self, question: str, sql_query: str, query_results: Dict[str, Any]) -> str:
        """Format the query results into a natural language response using POML-enhanced prompting."""
        
        if not query_results.get("success"):
            return f"I encountered an error: {query_results.get('error')}"
        
        results = query_results.get("results", [])
        row_count = query_results.get("row_count", 0)
        
        if row_count == 0:
            return "No matching medical concepts found in the ontology."
        
        # Build context-aware formatting prompt with POML
        messages = []
        
        if self.use_poml:
            messages.append({
                "role": "system",
                "content": MEDICAL_ONTOLOGY_SYSTEM_PROMPT
            })
        
        messages.append({
            "role": "system",
            "content": f"""Format these medical ontology query results into a clear, informative response.
            
<guidelines>
- Explain medical concepts in accessible language
- Highlight standard codes (LOINC, SNOMED) when present
- Show hierarchical relationships when relevant
- Group related attributes together
- Use medical terminology accurately
</guidelines>"""
        })
        
        messages.append({
            "role": "user",
            "content": f"""Question: {question}

SQL Query: {sql_query}

Results ({row_count} rows):
{json.dumps(results[:10], indent=2)}

Please provide a clear, informative answer about these medical concepts."""
        })
        
        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=messages,
                temperature=0.3,
                max_tokens=1500
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            # Fallback to basic formatting
            return f"Found {row_count} medical concepts. Here are the results:\n\n{json.dumps(results[:5], indent=2)}"
    
    def query(self, question: str) -> Dict[str, Any]:
        """
        Main query method - converts natural language to SQL, executes, and formats response.
        
        Args:
            question: Natural language question about the medical ontology
            
        Returns:
            Dictionary with success status, response, SQL query, and results
        """
        # Generate SQL query
        sql_result = self._generate_sql_query(question)
        
        if not sql_result.get("success"):
            return sql_result
        
        sql_query = sql_result["sql"]
        
        # Execute query
        query_results = self._execute_query(sql_query)
        
        if not query_results.get("success"):
            # Return error with helpful information for General Agent to interpret
            return {
                "success": False,
                "question": question,
                "sql": sql_query,
                "error": query_results.get("error"),
                "error_category": query_results.get("error_category"),
                "error_hint": query_results.get("hint"),
                "error_type": query_results.get("error_type")
            }
        
        # Format response
        response_text = self._format_response(question, sql_query, query_results)
        
        # Update conversation history
        self.conversation_history.append({
            "role": "user",
            "content": question
        })
        self.conversation_history.append({
            "role": "assistant",
            "content": f"SQL: {sql_query}\n\n{response_text}"
        })
        
        return {
            "success": True,
            "question": question,
            "sql": sql_query,
            "response": response_text,
            "results": query_results["results"],
            "row_count": query_results["row_count"],
            "columns": query_results.get("columns", [])
        }
    
    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []
    
    def get_schema(self) -> str:
        """Get the database schema information."""
        return self.schema_info


def create_meddata_agent_from_env() -> MedDataSQLAgent:
    """
    Create a MedDataSQLAgent from environment variables.
    
    Returns:
        MedDataSQLAgent instance configured from .env
    """
    import os
    
    return MedDataSQLAgent(
        sql_server=os.getenv('MEDDATA_SQL_SERVER'),
        sql_database=os.getenv('MEDDATA_SQL_DATABASE', 'MedData'),
        sql_username=os.getenv('SQL_USERNAME'),
        sql_password=os.getenv('SQL_PASSWORD'),
        azure_openai_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT'),
        azure_openai_api_key=os.getenv('AZURE_OPENAI_API_KEY'),
        azure_openai_deployment=os.getenv('AZURE_OPENAI_DEPLOYMENT'),
        use_azure_ad=os.getenv('MEDDATA_USE_AZURE_AD', 'true').lower() == 'true',
        use_poml=True  # Enable POML by default
    )
