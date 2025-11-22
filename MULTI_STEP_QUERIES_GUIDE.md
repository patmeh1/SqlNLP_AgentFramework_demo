# Multi-Step Query Guide for Medical Ontology System

## Overview

The Medical Ontology Query System has been enhanced to handle complex, multi-step queries that require:
1. **Multiple database lookups** - Finding related entities across the database
2. **Relationship traversal** - Following semantic links between concepts
3. **Data enrichment** - Adding names, codes, and classifications
4. **Complex analysis** - Interpreting and explaining relationships

## Architecture for Complex Queries

### Query Processing Pipeline

```
User Question
    ↓
[Query Router] → Determines this needs SQL + General Agent
    ↓
[SQL Agent] → Generates T-SQL query
    ├─ Understands multi-hop relationships
    ├─ Builds complex joins across MED table
    ├─ Includes all semantic enrichment in single query
    └─ Returns complete result set
    ↓
[Database] → Executes SQL, returns results
    ↓
[General Agent] → Analyzes and interprets data
    ├─ Understands medical context
    ├─ Explains relationships and codes
    ├─ Connects data to original question
    ├─ Can suggest follow-up queries
    └─ Returns human-readable explanation
    ↓
[Response] → Formatted with metadata, routing info, SQL query
```

## Multi-Step Query Examples

### Example 1: Find Problems Indicated by a Procedure with Specific LOINC Code

**User Question:** "Can you provide a list of all Pt-Problems (patient problems) by name for all Tests that have LOINC code 2947-0, and also provide the SNOMED code for each of those patient problems?"

**Steps Encoded in Single SQL Query:**
1. Find all procedures with LOINC code 2947-0 (slot 212)
2. Get the codes of those procedures  
3. Use slot 150 to find what problems those procedures indicate
4. For each problem, get its name (slot 6) and SNOMED code (slot 266)
5. Return deduplicated results with all information

**SQL Generation Logic:**
```
FROM MED loinc_ref              -- Find procedures with LOINC
INNER JOIN MED indicates        -- Get their slot 150 relationships
INNER JOIN MED prob             -- Get the problem codes (from SLOT_VALUE)
LEFT JOIN MED pname             -- Get problem names
LEFT JOIN MED psnomed           -- Get SNOMED codes
WHERE loinc_ref.SLOT_NUMBER=212 
  AND loinc_ref.SLOT_VALUE='2947-0'
GROUP BY prob.CODE              -- Remove duplicates
```

**Expected Results:**
- Problem CODE: 3668
  - Name: Hypernatremia
  - SNOMED Code: 39355002
- Problem CODE: 19928
  - Name: Hyponatremia
  - SNOMED Code: 89627008

---

### Example 2: Find All Tests Related to a Specific Problem

**User Question:** "What are all the tests that indicate hypernatremia? Show me their LOINC codes if available."

**Steps:**
1. Find the problem code for "Hypernatremia" (search by name using slot 6)
2. Find all procedures that have slot 150 pointing to this problem
3. For each procedure, get its LOINC code (slot 212)
4. Get procedure names (slot 6)

**Key SQL Pattern:**
```
-- Find all procedures indicating a specific problem
FROM MED prob               -- Find problem by name
INNER JOIN MED indicates    -- Find reverse relationships
ON indicates.SLOT_VALUE = prob.CODE 
AND indicates.SLOT_NUMBER = 150
INNER JOIN MED procedures   -- Get the procedures
ON procedures.CODE = indicates.CODE
```

---

### Example 3: Hierarchical Classification Query

**User Question:** "Show me all the descendants of [medical concept]. Include their names and SNOMED codes."

**Steps:**
1. Find the starting concept by code or name
2. Find all descendants using slot 3 (DESCENDANT-OF)
3. For each descendant, get name and SNOMED code
4. Potentially traverse multiple levels

**Key SQL Pattern:**
```
-- Traverse semantic hierarchy
FROM MED root
INNER JOIN MED descendants 
ON descendants.SLOT_VALUE = root.CODE 
AND descendants.SLOT_NUMBER = 3
LEFT JOIN MED names 
ON descendants.CODE = names.CODE 
AND names.SLOT_NUMBER = 6
```

---

## Understanding the Slot-Based Data Model

### Key Concept: CODE vs SLOT_VALUE

The medical ontology uses a **semantic network** encoded in the MED table:

