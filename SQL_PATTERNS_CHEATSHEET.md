# Quick Reference: Multi-Step Query Patterns

## Core Concept: The Semantic Network

The medical ontology is encoded as a **semantic network** where:
- Each CODE = a medical concept (procedure, problem, test, etc.)
- Each (CODE, SLOT_NUMBER, SLOT_VALUE) row = a relationship or attribute
- SLOT_NUMBER = type of relationship/attribute
- SLOT_VALUE = the value or reference to another CODE

```
Example: Procedure 1302 with LOINC 2947-0 indicates problems 3668 and 19928

Row 1: CODE=1302, SLOT_NUMBER=212, SLOT_VALUE='2947-0'     (LOINC code)
Row 2: CODE=1302, SLOT_NUMBER=150, SLOT_VALUE='3668'       (indicates problem 3668)
Row 3: CODE=1302, SLOT_NUMBER=150, SLOT_VALUE='19928'      (indicates problem 19928)
Row 4: CODE=1302, SLOT_NUMBER=6, SLOT_VALUE='Sodium...'    (name)

Row 5: CODE=3668, SLOT_NUMBER=6, SLOT_VALUE='Hypernatr.'  (problem name)
Row 6: CODE=3668, SLOT_NUMBER=266, SLOT_VALUE='39355002'  (SNOMED code)
```

---

## Most Common Slot Numbers

| Slot # | Type | Meaning | Example |
|--------|------|---------|---------|
| 6 | String | Human-readable name | "Sodium Ion" |
| 212 | String | LOINC code | "2947-0" |
| 266 | String | SNOMED code | "39355002" |
| 150 | Reference | Procedure indicates problem | SLOT_VALUE='3668' |
| 149 | Reference | Problem indicated by procedure | SLOT_VALUE='1302' |
| 3 | Reference | Descendant of (hierarchy) | SLOT_VALUE=parent |
| 4 | Reference | Subclass of | SLOT_VALUE=parent |

---

## Multi-Step Query Patterns

### Pattern 1: Forward Relationship (A → B)
**"What problems does this procedure indicate?"**

```sql
-- Step 1: Find procedure with specific LOINC
FROM MED source
WHERE source.SLOT_NUMBER = 212 AND source.SLOT_VALUE = '2947-0'

-- Step 2: Get their relationships (slot 150)
INNER JOIN MED rel ON rel.CODE = source.CODE AND rel.SLOT_NUMBER = 150

-- Step 3: Get the target entity details
INNER JOIN MED target ON target.CODE = rel.SLOT_VALUE
WHERE target.SLOT_NUMBER = 6  -- Get name, or use LEFT JOIN for optional

GROUP BY target.CODE
```

**Key Point:** `rel.SLOT_VALUE` becomes `target.CODE`

---

### Pattern 2: Reverse Relationship (B ← A)
**"What procedures indicate this problem?"**

```sql
-- Step 1: Find problem
FROM MED target
WHERE target.SLOT_NUMBER = 6 AND target.SLOT_VALUE LIKE '%Hypernatr%'

-- Step 2: Find relationships pointing to this problem
INNER JOIN MED rel ON rel.SLOT_VALUE = target.CODE AND rel.SLOT_NUMBER = 150

-- Step 3: Get the procedure details
INNER JOIN MED source ON source.CODE = rel.CODE
WHERE source.SLOT_NUMBER = 212  -- Get LOINC, or use LEFT JOIN for optional

GROUP BY source.CODE
```

**Key Point:** `target.CODE` matches `rel.SLOT_VALUE`, then `rel.CODE` gives source

---

### Pattern 3: Hierarchical (Descendants)
**"Show me all descendants of this concept"**

```sql
FROM MED root
WHERE root.CODE = 'CONCEPT_ID'

INNER JOIN MED descendants ON descendants.SLOT_VALUE = root.CODE 
AND descendants.SLOT_NUMBER = 3  -- DESCENDANT-OF relationship

LEFT JOIN MED names ON names.CODE = descendants.CODE AND names.SLOT_NUMBER = 6

GROUP BY descendants.CODE
```

**Key Point:** Slot 3 = DESCENDANT-OF, slot 4 = SUBCLASS-OF

---

### Pattern 4: Enrichment (Add attributes)
**"Get all attributes for these codes"**

