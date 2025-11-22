# Testing the MedData Agent Fix

## Overview
This document provides step-by-step instructions to test that the authentication error fix is working correctly.

## Test 1: Without MedData Configuration (Most Important)

### Purpose
Verify that the app works correctly when MedData is NOT configured, and medical queries are gracefully handled.

### Steps
1. **Remove MedData configuration** from your `.env` file:
   ```bash
   # Comment out or remove these lines:
   # MEDDATA_SQL_SERVER=...
   # MEDDATA_SQL_DATABASE=...
   # MEDDATA_SQL_USERNAME=...
   # MEDDATA_SQL_PASSWORD=...
   ```

2. **Start the application:**
   ```bash
   python app.py
   ```

3. **Check startup logs** - Should see:
   ```
   ℹ️  MedData Agent not configured - will route medical queries to General Agent
   ```

4. **Test medical queries** in the web interface (http://localhost:5000):
   - Query: `"show me sodium tests"`
   - Expected: Routes to General Agent
   - Expected Response: "I don't have access to medical databases..." (or similar)
   - **Should NOT see**: `Login failed for user ''. (18456)`

5. **Test regular queries** - Should work normally:
   - Query: `"show me all customers"`
   - Expected: Routes to SQL Agent (Northwind)
   - Expected Response: List of customers

### ✅ Success Criteria
- ✅ No authentication errors
- ✅ Medical keywords detected but routed to General Agent
- ✅ General Agent provides helpful response
- ✅ Regular SQL queries still work

## Test 2: With MedData Configuration

### Purpose
Verify that MedData agent works when properly configured.

### Prerequisites
- Azure SQL Database "MedData" created and populated
- Connection details available

### Steps
1. **Add MedData configuration** to `.env`:
   ```bash
   MEDDATA_SQL_SERVER=your-server.database.windows.net
   MEDDATA_SQL_DATABASE=MedData
   MEDDATA_USE_AZURE_AD=true
   # OR if using SQL authentication:
   # MEDDATA_SQL_USERNAME=your-username
   # MEDDATA_SQL_PASSWORD=your-password
   ```

2. **Start the application:**
   ```bash
   python app.py
   ```

3. **Check startup logs** - Should see:
   ```
   ✅ MedData Agent initialized successfully
   ```

4. **Test medical queries:**
   - Query: `"show me sodium tests"`
   - Expected: Routes to MedData Agent
   - Expected Response: List of tests with SLOT_NUMBER=11
   
   - Query: `"what are all the available slot types?"`
   - Expected: Routes to MedData Agent
   - Expected Response: 13 slot types from MED_SLOTS table

5. **Test regular queries** - Should still work:
   - Query: `"show me all customers"`
   - Expected: Routes to SQL Agent (Northwind)
   - Expected Response: List of customers

### ✅ Success Criteria
- ✅ MedData agent initializes successfully
- ✅ Medical queries route to MedData agent
- ✅ Medical queries return correct results
- ✅ Regular SQL queries still work

## Test 3: Forced Routing (Advanced)

### Purpose
Verify that forced routing handles unavailable MedData gracefully.

### Steps (Without MedData Configured)
1. **Try to force MedData routing** (requires modifying test code or using API):
   ```python
   # In test script or API call
   result = await orchestrator.query_with_agent_choice(
       "test query",
       "meddata"
   )
   ```

2. **Expected Result:**
   ```json
   {
       "response": "⚠️ MedData Agent is not configured...",
       "agent_used": "None (MedData not available)",
       "agent_type": "error",
       "success": false
   }
   ```

### ✅ Success Criteria
- ✅ Clear error message explaining MedData not configured
- ✅ No database connection attempt
- ✅ No authentication error

## Test 4: Agent List API

### Purpose
Verify that available agents list is dynamic.

### Steps
1. **Without MedData configured:**
   ```bash
   curl http://localhost:5000/api/agents
   ```
   
   Expected Response:
   ```json
   {
       "sql": "SQL Agent for Northwind...",
       "general": "General Agent..."
       // No 'meddata' key
   }
   ```

2. **With MedData configured:**
   ```bash
   curl http://localhost:5000/api/agents
   ```
   
   Expected Response:
   ```json
   {
       "sql": "SQL Agent for Northwind...",
       "meddata": "MedData Agent...",
       "general": "General Agent..."
   }
   ```

### ✅ Success Criteria
- ✅ Agent list reflects actual availability
- ✅ MedData only appears when configured

## Common Issues

### Issue: Still getting authentication error
**Solution:** Make sure you pulled latest code changes to `orchestrator.py` and `app.py`

### Issue: MedData not initializing even with configuration
**Solution:** 
1. Check all required environment variables are set
2. Check Azure SQL firewall allows your IP
3. Check Azure AD authentication if using `MEDDATA_USE_AZURE_AD=true`

### Issue: All queries going to General Agent
**Solution:** Check that medical keywords are in your query (sodium, loinc, snomed, slot, etc.)

## Quick Verification Script

```python
# test_meddata_fix.py
import asyncio
from agents.create_meddata_agent import is_meddata_configured
from agents.orchestrator import create_orchestrator_from_env

async def test_fix():
    print("=" * 60)
    print("Testing MedData Agent Fix")
    print("=" * 60)
    
    # Check configuration
    if is_meddata_configured():
        print("✅ MedData is configured")
    else:
        print("ℹ️  MedData is NOT configured (this is OK)")
    
    # Create orchestrator
    orchestrator = await create_orchestrator_from_env()
    
    # Test query
    print("\nTesting query: 'show me sodium tests'")
    result = await orchestrator.query("show me sodium tests")
    
    print(f"\nAgent Used: {result.get('agent_used')}")
    print(f"Success: {result.get('success')}")
    if result.get('error'):
        print(f"❌ ERROR: {result.get('error')}")
    else:
        print("✅ No errors!")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    asyncio.run(test_fix())
```

Run with:
```bash
python test_meddata_fix.py
```

## Expected Output

### Without MedData:
```
============================================================
Testing MedData Agent Fix
============================================================
ℹ️  MedData is NOT configured (this is OK)
ℹ️  MedData Agent not configured - will route medical queries to General Agent

Testing query: 'show me sodium tests'

Agent Used: General Agent (MedData not configured)
Success: True
✅ No errors!
============================================================
```

### With MedData:
```
============================================================
Testing MedData Agent Fix
============================================================
✅ MedData is configured
✅ MedData Agent initialized successfully

Testing query: 'show me sodium tests'

Agent Used: MedData Agent
Success: True
✅ No errors!
============================================================
```
