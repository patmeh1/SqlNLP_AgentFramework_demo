"""
Flask Web Application for Multi-Agent SQL Demo
Provides a chat interface using Microsoft Agent Framework for intelligent routing.
Routes queries to SQL Agent for database queries or General Agent for other questions.
"""

from flask import Flask, render_template, request, jsonify, session
from dotenv import load_dotenv
import os
import secrets
import asyncio
from sql_agent import create_agent_from_env
from agents.sql_agent_wrapper import SQLAgentWrapper
from agents.orchestrator import create_orchestrator_from_env
from datetime import datetime

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', secrets.token_hex(32))

# Store orchestrator instances per session
orchestrators = {}


def get_orchestrator_for_session():
    """Get or create an orchestrator instance for the current session."""
    session_id = session.get('session_id')
    
    if not session_id:
        session_id = secrets.token_hex(16)
        session['session_id'] = session_id
    
    if session_id not in orchestrators:
        try:
            # Create SQL agent
            sql_agent = create_agent_from_env()
            sql_agent_wrapper = SQLAgentWrapper(sql_agent)
            
            # Create orchestrator with both SQL and General agents
            orchestrators[session_id] = create_orchestrator_from_env(sql_agent_wrapper)
        except Exception as e:
            print(f"Error creating orchestrator: {e}")
            return None
    
    return orchestrators[session_id]


@app.route('/')
def index():
    """Render the main chat interface."""
    return render_template('index.html')


@app.route('/api/query', methods=['POST'])
def query():
    """Handle natural language queries from the frontend."""
    try:
        data = request.get_json()
        user_question = data.get('question', '').strip()
        force_agent = data.get('agent', None)  # Optional: force specific agent
        
        if not user_question:
            return jsonify({
                'success': False,
                'error': 'Please provide a question.'
            }), 400
        
        # Get orchestrator for this session
        orchestrator = get_orchestrator_for_session()
        if not orchestrator:
            return jsonify({
                'success': False,
                'error': 'Failed to initialize multi-agent system. Check your configuration.'
            }), 500
        
        # Process the query (async operation)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            if force_agent:
                result = loop.run_until_complete(
                    orchestrator.query_with_agent_choice(user_question, force_agent)
                )
            else:
                result = loop.run_until_complete(
                    orchestrator.query(user_question)
                )
        finally:
            loop.close()
        
        # Format response
        response = {
            'success': result.get('success', False),
            'question': result.get('question', user_question),
            'response': result.get('response', ''),
            'agent_used': result.get('agent_used', 'Unknown'),
            'agent_type': result.get('agent_type', 'unknown'),
            'timestamp': datetime.now().isoformat()
        }
        
        # Add SQL-specific fields if available
        if 'sql' in result:
            response['sql'] = result['sql']
            response['explanation'] = result.get('explanation', '')
            response['results'] = result.get('results', None)
            response['row_count'] = result.get('row_count', 0)
        
        if not result.get('success', False):
            response['error'] = result.get('error', 'Unknown error occurred')
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500


@app.route('/api/history', methods=['GET'])
def get_history():
    """Get conversation history for the current session."""
    try:
        orchestrator = get_orchestrator_for_session()
        if not orchestrator:
            return jsonify({
                'success': False,
                'error': 'No active session'
            }), 404
        
        history = orchestrator.get_conversation_history()
        return jsonify({
            'success': True,
            'history': history
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
        orchestrator = get_orchestrator_for_session()
        if orchestrator:
            orchestrator.clear_history()
        
        return jsonify({
            'success': True,
            'message': 'History cleared'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error clearing history: {str(e)}'
        }), 500


@app.route('/api/agents', methods=['GET'])
def get_agents():
    """Get information about available agents."""
    try:
        orchestrator = get_orchestrator_for_session()
        if not orchestrator:
            return jsonify({
                'success': False,
                'error': 'No active session'
            }), 404
        
        agents_info = orchestrator.get_available_agents()
        return jsonify({
            'success': True,
            'agents': agents_info
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
        'SQL_SERVER',
        'SQL_DATABASE',
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
    print("Multi-Agent SQL Demo - Web Application")
    print("Powered by Microsoft Agent Framework")
    print("=" * 60)
    print(f"SQL Server: {os.getenv('SQL_SERVER')}")
    print(f"SQL Database: {os.getenv('SQL_DATABASE')}")
    print(f"Authentication: {'Azure AD' if auth_type == 'azure_ad' else 'SQL Authentication'}")
    print(f"Multi-Agent System: SQL Agent + General Agent")
    print(f"Azure OpenAI Deployment: {os.getenv('AZURE_OPENAI_DEPLOYMENT')}")
    print("=" * 60)
    print("\nStarting Flask application...")
    print("Access the application at: http://localhost:5002")
    print("\nPress CTRL+C to stop the server.")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5002)

