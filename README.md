# Multi-Agent SQL Demo - Intelligent Natural Language Interface

A sophisticated demo application powered by the **Microsoft Agent Framework** and **Azure OpenAI GPT-4o** that intelligently routes user queries to specialized agents. The system can handle both database queries and general knowledge questions through an intuitive chat interface.

![Multi-Agent Architecture](https://via.placeholder.com/800x400?text=Multi-Agent+SQL+Demo)

## 🎯 Features

### ✨ Medical Ontology Intelligence
- **MedData Agent**: Specialized for medical code queries (LOINC, SNOMED, medical terminology)
- **Smart Query Routing**: Automatic detection of medical query intent
- **General Agent**: Medical knowledge and explanations
- **Context Awareness**: Maintains conversation history across queries
- **Professional Formatting**: Beautiful, readable responses with medical data

### Intelligent Multi-Agent System
- **Smart Query Routing**: Automatic detection of query intent and routing to the appropriate agent
- **MedData Agent**: Translates natural language to SQL and queries medical ontology data
- **General Agent**: Handles medical knowledge questions and conversations
- **Context Awareness**: Maintains conversation history for medical discussions

### SQL Agent Capabilities
- **Natural Language Queries**: Ask questions about medical ontology in plain English
- **Intelligent SQL Generation**: GPT-4o automatically generates optimized queries
- **Real-time Results**: View medical codes and terminology in interactive tables
- **Safe Queries**: Read-only access to medical database
- **Query Explanations**: Understand the SQL being executed

### MedData Agent Capabilities
- **Medical Code Queries**: Search LOINC, SNOMED, and other medical ontology data
- **Medical Terminology**: Access standardized medical codes and their properties
- **Semantic Relationships**: Explore relationships between medical codes
- **Comprehensive Lookup**: Query complete medical ontology databases
- **Safe Access**: Read-only queries to medical reference data

### General Agent Capabilities
- **General Knowledge**: Ask about any topic, not just database-related
- **Conversations**: Have natural conversations with the AI
- **Information Retrieval**: Get information from various sources
- **Flexible Responses**: Not constrained to database operations

### User Interface
- **Beautiful Chat Interface**: Modern web UI with conversation history
- **Agent Transparency**: See which agent handled each query
- **Mixed Query Support**: Seamlessly switch between SQL, medical, and general queries
- **Session Management**: Conversation history per session
- **Collapsible SQL Details**: SQL queries and data tables hidden by default, expandable on demand
- **Professional Styling**: Gradient headers, proper spacing, print-friendly design

## 🏗️ Architecture

```
User Question (Medical Query)
     ↓
Multi-Agent Orchestrator (Smart Router)
     ↓
   ┌─┴──┬────┐
   ↓    ↓    ↓
Medical  General  Query
Agent    Agent    Analyzer
   ↓     ↓      ↓
MedData  AI    Response
Database Knowledge
```

The system uses **specialized agents** intelligently routed based on query content:
- **MedData Agent**: Medical ontology data (LOINC, SNOMED codes, medical terminology)
- **General Agent**: Medical knowledge, explanations, and general queries
- **Smart Router**: Analyzes queries and selects the optimal agent

**See [MULTI_AGENT_ARCHITECTURE.md](MULTI_AGENT_ARCHITECTURE.md) for detailed architecture documentation.**

## 📋 Prerequisites

- **Python 3.9+**
- **Azure Subscription**
- **Azure CLI** installed and configured
- **ODBC Driver 18 for SQL Server** ([Download](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server))

### Installing ODBC Driver

**macOS:**
```bash
brew tap microsoft/mssql-release https://github.com/Microsoft/homebrew-mssql-release
brew update
brew install msodbcsql18 mssql-tools18
```

**Linux (Ubuntu/Debian):**
```bash
curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
curl https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list | sudo tee /etc/apt/sources.list.d/mssql-release.list
sudo apt-get update
sudo ACCEPT_EULA=Y apt-get install -y msodbcsql18
```

**Windows:**
Download and install from [Microsoft's website](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)

## 🚀 Setup Instructions

### 1. Clone or Navigate to the Demo Directory

```bash
cd MedData-SqlAgent-Demo
```

### 2. Set Up Azure Resources

Make the setup script executable and run it:

```bash
chmod +x scripts/setup_azure_resources.sh
cd scripts
./setup_azure_resources.sh
```

This script will:
- Create an Azure Resource Group: `MedData_sql_agent`
- Deploy an Azure SQL Server and Database
- Set up firewall rules
- Configure storage and key vault
- Generate a `.env` configuration file

**Important:** You'll be prompted to enter a SQL admin password. Make it strong!

### 3. Load the MedData Database

After the Azure resources are created, load the medical ontology data:

**Option A: Using sqlcmd (recommended)**
```bash
cd ..
sqlcmd -S <your-server-name>.database.windows.net -d MedData -U sqladmin -P '<your-password>' -i database/meddata.sql
```

**Option B: Using Azure Data Studio or SQL Server Management Studio**
1. Connect to your Azure SQL Database
2. Open `database/meddata.sql`
3. Execute the script

### 4. Set Up Azure AI Foundry Project

Since Azure CLI doesn't fully support AI Foundry project creation yet, complete this in the Azure Portal:

1. Go to [https://ai.azure.com](https://ai.azure.com)
2. Sign in with your Azure account
3. Create a new project:
   - **Project Name**: `NYP_AIFoundry`
   - **Hub**: Select the hub created by the script
4. Deploy GPT-4o:
   - Navigate to **Deployments**
   - Click **+ Create deployment**
   - Select **GPT-4o** model
   - **Deployment Name**: `NYP_demo`
   - Configure settings and create

5. Get your credentials:
   - Go to your deployment
   - Copy the **Endpoint URL**
   - Copy the **API Key**

### 5. Configure Environment Variables

Update the `.env` file in the project root with your Azure OpenAI credentials:

```bash
# The script created this file, but you need to update these values:
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here
```

### 6. Create Python Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 7. Install Python Dependencies

```bash
pip install -r requirements.txt
```

**Note:** This will install:
- Microsoft Agent Framework and dependencies
- Azure OpenAI SDK
- Flask web framework
- Database connectors
- And other required packages

### 8. Run the Application

```bash
python app.py
```

The application will start on `http://localhost:5001` with the multi-agent system enabled.

## 💬 Using the Application

1. Open your browser and navigate to `http://localhost:5001`
2. Type natural language questions in the chat input
3. The system automatically routes your query to the appropriate agent
4. View the response with agent information and results
5. Mix database queries with general questions seamlessly!

### Example Questions

#### MedData Agent Queries (Medical Ontology)
- "What does LOINC code 2947-0 represent?"
- "Show me SNOMED codes for diabetes"
- "What are all the LOINC codes for glucose tests?"
- "Find medical terminology for cardiovascular conditions"
- "What procedures are in the medical database?"
- "Show me lab test codes and their descriptions"
- "What SNOMED codes are related to hypertension?"
- "List all available medical codes in each category"

#### General Agent Queries (Medical Knowledge)
- "Explain what LOINC codes are"
- "What is the difference between LOINC and SNOMED?"
- "Tell me about medical ontologies"
- "What are best practices for medical coding?"
- "How is medical data standardized in healthcare?"

#### Mixed Conversation Example
1. "What LOINC codes are for glucose tests?" *(MedData Agent)*
2. "Explain what glucose testing means" *(General Agent)*
3. "Show me SNOMED codes for diabetes" *(MedData Agent)*
4. "What is the medical significance of diabetes codes?" *(General Agent)*

## 🤖 Multi-Agent System

### Available Agents

**1. SQL Agent** 🗄️
- Specializes in database queries
- Converts natural language to SQL
- Executes queries safely
- Provides formatted results

**2. General Agent** 🌐
- Handles general knowledge questions
- Provides information and explanations
- Supports conversations
- Not limited to database topics

### How Routing Works

The **Multi-Agent Orchestrator** analyzes each query and:
1. Examines the question content
2. Considers conversation context
3. Reviews database schema
4. Makes a routing decision with confidence score
5. Routes to the most appropriate agent

You can see which agent handled each response in the UI!

## 📁 Project Structure

```
MAF_SqlAgent_demo/
├── app.py                      # Flask web application with multi-agent support
├── sql_agent.py                # Original SQL Agent implementation
├── agents/                     # Multi-agent system
│   ├── __init__.py            # Package initialization
│   ├── orchestrator.py        # Multi-agent orchestrator with routing
│   ├── sql_agent_wrapper.py   # SQL Agent wrapper for framework
│   └── general_agent.py       # General knowledge agent
├── requirements.txt            # Python dependencies (including agent-framework)
├── .env                        # Environment configuration (created by setup)
├── .env.template               # Template for environment variables
├── .gitignore                  # Git ignore rules
├── README.md                   # This file
├── MULTI_AGENT_ARCHITECTURE.md # Detailed architecture documentation
├── database/
│   └── meddata.sql             # MedData medical ontology schema and data
├── scripts/
│   └── setup_azure_resources.sh # Azure infrastructure setup script
├── templates/
│   └── index.html              # Web chat interface
└── static/                     # (Optional) Static assets
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `SQL_SERVER` | Azure SQL Server hostname | `meddata-sql-server.database.windows.net` | Yes |
| `SQL_DATABASE` | Database name | `MedData` | Yes |
| `SQL_USERNAME` | SQL admin username | `sqladmin` | Optional* |
| `SQL_PASSWORD` | SQL admin password | `YourPassword123!` | Optional* |
| `SQL_AUTH_TYPE` | Authentication type | `azure_ad` or `sql` | No (default: azure_ad) |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint URL | `https://xxx.openai.azure.com/` | Yes |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API key | `abc123...` | Yes |
| `AZURE_OPENAI_DEPLOYMENT` | GPT-4o deployment name | `NYP_demo` | Yes |
| `AZURE_OPENAI_API_VERSION` | API version | `2024-08-01-preview` | No |
| `FLASK_SECRET_KEY` | Flask session secret | Auto-generated | No |

*SQL credentials are optional when using Azure AD authentication

## 🔌 API Endpoints

### POST `/api/query`
Process a user query with automatic or forced agent routing.

**Request:**
```json
{
  "question": "What are the top selling products?",
  "agent": "sql"  // Optional: "sql" or "general" to force specific agent
}
```

**Response:**
```json
{
  "success": true,
  "question": "What are the top selling products?",
  "response": "Based on the database...",
  "agent_used": "SQL Agent",
  "agent_type": "sql",
  "sql": "SELECT TOP 5 ...",
  "explanation": "This query retrieves...",
  "results": [...],
  "row_count": 5,
  "timestamp": "2024-10-29T12:00:00"
}
```

### GET `/api/agents`
Get information about available agents.

**Response:**
```json
{
  "success": true,
  "agents": {
    "sql": "Specialist in querying Azure SQL Database...",
    "general": "General knowledge assistant..."
  }
}
```

### GET `/api/history`
Retrieve conversation history for the current session.

### POST `/api/clear`
Clear conversation history and reset all agents.

### GET `/api/health`
Health check endpoint.

## 🎨 Customization

### Adding New Agents

The multi-agent architecture is designed to be extensible. To add a new specialized agent:

1. **Create a new agent class** in `agents/`:
```python
# agents/document_agent.py
from typing import List
from agent_framework import ChatMessage, Role

class DocumentAgent:
    def __init__(self, ...):
        self.name = "DocumentAgent"
        self.description = "Analyzes and queries documents..."
    
    async def run(self, messages: List[ChatMessage]) -> List[ChatMessage]:
        # Your agent logic here
        return response_messages
```

2. **Update the orchestrator** (`agents/orchestrator.py`):
```python
def __init__(self, ..., document_agent: DocumentAgent):
    self.document_agent = document_agent
    # Add routing logic in _route_query()
```

3. **Update the factory function**:
```python
def create_orchestrator_from_env(...):
    document_agent = DocumentAgent(...)
    orchestrator = MultiAgentOrchestrator(
        ...,
        document_agent=document_agent
    )
```

See [MULTI_AGENT_ARCHITECTURE.md](MULTI_AGENT_ARCHITECTURE.md) for detailed instructions.

### Customizing Agent Behavior

Each agent can be customized:

**SQL Agent:**
- Modify SQL generation prompts in `sql_agent.py`
- Adjust temperature and token limits
- Add custom SQL validation

**General Agent:**
- Update instructions in `agents/general_agent.py`
- Change the model (e.g., GPT-4o-mini for faster responses)
- Add tools and capabilities

**Orchestrator:**
- Tune routing confidence thresholds
- Adjust context window size
- Modify routing decision prompts

### Adding More Sample Questions

Edit `templates/index.html` and add questions to the sample questions list:

```html
<li onclick="askQuestion('Your question here')">• Your question here</li>
```

### Modifying the Database Schema

The agent automatically reads the database schema on initialization. To use a different database:

1. Update the SQL connection settings in `.env`
2. Ensure the database is accessible
3. The agent will automatically adapt to the new schema

### Changing the UI Theme

The chat interface uses CSS in `templates/index.html`. Customize colors by modifying the gradient values:

```css
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
```

## 🔐 Security Considerations

### For Production Deployment:

1. **Use Azure AD Authentication** instead of SQL authentication
2. **Implement rate limiting** on API endpoints
3. **Add input validation** and sanitization
4. **Enable CORS** only for trusted domains
5. **Use Azure Key Vault** for secrets management
6. **Implement logging and monitoring** with Azure Application Insights
7. **Enable HTTPS** with valid SSL certificates
8. **Restrict database firewall rules** to specific IP ranges
9. **Use read-only database credentials** for the agent
10. **Implement user authentication** for the web application

### Current Security Measures:

- Read-only SELECT queries (INSERT, UPDATE, DELETE blocked)
- Azure SQL firewall rules
- Encrypted database connections
- Environment variable configuration
- Session-based agent instances

## 🐛 Troubleshooting

### ODBC Driver Not Found

**Error:** `[Microsoft][ODBC Driver Manager] Data source name not found`

**Solution:** Install ODBC Driver 18 for SQL Server (see Prerequisites section)

### Connection Timeout

**Error:** `Connection timeout`

**Solutions:**
- Check firewall rules in Azure Portal
- Verify your IP is whitelisted
- Ensure Azure services can access the server

### Azure OpenAI Rate Limits

**Error:** `Rate limit exceeded`

**Solutions:**
- Wait and retry
- Increase your Azure OpenAI quota
- Implement request throttling in the application

### Missing Environment Variables

**Error:** `Missing required environment variables`

**Solution:** Ensure all variables in `.env.template` are set in `.env`

## 📊 Demo Scenarios

### Scenario 1: Product Analysis
```
Q: "What are the most expensive products?"
Q: "Show me discontinued products"
Q: "How many products are there in each category?"
```

### Scenario 2: Customer Insights
```
Q: "How many customers are in each country?"
Q: "Show me customers from France"
Q: "Which customer has the most orders?"
```

### Scenario 3: Sales Analysis
```
Q: "What is the total revenue?"
Q: "Show me orders with freight cost over $50"
Q: "Which employee has the highest sales?"
```

## 🤝 Contributing

This is a demo application. For production use, consider:
- Adding comprehensive error handling
- Implementing user authentication
- Adding query result caching
- Supporting complex queries with JOIN operations
- Adding export functionality for results
- Implementing query history persistence

## 📝 License

This demo is provided as-is for educational and demonstration purposes.

## 🆘 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review Azure SQL Database documentation
3. Check Azure OpenAI service status
4. Verify all environment variables are correctly set

## 🎓 Learning Resources

- [Azure OpenAI Service Documentation](https://learn.microsoft.com/en-us/azure/ai-services/openai/)
- [Azure SQL Database Documentation](https://learn.microsoft.com/en-us/azure/azure-sql/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [LOINC Database Reference](https://loinc.org/)
- [SNOMED CT Reference](https://www.snomed.org/)

---

**Built with ❤️ for customer demos**
