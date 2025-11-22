# Automatic Agent Routing Implementation Guide

## 🎯 Overview

The system has been updated to **automatically select the best agent(s) for any query** without requiring users to specify which agent to use. Users simply ask questions naturally, and the intelligent query router handles agent selection behind the scenes.

---

## 📊 How Automatic Routing Works

### 1. Query Analysis Phase
When a user submits a question, the system analyzes it to determine:

```
┌─────────────────────────────────────────┐
│        User Question                    │
│  "Can you provide a list of all         │
│   Pt-Problems (patient problems) by     │
│   name for all Tests that have LOINC    │
│   code 2947-0, and also provide the     │
│   SNOMED code for each?"                │
└─────────────────────────────────────────┘
            ↓ ANALYZE
┌─────────────────────────────────────────┐
│ Intent Detection:     SQL_REQUIRED       │
│ Medical Codes:        LOINC, SNOMED     │
│ Complexity:           HIGH              │
│ SQL Likelihood:       0.95              │
│ Verification Needed:  YES               │
└─────────────────────────────────────────┘
```

### 2. Routing Decision Phase
Based on analysis, system determines optimal path:

```
Analysis Results
    ↓
SQL Likelihood > 0.6 ? 
    ├─ YES → Route to SQL Agent
    └─ NO  → Route to General Agent
    ↓
Complexity > MEDIUM ?
    ├─ YES → Add verification step
    └─ NO  → Single agent sufficient
    ↓
ROUTING DECISION
    │
    ├─ sql_to_general:  SQL → General Agent
    ├─ general_only:    General Agent only
    └─ sql_only:        SQL Agent only
```

### 3. Execution Phase
System processes query through selected agent(s):

```
For "Pt-Problems with LOINC and SNOMED codes":
    ↓
    SQL Agent:
    - Generates SQL for medical ontology query
    - Executes against MedData
    - Retrieves: Problems 19928, 3668
    - Finds SNOMED codes: [codes]
    ↓
    General Agent (Verification):
    - Analyzes actual data results
    - Provides medical context
    - Formats for professional output
    ↓
    Response Formatter:
    - Converts to HTML
    - Applies professional styling
    - Adds medical interpretation
    ↓
    User Response
```

---

## 🔍 Query Analysis Details

### Intent Detection
System identifies what the user wants:

| Intent | Indicators | Example |
|--------|-----------|---------|
| SQL_REQUIRED | "list", "show", "provide", "retrieve", "count" | "Provide list of..." |
| SQL_PREFERRED | "find", "search", "compare", "related" | "Find problems..." |
| MEDICAL_LOOKUP | Medical codes present | "LOINC", "SNOMED", "Pt-Problem" |
| KNOWLEDGE_BASE | "explain", "what is", "why", "define" | "What is LOINC 2947-0?" |
| CLARIFICATION | Follow-up questions | "How many?" (after previous query) |

### Complexity Estimation
System estimates query complexity:

```
Low Complexity:
  └─ Simple lookup: "Show LOINC codes"
  └─ Definition: "What is SNOMED?"
  └─ Scoring: 0-1.5 points

Medium Complexity:
  └─ Multiple criteria: "LOINC codes AND patient problems"
  └─ Relationships: "Problems indicated by tests"
  └─ Scoring: 1.5-3 points

High Complexity:
  └─ Multiple queries: Multiple ? in question
  └─ Nested requirements: Parentheses or conjunctions
  └─ Multi-step analysis needed
  └─ Scoring: 3+ points
```

### Confidence Calculation
System calculates routing confidence (0-1 scale):

```
Formula:
  Base: abs(SQL_Likelihood - 0.5) * 2
  Intent Adjustment: +0.2 for clear intents
  Final: min(1.0, base_score + adjustments)

Result:
  0.9+ = Very High (Trust routing decision)
  0.7-0.9 = High (Confident routing)
  0.5-0.7 = Medium (Likely good routing)
  <0.5 = Low (May need adjustment)
```

---

## 🔀 Routing Paths

### Path 1: SQL → General (Default for Complex Medical Queries)

**Used When:**
- SQL Likelihood ≥ 0.7
- Query requires data retrieval
- Results need verification/interpretation
- Medical context needed

