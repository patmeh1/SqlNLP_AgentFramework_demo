"""
Flask Web Application for Multi-Agent SQL Demo
Provides a chat interface using Microsoft Agent Framework with intelligent automatic routing.
Automatically selects appropriate agents (SQL/General) based on query analysis.
"""

from flask import Flask, render_template, request, jsonify, session
from dotenv import load_dotenv
import os
import secrets
import asyncio
from hybrid_agent_with_memory import create_hybrid_agent_from_env
from response_formatter import ResponseFormatter, format_general_agent_response
from query_router import create_query_processor
from datetime import datetime

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', secrets.token_hex(32))

# Store Hybrid agent instances per session
hybrid_agents = {}

# Initialize query processor for intelligent routing
query_processor = create_query_processor()


def get_orchestrator_for_session():
    """Get or create a Hybrid Agent instance for the current session."""
    session_id = session.get('session_id')
    
    if not session_id:
        session_id = secrets.token_hex(16)
        session['session_id'] = session_id
    
    if session_id not in hybrid_agents:
        try:
            # Create Hybrid Agent with SQL-to-General chaining and memory
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                hybrid_agents[session_id] = loop.run_until_complete(create_hybrid_agent_from_env())
                print("✓ Hybrid Agent initialized with SQL→General chaining + Memory")
            finally:
                loop.close()
        except Exception as e:
            print(f"Error creating hybrid agent: {e}")
            return None
    
    return hybrid_agents[session_id]


@app.route('/')
def index():
    """Render the main chat interface."""
    return render_template('index.html')


@app.route('/api/query', methods=['POST'])
def query():
    """Handle natural language queries from the frontend with automatic agent routing."""
    try:
        data = request.get_json()
        user_question = data.get('question', '').strip()
        
        if not user_question:
            return jsonify({
                'success': False,
                'error': 'Please provide a question.'
            }), 400
        
        # Step 1: Analyze query and determine optimal routing
        routing_strategy = query_processor.get_processing_strategy(user_question)
        print(f"\n[Query Analysis] Route: {routing_strategy['routing']}")
        print(f"  - Agents: {routing_strategy['agents']['primary']}", end="")
        if routing_strategy['agents']['secondary']:
            print(f" + {routing_strategy['agents']['secondary']}")
        else:
            print()
        print(f"  - Strategy: {routing_strategy['strategy']}")
        print(f"  - Complexity: {routing_strategy['analysis']['complexity']}")
        print(f"  - Confidence: {routing_strategy['analysis']['confidence']}")
        
        # Get Hybrid agent for this session
        agent = get_orchestrator_for_session()
        if not agent:
            return jsonify({
                'success': False,
                'error': 'Failed to initialize hybrid agent system. Check your configuration.'
            }), 500
        
        # Step 2: Process the query through the optimal agent chain
        # The hybrid agent will internally determine whether to use SQL or General agent
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(agent.query(user_question))
        finally:
            loop.close()
        
        # Step 3: Format response with routing metadata
        response = {
            'success': result.get('success', False),
            'question': result.get('question', user_question),
            'response': result.get('final_response', ''),
            'agent_used': 'Intelligent Hybrid Agent',
            'agent_type': 'auto_routed',
            'routing_strategy': routing_strategy['routing'],
            'agents_involved': routing_strategy['agents'],
            'agent_chain': result.get('agent_chain', 'Hybrid Agent → Memory'),
            'timestamp': result.get('timestamp', datetime.now().isoformat()),
            'memory_size': result.get('memory_size', 0),
            # Add routing details for transparency
            'auto_routing': True,
            'query_complexity': routing_strategy['analysis']['complexity'],
            'routing_confidence': routing_strategy['analysis']['confidence']
        }
        
        # Format the general agent response with proper HTML structure
        if result.get('final_response'):
            query_data = result.get('results', None)
            formatted = format_general_agent_response(result['final_response'], query_data)
            response['response_html'] = formatted['html']
            response['response_formatted'] = True
        
        # Add SQL-specific fields if SQL was used
        if 'sql_query' in result:
            response['sql'] = result['sql_query']
            response['sql_response'] = result.get('sql_response', '')
            response['results'] = result.get('results', None)
            response['row_count'] = result.get('row_count', 0)
            response['columns'] = result.get('columns', [])
            response['sql_used'] = True
        else:
            response['sql_used'] = False
        
        if not result.get('success', False):
            response['error'] = result.get('error', 'Unknown error occurred')
        
        return jsonify(response)
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500


