# Hybrid Agent - How to Use

## Overview

The hybrid agent system has been **FIXED** to properly chain SQL query results through the General Agent for analysis.

**Flow**: SQL Execution → Data Results → General Agent Analysis → Memory Storage

---

## What Was Fixed

**Before**: General Agent received SQL statements
**After**: General Agent receives ACTUAL DATA ROWS from executed queries

---

## Using the System

### 1. Flask Web Interface

Start the application:
```bash
python app.py
```

Access at: http://localhost:5002

The web interface allows you to:
- Ask medical ontology questions
- View SQL queries generated
- See data results
- Read General Agent analysis
- Track conversation memory

### 2. Python API

```python
import asyncio
from hybrid_agent_with_memory import create_hybrid_agent_from_env

async def main():
    # Create agent
    agent = await create_hybrid_agent_from_env()
    
    # Ask a question
    result = await agent.query("Find all tests with LOINC code 2947-0")
    
    # Result contains:
    # - question: Your question
    # - sql_query: Generated SQL
    # - row_count: Number of rows returned
    # - results: Actual data rows
    # - final_response: General Agent analysis
    # - memory_size: Total interactions stored

asyncio.run(main())
```

### 3. Example Query

**Question**: "Find all tests with LOINC code 2947-0"

**What Happens**:
1. SQL Agent generates: `SELECT ... FROM MED WHERE LOINC_CODE = '2947-0'`
2. Query executes on database: Returns 11 rows
3. Data formatted as table:
   ```
   CODE  | Test Name
   ------+------------------------------------
   111465| BKR (CM) Result: Sodium Whole Blood POC
   112423| BKR (CM) Result: Sodium WB
   ... (9 more)
   ```
4. General Agent analyzes this data table
5. Provides response based on actual data

**Response from General Agent**:
"I found 11 tests with LOINC code 2947-0. All are sodium measurement tests performed on whole blood samples. They include:
- Point-of-care (POC) tests using BKR equipment
- EPOC analyzer tests
- Stat (urgent) tests
- CPMC Laboratory tests
The variety of test names reflects different hospital systems and equipment..."

---

## Memory Management

### View Memory
```python
# Get summary
summary = agent.get_memory_summary()
print(f"Total interactions: {summary['total_interactions']}")

# Get recent interactions
recent = agent.get_recent_interactions(n=5)
```

### Export Memory
```python
# Export to JSON
agent.export_memory('my_memory.json')
```

### Clear Memory
```python
agent.clear_memory()
```

---

## Medical Ontology Data

The system queries the **MedData** database:

**Tables**:
- `MED`: 287 rows with medical concept definitions
  - CODE: Medical concept code
  - SLOT_NUMBER: Semantic relationship identifier
  - SLOT_VALUE: Relationship value

- `MED_SLOTS`: 13 semantic relationship definitions
  - LOINC-CODE: Lab test codes
  - SNOMED-CODE: Medical coding
  - PRINT-NAME: Display names
  - PT-PROBLEM indicators: Clinical relationships
  - And more...

---

## Key Medical Queries

### Find Tests by LOINC Code
```
"Find all tests with LOINC code 2947-0"
```

### Find Related Problems
```
"What patient problems do those tests indicate?"
```

### Get SNOMED Codes
```
"Show me the SNOMED codes for those problems"
```

### Multi-Step Reasoning
```
"Which sodium tests are indicated by hypernatremia?"
```

---

## Architecture

```
User Question
    ↓
SQL Agent (POML-Enhanced)
- Understands medical ontology
- Generates contextual SQL
- Executes queries
    ↓
Data Results
- Actual database rows
- Formatted as tables
    ↓
General Agent (GPT-4o)
- Analyzes data
- Provides medical insights
- Answers questions
    ↓
Memory Storage
- Complete interaction history
- Context for follow-ups
    ↓
Final Response
```

---

## Configuration

### Environment Variables (.env)

```env
# SQL Server
MEDDATA_SQL_SERVER=nyp-sql-1762356746.database.windows.net
MEDDATA_SQL_DATABASE=MedData
MEDDATA_USE_AZURE_AD=true

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://...
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_DEPLOYMENT=gpt-4o
```

---

## Troubleshooting

### Issue: "SQL Agent failed"
- Check database connection
- Verify Azure AD authentication
- Check SQL Server firewall rules

### Issue: "General Agent returned no response"
- Check Azure OpenAI credentials
- Verify API key is valid
- Check deployment name

### Issue: "Memory not persisting"
- Call `export_memory()` to save to file
- Check file permissions

---

## Files

- `app.py` - Flask web application
- `hybrid_agent_with_memory.py` - Main hybrid agent class
- `meddata_sql_agent.py` - SQL generation and execution
- `agents/general_agent.py` - General reasoning agent
- `HYBRID_AGENT_FIX_SUMMARY.md` - Technical fix details

---

## Performance

- SQL execution: ~1-2 seconds
- Data formatting: <1 second
- General Agent analysis: ~5-10 seconds (API calls)
- Total request: ~10-15 seconds

---

## Advanced Usage

### Custom SQL Queries
```python
# Use SQL agent directly
sql_result = agent.sql_agent.query("Your question")

# results contains:
# - sql: The SQL statement
# - results: Data rows
# - row_count: Number of rows
# - response: SQL Agent's text response
```

### Prompt Customization
```python
# Modify the verification prompt for different behaviors
# See _build_verification_prompt() in hybrid_agent_with_memory.py
```

### Multi-Turn Conversations
```python
# Queries automatically use recent context
result1 = await agent.query("Query 1")
result2 = await agent.query("Follow-up question")
# Query 2 gets context from Query 1
```

---

## Notes

- All data is from the MedData database (medical ontology)
- Sodium-focused test data (287 rows total)
- System uses Azure AD for database authentication
- General Agent uses GPT-4o for analysis
- POML framework optimizes medical prompts

---

**Status**: Production Ready
**Last Tested**: 2025-11-22 12:01 UTC
**Coverage**: SQL → Execute → Data → General Agent → Memory

