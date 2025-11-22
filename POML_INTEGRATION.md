# POML Integration for Medical Ontology Query System

## Overview

This system integrates **POML (Prompt Optimization Markup Language)** to provide advanced prompt engineering for querying a medical ontology database with a slot-based structure.

**POML Documentation**: https://microsoft.github.io/poml/latest/

## What is POML?

POML is Microsoft's framework for creating structured, maintainable, and optimized prompts for Large Language Models (LLMs). It uses XML-like markup to organize prompt components including:

- **System roles and context**
- **Knowledge base structures**
- **Reasoning guidelines**
- **Output formatting rules**
- **Examples and patterns**

## Medical Ontology Database Structure

The MedData database uses a **slot-based architecture** where medical concepts are represented as:

### Tables
- **MED**: Medical concepts with attribute-value pairs
  - `CODE`: Unique identifier for medical concepts
  - `SLOT_NUMBER`: Type of attribute (references MED_SLOTS)
  - `SLOT_VALUE`: The actual value for this attribute

- **MED_SLOTS**: Definitions of slot semantics
  - `SLOT_NUMBER`: Unique slot identifier
  - `SLOT_NAME`: Name and data type of the slot

### Key Slot Types

| Slot # | Name | Purpose |
|--------|------|---------|
| 3 | DESCENDANT-OF | Hierarchical relationships |
| 4 | SUBCLASS-OF | Classification relationships |
| 6 | PRINT-NAME | Human-readable concept names |
| 9 | CPMC-LAB-PROC-CODE | Institutional procedure codes |
| 15 | MEASURED-BY-PROCEDURE | Test-procedure relationships |
| 16 | ENTITY-MEASURED | What the test measures |
| 20 | CPMC-LAB-TEST-CODE | Institutional test codes |
| 149 | PT-PROBLEM-(INDICATED-BY)->PROCEDURE | Clinical indications |
| 150 | PROCEDURE-(INDICATES)->PT-PROBLEM | Diagnostic implications |
| 212 | LOINC-CODE | Standardized LOINC codes |
| 264 | MILLENNIUM-LAB-CODE | System-specific codes |
| 266 | SNOMED-CODE | SNOMED CT codes |
| 277 | EPIC-COMPONENT-ID | EHR integration codes |

## POML System Prompt Structure

The system uses a comprehensive POML prompt that includes:

```xml
<system>
<role>Medical Ontology Query Expert</role>
<context>
  <knowledge_base_structure>
    Database schema and slot definitions
  </knowledge_base_structure>
  
  <query_patterns>
    Common medical query patterns and strategies
  </query_patterns>
  
  <reasoning_guidelines>
    SQL generation best practices for ontology
  </reasoning_guidelines>
  
  <output_format>
    Medical response formatting rules
  </output_format>
</context>
</system>
```

## How POML Enhances the System

### 1. **Context-Aware SQL Generation**
POML provides the LLM with:
- Complete database schema understanding
- Slot semantic meanings
- Common query patterns
- JOIN strategies for slot-based data

### 2. **Medical Domain Expertise**
The prompt instructs the LLM to:
- Recognize standard medical codes (LOINC, SNOMED)
- Understand hierarchical relationships
- Interpret clinical indications
- Use appropriate medical terminology

### 3. **Structured Reasoning**
POML guidelines ensure:
- Proper JOIN usage (MED + MED_SLOTS)
- Fuzzy text matching for searches
- Semantic understanding of multi-attribute concepts
- Prioritization of standardized codes

### 4. **Response Quality**
Formatting instructions produce:
- Clear medical explanations
- Highlighted standard codes
- Grouped related attributes
- Accessible language with accurate terminology

## Implementation

### Location
The POML prompt is defined in: `meddata_sql_agent.py`

```python
MEDICAL_ONTOLOGY_SYSTEM_PROMPT = """
<system>
<role>Medical Ontology Query Expert</role>
...
</system>
"""
```

### Usage
The agent automatically applies the POML prompt when:

1. **Generating SQL Queries**
   ```python
   messages = [
       {"role": "system", "content": MEDICAL_ONTOLOGY_SYSTEM_PROMPT},
       {"role": "system", "content": "Database Schema: ..."},
       {"role": "user", "content": user_question}
   ]
   ```

2. **Formatting Responses**
   ```python
   messages = [
       {"role": "system", "content": MEDICAL_ONTOLOGY_SYSTEM_PROMPT},
       {"role": "system", "content": "Formatting guidelines..."},
       {"role": "user", "content": "Format these results..."}
   ]
   ```

### Configuration
POML is enabled by default. To disable:
```python
agent = MedDataSQLAgent(..., use_poml=False)
```

## Example Queries

### 1. Find Tests by LOINC Code
**Query**: "Show me all tests with LOINC code 2947-0"

**POML Impact**:
- Recognizes LOINC as slot 212
- Joins MED_SLOTS to show slot names
- Includes PRINT-NAME for readability
- Groups related attributes

### 2. Hierarchical Relationships
**Query**: "What are the descendants of code 19928?"

**POML Impact**:
- Identifies DESCENDANT-OF (slot 3)
- Constructs recursive or multi-level query
- Explains parent-child relationships

### 3. Clinical Indications
**Query**: "What problems are indicated by procedure code 1302?"

**POML Impact**:
- Recognizes diagnostic relationship (slot 150)
- Retrieves related problem codes
- Explains clinical significance

## Benefits

1. **Accuracy**: Structured prompts reduce hallucinations and improve SQL correctness
2. **Consistency**: Standard format ensures predictable behavior
3. **Maintainability**: Easy to update domain knowledge without code changes
4. **Explainability**: Clear reasoning guidelines make LLM decisions transparent
5. **Extensibility**: New slots or query patterns can be added to POML sections

## Best Practices

### When to Update POML
- Adding new slot types to the database
- Discovering new query patterns
- Improving medical terminology usage
- Enhancing response formatting

### POML Maintenance
1. Keep `<knowledge_base_structure>` synchronized with database schema
2. Add common query patterns to `<query_patterns>`
3. Document SQL best practices in `<reasoning_guidelines>`
4. Refine `<output_format>` based on user feedback

### Testing
Test POML changes with representative queries:
```python
agent = create_meddata_agent_from_env()
result = agent.query("Find sodium tests with LOINC 2947-0")
print(result['sql'])  # Verify SQL quality
print(result['response'])  # Verify response clarity
```

## Future Enhancements

1. **Dynamic Slot Discovery**: Auto-generate slot descriptions from database
2. **Query Templates**: Pre-defined POML templates for common medical searches
3. **Multi-language Support**: POML sections for different human languages
4. **Feedback Loop**: Collect user feedback to refine POML prompts
5. **A/B Testing**: Compare POML vs non-POML performance metrics

## Resources

- **POML Documentation**: https://microsoft.github.io/poml/latest/
- **Medical Ontology Guide**: See `README.md` for database structure
- **Slot Definitions**: Query `SELECT * FROM MED_SLOTS` for current slots
- **Example Queries**: See `DEMO_GUIDE.md` for medical query examples

## Support

For questions about POML integration:
1. Review POML documentation
2. Check `meddata_sql_agent.py` for prompt structure
3. Test with sample queries
4. Consult medical domain experts for terminology validation
