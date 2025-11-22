---
layout: default
title: System Architecture
---

# 🏗️ System Architecture

## High-Level Overview

```
┌─────────────────────────────────────────────────────────┐
│                   Web Browser UI                        │
│              (Modern Chat Interface)                    │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP/WebSocket
                       ↓
┌─────────────────────────────────────────────────────────┐
│                  Flask Web Application                  │
│  - Session Management                                   │
│  - Request Handling                                     │
│  - Response Formatting                                  │
│  - Error Handling                                       │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────┐
│            Multi-Agent Orchestrator                     │
│  - Query Router                                         │
│  - Intent Analysis                                      │
│  - Agent Selection                                      │
│  - Confidence Scoring                                   │
└──────────┬──────────────────────────┬──────────────────┘
           │                          │
           ↓                          ↓
    ┌─────────────┐           ┌──────────────┐
    │  SQL Agent  │           │ General Agent│
    │             │           │              │
    │- Schema     │           │- Knowledge   │
    │  Analysis   │           │  Retrieval   │
    │- Query Gen. │           │- Reasoning   │
    │- Execution  │           │- Responses   │
    └────┬────────┘           └──────┬───────┘
         │                           │
         ├───────────────┬───────────┤
         ↓               ↓           ↓
    ┌──────────────────────────────────────┐
    │    Azure OpenAI (GPT-4o)             │
    │  - Language Processing               │
    │  - SQL Generation                    │
    │  - Intent Understanding              │
    │  - Response Generation               │
    └──────────────────┬───────────────────┘
                       │
                       ↓
    ┌──────────────────────────────────────┐
    │     Azure SQL Database               │
    │  - Query Execution                   │
    │  - Data Retrieval                    │
    │  - Schema Information                │
    │  - Result Formatting                 │
    └──────────────────────────────────────┘
```

---

## Component Details

### 1. Web Interface Layer

**Location**: `templates/index.html`

**Features**:
- Modern, responsive chat interface
- Real-time execution panel
- SQL query visualization
- Data table display
- Sample questions

**Technology**:
- HTML5 for structure
- CSS3 for styling (gradients, flexbox)
- JavaScript for interactivity
- Fetch API for communication

---

### 2. Flask Application Layer

**Location**: `app.py`

**Responsibilities**:
```python
- @app.route('/api/query', methods=['POST'])
  ↓ Receives user questions
  ↓ Calls orchestrator
  ↓ Returns formatted responses

- @app.route('/api/agents')
  ↓ Lists available agents
  
- @app.route('/api/history')
  ↓ Returns conversation history
  
- @app.route('/api/health')
  ↓ Checks system status
```

**Session Management**:
- Maintains agent instances
- Tracks conversation history
- Manages user context

---

### 3. Multi-Agent Orchestrator

**Location**: `agents/orchestrator.py`

**Decision Flow**:

```
User Query
   ↓
1. Intent Analysis
   - Parse question
   - Identify keywords
   - Extract entities
   ↓
2. Context Review
   - Check history
   - Consider previous answers
   - Maintain state
   ↓
3. Schema Analysis
   - Check database schema
   - Relevant tables/columns
   - Feasibility assessment
   ↓
4. Routing Decision
   - SQL Agent? → Database queries
   - General Agent? → Knowledge questions
   - Confidence score
   ↓
5. Execute Selected Agent
   ↓
6. Format & Return Result
```

---

### 4. SQL Agent

**Location**: `agents/sql_agent_wrapper.py` / `sql_agent.py`

**Capabilities**:

```
Input: "Show me top 5 expensive products"
   ↓
1. Schema Analysis
   - Read database schema
   - Identify relevant tables
   - Plan query structure
   ↓
2. SQL Generation
   - Create SQL query
   - Apply filters/sorting
   - Format results
   
   Result: SELECT TOP 5 * FROM Products 
           ORDER BY Price DESC
   ↓
3. Query Validation
   - Check syntax
   - Verify safety (SELECT only)
   - Ensure optimization
   ↓
4. Execution
   - Execute query
   - Retrieve results
   - Handle errors
   ↓
5. Response Generation
   - Format results
   - Create explanation
   - Display query
   ↓
Output: Formatted table + explanation
```

---

### 5. General Agent

**Location**: `agents/general_agent.py`

**Workflow**:

```
Input: "Explain machine learning"
   ↓
1. Intent Recognition
   - Identify knowledge question
   - Not database-specific
   ↓
2. Information Gathering
   - Consider database context
   - Relevant to current conversation
   ↓
3. Response Generation
   - Compose comprehensive answer
   - Include relevant examples
   - Format professionally
   ↓
Output: Detailed explanation
```

---

### 6. Azure OpenAI Integration

**Service**: GPT-4o Model

**Functions**:

1. **Intent Classification**
   ```
   Input: Natural language question
   Output: Agent selection + confidence
   ```

2. **SQL Generation**
   ```
   Input: Database schema + natural language
   Output: Optimized SQL query
   ```

3. **Response Generation**
   ```
   Input: Question + context
   Output: Detailed answer
   ```

4. **Error Analysis**
   ```
   Input: Error message
   Output: Explanation + recovery suggestion
   ```

---

### 7. Database Layer

**Type**: Azure SQL Database

**Interaction Model**:

```
Agent
  ↓
Generate SQL
  ↓
pyodbc connection
  ↓
ODBC Driver 18
  ↓
TLS/SSL Encryption
  ↓
Azure SQL Database
  ↓
Execute Query
  ↓
Return Results
  ↓
Format & Display
```

