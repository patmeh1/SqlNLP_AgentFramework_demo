# Hybrid Agent Architecture with Memory

## 🏗️ System Architecture

The system now uses a **Hybrid Agent Architecture** that chains SQL query execution through a General Agent for verification and response refinement, with persistent conversation memory.

```
┌─────────────────────────────────────────────────────────────┐
│                      User Question                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 1: SQL Agent (POML-Enhanced)                          │
│  • Generates SQL query from natural language                │
│  • Executes query against MedData database                  │
│  • Formats initial response                                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ SQL Results + Response
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 2: General Agent (Verification)                       │
│  • Reviews SQL results for accuracy                         │
│  • Verifies response answers the question                   │
│  • Adds medical context from memory                         │
│  • Refines and clarifies the response                       │
│  • Highlights key findings                                  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ Verified Response
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 3: Memory Storage                                     │
│  • Stores complete interaction:                             │
│    - Original question                                      │
│    - SQL query executed                                     │
│    - SQL results                                            │
│    - SQL agent response                                     │
│    - Final verified response                                │
│    - Timestamp                                              │
│  • Enables context-aware follow-up questions                │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
                 Final Response
```

## 🎯 Key Features

### 1. **SQL-to-General Agent Chaining**
- SQL agent executes database queries with POML-enhanced prompts
- General agent reviews and verifies the response
- Ensures accuracy and improves clarity
- Adds contextual information from conversation history

### 2. **Persistent Conversation Memory**
Each interaction stores:
- **Question**: User's original query
- **SQL Query**: Generated SQL statement
- **SQL Results**: Raw database results
- **SQL Response**: Initial SQL agent response
- **Final Response**: Verified and refined response
- **Timestamp**: When the interaction occurred

### 3. **Context-Aware Follow-ups**
- System remembers previous interactions
- Can answer follow-up questions using context
- Example:
  ```
  Q1: "Show me tests with LOINC 2947-0"
  Q2: "What problems do those tests indicate?" ← Uses context from Q1
  Q3: "Give me the SNOMED codes for those problems" ← Uses context from Q1 & Q2
  ```

## 📡 API Endpoints

### Query Endpoint
**POST** `/api/query`
```json
Request:
{
  "question": "Show me tests with LOINC code 2947-0"
}

Response:
{
  "success": true,
  "question": "Show me tests with LOINC code 2947-0",
  "sql": "SELECT ...",
  "sql_response": "Initial SQL agent response",
  "final_response": "Verified and refined response",
  "results": [...],
  "row_count": 11,
  "agent_used": "Hybrid Agent (SQL→General)",
  "agent_chain": "SQL → General Agent → Memory",
  "memory_size": 5,
  "timestamp": "2025-11-22T11:42:30.123456"
}
```

### Memory Endpoints

#### Get Memory
**GET** `/api/memory`
```json
Response:
{
  "success": true,
  "memory": {
    "total_interactions": 5,
    "interactions": [
      {
        "timestamp": "2025-11-22T11:42:30",
        "question": "Show me tests with LOINC 2947-0",
        "sql_query": "SELECT ...",
        "row_count": 11,
        "final_response": "Found 11 tests..."
      }
    ]
  }
}
```

#### Get History
**GET** `/api/history`
```json
Response:
{
  "success": true,
  "total_interactions": 5,
  "history": [...]
}
```

#### Clear Memory
**POST** `/api/clear`
```json
Response:
{
  "success": true,
  "message": "History and memory cleared"
}
```

#### Export Memory
**POST** `/api/memory/export`
```json
Response:
{
  "success": true,
  "message": "Memory exported to memory_export_abc123_20251122_114230.json",
  "filename": "memory_export_abc123_20251122_114230.json"
}
```

## 💡 How It Works

### Example Interaction Flow

**User asks**: "What are the patient problems for tests with LOINC 2947-0?"

1. **SQL Agent (Step 1)**:
   ```sql
   -- Generated with POML context
   SELECT DISTINCT 
       m1.SLOT_VALUE as PROBLEM_CODE,
       problem_name.SLOT_VALUE as PROBLEM_NAME,
       problem_snomed.SLOT_VALUE as PROBLEM_SNOMED
   FROM MED m1
   LEFT JOIN MED problem_name ON m1.SLOT_VALUE = problem_name.CODE 
       AND problem_name.SLOT_NUMBER = 6
   LEFT JOIN MED problem_snomed ON m1.SLOT_VALUE = problem_snomed.CODE 
       AND problem_snomed.SLOT_NUMBER = 266
   WHERE m1.SLOT_NUMBER = 150
   AND m1.CODE IN (
       SELECT CODE FROM MED WHERE SLOT_NUMBER = 212 AND SLOT_VALUE = '2947-0'
   )
   ```
   
   **SQL Response**: "Found 2 patient problems. Here are the results: [data]"

2. **General Agent (Step 2)** receives:
   - Original question
   - SQL query
   - Results (2 rows: Hyponatremia, Hypernatremia)
   - SQL agent's response
   - Recent conversation context
   
   **Verification Prompt**:
   ```
   Review this medical database query response:
   
   User Question: "What are the patient problems for tests with LOINC 2947-0?"
   SQL Query: [above SQL]
   Results: 2 rows returned
   
   Please verify accuracy and refine the response...
   ```
   
   **Refined Response**:
   ```
   Based on the medical ontology database, tests with LOINC code 2947-0 
   (Sodium Whole Blood tests) indicate two patient problems:
   
   1. **Hyponatremia** (Code: 19928, SNOMED: 89627008)
      - Low blood sodium level
      - Clinical condition requiring monitoring
   
   2. **Hypernatremia** (Code: 3668, SNOMED: 39355002)
      - High blood sodium level
      - Opposite condition from hyponatremia
   
   These sodium tests can detect both abnormally low and abnormally high 
   sodium levels, which is why both conditions are associated with the 
   LOINC code 2947-0.
   ```

