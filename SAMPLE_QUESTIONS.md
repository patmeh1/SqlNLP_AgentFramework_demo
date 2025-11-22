# Sample Questions for Medical Data System

## 🏥 Complex Medical Queries (The queries end users will ask)

### Query Type 1: Patient Problems + LOINC Codes + SNOMED Codes
These complex queries combine multiple medical concepts and data types.

**Examples:**
1. "Can you provide a list of all Pt-Problems (patient problems) by name for all Tests that have LOINC code 2947-0, and also provide the SNOMED code for each of those patient problems?"
   - *Analysis*: Requires LOINC lookup, Pt-Problem association, SNOMED code retrieval
   - *Routing*: SQL Agent → General Agent for analysis
   - *Response Type*: Structured table with medical context

2. "What patient problems are indicated by tests with LOINC code 2947-0? Show me the SNOMED CT codes for each."
   - *Analysis*: Same as above, simpler phrasing
   - *Routing*: SQL Agent for data, General Agent for interpretation

3. "List all the Pt-Problems for LOINC 2947-0 with their SNOMED codes and medical meanings"
   - *Analysis*: Combines data retrieval with medical terminology explanation
   - *Routing*: SQL Agent + General Agent for context

### Query Type 2: LOINC Code Discovery
Finding available LOINC codes and related information.

**Examples:**
1. "What LOINC codes are available in the database? Show me a few examples."
   - *Analysis*: Simple data retrieval
   - *Routing*: SQL Agent only
   - *Response Type*: List of codes with descriptions

2. "How many tests have LOINC code 2947-0?"
   - *Analysis*: Aggregation query
   - *Routing*: SQL Agent
   - *Response Type*: Numeric result with context

3. "Show me all LOINC codes related to glucose testing"
   - *Analysis*: Search and filter
   - *Routing*: SQL Agent with text search
   - *Response Type*: Filtered list

### Query Type 3: Patient Problem Analysis
Understanding patient problems and their characteristics.

**Examples:**
1. "What are patient problems 19928 and 3668? Show me their names and SNOMED codes."
   - *Analysis*: Code lookup with name and attribute retrieval
   - *Routing*: SQL Agent
   - *Response Type*: Lookup table with details

2. "For patient problems 19928 and 3668, what are their SNOMED codes and names?"
   - *Analysis*: Same as above
   - *Routing*: SQL Agent
   - *Response Type*: Lookup results

3. "Which patient problems are associated with glucose testing?"
   - *Analysis*: Relationship discovery
   - *Routing*: SQL Agent with join logic

### Query Type 4: Medical Relationships
Understanding how medical concepts relate.

**Examples:**
1. "What is the relationship between LOINC 2947-0 and patient problems?"
   - *Analysis*: Knowledge-based with data validation
   - *Routing*: General Agent + SQL Agent for verification

2. "How are tests, patient problems, and SNOMED codes related in the database?"
   - *Analysis*: Schema and relationship explanation
   - *Routing*: General Agent (knowledge)

3. "Show me the diagnostic pathway for LOINC code 2947-0"
   - *Analysis*: Relationship traversal with interpretation
   - *Routing*: SQL Agent for pathway, General Agent for context

### Query Type 5: Comparative Queries
Comparing multiple medical codes or concepts.

**Examples:**
1. "Compare LOINC code 2947-0 with other glucose tests"
   - *Analysis*: Comparative retrieval and analysis
   - *Routing*: SQL Agent for comparison data

2. "What are the differences between patient problems 19928 and 3668?"
   - *Analysis*: Comparison with medical context
   - *Routing*: SQL Agent for data, General Agent for analysis

### Query Type 6: Medical Terminology
Understanding medical codes and standards.

**Examples:**
1. "What does LOINC code 2947-0 represent?"
   - *Analysis*: Definition lookup
   - *Routing*: General Agent (knowledge)

2. "Explain SNOMED CT codes and how they relate to LOINC codes"
   - *Analysis*: Terminology education
   - *Routing*: General Agent
   - *Response Type*: Educational explanation

3. "What is a Pt-Problem in this database?"
   - *Analysis*: Schema explanation
   - *Routing*: General Agent

---

## 🤖 System Behavior for Each Query Type

### Complex Medical Queries (Type 1)
**Query:** "Can you provide a list of all Pt-Problems (patient problems) by name for all Tests that have LOINC code 2947-0, and also provide the SNOMED code for each of those patient problems?"

**System Processing:**
```
1. Query Analysis:
   ✓ Intent: SQL_REQUIRED (needs data retrieval)
   ✓ Medical codes detected: LOINC, Pt-Problem, SNOMED
   ✓ Complexity: HIGH (multiple criteria)
   ✓ SQL Likelihood: 0.95

2. Routing Decision:
   ✓ Route: sql_to_general
   ✓ Primary Agent: SQL Agent
   ✓ Secondary Agent: General Agent
   ✓ Strategy: Execute query, analyze results, provide medical context

3. Execution:
   → SQL Agent generates and executes query
   → Retrieves patient problems 19928, 3668 for LOINC-2947-0
   → Finds associated SNOMED codes
   → General Agent formats and contextualizes results

4. Response:
   ✓ Returns structured table
   ✓ Includes medical interpretations
   ✓ Shows related SNOMED codes
   ✓ Provides clinical context
```

