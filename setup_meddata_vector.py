"""
Vector Database Setup for MedData
Creates embeddings of MedData schema and sample data for semantic search
"""
import os
import pyodbc
import struct
from azure.identity import DefaultAzureCredential, AzureCliCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchableField,
    SearchField,
    SearchFieldDataType,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchProfile,
    AzureOpenAIVectorizer,
    AzureOpenAIParameters
)
from azure.core.credentials import AzureKeyCredential
from openai import AzureOpenAI
from dotenv import load_dotenv
import json

load_dotenv()

class MedDataVectorizer:
    """Vectorizes MedData database content for semantic search"""
    
    def __init__(self):
        """Initialize vectorizer with Azure services"""
        # Azure OpenAI for embeddings
        self.openai_client = AzureOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version="2024-08-01-preview"
        )
        self.embedding_deployment = "text-embedding-3-large"  # or your embedding model deployment
        
        # Azure AI Search
        self.search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
        self.search_key = os.getenv("AZURE_SEARCH_KEY")
        
        if not self.search_endpoint or not self.search_key:
            raise ValueError("AZURE_SEARCH_ENDPOINT and AZURE_SEARCH_KEY must be set in .env")
        
        self.credential = AzureKeyCredential(self.search_key)
        self.index_name = "meddata-index"
        
    def get_sql_connection(self):
        """Get connection to MedData database"""
        credential = AzureCliCredential()
        token = credential.get_token("https://database.windows.net/.default")
        token_bytes = token.token.encode("utf-16-le")
        token_struct = struct.pack(f'<I{len(token_bytes)}s', len(token_bytes), token_bytes)
        
        connection_string = (
            f"Driver={{ODBC Driver 18 for SQL Server}};"
            f"Server=tcp:{os.getenv('MEDDATA_SQL_SERVER')},1433;"
            f"Database={os.getenv('MEDDATA_SQL_DATABASE')};"
            f"Encrypt=yes;"
            f"TrustServerCertificate=no;"
            f"Connection Timeout=30;"
        )
        
        return pyodbc.connect(connection_string, attrs_before={1256: token_struct})
    
    def create_search_index(self):
        """Create Azure AI Search index with vector support"""
        print("\n📊 Creating Azure AI Search index...")
        
        index_client = SearchIndexClient(
            endpoint=self.search_endpoint,
            credential=self.credential
        )
        
        # Define vector search configuration
        vector_search = VectorSearch(
            profiles=[
                VectorSearchProfile(
                    name="meddata-vector-profile",
                    algorithm_configuration_name="meddata-hnsw"
                )
            ],
            algorithms=[
                HnswAlgorithmConfiguration(
                    name="meddata-hnsw",
                    parameters={
                        "m": 4,
                        "efConstruction": 400,
                        "efSearch": 500,
                        "metric": "cosine"
                    }
                )
            ]
        )
        
        # Define index fields
        fields = [
            SimpleField(name="id", type=SearchFieldDataType.String, key=True),
            SearchableField(name="code", type=SearchFieldDataType.String, filterable=True),
            SearchableField(name="slot_number", type=SearchFieldDataType.Int32, filterable=True),
            SearchableField(name="slot_name", type=SearchFieldDataType.String, filterable=True),
            SearchableField(name="slot_value", type=SearchFieldDataType.String),
            SearchableField(name="content", type=SearchFieldDataType.String),
            SearchableField(name="entity_type", type=SearchFieldDataType.String, filterable=True),
            SearchField(
                name="content_vector",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                vector_search_dimensions=3072,  # text-embedding-3-large dimension
                vector_search_profile_name="meddata-vector-profile"
            )
        ]
        
        # Create the index
        index = SearchIndex(
            name=self.index_name,
            fields=fields,
            vector_search=vector_search
        )
        
        try:
            result = index_client.create_or_update_index(index)
            print(f"✅ Search index '{self.index_name}' created successfully")
            return result
        except Exception as e:
            print(f"❌ Error creating index: {e}")
            raise
    
    def generate_embedding(self, text):
        """Generate embedding for text using Azure OpenAI"""
        try:
            response = self.openai_client.embeddings.create(
                input=text,
                model=self.embedding_deployment
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Warning: Could not generate embedding: {e}")
            return None
    
    def extract_and_vectorize_data(self):
        """Extract data from MedData and create vector embeddings"""
        print("\n📥 Extracting data from MedData database...")
        
        conn = self.get_sql_connection()
        cursor = conn.cursor()
        
        documents = []
        doc_id = 1
        
        # 1. Vectorize slot definitions (schema information)
        print("  - Vectorizing slot definitions...")
        cursor.execute("SELECT SLOT_NUMBER, SLOT_NAME FROM MED_SLOTS ORDER BY SLOT_NUMBER")
        slots = cursor.fetchall()
        
        slot_map = {}
        for slot_num, slot_name in slots:
            slot_map[slot_num] = slot_name
            
            # Create searchable content
            content = f"Slot {slot_num}: {slot_name}. This represents {slot_name.split(',')[0].replace('-', ' ').lower()} information."
            
            doc = {
                "id": f"slot_{slot_num}",
                "code": "",
                "slot_number": slot_num,
                "slot_name": slot_name,
                "slot_value": "",
                "content": content,
                "entity_type": "SLOT_DEFINITION",
                "content_vector": self.generate_embedding(content)
            }
            documents.append(doc)
        
        print(f"    ✓ Created {len(documents)} slot definition vectors")
        
        # 2. Vectorize medical codes with their attributes
        print("  - Vectorizing medical codes...")
        cursor.execute("""
            SELECT DISTINCT CODE FROM MED ORDER BY CODE
        """)
        codes = [row[0] for row in cursor.fetchall()]
        
        for code in codes:
            # Get all attributes for this code
            cursor.execute("""
                SELECT SLOT_NUMBER, SLOT_VALUE 
                FROM MED 
                WHERE CODE = ? 
                ORDER BY SLOT_NUMBER
            """, code)
            
            attributes = cursor.fetchall()
            
            # Build content for embedding
            content_parts = [f"Medical Code: {code}"]
            code_name = ""
            loinc_code = ""
            snomed_code = ""
            
            for slot_num, slot_val in attributes:
                if not slot_val:
                    continue
                    
                slot_name = slot_map.get(slot_num, f"Slot {slot_num}")
                
                if slot_num == 6:  # PRINT-NAME
                    code_name = slot_val
                    content_parts.append(f"Name: {slot_val}")
                elif slot_num == 212:  # LOINC-CODE
                    loinc_code = slot_val
                    content_parts.append(f"LOINC Code: {slot_val}")
                elif slot_num == 266:  # SNOMED-CODE
                    snomed_code = slot_val
                    content_parts.append(f"SNOMED Code: {slot_val}")
                elif slot_num == 3:  # DESCENDANT-OF
                    content_parts.append(f"Descendant of: {slot_val}")
                elif slot_num == 4:  # SUBCLASS-OF
                    content_parts.append(f"Subclass of: {slot_val}")
                elif slot_num == 150:  # PROCEDURE-(INDICATES)->PT-PROBLEM
                    content_parts.append(f"Indicates problem: {slot_val}")
            
            content = ". ".join(content_parts)
            
            # Create document
            doc = {
                "id": f"code_{code}",
                "code": code,
                "slot_number": 0,  # Multiple slots
                "slot_name": code_name,
                "slot_value": loinc_code or snomed_code or "",
                "content": content,
                "entity_type": "MEDICAL_CODE",
                "content_vector": self.generate_embedding(content)
            }
            documents.append(doc)
        
        print(f"    ✓ Created {len(codes)} medical code vectors")
        
        # 3. Create relationship vectors
        print("  - Vectorizing relationships...")
        cursor.execute("""
            SELECT DISTINCT m1.CODE, m1.SLOT_VALUE as TargetCode, ms.SLOT_NAME
            FROM MED m1
            JOIN MED_SLOTS ms ON m1.SLOT_NUMBER = ms.SLOT_NUMBER
            WHERE m1.SLOT_NUMBER IN (3, 4, 150)  -- Relationship slots
            AND m1.SLOT_VALUE != ''
        """)
        
        relationships = cursor.fetchall()
        rel_count = 0
        
        for source_code, target_code, relationship_type in relationships:
            rel_type_clean = relationship_type.split(',')[0].replace('-', ' ').lower()
            content = f"Code {source_code} has relationship '{rel_type_clean}' with code {target_code}"
            
            doc = {
                "id": f"rel_{doc_id}",
                "code": source_code,
                "slot_number": 0,
                "slot_name": relationship_type,
                "slot_value": target_code,
                "content": content,
                "entity_type": "RELATIONSHIP",
                "content_vector": self.generate_embedding(content)
            }
            documents.append(doc)
            doc_id += 1
            rel_count += 1
        
        print(f"    ✓ Created {rel_count} relationship vectors")
        
        conn.close()
        
        print(f"\n✅ Total documents to index: {len(documents)}")
        return documents
    
    def upload_to_search(self, documents):
        """Upload documents to Azure AI Search"""
        print(f"\n📤 Uploading {len(documents)} documents to Azure AI Search...")
        
        search_client = SearchClient(
            endpoint=self.search_endpoint,
            index_name=self.index_name,
            credential=self.credential
        )
        
        # Filter out documents with no vector
        valid_docs = [doc for doc in documents if doc.get("content_vector")]
        print(f"  - Valid documents with vectors: {len(valid_docs)}")
        
        # Upload in batches
        batch_size = 100
        for i in range(0, len(valid_docs), batch_size):
            batch = valid_docs[i:i + batch_size]
            try:
                result = search_client.upload_documents(documents=batch)
                succeeded = sum(1 for r in result if r.succeeded)
                print(f"  - Uploaded batch {i//batch_size + 1}: {succeeded}/{len(batch)} succeeded")
            except Exception as e:
                print(f"  ❌ Error uploading batch: {e}")
        
        print("✅ Upload complete!")
    
    def test_search(self, query):
        """Test semantic search"""
        print(f"\n🔍 Testing search with query: '{query}'")
        
        search_client = SearchClient(
            endpoint=self.search_endpoint,
            index_name=self.index_name,
            credential=self.credential
        )
        
        # Generate query vector
        query_vector = self.generate_embedding(query)
        
        # Perform vector search
        results = search_client.search(
            search_text=None,
            vector_queries=[{
                "vector": query_vector,
                "k_nearest_neighbors": 5,
                "fields": "content_vector"
            }],
            select=["code", "slot_name", "content", "entity_type"]
        )
        
        print("\nTop 5 results:")
        for i, result in enumerate(results, 1):
            print(f"\n{i}. [{result['entity_type']}] Code: {result.get('code', 'N/A')}")
            print(f"   {result['content'][:150]}...")
            print(f"   Score: {result['@search.score']:.4f}")
    
    def run_full_setup(self):
        """Run complete vectorization setup"""
        try:
            print("="*80)
            print("MedData Vectorization Setup")
            print("="*80)
            
            # Create index
            self.create_search_index()
            
            # Extract and vectorize data
            documents = self.extract_and_vectorize_data()
            
            # Upload to search
            self.upload_to_search(documents)
            
            # Test search
            self.test_search("tests with LOINC code 2947-0")
            self.test_search("sodium tests in whole blood")
            
            print("\n" + "="*80)
            print("✅ Vectorization setup complete!")
            print("="*80)
            
        except Exception as e:
            print(f"\n❌ Error during setup: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    vectorizer = MedDataVectorizer()
    vectorizer.run_full_setup()
