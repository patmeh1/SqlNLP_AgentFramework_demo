# MedData Agent Integration Guide

## Overview

The **MedData Agent** is a specialized agent for querying the MedData Azure SQL Database, which contains medical slot definitions and code information. It has been integrated into the multi-agent orchestrator alongside the existing SQL Agent (for Northwind business data) and General Agent.

## Architecture

The system now supports **three specialized agents**:

1. **SQL Agent** - Queries Northwind database (products, orders, customers, etc.)
2. **MedData Agent** - Queries MedData database (medical codes, slots, LOINC, SNOMED, etc.)
3. **General Agent** - Handles general knowledge questions and web searches

The orchestrator intelligently routes queries to the appropriate agent based on keywords and context.

## Files Added

### Core Agent Files
- **`agents/meddata_agent_wrapper.py`** - MedData agent wrapper following the same pattern as SQLAgentWrapper
- **`agents/create_meddata_agent.py`** - Helper functions to create MedData agent from environment variables

### Configuration Files
- **`.env.meddata.example`** - Example environment variable configuration for MedData

### Database Setup Files (in `scripts/` and `database/`)
- `scripts/setup_meddata_database.py` - Automated Azure SQL Database setup
- `scripts/setup_meddata.ps1` - PowerShell automation script
- `scripts/test_meddata.py` - Database verification script
- `database/meddata.sql` - SQL script for manual setup
- `scripts/MEDDATA_README.md` - Comprehensive setup documentation
- `scripts/MEDDATA_QUICK_REFERENCE.md` - Quick command reference

## How It Works

### 1. Routing Logic

The orchestrator routes queries based on keywords:

**MedData Agent** is triggered by:
- Medical terms: `medical`, `slot`, `loinc`, `snomed`, `test`, `procedure`, `lab`
- Specific terms: `sodium`, `measurement`, `cpmc`, `millennium`, `epic`
- Medical codes and terminology

**SQL Agent** is triggered by:
- Business terms: `product`, `order`, `customer`, `employee`, `supplier`
- Data operations: `show`, `list`, `get`, `count`, `top`
- Northwind-specific tables

**General Agent** handles:
- Conceptual questions
- Definitions and explanations
- Web searches

### 2. Follow-up Context

The orchestrator maintains context, so follow-up questions automatically route to the same agent:

```
User: "show me sodium tests"
→ Routes to MedData Agent

User: "how many are there?"
→ Continues with MedData Agent (context-aware)
```

### 3. Error Recovery

If a database agent fails, the query is automatically passed to the General Agent for a helpful explanation.

## Setup Instructions

### Step 1: Create MedData Database

Choose one of the following methods:

#### Option A: Automated PowerShell Script (Recommended)
```powershell
cd scripts
.\setup_meddata.ps1
```

#### Option B: Python Script
```powershell
# Set environment variables
$env:AZURE_SUBSCRIPTION_ID = "your-subscription-id"
$env:RESOURCE_GROUP = "meddata-rg"
$env:SQL_SERVER_NAME = "meddata-sql-server"
$env:SQL_ADMIN_PASSWORD = "YourSecurePassword123!"

# Run setup
pip install -r scripts/meddata_requirements.txt
python scripts/setup_meddata_database.py
```

#### Option C: Manual SQL Script
1. Create Azure SQL Database named "MedData" in Azure Portal
2. Connect with Azure Data Studio or SSMS
3. Run `database/meddata.sql`

### Step 2: Configure Environment Variables

Add MedData configuration to your `.env` file:

#### Using Azure AD Authentication (Recommended)
```env
MEDDATA_SQL_SERVER=meddata-sql-server.database.windows.net
MEDDATA_SQL_DATABASE=MedData
MEDDATA_USE_AZURE_AD=true
```

#### Using SQL Authentication
```env
MEDDATA_SQL_SERVER=meddata-sql-server.database.windows.net
MEDDATA_SQL_DATABASE=MedData
MEDDATA_USE_AZURE_AD=false
MEDDATA_SQL_USERNAME=sqladmin
MEDDATA_SQL_PASSWORD=YourSecurePassword123!
```

**Note:** The existing `AZURE_OPENAI_*` variables are shared across all agents.

### Step 3: Test MedData Agent

#### Test Database Connection
```powershell
$env:SQL_SERVER_NAME = "meddata-sql-server"
$env:SQL_ADMIN_PASSWORD = "your-password"
python scripts/test_meddata.py
```

#### Test in Application
```powershell
python app.py
```

Then try these queries in the chat interface:
- "Show me all medical slots"
- "What LOINC codes are available?"
- "Find sodium test procedures"
- "List medical codes with SNOMED codes"