```sql
SELECT entity.CODE,
  MAX(CASE WHEN names.SLOT_NUMBER = 6 THEN names.SLOT_VALUE END) AS Name,
  MAX(CASE WHEN loinc.SLOT_NUMBER = 212 THEN loinc.SLOT_VALUE END) AS LOINC,
  MAX(CASE WHEN snomed.SLOT_NUMBER = 266 THEN snomed.SLOT_VALUE END) AS SNOMED

FROM entity_list entity
LEFT JOIN MED names ON names.CODE = entity.CODE AND names.SLOT_NUMBER = 6
LEFT JOIN MED loinc ON loinc.CODE = entity.CODE AND loinc.SLOT_NUMBER = 212
LEFT JOIN MED snomed ON snomed.CODE = entity.CODE AND snomed.SLOT_NUMBER = 266

GROUP BY entity.CODE
```

**Key Point:** LEFT JOIN preserves rows even if attributes missing

---

## Complete Multi-Step Example

**Question:** "For LOINC 2947-0, show problems, their names, and SNOMED codes"

```sql
SELECT DISTINCT 
  prob.CODE,
  MAX(CASE WHEN pname.SLOT_NUMBER = 6 THEN pname.SLOT_VALUE END) AS Problem_Name,
  MAX(CASE WHEN psnomed.SLOT_NUMBER = 266 THEN psnomed.SLOT_VALUE END) AS SNOMED_Code

FROM MED loinc_ref                    -- Step 1: Find procedures with LOINC
INNER JOIN MED indicates ON 
  loinc_ref.CODE = indicates.CODE     -- Same procedure
  AND indicates.SLOT_NUMBER = 150     -- Indicates relationship

INNER JOIN MED prob ON 
  indicates.SLOT_VALUE = prob.CODE    -- SLOT_VALUE → problem CODE

LEFT JOIN MED pname ON 
  prob.CODE = pname.CODE 
  AND pname.SLOT_NUMBER = 6           -- Get name

LEFT JOIN MED psnomed ON 
  prob.CODE = psnomed.CODE 
  AND psnomed.SLOT_NUMBER = 266       -- Get SNOMED

WHERE 
  loinc_ref.SLOT_NUMBER = 212 
  AND loinc_ref.SLOT_VALUE = '2947-0'

GROUP BY prob.CODE
```

**Steps:**
1. Find procedures with LOINC code (slot 212 = '2947-0')
2. Get their slot 150 relationships (indicates problem)
3. For each SLOT_VALUE (problem CODE), get problem details
4. Left join to get optional attributes (names, SNOMED)
5. GROUP BY to deduplicate

**Result:**
```
prob.CODE | Problem_Name      | SNOMED_Code
----------|-------------------|-------------
3668      | Hypernatremia     | 39355002
19928     | Hyponatremia      | 89627008
```

---

## Common Mistakes & Fixes

### ❌ Mistake 1: Using Wrong Join Direction
```sql
-- WRONG
FROM MED proc 
INNER JOIN MED ind ON proc.CODE = ind.SLOT_VALUE  -- Backwards!

-- CORRECT
FROM MED proc 
INNER JOIN MED ind ON proc.CODE = ind.CODE AND ind.SLOT_NUMBER = 150
```
**Fix:** CODE matches to CODE, then SLOT_NUMBER filters, then SLOT_VALUE connects

---

### ❌ Mistake 2: Missing GROUP BY
```sql
-- WRONG
SELECT prob.CODE, MAX(name.SLOT_VALUE)
FROM ... 

-- CORRECT
SELECT prob.CODE, MAX(name.SLOT_VALUE)
FROM ...
GROUP BY prob.CODE
```
**Fix:** Always GROUP BY when using aggregate functions

---

### ❌ Mistake 3: INNER JOIN on Optional Attributes
```sql
-- WRONG - loses rows without names
FROM problems
INNER JOIN names ON problems.CODE = names.CODE

-- CORRECT
FROM problems
LEFT JOIN names ON problems.CODE = names.CODE
```
**Fix:** Use LEFT JOIN for optional attributes (names, codes, etc.)

---

### ❌ Mistake 4: Missing DISTINCT
```sql
-- WRONG - returns duplicates
SELECT prob.CODE
FROM MED proc
INNER JOIN MED ind ON proc.CODE = ind.CODE AND ind.SLOT_NUMBER = 150
INNER JOIN MED prob ON ind.SLOT_VALUE = prob.CODE

-- CORRECT
SELECT DISTINCT prob.CODE
```
**Fix:** Use DISTINCT when joining multiple times to same table

---

### ❌ Mistake 5: Confusing CODE and SLOT_VALUE
```sql
-- WRONG - treats slot value as if it's the code
WHERE prob.CODE = '2947-0'

-- CORRECT - recognizes LOINC is stored in slot value
WHERE loinc_proc.SLOT_NUMBER = 212 AND loinc_proc.SLOT_VALUE = '2947-0'
```
**Fix:** LOINC/SNOMED codes are in SLOT_VALUE, not CODE

