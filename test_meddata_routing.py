"""
Test script to verify that questions starting with "Meddata" route to MedData agent
"""

import asyncio
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.orchestrator import create_orchestrator_from_env


async def test_meddata_routing():
    """Test that questions starting with 'Meddata' route to MedData agent"""
    
    print("\n" + "="*70)
    print("  TESTING MEDDATA EXPLICIT ROUTING")
    print("="*70)
    
    # Create orchestrator
    print("\n📦 Creating orchestrator...")
    orchestrator = await create_orchestrator_from_env()
    
    if not orchestrator.meddata_available:
        print("⚠️  WARNING: MedData agent not configured!")
        print("   Add these to your .env file:")
        print("   MEDDATA_SQL_SERVER=nyp-sql-1762356746.database.windows.net")
        print("   MEDDATA_SQL_DATABASE=MedData")
        print("   MEDDATA_USE_AZURE_AD=true")
        print("\n   Skipping tests...")
        return
    
    print("✅ Orchestrator created with MedData agent available")
    
    # Test cases
    test_queries = [
        ("Meddata show me all slots", "Should route to MedData (explicit prefix)"),
        ("MEDDATA what codes are available?", "Should route to MedData (case insensitive)"),
        ("meddata how many medical codes?", "Should route to MedData (lowercase prefix)"),
        ("Show me all sodium tests", "Should route to MedData (keyword match)"),
        ("Show me all customers", "Should route to SQL (Northwind data)"),
        ("What is machine learning?", "Should route to General (conceptual)"),
    ]
    
    print("\n" + "="*70)
    print("  ROUTING TESTS")
    print("="*70)
    
    for i, (query, expected) in enumerate(test_queries, 1):
        print(f"\n--- Test {i} ---")
        print(f"Query: \"{query}\"")
        print(f"Expected: {expected}")
        
        # Get routing decision (without executing query)
        from agent_framework.chat_protocol import ChatMessage, Role
        agent_type = await orchestrator._route_query(query, [])
        
        print(f"Result: Routed to {agent_type.value} agent")
        
        # Verify expectation
        if "MedData" in expected and agent_type.value == "meddata":
            print("✅ PASS - Correctly routed to MedData")
        elif "SQL" in expected and agent_type.value == "sql":
            print("✅ PASS - Correctly routed to SQL")
        elif "General" in expected and agent_type.value == "general":
            print("✅ PASS - Correctly routed to General")
        else:
            print(f"⚠️  UNEXPECTED - Expected different routing")
    
    print("\n" + "="*70)
    print("  FULL QUERY TEST")
    print("="*70)
    
    # Test a full query with "Meddata" prefix
    test_query = "Meddata show me all slot types"
    print(f"\nExecuting query: \"{test_query}\"")
    
    result = await orchestrator.query(test_query)
    
    print(f"\nAgent Used: {result.get('agent_used')}")
    print(f"Success: {result.get('success')}")
    
    if result.get('success'):
        print(f"Response preview: {result.get('response', '')[:200]}...")
    else:
        print(f"Error: {result.get('error', 'Unknown error')}")
    
    if 'MedData' in result.get('agent_used', ''):
        print("\n✅ SUCCESS - Query with 'Meddata' prefix was routed to MedData agent!")
    else:
        print(f"\n❌ FAILED - Expected MedData agent but got: {result.get('agent_used')}")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    asyncio.run(test_meddata_routing())
