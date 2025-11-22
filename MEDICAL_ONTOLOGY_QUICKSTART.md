# Medical Ontology Query System - Quick Start Guide

## 🚀 System Overview

This is a **Medical Ontology Query System** powered by:
- **Microsoft Agent Framework** for intelligent query processing
- **POML (Prompt Optimization Markup Language)** for advanced prompt engineering
- **Azure SQL Database** (MedData) with slot-based medical ontology
- **Azure OpenAI GPT-4o** for natural language to SQL translation

## 📊 Database Structure

### Slot-Based Medical Ontology

The system uses a **slot-based architecture** where medical concepts are represented as CODE + SLOT_NUMBER + SLOT_VALUE triplets:

**Example**: Sodium Blood Test (Code 1302)
```
CODE    SLOT_NUMBER  SLOT_VALUE
1302    6            "Stat Whole Blood Sodium Ion Measurement"  (PRINT-NAME)
1302    212          "2947-0"                                    (LOINC-CODE)
1302    266          "43194008"                                  (SNOMED-CODE)
1302    150          "19928"                                     (INDICATES: Hyponatremia)
```

### Database Tables

**MED Table** (287 rows, 35 unique codes)
- `CODE` (NVARCHAR 50): Medical concept identifier
- `SLOT_NUMBER` (INT): Attribute type reference
- `SLOT_VALUE` (NVARCHAR 200): Attribute value

**MED_SLOTS Table** (13 slot definitions)
- `SLOT_NUMBER` (INT): Slot identifier
- `SLOT_NAME` (NVARCHAR 100): Slot semantic meaning

## 🎯 Key Features

### 1. **POML-Enhanced Prompting**
The system uses structured XML-like prompts that define:
- Medical ontology context and structure
- Query pattern recognition
- SQL generation strategies
- Response formatting rules

### 2. **Intelligent Query Processing**
- Natural language → SQL translation
- Automatic JOIN generation for slot lookups
- Fuzzy text matching for concept searches
- Standard code prioritization (LOINC, SNOMED)

### 3. **Medical Domain Expertise**
- Recognizes medical terminologies
- Understands hierarchical relationships
- Interprets clinical indications
- Provides accessible explanations

## 🔧 Running the System

### Start the Server
```bash
python app.py
```

### Access Points
- **Web Interface**: http://localhost:5002
- **API Endpoint**: http://localhost:5002/api/query

### Stop the Server
Press `CTRL+C` in the terminal

## 💬 Example Queries

### 1. Find Tests by LOINC Code
**Query**: "Show me all tests with LOINC code 2947-0"

**What happens**:
- POML identifies LOINC as slot 212
- Joins MED + MED_SLOTS for readable output
- Includes PRINT-NAME and other attributes

### 2. Search by Test Name
**Query**: "Find sodium tests"

**What happens**:
- Searches PRINT-NAME field (slot 6)
- Uses LIKE '%sodium%' for fuzzy matching
- Returns all matching medical concepts

### 3. Find Clinical Relationships
**Query**: "What problems does code 1302 indicate?"

**What happens**:
- Recognizes diagnostic relationship (slot 150)
- Retrieves linked problem codes
- Explains clinical significance

### 4. Hierarchical Queries
**Query**: "What are the descendants of code 19928?"

**What happens**:
- Uses DESCENDANT-OF slot (slot 3)
- Constructs hierarchy traversal
- Shows parent-child relationships

### 5. Multi-Code Lookup
**Query**: "Show me codes with SNOMED 43194008"

**What happens**:
- Searches SNOMED-CODE slot (slot 266)
- Returns all attributes for matching codes
- Displays complete concept profile

## 📋 Slot Reference Guide

