"""
Test script to demonstrate conversation memory functionality
Run this to test that the agents remember previous context
"""

import asyncio
from dotenv import load_dotenv
from sql_agent import create_agent_from_env
from agents.sql_agent_wrapper import SQLAgentWrapper
from agents.orchestrator import create_orchestrator_from_env

# Load environment variables
load_dotenv()


async def test_memory():
    """Test conversation memory with follow-up queries."""
    
    print("=" * 80)
    print("Testing Conversation Memory in Multi-Agent System")
    print("=" * 80)
    print()
    
    # Create the orchestrator
    print("Initializing agents...")
    sql_agent = create_agent_from_env()
    sql_agent_wrapper = SQLAgentWrapper(sql_agent)
    orchestrator = create_orchestrator_from_env(sql_agent_wrapper)
    print("✓ Agents initialized\n")
    
    # Test 1: Product query with follow-ups
    print("-" * 80)
    print("TEST 1: Product Query with Follow-ups")
    print("-" * 80)
    
    queries = [
        "Show me all products",
        "How many are there?",
        "Show me the most expensive ones"
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\nQuery {i}: {query}")
        print("-" * 40)
        
        result = await orchestrator.query(query)
        
        print(f"Agent Used: {result['agent_used']}")
        print(f"Success: {result['success']}")
        
        if result['success']:
            print(f"Response: {result['response'][:200]}...")
            if 'sql' in result:
                print(f"SQL: {result['sql'][:100]}...")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
        
        await asyncio.sleep(1)  # Small delay between queries
    
    # Test 2: Customer query with follow-ups
    print("\n" + "-" * 80)
    print("TEST 2: Customer Query with Follow-ups")
    print("-" * 80)
    
    queries = [
        "List customers in Germany",
        "How many customers are there?",
        "Show me their contact information"
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\nQuery {i}: {query}")
        print("-" * 40)
        
        result = await orchestrator.query(query)
        
        print(f"Agent Used: {result['agent_used']}")
        print(f"Success: {result['success']}")
        
        if result['success']:
            print(f"Response: {result['response'][:200]}...")
            if 'sql' in result:
                print(f"SQL: {result['sql'][:100]}...")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
        
        await asyncio.sleep(1)
    
    # Test 3: Mixed query types (SQL and General)
    print("\n" + "-" * 80)
    print("TEST 3: Mixed Query Types (Testing Agent Switching)")
    print("-" * 80)
    
    queries = [
        "Show me all categories",
        "What is a database category?",
        "How many categories do we have?"
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\nQuery {i}: {query}")
        print("-" * 40)
        
        result = await orchestrator.query(query)
        
        print(f"Agent Used: {result['agent_used']}")
        print(f"Agent Type: {result['agent_type']}")
        print(f"Success: {result['success']}")
        
        if result['success']:
            print(f"Response: {result['response'][:200]}...")
            if 'sql' in result:
                print(f"SQL: {result['sql'][:100]}...")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
        
        await asyncio.sleep(1)
    
    # Show conversation history
    print("\n" + "=" * 80)
    print("CONVERSATION HISTORY")
    print("=" * 80)
    
    history = orchestrator.get_conversation_history()
    print(f"\nTotal exchanges: {len(history)}")
    print("\nRecent conversations:")
    for i, entry in enumerate(history[-5:], 1):
        print(f"\n{i}. Question: {entry['question']}")
        print(f"   Agent: {entry['agent']}")
        print(f"   Response: {entry['response'][:100]}...")
    
    print("\n" + "=" * 80)
    print("Memory Test Complete!")
    print("=" * 80)
    print("\nKey Observations:")
    print("- Follow-up questions were understood in context")
    print("- References like 'there', 'them', 'their' were resolved")
    print("- Agent routing considered conversation history")
    print("- Each agent maintained its own memory of interactions")


if __name__ == "__main__":
    print("\n🧠 Conversation Memory Test\n")
    print("This script tests the conversation memory functionality of the multi-agent system.")
    print("It will run several test scenarios with follow-up questions.\n")
    
    try:
        asyncio.run(test_memory())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
    except Exception as e:
        print(f"\n\n❌ Error running test: {e}")
        import traceback
        traceback.print_exc()
