# Response Formatting - Visual Examples

## Example 1: Medical Data Analysis Query

### User Question
```
"What patient problems are associated with LOINC code 2947-0?"
```

---

### BEFORE (Plain Text Only)
```
Here is my analysis and response based on the ACTUAL DATA RESULTS provided:
---
### 1. Analysis of the Data
The dataset includes 204 rows of results, all pertaining to tests with the LOINC code 2947-0, 
which corresponds to tests measuring blood sodium levels.

#### Key Observations:
- Test Name and Codes:
  - Two tests are associated with the LOINC code:
    - Test Code 111465: "BKR (CM) Result: Sodium Whole Blood POC."
    - Test Code 112423: "BKR (CM) Result: Sodium WB."
- Patient Problem Names (Pt-Problems):
  - Only two unique Pt-Problem names are present across the dataset:
    - Hypernatremia (elevated sodium levels in blood).
    - Hyponatremia (reduced sodium levels in blood).

### 2. Extract Key Findings
The data reveals the following important points:
1. Unique Pt-Problems: There are only two Pt-Problem names related to the tests with LOINC code 2947-0:
   - Hypernatremia
   - Hyponatremia
2. Relationship Between Tests and Pt-Problems: Both test codes (111465 and 112423) are linked to 
   the same two Pt-Problems, confirming consistent patterns.

### 3. Direct Answer to the Question
| Patient Problem (Pt-Problem Name) |
|---|
| Hypernatremia |
| Hyponatremia |

### 4. Medical Context and Explanation
LOINC Code 2947-0
- LOINC (Logical Observation Identifiers Names and Codes) is a globally recognized standard 
  for coding laboratory and clinical tests.
- The specific LOINC code 2947-0 represents "Sodium [Moles/volume] in Blood."
```

**Issues**:
❌ Hard to scan
❌ No visual hierarchy
❌ Paragraph walls
❌ Tables not styled
❌ No formatting
❌ Cluttered appearance

---

### AFTER (With Formatting)

```
═══════════════════════════════════════════════════════════════════════════

🌐 General Agent

═══════════════════════════════════════════════════════════════════════════

Analysis of the Data
───────────────────────────────────────────────────────────────────────────

The dataset includes 204 rows of results, all pertaining to tests with 
the LOINC code 2947-0, which corresponds to tests measuring blood sodium 
levels.

Key Observations

Test Name and Codes
  • Two tests are associated with the LOINC code:
    ◦ Test Code 111465: "BKR (CM) Result: Sodium Whole Blood POC."
    ◦ Test Code 112423: "BKR (CM) Result: Sodium WB."

Patient Problem Names
  • Only two unique Pt-Problem names are present:
    ◦ Hypernatremia (elevated sodium levels)
    ◦ Hyponatremia (reduced sodium levels)

───────────────────────────────────────────────────────────────────────────

Extract Key Findings
───────────────────────────────────────────────────────────────────────────

The data reveals the following important points:

  1. Unique Pt-Problems: There are only two Pt-Problem names related to 
     tests with LOINC code 2947-0:
     • Hypernatremia
     • Hyponatremia

  2. Relationship Between Tests and Pt-Problems: Both test codes (111465 
     and 112423) are linked to the same two Pt-Problems, confirming 
     consistent patterns.

───────────────────────────────────────────────────────────────────────────

Direct Answer to the Question
───────────────────────────────────────────────────────────────────────────

┌──────────────────────────┐
│ Patient Problem          │
├──────────────────────────┤
│ Hypernatremia            │
├──────────────────────────┤
│ Hyponatremia             │
└──────────────────────────┘

───────────────────────────────────────────────────────────────────────────

Medical Context and Explanation
───────────────────────────────────────────────────────────────────────────

LOINC Code 2947-0

• LOINC (Logical Observation Identifiers Names and Codes) is a globally 
  recognized standard for coding laboratory and clinical tests.

• The specific LOINC code 2947-0 represents "Sodium [Moles/volume] in 
  Blood."

• Sodium is a critical electrolyte involved in regulating fluid balance, 
  nerve function, and muscle contraction. Accurate measurement of blood 
  sodium levels is important in diagnosing various medical conditions.

Patient Problems

  1. Hypernatremia
     Definition: Elevated blood sodium levels (above 135-145 mmol/L)
     Causes: Dehydration, excessive sodium intake, diabetes insipidus
     Symptoms: Thirst, confusion, lethargy, muscle twitching

  2. Hyponatremia
     Definition: Low blood sodium levels (below 135 mmol/L)
     Causes: Overhydration, kidney disease, heart failure, liver cirrhosis
     Symptoms: Nausea, headache, confusion, fatigue

───────────────────────────────────────────────────────────────────────────

View SQL Query & Data ▼                                      204 rows returned

[SQL Details Hidden - Click to expand]

═══════════════════════════════════════════════════════════════════════════
```

