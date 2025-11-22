# MedData Agent Authentication Error Fix

## Problem Summary
When the MedData agent was not configured (missing `MEDDATA_SQL_SERVER` environment variable), the orchestrator would create a dummy SQLAgent with placeholder credentials, causing this error:
```
Login failed for user ''. (18456)
```

## Root Cause
The `create_orchestrator_from_env()` function was creating a dummy SQLAgent instance when `meddata_agent` was `None`:
```python
# OLD CODE (PROBLEMATIC)
if meddata_agent is None:
    meddata_agent = SQLAgent(
        connection_string="",  # Empty connection string!
        database_name="MedData",
        # ... other parameters
    )
```

This dummy agent would attempt to connect to a database with empty credentials when any medical-related query was processed.

## Solution Implemented

### 1. Removed Dummy Agent Creation
Changed `create_orchestrator_from_env()` to pass `None` when MedData is not configured:
```python
# NEW CODE
if meddata_agent is None:
    meddata_agent_available = False
    print("ℹ️  MedData Agent not configured - will route medical queries to General Agent")
else:
    meddata_agent_available = True
```

### 2. Added Availability Flag
Added `meddata_available` flag to orchestrator's `__init__`:
```python
def __init__(self, sql_agent, general_agent, meddata_agent=None, ...):
    self.sql_agent = sql_agent
    self.general_agent = general_agent
    self.meddata_agent = meddata_agent
    self.meddata_available = meddata_agent is not None  # NEW FLAG
```

### 3. Updated Routing Logic
Modified `_route_query()` to check availability before routing to MedData:
```python
if agent_choice == "meddata":
    if not self.meddata_available:
        print(f"🎯 Router Decision: meddata requested but not available - routing to General Agent")
        return AgentType.GENERAL
    return AgentType.MEDDATA
```

### 4. Updated Query Processing
Modified `query()` method to handle unavailable MedData agent:
```python
if agent_type == AgentType.MEDDATA:
    if not self.meddata_available:
        # Fallback to General Agent if MedData not configured
        print(f"⚠️  MedData Agent not available, routing to General Agent")
        result = await self.general_agent.process_query(user_question)
        result['agent_used'] = 'General Agent (MedData not configured)'
    else:
        # Process with MedData agent
        result = await self.meddata_agent.process_query(user_question)
```

### 5. Updated System Prompt
Modified routing system prompt to conditionally include MedData:
```python
agent_list = "1. SQL Agent (Northwind data)"
if self.meddata_available:
    agent_list += "\n2. MedData Agent (Medical terminology, LOINC/SNOMED codes)"
    meddata_schema = self.meddata_agent.schema_description
else:
    meddata_schema = ""
agent_list += "\n3. General Agent (Other questions)"
```

### 6. Updated Helper Methods
- **`clear_history()`**: Check availability before calling `meddata_agent.clear_history()`
- **`get_available_agents()`**: Only include 'meddata' in returned dict when available
- **`query_with_agent_choice()`**: Return error message if MedData forced but not configured

## Testing Scenarios

### Scenario 1: Without MedData Configured
✅ **Expected Behavior:**
- User asks: "show me sodium tests"
- Routing detects medical keywords → routes to MedData
- MedData unavailable → falls back to General Agent
- General Agent responds: "I don't have access to medical databases..."

### Scenario 2: With MedData Configured
✅ **Expected Behavior:**
- User asks: "show me sodium tests"
- Routing detects medical keywords → routes to MedData
- MedData available → executes query on MedData database
- Returns results from MED table with SLOT_NUMBER=11 (Sodium)

## Files Modified
1. `agents/orchestrator.py` - Core routing and availability logic
2. `app.py` - Optional MedData agent initialization
3. `agents/create_meddata_agent.py` - Helper function with `is_meddata_configured()`

## Verification Steps
1. **Test without MedData:**
   ```bash
   # Remove MedData configuration from .env
   # Run: python app.py
   # Ask: "show me sodium tests"
   # Should: Route to General Agent without error
   ```

2. **Test with MedData:**
   ```bash
   # Add MEDDATA_SQL_SERVER, MEDDATA_SQL_DATABASE to .env
   # Run: python app.py
   # Ask: "show me sodium tests"
   # Should: Route to MedData Agent and return results
   ```

## Key Learnings
- **Don't create placeholder objects** for optional components - use `None` instead
- **Check availability** before using optional components
- **Provide fallback behavior** when optional components are unavailable
- **Make configuration truly optional** - app should work with or without MedData

## Remaining Type Hints Issue
The lint errors for `meddata_agent: MedDataAgentWrapper = None` are cosmetic. To fix, change to:
```python
from typing import Optional
meddata_agent: Optional[MedDataAgentWrapper] = None
```
This is a nice-to-have improvement but doesn't affect functionality.