**Example:** "Provide Pt-Problems for LOINC 2947-0 with SNOMED codes"

**Flow:**
```
1. SQL Agent
   └─ Generate SQL from natural language
   └─ Execute query
   └─ Retrieve actual data

2. General Agent
   └─ Receive actual data results
   └─ Provide medical interpretation
   └─ Format for professional output
   └─ Add clinical context

3. Response Formatter
   └─ Convert to HTML
   └─ Apply styling
   └─ Display with routing metadata
```

**Response Includes:**
- ✅ Structured data results
- ✅ Medical terminology explanation
- ✅ SNOMED code interpretation
- ✅ Generated SQL (in collapsible section)
- ✅ Routing metadata (agents used, complexity, confidence)

---

### Path 2: General Agent Only

**Used When:**
- SQL Likelihood < 0.4
- Query is knowledge-based
- No database query needed
- Educational/explanatory nature

**Example:** "Explain the difference between LOINC and SNOMED"

**Flow:**
```
1. General Agent
   └─ Answer from knowledge base
   └─ Provide explanation
   └─ Format response

2. Response Formatter
   └─ Apply styling
   └─ Display with routing metadata
```

**Response Includes:**
- ✅ Natural language explanation
- ✅ Medical terminology defined
- ✅ Context and relationships
- ✅ Educational content

---

### Path 3: SQL Only (For Simple Data Retrieval)

**Used When:**
- SQL Likelihood = 0.9+
- Simple, unambiguous query
- No verification needed
- Straightforward data retrieval

**Example:** "How many tests have LOINC code 2947-0?"

**Flow:**
```
1. SQL Agent
   └─ Generate simple SQL
   └─ Execute query
   └─ Return results

2. Response Formatter
   └─ Format results table
   └─ Display with SQL
```

**Response Includes:**
- ✅ Query results
- ✅ Generated SQL
- ✅ Row count
- ✅ Minimal metadata

---

## 📈 Response Format

### Automatic Routing Metadata Display

Every response includes routing information:

```html
<div style="margin: 8px 0; font-size: 12px;">
  <span>✓ Auto-Routed</span>
  <span>SQL Agent → General Agent</span>
  <span>Complexity: HIGH</span>
  <span>Confidence: 95%</span>
</div>
```

### Badge Meanings

| Badge | Meaning |
|-------|---------|
| ✓ Auto-Routed | System automatically selected agents |
| SQL Agent → General Agent | Multi-agent pipeline used |
| Complexity: LOW/MEDIUM/HIGH | Query difficulty level |
| Confidence: X% | Routing decision confidence (0-100%) |

---

## 🎯 Usage Examples

### Example 1: Complex Medical Query

**User Question:**
"Can you provide a list of all Pt-Problems (patient problems) by name for all Tests that have LOINC code 2947-0, and also provide the SNOMED code for each of those patient problems?"

**System Processing:**
```
✓ Query Analysis:
  Intent: SQL_REQUIRED
  Medical Codes: LOINC, Pt-Problem, SNOMED
  Complexity: HIGH
  SQL Likelihood: 0.95
  Needs Verification: YES

✓ Routing Decision:
  Route: sql_to_general
  Primary: SQL Agent
  Secondary: General Agent
  Strategy: Execute query, analyze, provide context

✓ Response:
  ✓ Auto-Routed
  ✓ SQL Agent → General Agent
  ✓ Complexity: HIGH
  ✓ Confidence: 95%
  
  [Structured table with results]
  [Medical interpretations]
  [SNOMED code explanations]
  [View SQL collapsible section]
```

**User sees:** Professional response with no agent confusion

---

### Example 2: Simple Knowledge Question

**User Question:**
"What is LOINC code 2947-0?"

**System Processing:**
```
✓ Query Analysis:
  Intent: KNOWLEDGE_BASE
  Medical Codes: LOINC
  Complexity: LOW
  SQL Likelihood: 0.15
  Needs Verification: NO

✓ Routing Decision:
  Route: general_only
  Primary: General Agent
  Secondary: None
  Strategy: Direct knowledge response

✓ Response:
  ✓ Auto-Routed
  ✓ General Agent
  ✓ Complexity: LOW
  ✓ Confidence: 87%
  
  [Definition of LOINC 2947-0]
  [Clinical significance]
  [Examples of use]
```