```
MED Table Structure:
┌──────┬──────────────┬──────────────┐
│ CODE │ SLOT_NUMBER  │ SLOT_VALUE   │
├──────┼──────────────┼──────────────┤
│ 1302 │ 6            │ "Sodium..."  │  ← Name
│ 1302 │ 212          │ "2947-0"     │  ← LOINC Code
│ 1302 │ 150          │ "3668"       │  ← Indicates Problem 3668
│ 1302 │ 150          │ "19928"      │  ← Indicates Problem 19928
│ 3668 │ 6            │ "Hypernat..."│  ← Problem Name
│ 3668 │ 266          │ "39355002"   │  ← SNOMED Code
└──────┴──────────────┴──────────────┘
```

### Relationship Join Pattern

When traversing relationships (e.g., procedures → problems):

```
Step 1: Find the procedure with LOINC code
  table1.CODE = procedure_code
  table1.SLOT_NUMBER = 212
  table1.SLOT_VALUE = '2947-0'

Step 2: Get relationships from this procedure  
  table2.CODE = table1.CODE          ← Same procedure
  table2.SLOT_NUMBER = 150           ← Indicates relationship
  table2.SLOT_VALUE = problem_code   ← Contains related code

Step 3: Get details of related entity
  table3.CODE = table2.SLOT_VALUE    ← SLOT_VALUE becomes CODE
  table3.SLOT_NUMBER = 6             ← Get name or other attribute
```

---

## SQL Generation for Complex Queries

### Rules for Multi-Step Queries

1. **Start with Base Entity**
   - Find the starting entity (procedure, test, problem) using specific criteria
   - Use WHERE clause early to filter

2. **Traverse Relationships**
   - Join to find related entities through slot relationships
   - Remember: SLOT_VALUE points to the related CODE
   - Use INNER JOIN for required relationships, LEFT JOIN for optional

3. **Enrich with Attributes**
   - Once you have all entity CODEs, join to get their attributes
   - Names (slot 6), SNOMED codes (slot 266), LOINC codes (slot 212), etc.
   - Use LEFT JOINs for optional attributes

4. **Aggregate and Deduplicate**
   - Use DISTINCT to avoid duplicate rows from multiple joins
   - Use GROUP BY with MAX(CASE WHEN) to get all attributes per entity
   - Result: One row per unique entity with all its attributes

5. **Return Complete Data**
   - Single query that returns all requested information
   - No multiple queries or suggestions for follow-up steps
   - All relationships and enrichment included

---

## System Prompt Enhancements

The SQL Agent's system prompt has been enhanced with:

### 1. Multi-Step Query Patterns
- Examples of hierarchical traversal
- Relationship filtering patterns
- Complex aggregation techniques

### 2. Data Model Understanding
- Explanation of how semantic networks work
- CODE vs SLOT_VALUE semantics
- How relationships are encoded

### 3. Join Logic Documentation
- Detailed join patterns for each relationship type
- Examples of correct and incorrect joins
- Common mistakes and how to avoid them

### 4. Optimization Guidelines
- When to use DISTINCT vs GROUP BY
- How to filter early with WHERE clauses
- When to use TOP N for performance

---

## General Agent Enhancements

The General Agent's analysis prompt has been updated to:

1. **Understand Relationships**
   - Recognize when data shows connections between entities
   - Explain procedure-to-problem relationships clearly
   - Interpret medical codes in context

2. **Provide Clinical Context**
   - Explain medical significance of findings
   - Connect procedures to diagnoses
   - Clarify what procedures measure

3. **Handle Complex Results**
   - Format multi-dimensional data clearly
   - Use tables and bullet points for clarity
   - Group related information logically

4. **Support Follow-Up Queries**
   - Suggest related queries when appropriate
   - Explain data gaps or limitations
   - Help users understand what's possible

---

## Complex Query Examples and Responses

### Example: Multi-Level Relationship Query

**Q:** "For procedures with LOINC code 2947-0, show me all the problems they indicate. For each problem, also show what other procedures indicate the same problem."

**Processing:**
1. SQL Agent generates query that:
   - Finds procedures with LOINC 2947-0
   - Gets problems indicated by these procedures
   - For each problem, finds all other procedures that indicate it
   - Returns procedures with their names, problems, and problem relationships

2. General Agent analyzes results and explains:
   - Which procedures have this LOINC code
   - What problems they indicate
   - Common problems across procedures
   - Shared diagnostic implications

