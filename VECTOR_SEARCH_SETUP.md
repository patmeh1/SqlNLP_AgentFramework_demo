# Vector Search Setup for MedData Agent

This guide explains how to set up vector search capabilities for the MedData agent using Azure AI Search.

## Architecture

```
User Query
    ↓
1. Vector Search (Azure AI Search)
   - Semantic understanding of query
   - Find relevant codes, slots, relationships
    ↓
2. Context Building
   - Extract relevant schema information
   - Identify key medical codes
   - Map relationships
    ↓
3. SQL Query Generation
   - Enhanced with vector search context
   - More accurate queries
    ↓
4. SQL Execution (Azure SQL Database)
   - Execute against MedData database
    ↓
5. Return Results
```

## Prerequisites

1. **Azure AI Search Service**
   - Create an Azure AI Search resource
   - Note the endpoint and admin key

2. **Azure OpenAI Embeddings**
   - Deploy `text-embedding-3-large` model
   - Note the deployment name

3. **Required Python Packages**
   ```bash
   pip install azure-search-documents azure-identity
   ```

## Setup Steps

### Step 1: Create Azure AI Search Service

```bash
# Using Azure CLI
az search service create \
  --name <your-search-service-name> \
  --resource-group <your-resource-group> \
  --sku basic \
  --partition-count 1 \
  --replica-count 1

# Get admin key
az search admin-key show \
  --service-name <your-search-service-name> \
  --resource-group <your-resource-group>
```

Or create via Azure Portal:
1. Go to Azure Portal
2. Create new resource → "Azure AI Search"
3. Choose Basic tier for testing
4. After creation, go to Keys section
5. Copy the Primary admin key

### Step 2: Update .env Configuration

Add these lines to your `.env` file:

```properties
# Azure AI Search Configuration
AZURE_SEARCH_ENDPOINT=https://<your-search-service>.search.windows.net
AZURE_SEARCH_KEY=<your-admin-key>
```

### Step 3: Deploy Text Embedding Model

If not already deployed:

```bash
# Deploy text-embedding-3-large
az cognitiveservices account deployment create \
  --name <your-openai-resource> \
  --resource-group <your-resource-group> \
  --deployment-name text-embedding-3-large \
  --model-name text-embedding-3-large \
  --model-version "1" \
  --model-format OpenAI \
  --sku-capacity 120 \
  --sku-name "Standard"
```

Or via Azure OpenAI Studio:
1. Go to your Azure OpenAI resource
2. Navigate to "Deployments"
3. Create new deployment
4. Select `text-embedding-3-large`
5. Set capacity (e.g., 120K tokens/min)

### Step 4: Run Vectorization Script

```bash
# This will:
# 1. Create Azure AI Search index
# 2. Extract data from MedData SQL database
# 3. Generate embeddings for all content
# 4. Upload to Azure AI Search
python setup_meddata_vector.py
```

Expected output:
```
================================================================================
MedData Vectorization Setup
================================================================================

📊 Creating Azure AI Search index...
✅ Search index 'meddata-index' created successfully

📥 Extracting data from MedData database...
  - Vectorizing slot definitions...
    ✓ Created 13 slot definition vectors
  - Vectorizing medical codes...
    ✓ Created 35 medical code vectors
  - Vectorizing relationships...
    ✓ Created XX relationship vectors

✅ Total documents to index: XXX

📤 Uploading XXX documents to Azure AI Search...
  - Valid documents with vectors: XXX
  - Uploaded batch 1: 100/100 succeeded
  ...
✅ Upload complete!

🔍 Testing search with query: 'tests with LOINC code 2947-0'
Top 5 results:
...
✅ Vectorization setup complete!
```

### Step 5: Update Orchestrator to Use Vector-Enhanced Agent

Modify `agents/create_meddata_agent.py`:

```python
from agents.vector_enhanced_meddata_agent import create_vector_enhanced_meddata_agent

def create_meddata_agent_from_env():
    """Create MedData agent with vector search"""
    return create_vector_enhanced_meddata_agent()
```

### Step 6: Test Vector Search

```bash
python agents/vector_enhanced_meddata_agent.py
```

## How It Works

### 1. Vector Search Process

When a user asks a question:

