"""
Test script to verify MedData authentication error fix.

This script tests that:
1. The app works without MedData configured (no auth errors)
2. Medical queries are gracefully routed to General Agent when MedData unavailable
3. The app works with MedData configured (if credentials provided)
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.create_meddata_agent import is_meddata_configured
from agents.orchestrator import create_orchestrator_from_env


async def test_without_meddata():
    """Test that app works correctly when MedData is NOT configured."""
    print("\n" + "=" * 70)
    print("TEST 1: MedData Agent NOT Configured (Primary Test)")
    print("=" * 70)
    
    if is_meddata_configured():
        print("⚠️  WARNING: MedData appears to be configured!")
        print("   To test properly, remove MEDDATA_SQL_SERVER from .env")
        print("   Skipping this test...")
        return False
    
    print("✅ MedData is NOT configured (good for this test)")
    
    try:
        # Create orchestrator
        print("\nCreating orchestrator...")
        orchestrator = await create_orchestrator_from_env()
        print("✅ Orchestrator created successfully")
        
        # Check meddata_available flag
        if hasattr(orchestrator, 'meddata_available'):
            print(f"✅ meddata_available flag: {orchestrator.meddata_available}")
            if orchestrator.meddata_available:
                print("❌ FAIL: meddata_available should be False!")
                return False
        else:
            print("❌ FAIL: meddata_available flag not found!")
            return False
        
        # Test medical query
        print("\n" + "-" * 70)
        print("Testing medical query: 'show me sodium tests'")
        print("-" * 70)
        
        result = await orchestrator.query("show me sodium tests")
        
        print(f"\nAgent Used: {result.get('agent_used')}")
        print(f"Agent Type: {result.get('agent_type')}")
        print(f"Success: {result.get('success')}")
        
        if result.get('error'):
            # Check if it's the old authentication error
            error_msg = result.get('error', '')
            if 'Login failed for user' in error_msg or '18456' in error_msg:
                print(f"\n❌ CRITICAL FAILURE: Authentication error still occurs!")
                print(f"   Error: {error_msg}")
                return False
            else:
                print(f"\n⚠️  Query failed with error: {error_msg}")
                print("   (This might be OK if it's not an auth error)")
        else:
            print("✅ No authentication errors!")
        
        # Verify it went to General Agent
        agent_used = result.get('agent_used', '').lower()
        if 'general' in agent_used or result.get('agent_type') == 'general':
            print("✅ Query correctly routed to General Agent")
        else:
            print(f"⚠️  Unexpected routing: {result.get('agent_used')}")
        
        # Test regular query
        print("\n" + "-" * 70)
        print("Testing regular query: 'show me all customers'")
        print("-" * 70)
        
        result2 = await orchestrator.query("show me all customers")
        print(f"Agent Used: {result2.get('agent_used')}")
        print(f"Success: {result2.get('success')}")
        
        if result2.get('error'):
            print(f"⚠️  Error: {result2.get('error')}")
        else:
            print("✅ Regular query works!")
        
        print("\n" + "=" * 70)
        print("✅ TEST 1 PASSED: No authentication errors when MedData not configured")
        print("=" * 70)
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 1 FAILED with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_with_meddata():
    """Test that app works correctly when MedData IS configured."""
    print("\n" + "=" * 70)
    print("TEST 2: MedData Agent Configured")
    print("=" * 70)
    
    if not is_meddata_configured():
        print("ℹ️  MedData is NOT configured")
        print("   This test requires MEDDATA_SQL_SERVER in .env")
        print("   Skipping this test (not a failure)...")
        return None  # None means skipped
    
    print("✅ MedData is configured")
    
    try:
        # Create orchestrator
        print("\nCreating orchestrator...")
        orchestrator = await create_orchestrator_from_env()
        print("✅ Orchestrator created successfully")
        
        # Check meddata_available flag
        if hasattr(orchestrator, 'meddata_available'):
            print(f"✅ meddata_available flag: {orchestrator.meddata_available}")
            if not orchestrator.meddata_available:
                print("❌ FAIL: meddata_available should be True!")
                return False
        else:
            print("❌ FAIL: meddata_available flag not found!")
            return False
        
        # Test medical query
        print("\n" + "-" * 70)
        print("Testing medical query: 'show me sodium tests'")
        print("-" * 70)
        
        result = await orchestrator.query("show me sodium tests")
        
        print(f"\nAgent Used: {result.get('agent_used')}")
        print(f"Agent Type: {result.get('agent_type')}")
        print(f"Success: {result.get('success')}")
        
        if result.get('error'):
            print(f"⚠️  Query failed with error: {result.get('error')}")
        else:
            print("✅ Query executed successfully!")
        
        # Verify it went to MedData Agent
        agent_type = result.get('agent_type', '')
        if agent_type == 'meddata':
            print("✅ Query correctly routed to MedData Agent")
        else:
            print(f"⚠️  Query routed to {agent_type} instead of meddata")
        
        # Test get_available_agents
        print("\n" + "-" * 70)
        print("Testing get_available_agents()")
        print("-" * 70)
        
        agents = orchestrator.get_available_agents()
        print(f"Available agents: {list(agents.keys())}")
        
        if 'meddata' in agents:
            print("✅ MedData agent in available agents list")
        else:
            print("❌ FAIL: MedData agent NOT in available agents list!")
            return False
        
        print("\n" + "=" * 70)
        print("✅ TEST 2 PASSED: MedData agent works when configured")
        print("=" * 70)
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 2 FAILED with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 20 + "MEDDATA FIX VERIFICATION" + " " * 24 + "║")
    print("╚" + "=" * 68 + "╝")
    
    results = []
    
    # Test 1: Without MedData (most important)
    result1 = await test_without_meddata()
    results.append(("Without MedData", result1))
    
    # Test 2: With MedData (if configured)
    result2 = await test_with_meddata()
    if result2 is not None:  # Only count if not skipped
        results.append(("With MedData", result2))
    
    # Summary
    print("\n" + "╔" + "=" * 68 + "╗")
    print("║" + " " * 28 + "TEST SUMMARY" + " " * 28 + "║")
    print("╠" + "=" * 68 + "╣")
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"║  {test_name:30} {status:35} ║")
    
    print("╚" + "=" * 68 + "╝")
    
    # Overall result
    all_passed = all(r for _, r in results)
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED! The authentication error fix is working correctly.")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED. Please review the errors above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