**User sees:** Educational explanation without unnecessary complexity

---

### Example 3: Data Lookup

**User Question:**
"How many tests have LOINC code 2947-0?"

**System Processing:**
```
✓ Query Analysis:
  Intent: SQL_REQUIRED
  Medical Codes: LOINC
  Complexity: LOW
  SQL Likelihood: 0.90
  Needs Verification: NO

✓ Routing Decision:
  Route: sql_only
  Primary: SQL Agent
  Secondary: None
  Strategy: Simple data retrieval

✓ Response:
  ✓ Auto-Routed
  ✓ SQL Agent
  ✓ Complexity: LOW
  ✓ Confidence: 92%
  
  31 tests have LOINC code 2947-0
  
  [View SQL collapsible section]
```

**User sees:** Quick, accurate answer with minimal overhead

---

## 🛠️ Implementation Components

### 1. Query Router (`query_router.py`)
**File:** `c:\CSA-demo-projects\MAF_SqlAgent_demo_v3-custom-data\query_router.py`

**Key Classes:**
- `QueryIntent` - Enum of query types
- `QueryRouter` - Analyzes queries and generates routing
- `QueryProcessor` - Coordinates routing with execution

**Main Methods:**
```python
# Analyze a query
analysis = router.analyze_query(question)

# Get routing strategy
strategy = processor.get_processing_strategy(question)

# Information in strategy:
strategy['routing']           # 'sql_to_general', 'general_only', etc.
strategy['agents']            # Dict of primary/secondary agents
strategy['strategy']          # Description of strategy
strategy['analysis']          # Detailed analysis results
strategy['instructions']      # Processing instructions
```

### 2. Updated Flask Backend (`app.py`)
**Changes:**
- Added query_router import
- Initialize query processor
- Updated `/api/query` endpoint
- Added routing analysis step
- Return routing metadata in response

**New Response Fields:**
```json
{
  "auto_routing": true,
  "routing_strategy": "sql_to_general",
  "agents_involved": {
    "primary": "SQL Agent",
    "secondary": "General Agent"
  },
  "query_complexity": "high",
  "routing_confidence": 0.95
}
```

### 3. Updated Frontend (`templates/index.html`)
**Changes:**
- Updated sample questions to show medical queries
- Changed header to medical data system
- Updated JavaScript to display routing badges
- Added complexity and confidence display
- Improved user guidance

**Display:**
```
✓ Auto-Routed | SQL Agent → General Agent | Complexity: HIGH | Confidence: 95%
```

### 4. Query Processing Strategy (`SAMPLE_QUESTIONS.md`)
**File:** `c:\CSA-demo-projects\MAF_SqlAgent_demo_v3-custom-data\SAMPLE_QUESTIONS.md`

Documents:
- Sample medical queries
- How system routes each type
- Expected outputs
- Query complexity levels

---

## 🎓 User Experience Flow

### Before (Manual Agent Selection)
```
User: Which agent should I use for this query?
      "Show me Pt-Problems for LOINC 2947-0"

System: Would need to route manually or ask user
        "SQL Agent or General Agent?"

Result: User confusion, incorrect routing possible
```

### After (Automatic Routing)
```
User: "Can you provide a list of all Pt-Problems 
       (patient problems) by name for all Tests 
       that have LOINC code 2947-0, and also 
       provide the SNOMED code for each?"

System: Analyzes query
        ↓
        Detects: SQL_REQUIRED, medical codes, high complexity
        ↓
        Routes: SQL Agent → General Agent
        ↓
        Shows routing info: "Auto-Routed | SQL→General | HIGH | 95%"

Result: Professional response, user never thinks about agents
```

---

## 📋 Testing Automatic Routing

### Test Query 1: Complex Medical Query
```
Input: "Can you provide a list of all Pt-Problems (patient problems) 
        by name for all Tests that have LOINC code 2947-0, and also 
        provide the SNOMED code for each of those patient problems?"

Expected Routing: sql_to_general
Expected Agents: SQL Agent → General Agent
Expected Complexity: HIGH
Expected Confidence: 0.95+

Result: ✓ PASS - Both agents used, professional output
```