3. **Memory Storage (Step 3)**:
   Stores complete interaction for future context

## 🧠 Memory Management

### InteractionMemory Class
Manages conversation history with SQL context:

```python
memory = InteractionMemory()

# Add interaction
memory.add_interaction(
    question="What tests have LOINC 2947-0?",
    sql_query="SELECT ...",
    sql_results=[...],
    sql_response="Initial response",
    final_response="Verified response",
    timestamp=datetime.now()
)

# Get recent context for next query
context = memory.get_recent_context(n=3)  # Last 3 interactions

# Export to file
memory_dict = memory.to_dict()
```

### Benefits of Memory
1. **Follow-up Questions**: "What are their SNOMED codes?" ← knows what "their" refers to
2. **Context Continuity**: Maintains thread across multiple questions
3. **Improved Accuracy**: General agent uses past context for better responses
4. **Debugging**: Export memory to review conversation flow
5. **Session Persistence**: Each user session has independent memory

## 🔧 Configuration

### Environment Variables
All existing configuration in `.env` still applies:
- `MEDDATA_SQL_SERVER`
- `MEDDATA_SQL_DATABASE`
- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_API_KEY`
- `AZURE_OPENAI_DEPLOYMENT`

### Agent Initialization
```python
from hybrid_agent_with_memory import create_hybrid_agent_from_env

# Create hybrid agent
agent = await create_hybrid_agent_from_env()

# Query with chaining and memory
result = await agent.query("Show me tests with LOINC 2947-0")

# Access memory
memory_summary = agent.get_memory_summary()
recent = agent.get_recent_interactions(n=5)

# Clear memory
agent.clear_memory()

# Export memory
agent.export_memory('session_memory.json')
```

## 🎨 Example Use Cases

### 1. Multi-Turn Medical Queries
```
User: "Show me all sodium tests"
Agent: [Lists 11 sodium tests with LOINC 2947-0]

User: "What problems do they indicate?"
Agent: [Uses context to know "they" = those 11 tests]
       "Those sodium tests indicate Hyponatremia and Hypernatremia..."

User: "Give me the SNOMED codes"
Agent: [Uses context to know "the problems" from previous answer]
       "Hyponatremia: SNOMED 89627008, Hypernatremia: SNOMED 39355002"
```

### 2. Response Verification
```
SQL Agent: "Found 287 rows in database"

General Agent Review:
- Checks if 287 rows answers the question
- Adds context: "This represents 35 unique medical codes..."
- Highlights key findings
- Formats for readability
```

### 3. Error Correction
```
SQL Agent: Returns confusing technical response

General Agent:
- Detects unclear response
- Rephrases in clearer language
- Adds medical terminology explanations
- Organizes data into readable sections
```

## 📊 Performance Monitoring

### Response Metadata
Each response includes:
```json
{
  "agent_chain": "SQL → General Agent → Memory",
  "memory_size": 12,
  "timestamp": "2025-11-22T11:42:30",
  "sql": "SELECT ...",
  "row_count": 11
}
```

### Memory Export Format
```json
{
  "total_interactions": 12,
  "interactions": [
    {
      "timestamp": "2025-11-22T11:42:30",
      "question": "...",
      "sql_query": "...",
      "row_count": 11,
      "final_response": "..."
    }
  ]
}
```

## 🚀 Running the System

### Start the Server
```bash
python app.py
```

**Console Output**:
```
============================================================
Medical Ontology Query System
Powered by Hybrid Agent Architecture + POML
============================================================
SQL Server: nyp-sql-1762356746.database.windows.net
SQL Database: MedData
Authentication: Azure AD
Knowledge Base: Medical Ontology (Slot-Based Structure)
Azure OpenAI Deployment: gpt-4o
Prompt Framework: POML (Prompt Optimization Markup Language)
Agent Architecture: SQL Agent → General Agent → Memory
============================================================

✓ Hybrid Agent initialized with SQL→General chaining + Memory

 * Running on http://localhost:5002
```

### Access the Application
- **Web Interface**: http://localhost:5002
- **API**: http://localhost:5002/api/*

## 🔍 Debugging

### View Memory During Session
```python
# In Python console or script
import requests

# Get current memory state
response = requests.get('http://localhost:5002/api/memory')
memory = response.json()

print(f"Total interactions: {memory['memory']['total_interactions']}")
for interaction in memory['memory']['interactions']:
    print(f"\nQ: {interaction['question']}")
    print(f"SQL: {interaction['sql_query'][:100]}...")
    print(f"Rows: {interaction['row_count']}")
```

### Export Memory for Analysis
```python
import requests

response = requests.post('http://localhost:5002/api/memory/export')
result = response.json()
print(f"Memory saved to: {result['filename']}")

# Now analyze the JSON file
import json
with open(result['filename']) as f:
    memory_data = json.load(f)
    # Analyze interactions...
```

## 📝 Summary

The new **Hybrid Agent Architecture** provides:

✅ **SQL Query Execution** with POML-enhanced prompts  
✅ **Response Verification** through General Agent  
✅ **Conversation Memory** for context-aware interactions  
✅ **Follow-up Question Support** using stored context  
✅ **Response Quality Assurance** with dual-agent review  
✅ **Memory Export** for debugging and analysis  
✅ **Session Management** with independent user memories  

This architecture ensures accurate, contextual, and high-quality responses to medical ontology queries while maintaining conversation continuity across multiple interactions.
