# Quick Reference: Automatic Query Routing

## What Happened?
The system now **automatically selects the best agent for any query**. Users no longer need to specify which agent to use - just ask questions naturally.

---

## Key Changes

| Component | Status | What Changed |
|-----------|--------|-------------|
| `query_router.py` | ✨ NEW | Intelligent query analysis and routing engine |
| `app.py` | 📝 UPDATED | Added routing analysis, +30 lines |
| `templates/index.html` | 📝 UPDATED | Medical queries, routing badges, +50 lines |
| Documentation | ✨ NEW | 3 new comprehensive guides |

---

## How It Works (Simple Version)

```
User Question
    ↓
System Analyzes:
  • What are you asking?
  • Do you need data?
  • How complex is it?
  • What medical codes?
    ↓
System Decides:
  • SQL Agent only? 
  • General Agent only?
  • Both agents?
    ↓
System Processes:
  • Executes through selected agent(s)
  • Formats professional response
  • Shows routing info
    ↓
User Gets Answer
(Never thinks about agents)
```

---

## Query Types Supported

### ✅ Complex Medical Queries
"Can you provide a list of all Pt-Problems (patient problems) by name for all Tests that have LOINC code 2947-0, and also provide the SNOMED code for each?"
- **Routing:** SQL Agent + General Agent
- **Complexity:** HIGH
- **Confidence:** 95%+

### ✅ Simple Data Lookups
"What LOINC codes are available?"
- **Routing:** SQL Agent only
- **Complexity:** LOW
- **Confidence:** 90%+

### ✅ Knowledge Questions
"What is LOINC code 2947-0?"
- **Routing:** General Agent only
- **Complexity:** LOW
- **Confidence:** 85%+

### ✅ Aggregation Queries
"How many tests have LOINC code 2947-0?"
- **Routing:** SQL Agent only
- **Complexity:** LOW
- **Confidence:** 92%+

### ✅ Relationship Queries
"What patient problems are related to glucose testing?"
- **Routing:** SQL Agent + General Agent
- **Complexity:** MEDIUM
- **Confidence:** 85%+

### ✅ Comparative Queries
"Compare LOINC codes in the database"
- **Routing:** SQL Agent + General Agent
- **Complexity:** MEDIUM-HIGH
- **Confidence:** 80%+

---

## What You See in Responses

### Response Badge
```
✓ Auto-Routed | SQL Agent + General Agent | Complexity: HIGH | Confidence: 95%
```

### Meaning:
- ✓ Auto-Routed = Automatic routing decision made
- Agents Used = Which ones processed your query
- Complexity = LOW / MEDIUM / HIGH
- Confidence = How sure system is (0-100%)

---

## Files to Know About

| File | Purpose |
|------|---------|
| `query_router.py` | The routing brain - analyzes and routes queries |
| `AUTOMATIC_ROUTING_GUIDE.md` | Complete technical documentation |
| `SAMPLE_QUESTIONS.md` | Example queries and expected behavior |
| `AUTOMATIC_ROUTING_UPDATE.md` | What changed and why |
| `app.py` | Updated Flask backend with routing |
| `templates/index.html` | Updated web UI with medical examples |

---

## Testing Queries

### Try These to See Routing in Action:

```
1. "Can you provide a list of all Pt-Problems (patient problems) by name 
    for all Tests that have LOINC code 2947-0, and also provide the SNOMED 
    code for each of those patient problems?"
   Expected: AUTO-ROUTED | SQL+GENERAL | HIGH | 95%+

2. "What LOINC codes are available in the database?"
   Expected: AUTO-ROUTED | SQL ONLY | LOW | 90%+

3. "What is LOINC code 2947-0?"
   Expected: AUTO-ROUTED | GENERAL ONLY | LOW | 85%+

4. "How many tests have LOINC code 2947-0?"
   Expected: AUTO-ROUTED | SQL ONLY | LOW | 92%+

5. "What patient problems are related to glucose testing?"
   Expected: AUTO-ROUTED | SQL+GENERAL | MEDIUM | 85%+
```

---

## The Problem It Solves

### Before:
```
User: "Show me Pt-Problems for LOINC 2947-0"
System: "SQL Agent or General Agent?"
User: 😕 "I don't know..."
Result: ❌ Confusion possible
```

