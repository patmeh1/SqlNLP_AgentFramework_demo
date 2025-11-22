# Quick Start: MedData Vector Search Setup

This guide will help you quickly set up vector search for the MedData agent.

## 🚀 Quick Setup (5 minutes)

### Step 1: Install Dependencies

```bash
pip install azure-search-documents==11.4.0
```

### Step 2: Create Azure AI Search Service

**Option A: Automated Setup (Recommended)**
```bash
python setup_azure_search.py
```
This interactive script will:
- Check your Azure CLI login
- List your resource groups
- Create a new Azure AI Search service
- Retrieve the admin key
- Update your .env file automatically

**Option B: Manual Setup**
```bash
# Create search service
az search service create \
  --name meddata-search \
  --resource-group <your-rg> \
  --sku basic

# Get admin key
az search admin-key show \
  --service-name meddata-search \
  --resource-group <your-rg>

# Add to .env:
# AZURE_SEARCH_ENDPOINT=https://meddata-search.search.windows.net
# AZURE_SEARCH_KEY=<your-key>
```

### Step 3: Vectorize MedData Database

```bash
python setup_meddata_vector.py
```

This will:
- ✅ Create search index with vector fields
- ✅ Extract 13 slot definitions
- ✅ Extract 35 medical codes
- ✅ Extract relationships
- ✅ Generate embeddings for all content
- ✅ Upload ~300 documents to Azure AI Search

**Expected time:** 2-3 minutes

### Step 4: Test Vector Search

```bash
python agents/vector_enhanced_meddata_agent.py
```

## 📊 What Gets Vectorized?

### 1. Slot Definitions (13 documents)
```
Slot 212: LOINC-CODE,STRING
Slot 6: PRINT-NAME,STRING
Slot 150: PROCEDURE-(INDICATES)->PT-PROBLEM,SEMANTIC
...
```

### 2. Medical Codes (35 documents)
```
Code 1302: Stat Whole Blood Sodium Ion Measurement
- LOINC Code: 2947-0
- Descendant of: 32180
- Subclass of: 32180
```

### 3. Relationships (~250 documents)
```
Code 1302 has relationship 'descendant of' with code 32180
Code 1302 has relationship 'indicates problem' with code 19928
...
```

## 🧪 Testing the System

### Test 1: Simple LOINC Query
```python
query = "Show me tests with LOINC code 2947-0"

# Vector search finds:
# - Slot 212 (LOINC-CODE)
# - 11 codes with this LOINC
# - Relevant test names

# SQL generated automatically:
# SELECT m1.CODE, m2.SLOT_VALUE as TestName
# FROM MED m1
# JOIN MED m2 ON m1.CODE = m2.CODE AND m2.SLOT_NUMBER = 6
# WHERE m1.SLOT_NUMBER = 212 AND m1.SLOT_VALUE = '2947-0'
```

### Test 2: Semantic Query
```python
query = "What sodium tests are in whole blood?"

# Vector search finds:
# - Codes with "sodium" and "whole blood" in names
# - Test hierarchy relationships
# - Relevant procedures

# SQL generated with semantic understanding
```

### Test 3: Relationship Query
```python
query = "Which problems are indicated by sodium tests?"

# Vector search finds:
# - Slot 150 (problem relationships)
# - Sodium test codes
# - Problem codes (hyponatremia, hypernatremia)

# SQL joins across relationship slots
```

## 🔄 How It Works

```
┌─────────────────┐
│   User Query    │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│   1. Vector Search              │
│   - Generate query embedding    │
│   - Search Azure AI Search      │
│   - Find top 10 relevant items  │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│   2. Context Building           │
│   - Extract slot definitions    │
│   - Identify relevant codes     │
│   - Map relationships           │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│   3. Enhanced SQL Generation    │
│   - Use LLM with vector context │
│   - Generate accurate SQL       │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│   4. SQL Execution              │
│   - Execute against MedData DB  │
│   - Return results              │
└─────────────────────────────────┘
```

## 📈 Benefits

| Without Vector Search | With Vector Search |
|----------------------|-------------------|
| ❌ Manual schema navigation | ✅ Automatic schema understanding |
| ❌ Keyword-only matching | ✅ Semantic understanding |
| ❌ Brittle queries | ✅ Robust context-aware queries |
| ❌ Limited to exact matches | ✅ Handles synonyms and variations |
| ⏱️ Slower development | ⚡ Faster, more accurate |

## 🔧 Troubleshooting

### "AZURE_SEARCH_ENDPOINT not set"
Run `python setup_azure_search.py` or manually add to `.env`

### "Could not generate embedding"
Ensure `text-embedding-3-large` is deployed in your Azure OpenAI:
```bash
az cognitiveservices account deployment list \
  --name <your-openai-resource> \
  --resource-group <your-rg>
```

### "Index not found"
Run `python setup_meddata_vector.py` to create and populate the index

### Vector search returns no results
Check document count:
```python
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

client = SearchClient(
    endpoint="https://<your-service>.search.windows.net",
    index_name="meddata-index",
    credential=AzureKeyCredential("<your-key>")
)

print(f"Documents: {client.get_document_count()}")
```

## 💰 Cost Estimate

- **Azure AI Search (Basic)**: $75/month
- **Embeddings (text-embedding-3-large)**: 
  - Initial setup: ~$0.004 (one-time)
  - Per query: ~$0.000003
- **Total**: ~$75/month

## 📚 Next Steps

1. **Integrate with Orchestrator**
   ```python
   # In agents/create_meddata_agent.py
   from agents.vector_enhanced_meddata_agent import create_vector_enhanced_meddata_agent
   
   def create_meddata_agent_from_env():
       return create_vector_enhanced_meddata_agent()
   ```

2. **Test with Flask App**
   ```bash
   python app.py
   # Navigate to http://localhost:5000
   # Ask: "Meddata - show me sodium tests with LOINC 2947-0"
   ```

3. **Monitor Performance**
   - Check Azure AI Search metrics in Azure Portal
   - Review query latency and accuracy
   - Adjust `top_k` parameter if needed

4. **Expand Vectorization**
   - Add more entity types (results, units, etc.)
   - Include historical data
   - Add user feedback for continuous improvement

## 🎯 Success Criteria

✅ Azure AI Search service created
✅ ~300 documents indexed with vectors
✅ Test queries return relevant results
✅ SQL queries are more accurate
✅ Agent understands semantic intent

---

**Need help?** See full documentation in `VECTOR_SEARCH_SETUP.md`