```python
query = "What sodium tests have LOINC code 2947-0?"

# Step 1: Generate query embedding
query_vector = generate_embedding(query)

# Step 2: Search vector database
results = search_client.search(
    search_text=query,
    vector_queries=[{
        "vector": query_vector,
        "k_nearest_neighbors": 10,
        "fields": "content_vector"
    }]
)

# Results include:
# - Relevant slot definitions (e.g., LOINC-CODE slot)
# - Medical codes with sodium tests
# - Relationships between codes
```

### 2. Context Building

Vector results are transformed into context:

```
Based on semantic search of the MedData database:

Relevant Slot Definitions:
  - Slot 212: LOINC-CODE,STRING
  - Slot 6: PRINT-NAME,STRING

Relevant Medical Codes:
  - Code 1302: Stat Whole Blood Sodium Ion Measurement. LOINC Code: 2947-0
  - Code 35978: CPMC Laboratory Test: Sodium, Whole Blood. LOINC Code: 2947-0
  
Relevant Relationships:
  - Code 1302 is descendant of 32180
```

### 3. Enhanced SQL Generation

The SQL agent receives the enriched context and generates accurate queries:

```sql
SELECT m1.CODE, m2.SLOT_VALUE as TestName
FROM MED m1
JOIN MED m2 ON m1.CODE = m2.CODE AND m2.SLOT_NUMBER = 6
WHERE m1.SLOT_NUMBER = 212 AND m1.SLOT_VALUE = '2947-0'
```

## Benefits

✅ **Better Understanding**: Semantic search understands intent, not just keywords
✅ **Accurate Schema Navigation**: Knows which slots and relationships to use
✅ **Improved SQL**: Generates more accurate queries with context
✅ **Handles Ambiguity**: Can disambiguate similar medical terms
✅ **Faster Development**: No need to manually specify schema relationships

## Example Queries

### Query 1: Find Tests by LOINC Code
```
User: "Show me all tests with LOINC code 2947-0"

Vector Search Finds:
- Slot 212 (LOINC-CODE)
- 11 codes with this LOINC value
- Slot 6 (PRINT-NAME) for test names

SQL Generated:
SELECT m1.CODE, m2.SLOT_VALUE as TestName
FROM MED m1
JOIN MED m2 ON m1.CODE = m2.CODE AND m2.SLOT_NUMBER = 6
WHERE m1.SLOT_NUMBER = 212 AND m1.SLOT_VALUE = '2947-0'
```

### Query 2: Find Problems Indicated by Tests
```
User: "What problems are indicated by sodium tests?"

Vector Search Finds:
- Slot 150 (PROCEDURE-(INDICATES)->PT-PROBLEM)
- Codes for sodium tests
- Problem codes (hyponatremia, hypernatremia)

SQL Generated:
SELECT DISTINCT m1.CODE, m2.SLOT_VALUE as TestName, m3.SLOT_VALUE as Problem
FROM MED m1
JOIN MED m2 ON m1.CODE = m2.CODE AND m2.SLOT_NUMBER = 6
JOIN MED m3 ON m1.CODE = m3.CODE AND m3.SLOT_NUMBER = 150
WHERE m2.SLOT_VALUE LIKE '%Sodium%'
```

## Troubleshooting

### Issue: "AZURE_SEARCH_ENDPOINT not set"
**Solution**: Update `.env` file with your Azure AI Search endpoint

### Issue: "Could not generate embedding"
**Solution**: Ensure `text-embedding-3-large` is deployed in Azure OpenAI

### Issue: "Index not found"
**Solution**: Run `setup_meddata_vector.py` first

### Issue: "No vector results found"
**Solution**: Check that documents were uploaded successfully. Verify with:
```python
from azure.search.documents import SearchClient
client = SearchClient(endpoint, "meddata-index", credential)
result = client.get_document_count()
print(f"Documents in index: {result}")
```

## Cost Considerations

- **Azure AI Search Basic**: ~$75/month
- **Embeddings**: ~$0.13 per 1M tokens
  - Initial setup: ~300 documents × 100 tokens = 30K tokens = $0.004
  - Per query: ~1 query × 20 tokens = $0.000003
- **Total estimated**: ~$75/month + negligible embedding costs

## Next Steps

1. Monitor search quality and adjust top_k parameter
2. Add more entity types (procedures, results, etc.)
3. Implement caching for frequent queries
4. Add user feedback loop to improve results