@app.route('/api/history', methods=['GET'])
def get_history():
    """Get conversation history for the current session."""
    try:
        agent = get_orchestrator_for_session()
        if not agent:
            return jsonify({
                'success': False,
                'error': 'No active session'
            }), 404
        
        # Get memory summary
        memory_summary = agent.get_memory_summary()
        
        return jsonify({
            'success': True,
            'history': memory_summary['interactions'],
            'total_interactions': memory_summary['total_interactions']
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error retrieving history: {str(e)}'
        }), 500


@app.route('/api/clear', methods=['POST'])
def clear_history():
    """Clear conversation history for the current session."""
    try:
        agent = get_orchestrator_for_session()
        if agent:
            agent.clear_memory()
        
        return jsonify({
            'success': True,
            'message': 'History and memory cleared'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error clearing history: {str(e)}'
        }), 500


@app.route('/api/memory', methods=['GET'])
def get_memory():
    """Get detailed memory information."""
    try:
        agent = get_orchestrator_for_session()
        if not agent:
            return jsonify({
                'success': False,
                'error': 'No active session'
            }), 404
        
        memory_summary = agent.get_memory_summary()
        
        return jsonify({
            'success': True,
            'memory': memory_summary
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error retrieving memory: {str(e)}'
        }), 500


@app.route('/api/memory/export', methods=['POST'])
def export_memory():
    """Export memory to file."""
    try:
        agent = get_orchestrator_for_session()
        if not agent:
            return jsonify({
                'success': False,
                'error': 'No active session'
            }), 404
        
        session_id = session.get('session_id', 'unknown')
        filename = f"memory_export_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        agent.export_memory(filename)
        
        return jsonify({
            'success': True,
            'message': f'Memory exported to {filename}',
            'filename': filename
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error exporting memory: {str(e)}'
        }), 500


@app.route('/api/agents', methods=['GET'])
def get_agents():
    """Get information about available agents."""
    try:
        return jsonify({
            'success': True,
            'agents': [{
                'name': 'Hybrid Medical Ontology Agent',
                'type': 'hybrid',
                'description': 'SQL agent chained with General agent for verified responses with conversation memory',
                'architecture': 'SQL Agent → General Agent → Memory Storage',
                'capabilities': [
                    'Medical ontology SQL query generation',
                    'Response verification and refinement',
                    'LOINC and SNOMED code search',
                    'Hierarchical relationship queries',
                    'Clinical indication analysis',
                    'Conversation memory and context',
                    'Multi-turn contextual queries'
                ],
                'features': [
                    'POML-enhanced SQL generation',
                    'General agent response verification',
                    'Persistent conversation memory',
                    'Context-aware follow-up questions',
                    'Memory export capability'
                ]
            }]
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error retrieving agents: {str(e)}'
        }), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500


if __name__ == '__main__':
    # Validate required environment variables
    # SQL_USERNAME and SQL_PASSWORD are optional (for Azure AD auth)
    required_vars = [
        'MEDDATA_SQL_SERVER',
        'MEDDATA_SQL_DATABASE',
        'AZURE_OPENAI_ENDPOINT',
        'AZURE_OPENAI_API_KEY',
        'AZURE_OPENAI_DEPLOYMENT'
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("ERROR: Missing required environment variables:")
        for var in missing_vars:
            print(f"  - {var}")
        print("\nPlease update your .env file with the required values.")
        exit(1)
    
    # Check authentication type
    sql_username = os.getenv('SQL_USERNAME')
    sql_password = os.getenv('SQL_PASSWORD')
    auth_type = os.getenv('SQL_AUTH_TYPE', 'azure_ad')
    
    if auth_type == 'sql' and (not sql_username or not sql_password):
        print("ERROR: SQL authentication requires SQL_USERNAME and SQL_PASSWORD")
        exit(1)
    
    print("=" * 60)
    print("Medical Ontology Query System")
    print("Powered by Hybrid Agent Architecture + POML")
    print("=" * 60)
    print(f"SQL Server: {os.getenv('MEDDATA_SQL_SERVER')}")
    print(f"SQL Database: {os.getenv('MEDDATA_SQL_DATABASE')}")
    print(f"Authentication: {'Azure AD' if auth_type == 'azure_ad' else 'SQL Authentication'}")
    print(f"Knowledge Base: Medical Ontology (Slot-Based Structure)")
    print(f"Azure OpenAI Deployment: {os.getenv('AZURE_OPENAI_DEPLOYMENT')}")
    print(f"Prompt Framework: POML (Prompt Optimization Markup Language)")
    print(f"Agent Architecture: SQL Agent → General Agent → Memory")
    print("=" * 60)
    print("\nStarting Flask application...")
    print("Access the application at: http://localhost:5002")
    print("\nPress CTRL+C to stop the server.")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5002)