---

## Slot Usage Reference

```
Finding by LOINC code:
  WHERE t.SLOT_NUMBER = 212 AND t.SLOT_VALUE = 'CODE'

Finding by SNOMED code:
  WHERE t.SLOT_NUMBER = 266 AND t.SLOT_VALUE = 'CODE'

Finding by name:
  WHERE t.SLOT_NUMBER = 6 AND t.SLOT_VALUE LIKE '%search%'

Finding relationships (procedure → problem):
  WHERE t.SLOT_NUMBER = 150 AND t.SLOT_VALUE = problem_code

Finding reverse relationships (problem ← procedure):
  WHERE t.SLOT_NUMBER = 149 AND t.SLOT_VALUE = procedure_code

Finding hierarchy (descendants):
  WHERE t.SLOT_NUMBER = 3 AND t.SLOT_VALUE = parent_code

Finding hierarchy (subclasses):
  WHERE t.SLOT_NUMBER = 4 AND t.SLOT_VALUE = parent_code
```

---

## Debugging Checklist

When a query returns 0 rows:

- [ ] Verify SLOT_NUMBER is correct for the relationship
- [ ] Verify SLOT_VALUE format (e.g., '2947-0' with quotes)
- [ ] Check join order: CODE to CODE first, then filter by SLOT_NUMBER
- [ ] Ensure INNER JOINs have required data, use LEFT for optional
- [ ] Use DISTINCT when doing multiple joins
- [ ] Check if relationship actually exists in database
- [ ] Simplify query step-by-step to find where it fails

---

## Performance Tips

1. **Filter early** - WHERE before JOIN
2. **Use specific SLOT_NUMBERs** - Reduces data scanned
3. **Add DISTINCT early** - Prevents duplicate processing
4. **Use TOP N** - Limit results when appropriate
5. **Left JOINs only for optional** - INNER JOINs reduce early when possible

---

## Quick Copy-Paste Templates

### Template 1: Find by Code and Get Details
```sql
SELECT entity.CODE,
  MAX(CASE WHEN a.SLOT_NUMBER = 6 THEN a.SLOT_VALUE END) AS Name,
  MAX(CASE WHEN b.SLOT_NUMBER = 212 THEN b.SLOT_VALUE END) AS LOINC,
  MAX(CASE WHEN c.SLOT_NUMBER = 266 THEN c.SLOT_VALUE END) AS SNOMED
FROM MED entity
LEFT JOIN MED a ON entity.CODE = a.CODE AND a.SLOT_NUMBER = 6
LEFT JOIN MED b ON entity.CODE = b.CODE AND b.SLOT_NUMBER = 212
LEFT JOIN MED c ON entity.CODE = c.CODE AND c.SLOT_NUMBER = 266
WHERE entity.SLOT_NUMBER = 212 AND entity.SLOT_VALUE = '[CODE]'
GROUP BY entity.CODE
```

### Template 2: Forward Relationship Chain
```sql
SELECT DISTINCT target.CODE,
  MAX(CASE WHEN tn.SLOT_NUMBER = 6 THEN tn.SLOT_VALUE END) AS Name
FROM MED source
INNER JOIN MED rel ON source.CODE = rel.CODE AND rel.SLOT_NUMBER = [SLOT#]
INNER JOIN MED target ON target.CODE = rel.SLOT_VALUE
LEFT JOIN MED tn ON target.CODE = tn.CODE AND tn.SLOT_NUMBER = 6
WHERE source.SLOT_NUMBER = [SLOT#] AND source.SLOT_VALUE = '[VALUE]'
GROUP BY target.CODE
```

### Template 3: Hierarchical Traversal
```sql
SELECT DISTINCT child.CODE,
  MAX(CASE WHEN cn.SLOT_NUMBER = 6 THEN cn.SLOT_VALUE END) AS Name
FROM MED parent
INNER JOIN MED hier ON hier.SLOT_VALUE = parent.CODE AND hier.SLOT_NUMBER = 3
INNER JOIN MED child ON child.CODE = hier.CODE
LEFT JOIN MED cn ON child.CODE = cn.CODE AND cn.SLOT_NUMBER = 6
WHERE parent.CODE = '[PARENT_CODE]'
GROUP BY child.CODE
```

---

**Last Updated:** November 22, 2025  
**Use With:** Medical Ontology Query System - Multi-Step Query Support