### After:
```
User: "Can you provide a list of all Pt-Problems (patient problems) 
       by name for all Tests that have LOINC code 2947-0, and also 
       provide the SNOMED code for each?"

System: [Auto-analyzes]
        [Auto-routes to SQL + General]
        "✓ Auto-Routed | SQL+General | HIGH | 95%"

Result: ✅ Perfect answer, no confusion
```

---

## Key Benefits

✅ **No Agent Confusion** - System picks agents automatically
✅ **Medical Query Support** - Handles LOINC, SNOMED, Pt-Problems
✅ **Intelligent Routing** - Simple queries stay efficient
✅ **Transparent** - Shows what routing was used
✅ **Confident** - Scores show system confidence in decision
✅ **Professional** - Formatted responses with medical context

---

## How to Start

1. **Run server:**
   ```bash
   python app.py
   ```

2. **Open browser:**
   ```
   http://localhost:5002
   ```

3. **Ask question:**
   "What patient problems are for LOINC 2947-0 with SNOMED codes?"

4. **System handles everything:**
   - Analyzes question ✓
   - Routes to SQL Agent ✓
   - Routes to General Agent ✓
   - Formats response ✓
   - Shows routing info ✓

---

## Routing Decisions Explained

### SQL Likelihood Score (0-1)
- **0.9-1.0**: SQL definitely needed (databases query)
- **0.7-0.9**: SQL very likely needed
- **0.5-0.7**: Could go either way
- **0.2-0.5**: SQL probably not needed
- **0.0-0.2**: SQL unlikely (knowledge-based)

### Complexity Score
- **LOW**: Simple, single-criterion queries
- **MEDIUM**: Multiple criteria or moderate complexity
- **HIGH**: Complex multi-step analysis

### Confidence Score (0-1.0)
- **0.9-1.0**: Very confident in routing decision
- **0.7-0.9**: Confident in routing
- **0.5-0.7**: Likely good routing
- **<0.5**: May need review

---

## Medical Concepts Recognized

The system understands:
- **LOINC codes** - Medical test codes (e.g., 2947-0)
- **SNOMED codes** - Medical terminology (e.g., 19928, 3668)
- **Pt-Problems** - Patient conditions/problems
- **ICD codes** - Diagnosis codes
- **CPT codes** - Procedure codes
- And medical terminology in general

---

## Examples of Each Routing Type

### Route: sql_to_general (SQL + General Agents)
Use: Complex medical queries with multi-step analysis
Example: "Pt-Problems for LOINC 2947-0 with SNOMED codes"
Why: Need database for data, General Agent for interpretation

### Route: general_only (General Agent Only)
Use: Knowledge-based questions, definitions, explanations
Example: "What is LOINC code 2947-0?"
Why: No database needed, knowledge-based answer

### Route: sql_only (SQL Agent Only)
Use: Simple data retrieval, lookups, aggregations
Example: "How many tests have LOINC 2947-0?"
Why: Simple database query, no analysis needed

---

## Console Output

When processing a complex query, server shows:
```
[Query Analysis] Route: sql_to_general
  - Agents: SQL Agent + General Agent
  - Strategy: Execute query, analyze, provide context
  - Complexity: high
  - Confidence: 0.95
```

This is the automatic routing decision in action.

---

## Response Includes

Every response now has:
- Answer/Results ✓
- Auto-routing badge ✓
- Agents used ✓
- Complexity level ✓
- Confidence score ✓
- Generated SQL (if used) ✓
- Medical context ✓
- Professional formatting ✓

---

## The Result

**Users simply ask questions.**
**System figures out everything else.**
**No confusion. Professional results.**

---

## Status: ✅ COMPLETE

- [x] Automatic routing implemented
- [x] Medical queries supported
- [x] No agent confusion
- [x] Professional responses
- [x] Documentation complete
- [x] Ready for production

---

**Quick Start**: Run `python app.py` → Go to `http://localhost:5002` → Ask any question
**Deep Dive**: See `AUTOMATIC_ROUTING_GUIDE.md` for technical details
**Examples**: See `SAMPLE_QUESTIONS.md` for query examples
