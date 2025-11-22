# System Flow Diagrams

## 1. Query Processing Flow

```mermaid
graph TD
    A[User Submits Query] --> B[Flask /api/query Endpoint]
    B --> C[Get Session Orchestrator]
    C --> D[Multi-Agent Orchestrator]
    D --> E{Analyze Query Intent}
    
    E --> F[Planner Agent<br/>GPT-4o Analysis]
    F --> G{Routing Decision}
    
    G -->|Database Related| H[SQL Agent]
    G -->|General Knowledge| I[General Agent]
    
    H --> J[Parse NL to SQL]
    J --> K[Execute Query]
    K --> L[Azure SQL Database]
    L --> M[Format Results]
    M --> N[Generate NL Response]
    
    I --> O[GPT-4o Processing]
    O --> P[Generate Response]
    
    N --> Q[Return to User]
    P --> Q
    Q --> R[Display in Chat UI]
    
    style D fill:#667eea
    style H fill:#48bb78
    style I fill:#ed8936
    style L fill:#4299e1
```

## 2. Multi-Agent Architecture

```mermaid
graph TB
    subgraph "Frontend Layer"
        UI[Web Chat Interface<br/>HTML/JavaScript]
    end
    
    subgraph "Application Layer"
        Flask[Flask Web Server<br/>app.py]
        Session[Session Management]
    end
    
    subgraph "Orchestration Layer"
        Orch[Multi-Agent Orchestrator<br/>orchestrator.py]
        Planner[Planner/Router Agent<br/>GPT-4o]
    end
    
    subgraph "Agent Layer"
        SQL[SQL Agent Wrapper<br/>sql_agent_wrapper.py]
        General[General Agent<br/>general_agent.py]
        Original[Original SQL Agent<br/>sql_agent.py]
    end
    
    subgraph "Data Layer"
        DB[(Azure SQL Database<br/>MedData)]
        OpenAI[Azure OpenAI<br/>GPT-4o]
    end
    
    UI --> Flask
    Flask --> Session
    Session --> Orch
    Orch --> Planner
    Planner -.Routes.-> SQL
    Planner -.Routes.-> General
    SQL --> Original
    Original --> DB
    SQL --> OpenAI
    General --> OpenAI
    
    style Orch fill:#667eea,color:#fff
    style SQL fill:#48bb78,color:#fff
    style General fill:#ed8936,color:#fff
    style DB fill:#4299e1,color:#fff
    style OpenAI fill:#9f7aea,color:#fff
```

## 3. Routing Decision Process

```mermaid
graph LR
    A[User Query] --> B[Extract Context]
    B --> C[Recent Conversation<br/>History]
    B --> D[Database Schema<br/>Information]
    B --> E[Query Content<br/>Analysis]
    
    C --> F{Planner Agent<br/>Decision Making}
    D --> F
    E --> F
    
    F -->|High Confidence<br/>0.8-1.0| G[Route to<br/>SQL Agent]
    F -->|Medium-High<br/>0.5-0.8| H[Route to<br/>General Agent]
    F -->|Low/Error<br/>< 0.5| I[Default to<br/>General Agent]
    
    G --> J[Execute Database<br/>Query]
    H --> K[Generate General<br/>Response]
    I --> K
    
    style F fill:#667eea,color:#fff
    style G fill:#48bb78,color:#fff
    style H fill:#ed8936,color:#fff
    style I fill:#ed8936,color:#fff
```

## 4. SQL Agent Processing Flow

```mermaid
sequenceDiagram
    participant U as User
    participant O as Orchestrator
    participant S as SQL Agent
    participant G as GPT-4o
    participant D as Database
    
    U->>O: "Show top 5 products"
    O->>O: Analyze intent
    O->>S: Route to SQL Agent
    
    S->>G: Generate SQL from NL
    Note over G: System prompt with<br/>database schema
    G-->>S: SQL: SELECT TOP 5...
    
    S->>D: Execute SQL Query
    D-->>S: Query Results
    
    S->>G: Generate NL Response
    G-->>S: Natural Language Answer
    
    S->>O: Response + SQL + Results
    O->>U: Display in Chat
    
    Note over U,D: Complete interaction with<br/>SQL transparency
```

## 5. General Agent Processing Flow

```mermaid
sequenceDiagram
    participant U as User
    participant O as Orchestrator
    participant G as General Agent
    participant AI as GPT-4o
    
    U->>O: "What is machine learning?"
    O->>O: Analyze intent
    O->>G: Route to General Agent
    
    G->>AI: Process with context
    Note over AI: Instructions for<br/>general knowledge
    AI-->>G: Comprehensive Answer
    
    G->>O: Response
    O->>U: Display in Chat
    
    Note over U,AI: Simple interaction<br/>without database
```

## 6. Session Management

```mermaid
graph TD
    A[First Request] --> B{Session ID<br/>Exists?}
    B -->|No| C[Generate New<br/>Session ID]
    B -->|Yes| D[Retrieve Session<br/>Orchestrator]
    
    C --> E[Create New<br/>Orchestrator]
    E --> F[Initialize SQL Agent]
    E --> G[Initialize General Agent]
    
    F --> H[Store in Session]
    G --> H
    
    H --> I[Process Query]
    D --> I
    
    I --> J[Update History]
    J --> K[Return Response]
    
    style E fill:#667eea,color:#fff
    style F fill:#48bb78,color:#fff
    style G fill:#ed8936,color:#fff
```

