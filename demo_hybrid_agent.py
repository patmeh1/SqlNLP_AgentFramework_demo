"""
Test the Hybrid Agent with Memory - Interactive Demo
Shows SQL→General chaining and conversation memory in action
"""

import asyncio
import sys
from hybrid_agent_with_memory import create_hybrid_agent_from_env
from datetime import datetime


async def demo_hybrid_agent():
    """Interactive demo of the hybrid agent system."""
    
    print("=" * 80)
    print("HYBRID AGENT INTERACTIVE DEMO")
    print("=" * 80)
    print("\nInitializing hybrid agent system...")
    print("Architecture: SQL Agent → General Agent → Memory\n")
    
    try:
        agent = await create_hybrid_agent_from_env()
        print("✅ Hybrid agent initialized successfully!\n")
    except Exception as e:
        print(f"❌ Error initializing agent: {e}")
        return
    
    # Demo scenario: Multi-turn conversation
    demo_questions = [
        {
            "question": "Show me all tests with LOINC code 2947-0",
            "description": "Initial query - finding sodium tests"
        },
        {
            "question": "What patient problems do those tests indicate?",
            "description": "Follow-up using context from Q1"
        },
        {
            "question": "Give me the SNOMED codes for those problems",
            "description": "Follow-up using context from Q1 and Q2"
        }
    ]
    
    print("=" * 80)
    print("SCENARIO: Multi-turn medical ontology query with context")
    print("=" * 80)
    print()
    
    for i, item in enumerate(demo_questions, 1):
        question = item['question']
        description = item['description']
        
        print(f"\n{'─' * 80}")
        print(f"QUERY {i}: {description}")
        print(f"{'─' * 80}")
        print(f"Question: \"{question}\"\n")
        
        # Process query
        start_time = datetime.now()
        result = await agent.query(question)
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        if not result['success']:
            print(f"❌ Error: {result.get('error')}")
            continue
        
        # Show SQL query
        print("┌─ SQL Query Generated ─────────────────────────────────────────────┐")
        sql_lines = result['sql_query'].split('\n')
        for line in sql_lines[:10]:  # Show first 10 lines
            print(f"│ {line:<68} │")
        if len(sql_lines) > 10:
            print(f"│ ... ({len(sql_lines) - 10} more lines) {' ' * 37} │")
        print("└────────────────────────────────────────────────────────────────────┘\n")
        
        # Show results
        print(f"📊 Results: {result['row_count']} rows returned")
        print()
        
        # Show agent chain processing
        print("🔄 Agent Chain Processing:")
        print("   Step 1: SQL Agent → Query executed ✓")
        print("   Step 2: General Agent → Response verified ✓")
        print("   Step 3: Memory → Interaction stored ✓")
        print()
        
        # Show final response
        print("📝 Final Response (Verified & Refined):")
        print("┌────────────────────────────────────────────────────────────────────┐")
        response_lines = result['final_response'].split('\n')
        for line in response_lines[:15]:  # Show first 15 lines
            # Wrap long lines
            if len(line) > 68:
                words = line.split()
                current_line = ""
                for word in words:
                    if len(current_line) + len(word) + 1 <= 68:
                        current_line += word + " "
                    else:
                        print(f"│ {current_line:<68} │")
                        current_line = word + " "
                if current_line:
                    print(f"│ {current_line:<68} │")
            else:
                print(f"│ {line:<68} │")
        
        if len(response_lines) > 15:
            print(f"│ ... ({len(response_lines) - 15} more lines) {' ' * 37} │")
        print("└────────────────────────────────────────────────────────────────────┘\n")
        
        # Show metadata
        print(f"⏱️  Processing time: {duration:.2f}s")
        print(f"💾 Memory size: {result['memory_size']} interactions")
        print()
        
        # Pause between queries
        if i < len(demo_questions):
            print("\n⏸️  Press Enter to continue to next query...")
            input()
    
    # Show final memory summary
    print("\n" + "=" * 80)
    print("MEMORY SUMMARY")
    print("=" * 80)
    
    memory_summary = agent.get_memory_summary()
    print(f"\nTotal interactions stored: {memory_summary['total_interactions']}\n")
    
    print("Interaction History:")
    print("┌────┬─────────────┬────────────────────────────────────────────────────┐")
    print("│ #  │ Time        │ Question                                           │")
    print("├────┼─────────────┼────────────────────────────────────────────────────┤")
    
    for i, interaction in enumerate(memory_summary['interactions'], 1):
        timestamp = interaction['timestamp']
        if isinstance(timestamp, str):
            time_str = timestamp[11:19]  # Extract HH:MM:SS
        else:
            time_str = timestamp.strftime("%H:%M:%S")
        
        question = interaction['question']
        if len(question) > 50:
            question = question[:47] + "..."
        
        print(f"│ {i:<2} │ {time_str} │ {question:<50} │")
    
    print("└────┴─────────────┴────────────────────────────────────────────────────┘\n")
    
    # Export memory
    print("\n💾 Exporting memory to file...")
    filename = f"demo_memory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    agent.export_memory(filename)
    
    print("\n" + "=" * 80)
    print("DEMO COMPLETE")
    print("=" * 80)
    print(f"""
Key Takeaways:
1. ✅ SQL queries generated with POML-enhanced prompts
2. ✅ Responses verified and refined by General Agent
3. ✅ Conversation memory enables context-aware follow-ups
4. ✅ Each interaction stored with complete details
5. ✅ Memory exportable for analysis

Next Steps:
- Try the web interface at http://localhost:5002
- Use API endpoints for programmatic access
- Export memory for debugging and analysis
- Test with your own medical queries
    """)


if __name__ == "__main__":
    print("\nStarting hybrid agent demo...\n")
    asyncio.run(demo_hybrid_agent())