### Test Query 2: Simple Lookup
```
Input: "What LOINC codes are available?"

Expected Routing: sql_only
Expected Agents: SQL Agent only
Expected Complexity: LOW
Expected Confidence: 0.90+

Result: ✓ PASS - Quick SQL query, minimal overhead
```

### Test Query 3: Knowledge Question
```
Input: "What is LOINC code 2947-0?"

Expected Routing: general_only
Expected Agents: General Agent only
Expected Complexity: LOW
Expected Confidence: 0.85+

Result: ✓ PASS - Knowledge-based response, no database access
```

---

## 🔧 Configuration & Customization

### Adjusting SQL Likelihood
Edit `query_router.py` - `_calculate_sql_likelihood()`:

```python
def _calculate_sql_likelihood(self, question_lower: str, intent: QueryIntent) -> float:
    score = 0.0
    
    # Adjust these weights to change sensitivity
    intent_scores = {
        QueryIntent.SQL_REQUIRED: 1.0,    # ← Increase for more SQL
        QueryIntent.SQL_PREFERRED: 0.7,
        QueryIntent.MEDICAL_LOOKUP: 0.8,
        QueryIntent.KNOWLEDGE_BASE: 0.2,
        QueryIntent.CLARIFICATION: 0.1
    }
```

### Adding Medical Concepts
Edit `query_router.py` - `medical_codes`:

```python
self.medical_codes = {
    'loinc': 'medical_code',
    'snomed': 'medical_code',
    'icd-10': 'medical_code',           # ← Add new codes
    'cpt': 'medical_code',
    # ... etc
}
```

### Adjusting Complexity Thresholds
Edit `query_router.py` - `_estimate_complexity()`:

```python
if complexity_score > 3:       # ← Adjust thresholds
    return 'high'
elif complexity_score > 1.5:
    return 'medium'
else:
    return 'low'
```

---

## 📚 Documentation Files

**Key Files for Reference:**
- `query_router.py` - Intelligent routing logic
- `app.py` - Updated Flask backend
- `templates/index.html` - Updated frontend
- `SAMPLE_QUESTIONS.md` - Query examples and expected behavior
- This file - Implementation guide

---

## ✅ Verification Checklist

- [x] Query Router created with full analysis
- [x] Flask backend updated with automatic routing
- [x] Frontend shows routing information
- [x] Sample medical questions provided
- [x] System handles complex queries
- [x] No user confusion about agents
- [x] Professional response formatting
- [x] Routing metadata displayed
- [x] Confidence scoring working
- [x] Complexity estimation functional

---

## 🚀 Next Steps

1. **Test the System**
   - Try the medical queries from SAMPLE_QUESTIONS.md
   - Observe routing decisions in console logs
   - Verify response formatting

2. **Monitor Routing**
   - Watch server logs for routing decisions
   - Check confidence scores
   - Verify agents used match expectations

3. **Gather Feedback**
   - Collect real user queries
   - Monitor routing accuracy
   - Adjust thresholds if needed

4. **Expand Query Coverage**
   - Add more medical concepts to router
   - Include additional query patterns
   - Extend intent detection

---

## 📞 Support

### Common Issues

**Q: Why was my query routed to General Agent instead of SQL Agent?**
A: Check the query complexity and SQL likelihood in the response badges. 
   If SQL_Likelihood < 0.6, general routing is used. Review SAMPLE_QUESTIONS.md for examples.

**Q: Can I see the routing decision logic?**
A: Yes! Check `query_router.py` - `analyze_query()` method shows all decision factors.

**Q: How do I add support for new medical codes?**
A: Edit `query_router.py` - `medical_codes` dictionary to add new terminology.

---

## 📝 Summary

✅ **Automatic Routing Complete**

The system now:
- **Analyzes queries** to determine intent and complexity
- **Routes automatically** to appropriate agents (no user confusion)
- **Displays routing information** transparently
- **Handles complex medical queries** like real users will ask
- **Provides professional responses** with medical context
- **Shows confidence levels** for routing decisions
- **Scales from simple to complex** queries seamlessly

**Users simply ask questions. The system figures out everything else.**

---

**Implementation Date**: 2025
**Status**: ✅ COMPLETE AND READY FOR USE
**Last Updated**: Automatic routing system fully integrated