## 7. Error Handling Flow

```mermaid
graph TD
    A[Query Received] --> B{Orchestrator<br/>Available?}
    B -->|No| C[Initialize Error]
    B -->|Yes| D[Route Query]
    
    D --> E{Routing<br/>Success?}
    E -->|No| F[Default to<br/>General Agent]
    E -->|Yes| G[Process with<br/>Selected Agent]
    
    G --> H{Agent<br/>Processing}
    H -->|Success| I[Format Response]
    H -->|Error| J[Catch Exception]
    
    J --> K[Log Error]
    K --> L[Return Error<br/>Response]
    
    C --> L
    F --> M[Try General<br/>Processing]
    M --> I
    
    I --> N[Return to User]
    L --> N
    
    style J fill:#f56565,color:#fff
    style K fill:#f56565,color:#fff
    style L fill:#f56565,color:#fff
```

## 8. Extension Pattern (Adding New Agent)

```mermaid
graph TD
    A[Create New Agent] --> B[agents/new_agent.py]
    B --> C[Implement run method]
    B --> D[Define description]
    B --> E[Add capabilities]
    
    F[Update Orchestrator] --> G[Import new agent]
    G --> H[Initialize in __init__]
    H --> I[Add to routing logic]
    I --> J[Update _route_query]
    
    K[Update App] --> L[Handle new responses]
    L --> M[Update API docs]
    
    C --> N[Test Integration]
    D --> N
    E --> N
    J --> N
    M --> N
    
    N --> O[Deploy]
    
    style B fill:#667eea,color:#fff
    style F fill:#48bb78,color:#fff
    style K fill:#ed8936,color:#fff
```

## 9. Data Flow - Complete Request

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │ HTTP POST /api/query
       │ {"question": "Show all products"}
       ↓
┌──────────────────────────────────────┐
│     Flask Application (app.py)       │
│  • Validate request                  │
│  • Get/create session orchestrator   │
└──────┬───────────────────────────────┘
       │ Python object
       │ orchestrator.query(question)
       ↓
┌──────────────────────────────────────┐
│   Orchestrator (orchestrator.py)     │
│  • Call _route_query()               │
│  • Analyze: content + context        │
│  • Decision: SQL Agent (0.95 conf)   │
└──────┬───────────────────────────────┘
       │ async call
       │ sql_agent.process_query()
       ↓
┌──────────────────────────────────────┐
│   SQL Agent (sql_agent_wrapper.py)   │
│  • Extract question                  │
│  • Call wrapped SQL agent            │
└──────┬───────────────────────────────┘
       │ sync call
       │ sql_agent.query()
       ↓
┌──────────────────────────────────────┐
│  Original SQL Agent (sql_agent.py)   │
│  • Generate SQL via GPT-4o           │
│  • Execute on database               │
│  • Format results                    │
└──────┬───────────────────────────────┘
       │ Query result dict
       ↓
┌──────────────────────────────────────┐
│   SQL Agent Wrapper                  │
│  • Format as ChatMessage             │
│  • Add metadata                      │
└──────┬───────────────────────────────┘
       │ Result dict with agent info
       ↓
┌──────────────────────────────────────┐
│   Orchestrator                       │
│  • Add to conversation history       │
│  • Format complete response          │
└──────┬───────────────────────────────┘
       │ JSON response
       ↓
┌──────────────────────────────────────┐
│   Flask Application                  │
│  • jsonify response                  │
│  • Set HTTP headers                  │
└──────┬───────────────────────────────┘
       │ HTTP 200 OK
       │ JSON payload
       ↓
┌─────────────┐
│   Browser   │
│  • Display  │
│  • Update   │
└─────────────┘
```

## 10. Comparison: Before vs After

### Before (Single Agent)
```
User Query → SQL Agent → Database → Response
             (Limited to DB queries only)
```

### After (Multi-Agent)
```
                    ┌→ SQL Agent → Database → Response
User Query → Router ┤
                    └→ General Agent → AI → Response
                    (Handles all query types)
```

---

## Technical Notes

### Key Technologies Visualized

1. **Microsoft Agent Framework**: Orchestration backbone
2. **Azure OpenAI GPT-4o**: Intelligence layer (routing + processing)
3. **Python asyncio**: Asynchronous execution
4. **Flask**: Web framework
5. **Azure SQL Database**: Data persistence

### Design Patterns Used

1. **Wrapper Pattern**: SQL Agent wrapper around original agent
2. **Strategy Pattern**: Different agents for different query types
3. **Factory Pattern**: create_orchestrator_from_env()
4. **Observer Pattern**: Session-based orchestrator instances
5. **Chain of Responsibility**: Routing through orchestrator

### Performance Characteristics

- **Routing Decision**: ~0.5-1.0 seconds (GPT-4o call)
- **SQL Query**: ~0.5-2.0 seconds (depends on query complexity)
- **General Response**: ~1.0-2.0 seconds (GPT-4o generation)
- **Total Latency**: 1.0-3.0 seconds average

---

**Repository**: https://github.com/patmeh1/MAF_SqlAgent_demo
**Last Updated**: October 29, 2025