**Expected Output:**
```
Patient Problems for LOINC Code 2947-0 (Glucose Testing)

| Problem Code | Problem Name | SNOMED Code | Clinical Context |
|--------------|--------------|-------------|-----------------|
| 19928 | [Condition A] | [SNOMED] | [Context] |
| 3668 | [Condition B] | [SNOMED] | [Context] |

Clinical Significance:
- LOINC 2947-0 is a glucose measurement test
- Associated problems indicate potential glucose-related conditions
- SNOMED codes provide standardized medical terminology
```

### Simple Data Queries (Type 2)
**Query:** "What LOINC codes are available in the database?"

**System Processing:**
```
1. Query Analysis:
   ✓ Intent: SQL_REQUIRED (data retrieval)
   ✓ Complexity: LOW
   ✓ SQL Likelihood: 0.90

2. Routing Decision:
   ✓ Route: sql_to_general (with verification)
   ✓ Primary Agent: SQL Agent
   ✓ Secondary Agent: General Agent (verification only)

3. Response Format: Simple list
```

### Knowledge-Based Queries (Type 6)
**Query:** "What does LOINC code 2947-0 represent?"

**System Processing:**
```
1. Query Analysis:
   ✓ Intent: KNOWLEDGE_BASE
   ✓ Complexity: LOW
   ✓ SQL Likelihood: 0.15

2. Routing Decision:
   ✓ Route: general_only
   ✓ Primary Agent: General Agent
   ✓ Secondary Agent: None

3. Response Format: Educational explanation
```

---

## 📊 Routing Confidence Levels

| Query Type | SQL Likelihood | Confidence | Typical Agents |
|------------|---|---|---|
| Complex Medical (Type 1) | 0.95 | HIGH | SQL → General |
| LOINC Discovery (Type 2) | 0.90 | HIGH | SQL → General |
| Patient Problem Analysis (Type 3) | 0.85 | HIGH | SQL → General |
| Relationships (Type 4) | 0.70 | MEDIUM | SQL + General |
| Comparative (Type 5) | 0.80 | HIGH | SQL → General |
| Terminology (Type 6) | 0.15 | MEDIUM | General only |

---

## ✨ How the System Helps

### No Agent Confusion
- **Before**: Users might specify "Use the SQL Agent" or "Use the General Agent"
- **After**: System automatically selects the best agent(s) - users just ask questions

### Intelligent Processing
- **Complex queries** → Uses both agents for thorough analysis
- **Simple queries** → Uses appropriate single agent for efficiency
- **Knowledge questions** → Uses General Agent only
- **Data lookups** → Uses SQL Agent only

### Transparent Processing
- Returns routing information so users understand what happened
- Shows query complexity and confidence
- Displays which agents were used and why

### Accurate Medical Results
- LOINC code 2947-0 correctly identified (Glucose testing)
- Patient problems properly associated (19928, 3668)
- SNOMED codes correctly retrieved and interpreted
- Clinical context automatically generated

---

## 🎯 Try These Queries

### Starter Queries
1. "What LOINC codes are available?"
2. "What is LOINC code 2947-0?"
3. "Show me patient problems"

### Intermediate Queries
1. "List patient problems for LOINC 2947-0"
2. "What are the SNOMED codes for problem 19928?"
3. "Compare LOINC codes in the database"

### Advanced Queries (Like Real Users Will Ask)
1. "Can you provide a list of all Pt-Problems (patient problems) by name for all Tests that have LOINC code 2947-0, and also provide the SNOMED code for each of those patient problems?"
2. "For the patient problems associated with glucose testing, show me their names, SNOMED codes, and medical meanings"
3. "List all tests with LOINC codes, their patient problems, and the SNOMED codes for those problems"

---

## 📝 Notes for Implementation

### Query Router Features
- ✅ Detects query intent automatically
- ✅ Identifies medical codes and concepts
- ✅ Calculates SQL likelihood (0-1 scale)
- ✅ Determines if verification needed
- ✅ Extracts medical concepts
- ✅ Classifies query complexity
- ✅ Routes to optimal agents

### Response Handling
- ✅ Formats responses based on query type
- ✅ Applies medical context automatically
- ✅ Shows generated SQL when relevant
- ✅ Provides structured output for complex queries
- ✅ Maintains conversation memory

### User Experience
- ✅ No need to select agents
- ✅ Just ask questions naturally
- ✅ System handles routing invisibly
- ✅ Results are professional and contextual
- ✅ Medical terminology properly explained

---

**Document Generated**: 2025
**Last Updated**: Implementation complete
**Status**: Ready for user testing ✅
