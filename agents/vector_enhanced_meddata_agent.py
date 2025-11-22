"""
Enhanced MedData Agent with Vector Search
Uses Azure AI Search for semantic understanding before SQL queries
"""
import os
from typing import List, Dict, Any, Optional
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from openai import AzureOpenAI
from dotenv import load_dotenv
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from agents.meddata_agent_wrapper import MedDataAgentWrapper

load_dotenv()


class VectorEnhancedMedDataAgent(MedDataAgentWrapper):
    """MedData Agent enhanced with vector search for better context understanding"""
    
    def __init__(self, *args, **kwargs):
        """Initialize with vector search capabilities"""
        super().__init__(*args, **kwargs)
        
        # Azure AI Search setup
        self.search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
        self.search_key = os.getenv("AZURE_SEARCH_KEY")
        
        if self.search_endpoint and self.search_key:
            self.search_client = SearchClient(
                endpoint=self.search_endpoint,
                index_name="meddata-index",
                credential=AzureKeyCredential(self.search_key)
            )
            self.vector_enabled = True
            print("✅ Vector search enabled for MedData agent")
        else:
            self.search_client = None
            self.vector_enabled = False
            print("⚠️  Vector search not configured - using standard SQL agent")
        
        # Azure OpenAI for embeddings
        self.openai_client = AzureOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version="2024-08-01-preview"
        )
        self.embedding_deployment = "text-embedding-3-large"
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text"""
        try:
            response = self.openai_client.embeddings.create(
                input=text,
                model=self.embedding_deployment
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Warning: Could not generate embedding: {e}")
            return None
    
    def vector_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Perform semantic search on vector database"""
        if not self.vector_enabled:
            return []
        
        try:
            # Generate query embedding
            query_vector = self.generate_embedding(query)
            if not query_vector:
                return []
            
            # Search with vector
            results = self.search_client.search(
                search_text=query,  # Hybrid search: text + vector
                vector_queries=[{
                    "vector": query_vector,
                    "k_nearest_neighbors": top_k,
                    "fields": "content_vector"
                }],
                select=["code", "slot_number", "slot_name", "slot_value", "content", "entity_type"],
                top=top_k
            )
            
            return [
                {
                    "code": r.get("code", ""),
                    "slot_number": r.get("slot_number", 0),
                    "slot_name": r.get("slot_name", ""),
                    "slot_value": r.get("slot_value", ""),
                    "content": r.get("content", ""),
                    "entity_type": r.get("entity_type", ""),
                    "score": r.get("@search.score", 0.0)
                }
                for r in results
            ]
        except Exception as e:
            print(f"Vector search error: {e}")
            return []
    
    def build_context_from_vector_results(self, vector_results: List[Dict]) -> str:
        """Build context string from vector search results"""
        if not vector_results:
            return ""
        
        context_parts = ["Based on semantic search of the MedData database:\n"]
        
        # Group by entity type
        by_type = {}
        for result in vector_results:
            entity_type = result.get("entity_type", "UNKNOWN")
            if entity_type not in by_type:
                by_type[entity_type] = []
            by_type[entity_type].append(result)
        
        # Add slot definitions
        if "SLOT_DEFINITION" in by_type:
            context_parts.append("\nRelevant Slot Definitions:")
            for item in by_type["SLOT_DEFINITION"]:
                context_parts.append(f"  - Slot {item['slot_number']}: {item['slot_name']}")
        
        # Add medical codes
        if "MEDICAL_CODE" in by_type:
            context_parts.append("\nRelevant Medical Codes:")
            for item in by_type["MEDICAL_CODE"][:3]:  # Top 3
                context_parts.append(f"  - Code {item['code']}: {item['content']}")
        
        # Add relationships
        if "RELATIONSHIP" in by_type:
            context_parts.append("\nRelevant Relationships:")
            for item in by_type["RELATIONSHIP"][:3]:  # Top 3
                context_parts.append(f"  - {item['content']}")
        
        return "\n".join(context_parts)
    
    def process_query(self, question: str, conversation_history: Optional[List] = None) -> str:
        """
        Enhanced query processing with vector search
        1. Search vector DB for semantic understanding
        2. Build context from vector results
        3. Generate SQL query with enhanced context
        4. Execute and return results
        """
        print(f"\n🔍 Processing query: {question}")
        
        # Step 1: Vector search for context
        if self.vector_enabled:
            print("  📊 Step 1: Searching vector database...")
            vector_results = self.vector_search(question, top_k=10)
            
            if vector_results:
                print(f"  ✓ Found {len(vector_results)} relevant vectors")
                
                # Display top results
                for i, result in enumerate(vector_results[:3], 1):
                    print(f"    {i}. [{result['entity_type']}] {result['content'][:80]}...")
                
                # Build context
                vector_context = self.build_context_from_vector_results(vector_results)
                
                # Step 2: Enhance the question with vector context
                enhanced_question = f"""{vector_context}

User Question: {question}

Use the semantic search results above to understand which codes, slots, and relationships are relevant.
Generate SQL queries that leverage this context to answer the question accurately."""
                
                print("\n  🤖 Step 2: Generating SQL with vector context...")
            else:
                print("  ⚠️  No vector results found, proceeding with standard query")
                enhanced_question = question
        else:
            enhanced_question = question
        
        # Step 3: Use base SQL agent to generate and execute query
        print("  💾 Step 3: Executing SQL query...")
        result = super().process_query(enhanced_question, conversation_history)
        
        return result


# Factory function for creating vector-enhanced agent
def create_vector_enhanced_meddata_agent():
    """Create MedData agent with vector search enhancement"""
    from dotenv import load_dotenv
    load_dotenv()
    
    sql_server = os.getenv("MEDDATA_SQL_SERVER")
    sql_database = os.getenv("MEDDATA_SQL_DATABASE")
    use_azure_ad = os.getenv("MEDDATA_USE_AZURE_AD", "true").lower() == "true"
    
    azure_openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_openai_api_key = os.getenv("AZURE_OPENAI_API_KEY")
    azure_openai_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    
    if not all([sql_server, sql_database, azure_openai_endpoint, azure_openai_api_key, azure_openai_deployment]):
        raise ValueError("Missing required environment variables for MedData agent")
    
    return VectorEnhancedMedDataAgent(
        sql_server=sql_server,
        sql_database=sql_database,
        sql_username=None,
        sql_password=None,
        azure_openai_endpoint=azure_openai_endpoint,
        azure_openai_api_key=azure_openai_api_key,
        azure_openai_deployment=azure_openai_deployment,
        use_azure_ad=use_azure_ad
    )


if __name__ == "__main__":
    # Test the vector-enhanced agent
    print("="*80)
    print("Testing Vector-Enhanced MedData Agent")
    print("="*80)
    
    agent = create_vector_enhanced_meddata_agent()
    
    # Test queries
    test_queries = [
        "Show me tests with LOINC code 2947-0",
        "What sodium tests are available in whole blood?",
        "Find all procedures that indicate hyponatremia"
    ]
    
    for query in test_queries:
        print(f"\n{'='*80}")
        result = agent.process_query(query)
        print(f"\nResult:\n{result}")