**Benefits**:
✅ Easy to scan
✅ Clear visual hierarchy
✅ Proper spacing
✅ Professional tables
✅ Clean formatting
✅ Professional appearance

---

## Example 2: Product Listing Query

### User Question
```
"Show me the top 5 most expensive products"
```

---

### BEFORE (Plain Text)
```
Based on the Northwind database, here are the top 5 most expensive products:

1. Côte de Blaye - Price: $263.50 - Category: Beverages
2. Thüringer Rostbratwurst - Price: $123.79 - Category: Meat/Poultry
3. Mishi Kobe Niku - Price: $97.00 - Category: Seafood
4. Sir Rodney's Marmalade - Price: $81.00 - Category: Confections
5. Carnarvon Tigers - Price: $62.50 - Category: Seafood

These are the highest-priced items in the product catalog...
```

**Issues**:
❌ No table structure
❌ Inline data mixed with text
❌ Hard to compare values
❌ Not scannable

---

### AFTER (With Formatting)

```
═══════════════════════════════════════════════════════════════════════════

🌐 General Agent

═══════════════════════════════════════════════════════════════════════════

Top 5 Most Expensive Products
───────────────────────────────────────────────────────────────────────────

Based on the Northwind database, the following products represent the 
highest-priced items in our catalog:

Top Products by Price

┌────────────────────────────┬───────────┬──────────────┐
│ Product Name               │ Price     │ Category     │
├────────────────────────────┼───────────┼──────────────┤
│ Côte de Blaye              │ $263.50   │ Beverages    │
├────────────────────────────┼───────────┼──────────────┤
│ Thüringer Rostbratwurst    │ $123.79   │ Meat/Poultry │
├────────────────────────────┼───────────┼──────────────┤
│ Mishi Kobe Niku            │ $97.00    │ Seafood      │
├────────────────────────────┼───────────┼──────────────┤
│ Sir Rodney's Marmalade     │ $81.00    │ Confections  │
├────────────────────────────┼───────────┼──────────────┤
│ Carnarvon Tigers           │ $62.50    │ Seafood      │
└────────────────────────────┴───────────┴──────────────┘

5 row(s) returned

───────────────────────────────────────────────────────────────────────────

Key Insights

• Price Range: Products range from $62.50 to $263.50
• Categories: Diverse categories represented (Beverages, Meat/Poultry, Seafood, Confections)
• Premium Positioning: These items are premium offerings in their respective categories
• Diversity: Different product types at different price points

───────────────────────────────────────────────────────────────────────────

View SQL Query & Data ▼                                      5 rows returned

[SQL Details Hidden - Click to expand]

═══════════════════════════════════════════════════════════════════════════
```

**Benefits**:
✅ Professional table layout
✅ Easy to scan and compare
✅ Clear columns and rows
✅ Price alignment for comparison
✅ Summary insights
✅ Professional appearance

---

## Example 3: Complex Analysis

### User Question
```
"Analyze customer order patterns and their relationship to product categories"
```

---

### AFTER (With Formatting)