| Slot | Name | Type | Purpose |
|------|------|------|---------|
| 3 | DESCENDANT-OF | SEMANTIC | Hierarchical parent-child |
| 4 | SUBCLASS-OF | SEMANTIC | Classification hierarchy |
| 6 | PRINT-NAME | STRING | Human-readable name |
| 9 | CPMC-LAB-PROC-CODE | STRING | Institutional procedure code |
| 15 | MEASURED-BY-PROCEDURE | SEMANTIC | Test-procedure link |
| 16 | ENTITY-MEASURED | SEMANTIC | What test measures |
| 20 | CPMC-LAB-TEST-CODE | STRING | Institutional test code |
| 149 | PT-PROBLEM-(INDICATED-BY)->PROCEDURE | SEMANTIC | Problem → Procedure |
| 150 | PROCEDURE-(INDICATES)->PT-PROBLEM | SEMANTIC | Procedure → Problem |
| 212 | LOINC-CODE | STRING | Standard LOINC identifier |
| 264 | MILLENNIUM-LAB-CODE | STRING | Millennium system code |
| 266 | SNOMED-CODE | STRING | SNOMED CT identifier |
| 277 | EPIC-COMPONENT-ID | STRING | Epic EHR identifier |

## 🎨 POML Integration

### What is POML?
**Prompt Optimization Markup Language** - Microsoft's framework for structured, maintainable LLM prompts.

**Documentation**: https://microsoft.github.io/poml/latest/

### How It's Used
1. **System Role Definition**: "Medical Ontology Query Expert"
2. **Knowledge Base Context**: Complete schema and slot definitions
3. **Query Patterns**: Common medical search strategies
4. **Reasoning Guidelines**: SQL generation best practices
5. **Output Formatting**: Medical response structure

### Benefits
- ✅ Higher SQL accuracy
- ✅ Consistent medical terminology
- ✅ Better JOIN strategies
- ✅ Clear, informative responses
- ✅ Easy maintenance and updates

## 🔐 Authentication

The system uses **Azure AD (Windows Authentication)**:
- No username/password required
- Requires `az login` before running
- Token automatically refreshed
- Secure, enterprise-grade authentication

## 📖 Documentation

- **POML Integration**: See `POML_INTEGRATION.md`
- **Database Details**: Query `SELECT * FROM MED_SLOTS` for current slots
- **API Reference**: See `app.py` for endpoint documentation

## 🧪 Testing

### Test Database Connection
```python
from meddata_sql_agent import create_meddata_agent_from_env

agent = create_meddata_agent_from_env()
result = agent.query("Show me the first 5 codes")
print(result['sql'])
print(result['response'])
```

### Test POML Prompts
```python
agent = create_meddata_agent_from_env()
# POML is enabled by default

# Disable POML for comparison
agent_no_poml = MedDataSQLAgent(..., use_poml=False)
```

## 🎓 Tips for Best Results

1. **Be Specific**: Mention LOINC, SNOMED, or slot names when known
2. **Use Medical Terms**: "sodium test" works better than "test for salt"
3. **Ask for Relationships**: "What does code X indicate?" leverages semantic slots
4. **Request Hierarchies**: "Show descendants" or "What are the parent codes"
5. **Combine Criteria**: "Find sodium tests with LOINC 2947-0"

## 🆘 Troubleshooting

### Connection Issues
- Ensure `az login` is completed
- Check SQL Server firewall allows your IP
- Verify `.env` has correct MEDDATA_SQL_SERVER

### Query Not Working
- Check SQL in response for syntax errors
- Verify slot numbers exist in MED_SLOTS
- Try simpler query first

### POML Not Helping
- Review `meddata_sql_agent.py` system prompt
- Update knowledge base section if schema changed
- Add new query patterns to POML prompt

## 🚀 Next Steps

1. **Explore the UI**: Open http://localhost:5002
2. **Try Example Queries**: Use the samples above
3. **Read POML Guide**: See `POML_INTEGRATION.md`
4. **Query the Slots**: `SELECT * FROM MED_SLOTS` to see all definitions
5. **Customize POML**: Edit system prompt for your use case

## 📞 Support

For technical issues:
- Check application logs in terminal
- Review `.env` configuration
- Consult `POML_INTEGRATION.md` for prompt details
- Verify Azure AD authentication with `az account show`

---

**Current Status**: ✅ Running on http://localhost:5002
**Database**: MedData (287 entries, 35 unique codes, 13 slots)
**AI Model**: GPT-4o with POML-enhanced prompts
**Authentication**: Azure AD (Windows Auth)