---

## Data Flow Diagrams

### Query Processing Flow

```
User Enters: "Show me customers from Germany"
           ↓
    Sent to /api/query
           ↓
    Parse request body
           ↓
    Get/create orchestrator
           ↓
    Call orchestrator.process_query()
           ↓
    ├─ Analyze intent
    │  └─ Determine: SQL Agent needed
    │
    ├─ Route to SQL Agent
    │  ├─ Get database schema
    │  ├─ Generate SQL
    │  │  (SELECT * FROM Customers WHERE Country='Germany')
    │  ├─ Validate query
    │  └─ Execute query
    │
    ├─ Get results
    │  ├─ Format data
    │  ├─ Count rows
    │  └─ Prepare explanation
    │
    └─ Return response
           ↓
    Format JSON response
           ↓
    Send to client
           ↓
    Display in UI
           ↓
    ├─ Show chat message
    ├─ Update execution panel
    ├─ Display results table
    └─ Show SQL query
```

---

## Error Handling Architecture

### Error Recovery System

```
Query Execution
        ↓
Error Detected?
    ├─ No → Return success
    │
    └─ Yes → Error Analysis
           ↓
        Categorize Error
        ├─ SYNTAX_ERROR
        ├─ COLUMN_ERROR
        ├─ TABLE_ERROR
        ├─ TYPE_ERROR
        ├─ AGGREGATE_ERROR
        └─ OTHER
           ↓
        Generate Error Hint
           ↓
        Route to General Agent
           ├─ Explain error
           ├─ Suggest fixes
           └─ Offer alternatives
           ↓
        Return helpful response
```

---

## Session Management

### User Session Lifecycle

```
Browser Opens App
      ↓
Create Session (Flask)
      ↓
Initialize Orchestrator
├─ Load SQL Agent
├─ Load General Agent
└─ Initialize history
      ↓
User Makes Query
      ↓
Orchestrator Processes
├─ Store in history
├─ Maintain context
└─ Keep agents stateful
      ↓
Multiple Queries
      ↓
Session Maintains State
      ↓
Browser Closes / Timeout
      ↓
Session Cleanup
```

---

## Execution Tracking

### Real-Time Step Visualization

```
Query Received
      ↓
Step 1: Query Analysis (Active → Success)
├─ Timestamp
├─ Status indicator
└─ Details shown
      ↓
Step 2: Intent Detection (Active → Success)
├─ Timestamp
├─ Status indicator
└─ Agent decision
      ↓
Step 3: Agent Routing (Active → Success)
├─ Timestamp
├─ Agent selected
└─ Confidence score
      ↓
Step 4: SQL Generation (Active → Success/Error)
├─ Timestamp
├─ SQL query shown
└─ Validation result
      ↓
Step 5: Query Execution (Active → Success/Error/Retry)
├─ Timestamp
├─ Result count
└─ Execution time
      ↓
Step 6: Result Processing (Active → Success)
├─ Timestamp
├─ Formatting applied
└─ Ready to display
      ↓
Complete - All steps visible in panel
```

---

## Security Architecture

### Defense Layers

```
┌─────────────────────────────────────┐
│   Layer 1: Web Layer                │
├─────────────────────────────────────┤
│  - HTTPS/TLS encryption             │
│  - CORS validation                  │
│  - Input sanitization               │
│  - Rate limiting                    │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│   Layer 2: Application Layer        │
├─────────────────────────────────────┤
│  - Authentication                   │
│  - Authorization                    │
│  - Session isolation                │
│  - Query validation                 │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│   Layer 3: Database Layer           │
├─────────────────────────────────────┤
│  - Read-only connection             │
│  - Parameterized queries            │
│  - Firewall rules                   │
│  - TLS encryption                   │
│  - Azure AD integration             │
└─────────────────────────────────────┘
```

---

## Scalability Design

### Horizontal Scaling

```
Load Balancer
      ↓
   ┌──┴──┐
   ↓     ↓
App1  App2  App3
   ↓     ↓     ↓
   └──┬──┘
      ↓
Shared Session Store
      ↓
Azure SQL Database (Connection Pool)
```

### Vertical Scaling
- Increase Flask workers
- Expand connection pool
- Cache query results
- Optimize agent prompts

---

## Performance Optimization

### Caching Strategy
```
Query
  ↓
Cache Check
├─ Hit → Return cached
│
└─ Miss → Execute → Store → Return
```

### Connection Pooling
```
Request 1 ─┐
Request 2 ─┼─> Pool (10 connections)
Request 3 ─┘
```

### Async Processing
```
synchronous ──────> takes longer

async
├─ Parse in parallel
├─ Generate in parallel  
└─ Return faster
```

---

## Deployment Architecture

### Development
```
Local Machine
├─ Python venv
├─ Local Flask server
├─ Local/Cloud DB
└─ OpenAI API
```

### Production
```
Azure App Service
├─ Multiple instances
├─ Auto-scaling
├─ Load balancing
├─ Application Insights
├─ Azure SQL Database
├─ Azure OpenAI Service
└─ Key Vault (secrets)
```

---

<div style="text-align: center; margin-top: 40px; padding: 20px; background: #f5f5f5; border-radius: 10px;">
  <h3>Understanding the System</h3>
  <p><a href="/">← Back to Home</a> | <a href="/features.html">View Features →</a></p>
</div>