```
═══════════════════════════════════════════════════════════════════════════

🌐 General Agent

═══════════════════════════════════════════════════════════════════════════

Customer Order Patterns Analysis
───────────────────────────────────────────────────────────────────────────

This analysis examines the relationship between customer ordering behavior 
and product category preferences across the Northwind database.

Executive Summary

Based on 830 order records across 89 customers, clear patterns emerge in 
product category preferences and ordering frequency.

═══════════════════════════════════════════════════════════════════════════

1. Order Volume by Category
───────────────────────────────────────────────────────────────────────────

Product categories show significant variation in order volume:

┌─────────────────┬──────────────┬──────────────┐
│ Category        │ Order Count  │ Percentage   │
├─────────────────┼──────────────┼──────────────┤
│ Beverages       │ 145          │ 17.5%        │
├─────────────────┼──────────────┼──────────────┤
│ Dairy Products  │ 128          │ 15.4%        │
├─────────────────┼──────────────┼──────────────┤
│ Seafood         │ 112          │ 13.5%        │
├─────────────────┼──────────────┼──────────────┤
│ Meat/Poultry    │ 98           │ 11.8%        │
├─────────────────┼──────────────┼──────────────┤
│ Confections     │ 92           │ 11.1%        │
├─────────────────┼──────────────┼──────────────┤
│ Other           │ 255          │ 30.7%        │
└─────────────────┴──────────────┴──────────────┘

═══════════════════════════════════════════════════════════════════════════

2. Key Findings
───────────────────────────────────────────────────────────────────────────

Customer Segmentation

  • High-Volume Customers: 12 customers account for 35% of all orders
  • Regular Customers: 34 customers place 2-5 orders per year
  • Occasional Customers: 43 customers place 1 order only

Category Preferences

  • Food Products: Comprise 71% of all orders
  • Beverages: Most popular single category (17.5%)
  • Dairy Products: Second most ordered (15.4%)
  • Specialty Items: Seafood and Meat/Poultry are premium categories

Ordering Patterns

  • Peak Season: Q4 shows 28% higher ordering activity
  • Average Order Value: $1,247 USD
  • Most customers: Prefer small quantity orders (1-3 units per category)

═══════════════════════════════════════════════════════════════════════════

3. Customer Segmentation Summary
───────────────────────────────────────────────────────────────────────────

┌──────────────────┬──────────────┬──────────────┬──────────────┐
│ Segment          │ Count        │ Avg Orders   │ Avg Value    │
├──────────────────┼──────────────┼──────────────┼──────────────┤
│ Premium (VIP)    │ 12           │ 15.2         │ $2,847       │
├──────────────────┼──────────────┼──────────────┼──────────────┤
│ Regular          │ 34           │ 3.8          │ $985         │
├──────────────────┼──────────────┼──────────────┼──────────────┤
│ Occasional       │ 43           │ 1.0          │ $342         │
└──────────────────┴──────────────┴──────────────┴──────────────┘

═══════════════════════════════════════════════════════════════════════════

4. Recommendations
───────────────────────────────────────────────────────────────────────────

Based on this analysis:

  1. Premium Product Focus: Allocate more inventory to Beverages and Dairy 
     Products due to consistent high demand

  2. VIP Customer Program: Implement loyalty program targeting the 12 
     high-volume customers (they represent 35% of revenue)

  3. Seasonal Planning: Prepare for 28% increase in Q4 ordering

  4. Category Expansion: Consider expanding Seafood and Meat/Poultry 
     offerings as premium categories

═══════════════════════════════════════════════════════════════════════════

View SQL Query & Data ▼                                      830 rows analyzed

[SQL Details Hidden - Click to expand]

═══════════════════════════════════════════════════════════════════════════
```

**Benefits**:
✅ Clear section organization
✅ Multiple professional tables
✅ Data easily scannable
✅ Insights highlighted
✅ Recommendations clear
✅ Professional appearance
✅ Easy to present

---

## Formatting Features Demonstrated

### Section Headers
```
═════════════════ (Main Title)
──────────────── (Section breaks)
```

### Lists
```
• Bullet points
  ◦ Sub-items
  ◦ More details

1. Numbered items
2. Ordered points
```

### Tables
```
┌─────────┐
│ Header  │
├─────────┤
│ Data    │
└─────────┘
```

### Text Formatting
```
**Bold text** for emphasis
*Italic* for subtle points
`code` for technical terms
```

---

## Mobile View Comparison

### Desktop (Full Width)
```
┌─────────────────────────────────────────────────────┐
│ [Agent Badge]                                       │
│ Large formatted response with wide table            │
│ ┌───────────────────────────────────────────────┐  │
│ │ Column 1      │ Column 2      │ Column 3      │  │
│ │ Data...       │ Data...       │ Data...       │  │
│ └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

### Mobile (Responsive)
```
┌─────────────────┐
│ [Agent Badge]   │
│ Formatted text  │
│ reflows nicely  │
│                 │
│ ┌─────────────┐ │
│ │ Col 1|Col 2 │ │
│ │ Data | Data │ │
│ └─────────────┘ │
│ (Scrollable)    │
└─────────────────┘
```

---

## Summary

The formatting system transforms responses from:
- **Plain text** → **Professional formatted content**
- **Unstructured** → **Well-organized sections**
- **Hard to read** → **Easy to scan**
- **Cluttered** → **Clean and professional**

Users receive polished, end-user-friendly responses that are easy to understand and present!