## Example Queries

### MedData Queries (Routes to MedData Agent)
```
✓ "Show me all medical slots"
✓ "What is the LOINC code for sodium?"
✓ "List all sodium test procedures"
✓ "Find medical codes with SNOMED codes"
✓ "Show me EPIC component IDs"
✓ "What are the CPMC lab tests?"
✓ "Display medical code 1302"
```

### Business Queries (Routes to SQL Agent)
```
✓ "Show me all products"
✓ "List customers in London"
✓ "What are the top 5 selling products?"
✓ "How many orders do we have?"
```

### General Queries (Routes to General Agent)
```
✓ "What is LOINC?" (explanation, not data)
✓ "Explain SQL databases"
✓ "What are best practices for medical coding?"
```

## Database Schema

### MED_SLOTS Table
Contains slot definitions for medical coding:
- `SLOT_NUMBER` (Primary Key): Unique identifier
- `SLOT_NAME`: Name of the slot (e.g., "LOINC-CODE", "SNOMED-CODE")
- `SLOT_TYPE`: Type (SEMANTIC or STRING)

**13 slot definitions** including:
- Slot 212: LOINC-CODE
- Slot 266: SNOMED-CODE
- Slot 277: EPIC-COMPONENT-ID
- Slot 6: PRINT-NAME (human-readable names)

### MED Table
Contains medical code-slot-value relationships:
- `ID` (Auto-increment Primary Key)
- `CODE`: Medical code identifier
- `SLOT_NUMBER`: Foreign key to MED_SLOTS
- `SLOT_VALUE`: Value for the slot

**155 medical records** with indexes on CODE and SLOT_NUMBER for performance.

## Optional Configuration

The MedData agent is **completely optional**. If not configured, the system works normally with just the SQL and General agents:

- ✅ Application runs without MedData configuration
- ✅ Medical queries route to General Agent for explanations
- ✅ No errors if MedData is not set up

To enable MedData, simply configure the environment variables and restart the application.

## Verification

Check if MedData is active when the application starts:

```
✓ MedData Agent initialized
  Server: meddata-sql-server.database.windows.net
  Database: MedData
  Auth: Azure AD
✓ MedData Agent available - medical queries enabled
```

If not configured, you'll see:
```
ℹ️  MedData not configured - set MEDDATA_SQL_SERVER to enable medical queries
```

## Troubleshooting

### Issue: "MedData Agent initialization failed"
**Solution:** Check your environment variables and database connection:
```powershell
# Test connection
az sql db show --name MedData --resource-group meddata-rg --server meddata-sql-server
```

### Issue: "Cannot connect to MedData database"
**Solutions:**
1. Verify firewall rules allow your IP
2. Check Azure AD login: `az login`
3. Verify credentials if using SQL auth

### Issue: Queries not routing to MedData Agent
**Solution:** Use medical keywords in your query:
- ✅ "Show me medical slots" (routes to MedData)
- ❌ "Show me slots" (might route to SQL Agent)

## Advanced Usage

### Force Agent Selection

You can force a specific agent via the API:

```javascript
fetch('/api/query', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        question: "show all records",
        agent: "meddata"  // Force MedData agent
    })
})
```

### Agent Types
- `agent: "sql"` - Force SQL Agent (Northwind)
- `agent: "meddata"` - Force MedData Agent
- `agent: "general"` - Force General Agent
- No agent specified - Automatic routing

## Architecture Benefits

✅ **Modular Design** - Each agent is independent and can be enabled/disabled  
✅ **Intelligent Routing** - Automatic agent selection based on query content  
✅ **Context Awareness** - Follow-up questions maintain agent context  
✅ **Error Recovery** - Graceful fallback to General Agent on errors  
✅ **Optional Components** - MedData agent only loads if configured  
✅ **Scalable** - Easy to add more specialized agents in the future  

## Next Steps

1. ✅ Set up MedData database (see `scripts/MEDDATA_README.md`)
2. ✅ Configure environment variables
3. ✅ Test the agent with medical queries
4. 📊 Explore the database schema
5. 🔍 Try various medical and business queries
6. 🎨 Customize routing keywords if needed

## Support

For detailed database setup instructions, see:
- `scripts/MEDDATA_README.md` - Comprehensive setup guide
- `scripts/MEDDATA_QUICK_REFERENCE.md` - Quick commands
- `MEDDATA_SETUP_SUMMARY.md` - Overview and file descriptions

For application issues, check the main `README.md` and project documentation.

---

**Ready to query medical data!** 🏥