**Response Format:**
```
Based on the data:

**Procedures with LOINC 2947-0 (Sodium):**
- Procedure 1302: Stat Whole Blood Sodium Ion Measurement

**Problems Indicated:**
1. Hypernatremia (CODE: 3668, SNOMED: 39355002)
   - Also indicated by: [other procedures]
   - Clinical significance: [explanation]

2. Hyponatremia (CODE: 19928, SNOMED: 89627008)
   - Also indicated by: [other procedures]
   - Clinical significance: [explanation]
```

---

## Troubleshooting Complex Queries

### Issue: Query Returns 0 Rows

**Common Causes:**
1. **Backwards relationship join** - SLOT_VALUE and CODE mixed up
2. **Wrong slot number** - Using incorrect slot for the relationship
3. **Case sensitivity** - Code values in SQL not matching exactly
4. **Missing relationship** - Not all relationships exist in data

**Solution:**
1. Verify slot number is correct for the relationship
2. Ensure join logic: CODE matches, then SLOT_NUMBER filters, then SLOT_VALUE connects
3. Test with simpler query first to verify data exists

### Issue: Too Many Duplicate Rows

**Common Causes:**
1. **Missing DISTINCT** - Multiple joins to same table create duplicates
2. **Missing GROUP BY** - Aggregate functions without grouping

**Solution:**
1. Add DISTINCT to SELECT
2. Add GROUP BY clause with primary entity CODE
3. Use MAX(CASE WHEN) for all optional attributes

### Issue: Missing Attributes in Results

**Common Cause:**
- Used INNER JOIN instead of LEFT JOIN for optional attributes
- Result: Rows without all attributes filtered out

**Solution:**
- Change to LEFT JOINs for optional attributes
- Rows with NULL values are valid - they represent missing data

---

## Testing Complex Queries

### Test Query 1: Basic Multi-Step
```
Question: "Show me problems indicated by procedures with LOINC 2947-0"
Expected: 2 results (Hypernatremia, Hyponatremia)
Check: Names and SNOMED codes present
```

### Test Query 2: Reverse Relationship
```
Question: "What procedures indicate hypernatremia?"
Expected: Multiple procedures
Check: LOINC codes included for each
```

### Test Query 3: Hierarchical
```
Question: "Show me all descendants of [concept]"
Expected: Full hierarchy
Check: All levels included with names
```

---

## Performance Considerations

1. **Use WHERE Early**: Filter by LOINC or name before joining
2. **Limit Results**: Use TOP N to limit for large result sets
3. **Index Usage**: The database is optimized for CODE and SLOT_NUMBER lookups
4. **Avoid Cartesian Products**: Ensure join conditions are specific

---

## Future Enhancements

Potential improvements for even more complex queries:

1. **Persistent Query Cache**: Store frequently-run query patterns
2. **Query Decomposition**: Break very complex queries into steps with intermediate results
3. **Graph Traversal**: For deep semantic hierarchies
4. **Semantic Similarity**: Find related concepts beyond direct relationships
5. **Temporal Analysis**: If the data includes time-based relationships

---

## Quick Reference: Common Join Patterns

### Pattern 1: Forward Relationships (X indicates/contains Y)
```sql
FROM MED source
INNER JOIN MED rel ON rel.CODE = source.CODE AND rel.SLOT_NUMBER = 150
INNER JOIN MED target ON target.CODE = rel.SLOT_VALUE
```

### Pattern 2: Reverse Relationships (Y is indicated by/contained in X)
```sql
FROM MED target
INNER JOIN MED rel ON rel.SLOT_VALUE = target.CODE AND rel.SLOT_NUMBER = 150
INNER JOIN MED source ON source.CODE = rel.CODE
```

### Pattern 3: Hierarchical (Descendants)
```sql
FROM MED root
INNER JOIN MED desc ON desc.SLOT_VALUE = root.CODE AND desc.SLOT_NUMBER = 3
```

### Pattern 4: Attribute Enrichment
```sql
LEFT JOIN MED names ON names.CODE = entity.CODE AND names.SLOT_NUMBER = 6
LEFT JOIN MED snomed ON snomed.CODE = entity.CODE AND snomed.SLOT_NUMBER = 266
```

---

**Last Updated:** November 22, 2025  
**System:** Medical Ontology Query System with Hybrid Agent Architecture
