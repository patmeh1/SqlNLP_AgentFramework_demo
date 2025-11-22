"""
Intelligent Query Router for Automatic Agent Selection
Routes queries to appropriate agents (SQL or General) without user confusion.
Analyzes query intent and data requirements to select optimal processing path.
"""

from typing import Dict, Any, Optional, List, Tuple
import re
from enum import Enum


class QueryIntent(Enum):
    """Classification of query intent."""
    SQL_REQUIRED = "sql_required"           # Needs database query
    SQL_PREFERRED = "sql_preferred"         # Can use SQL but not required
    KNOWLEDGE_BASE = "knowledge_base"       # General knowledge
    CLARIFICATION = "clarification"         # Asking for explanation
    MEDICAL_LOOKUP = "medical_lookup"       # Lookup medical codes/terms


class QueryRouter:
    """Intelligently routes queries to appropriate agents."""
    
    def __init__(self):
        """Initialize the query router."""
        self.sql_keywords = {
            'data': 1.0, 'database': 1.0, 'query': 0.8, 'list': 0.8,
            'show': 0.7, 'find': 0.7, 'get': 0.7, 'retrieve': 0.9,
            'count': 0.9, 'total': 0.8, 'where': 0.9, 'filter': 0.8,
            'search': 0.7, 'match': 0.7, 'related': 0.7, 'associated': 0.7
        }
        
        self.medical_codes = {
            'loinc': 'medical_code',
            'snomed': 'medical_code',
            'cpt': 'medical_code',
            'icd': 'medical_code',
            'pt-problem': 'medical_concept',
            'patient problem': 'medical_concept',
            'test': 'medical_test',
            'procedure': 'medical_test',
            'diagnosis': 'medical_condition',
            'condition': 'medical_condition'
        }
        
        self.query_indicators = {
            'how many': QueryIntent.SQL_REQUIRED,
            'count': QueryIntent.SQL_REQUIRED,
            'total': QueryIntent.SQL_REQUIRED,
            'list all': QueryIntent.SQL_REQUIRED,
            'show all': QueryIntent.SQL_REQUIRED,
            'what are': QueryIntent.SQL_REQUIRED,
            'provide': QueryIntent.SQL_REQUIRED,
            'retrieve': QueryIntent.SQL_REQUIRED,
            'find': QueryIntent.SQL_PREFERRED,
            'search': QueryIntent.SQL_PREFERRED,
            'compare': QueryIntent.SQL_PREFERRED,
            'difference': QueryIntent.KNOWLEDGE_BASE,
            'explain': QueryIntent.KNOWLEDGE_BASE,
            'what is': QueryIntent.KNOWLEDGE_BASE,
            'why': QueryIntent.KNOWLEDGE_BASE,
            'how': QueryIntent.KNOWLEDGE_BASE
        }
    
    def analyze_query(self, question: str) -> Dict[str, Any]:
        """
        Analyze a query to determine routing and strategy.
        
        Args:
            question: User's natural language question
            
        Returns:
            Dictionary with analysis results
        """
        question_lower = question.lower()
        
        # Detect query intent
        intent = self._detect_intent(question_lower)
        
        # Check for medical code references
        has_medical_codes = self._detect_medical_codes(question_lower)
        
        # Calculate SQL likelihood (0-1)
        sql_likelihood = self._calculate_sql_likelihood(question_lower, intent)
        
        # Determine if results need verification
        needs_verification = self._needs_verification(question_lower, intent)
        
        # Determine optimal routing
        should_use_sql = intent in [
            QueryIntent.SQL_REQUIRED,
            QueryIntent.SQL_PREFERRED,
            QueryIntent.MEDICAL_LOOKUP
        ] or sql_likelihood > 0.6
        
        analysis = {
            'intent': intent.value,
            'has_medical_codes': has_medical_codes,
            'sql_likelihood': sql_likelihood,
            'should_use_sql': should_use_sql,
            'needs_verification': needs_verification,
            'medical_concepts': self._extract_medical_concepts(question_lower),
            'query_type': self._classify_query_type(question_lower),
            'complexity': self._estimate_complexity(question_lower),
            'confidence': self._calculate_confidence(sql_likelihood, intent)
        }
        
        return analysis
    
    def route_query(self, question: str) -> Dict[str, Any]:
        """
        Route a query to the appropriate agent path.
        
        Args:
            question: User's natural language question
            
        Returns:
            Routing recommendation with strategy
        """
        analysis = self.analyze_query(question)
        
        # Determine routing
        if analysis['should_use_sql']:
            routing = {
                'route': 'sql_to_general',
                'primary_agent': 'SQL Agent',
                'secondary_agent': 'General Agent',
                'strategy': 'Execute SQL query, verify results with General Agent',
                'response_type': 'structured_data_with_analysis'
            }
        else:
            routing = {
                'route': 'general_only',
                'primary_agent': 'General Agent',
                'secondary_agent': None,
                'strategy': 'Direct knowledge-based response',
                'response_type': 'knowledge_based'
            }
        
        # Add handling instructions
        routing['instructions'] = self._generate_instructions(analysis)
        routing['analysis'] = analysis
        
        return routing
    
    def _detect_intent(self, question_lower: str) -> QueryIntent:
        """Detect the intent of the query."""
        # Check explicit indicators
        for phrase, intent in self.query_indicators.items():
            if phrase in question_lower:
                return intent
        
        # Default based on content
        if any(medical in question_lower for medical in self.medical_codes.keys()):
            return QueryIntent.MEDICAL_LOOKUP
        
        if any(char in question_lower for char in ['?', 'which', 'where', 'when']):
            return QueryIntent.SQL_PREFERRED
        
        return QueryIntent.KNOWLEDGE_BASE
    
    def _detect_medical_codes(self, question_lower: str) -> bool:
        """Check if query references medical codes or concepts."""
        return any(code in question_lower for code in self.medical_codes.keys())
    
    def _calculate_sql_likelihood(self, question_lower: str, intent: QueryIntent) -> float:
        """Calculate likelihood that SQL is needed (0-1)."""
        score = 0.0
        
        # Base score from intent
        intent_scores = {
            QueryIntent.SQL_REQUIRED: 1.0,
            QueryIntent.SQL_PREFERRED: 0.7,
            QueryIntent.MEDICAL_LOOKUP: 0.8,
            QueryIntent.KNOWLEDGE_BASE: 0.2,
            QueryIntent.CLARIFICATION: 0.1
        }
        score = intent_scores.get(intent, 0.3)
        
        # Adjust based on SQL keywords
        for keyword, weight in self.sql_keywords.items():
            if keyword in question_lower:
                score = min(1.0, score + (weight * 0.1))
        
        # Adjust based on medical codes
        if self._detect_medical_codes(question_lower):
            score = min(1.0, score + 0.15)
        
        # Check for specific data retrieval patterns
        if any(pattern in question_lower for pattern in [
            'for', 'with', 'related to', 'associated with',
            'by', 'from', 'in', 'code'
        ]):
            score = min(1.0, score + 0.1)
        
        return round(score, 2)
    
    def _needs_verification(self, question_lower: str, intent: QueryIntent) -> bool:
        """Determine if results need verification by general agent."""
        # Complex queries need verification
        if len(question_lower) > 100:
            return True
        
        # Multiple criteria need verification
        if question_lower.count('and') > 1 or question_lower.count(',') > 1:
            return True
        
        # Clarification or comparison queries need verification
        if intent in [QueryIntent.CLARIFICATION, QueryIntent.KNOWLEDGE_BASE]:
            return True
        
        # Queries asking for multiple things
        if '?' in question_lower and question_lower.count('?') > 1:
            return True
        
        return False
    
    def _extract_medical_concepts(self, question_lower: str) -> List[str]:
        """Extract medical concepts from query."""
        concepts = []
        for concept, concept_type in self.medical_codes.items():
            if concept in question_lower:
                concepts.append(concept)
        return concepts
    
    def _classify_query_type(self, question_lower: str) -> str:
        """Classify the type of query."""
        if any(x in question_lower for x in ['compare', 'difference', 'vs']):
            return 'comparative'
        elif any(x in question_lower for x in ['count', 'how many', 'total']):
            return 'aggregation'
        elif any(x in question_lower for x in ['list', 'show', 'all']):
            return 'retrieval'
        elif any(x in question_lower for x in ['related', 'associated', 'linked']):
            return 'relationship'
        elif any(x in question_lower for x in ['explain', 'what is', 'define']):
            return 'definition'
        else:
            return 'general'
    
    def _estimate_complexity(self, question_lower: str) -> str:
        """Estimate query complexity."""
        # Count complexity indicators
        complexity_score = 0
        
        # Multiple queries
        complexity_score += question_lower.count('?')
        
        # Conjunctions
        complexity_score += (question_lower.count('and') + 
                            question_lower.count('or') +
                            question_lower.count('but')) * 0.5
        
        # Nested requirements
        if '(' in question_lower or ')' in question_lower:
            complexity_score += 1
        
        # Length
        complexity_score += len(question_lower) / 100
        
        if complexity_score > 3:
            return 'high'
        elif complexity_score > 1.5:
            return 'medium'
        else:
            return 'low'
    
    def _calculate_confidence(self, sql_likelihood: float, intent: QueryIntent) -> float:
        """Calculate confidence in routing recommendation."""
        # Base confidence from SQL likelihood
        confidence = abs(sql_likelihood - 0.5) * 2  # Normalize 0-1
        
        # Increase confidence for clear intents
        clear_intents = [
            QueryIntent.SQL_REQUIRED,
            QueryIntent.KNOWLEDGE_BASE
        ]
        if intent in clear_intents:
            confidence = min(1.0, confidence + 0.2)
        
        return round(confidence, 2)
    
    def _generate_instructions(self, analysis: Dict[str, Any]) -> Dict[str, str]:
        """Generate processing instructions based on analysis."""
        instructions = {
            'format_response': 'structured_data' if analysis['should_use_sql'] else 'natural_language',
            'include_sql': 'yes' if analysis['should_use_sql'] else 'no',
            'medical_context': 'yes' if analysis['has_medical_codes'] else 'no',
            'verify_data': 'yes' if analysis['needs_verification'] else 'no'
        }
        
        # Add specific instructions based on query type
        query_type = analysis['query_type']
        if query_type == 'comparative':
            instructions['format_response'] = 'comparison_table'
        elif query_type == 'aggregation':
            instructions['format_response'] = 'summary_statistics'
        elif query_type == 'relationship':
            instructions['format_response'] = 'relationship_diagram'
        
        return instructions


class QueryProcessor:
    """Processes queries with automatic agent selection."""
    
    def __init__(self):
        """Initialize the query processor."""
        self.router = QueryRouter()
    
    def get_processing_strategy(self, question: str) -> Dict[str, Any]:
        """
        Get the complete processing strategy for a question.
        
        Args:
            question: User's natural language question
            
        Returns:
            Complete strategy including routing and instructions
        """
        routing = self.router.route_query(question)
        
        strategy = {
            'question': question,
            'routing': routing['route'],
            'agents': {
                'primary': routing['primary_agent'],
                'secondary': routing['secondary_agent']
            },
            'strategy': routing['strategy'],
            'response_type': routing['response_type'],
            'instructions': routing['instructions'],
            'analysis': routing['analysis'],
            'auto_routing': True,  # Indicate automatic routing
            'message_to_user': self._generate_user_message(routing)
        }
        
        return strategy
    
    def _generate_user_message(self, routing: Dict[str, Any]) -> str:
        """Generate a user-friendly message about the query handling."""
        if routing['route'] == 'sql_to_general':
            if routing['analysis'].get('complexity') == 'high':
                return "Complex medical query detected. Querying database and analyzing results..."
            elif routing['analysis'].get('has_medical_codes'):
                return "Medical query detected. Searching database for medical concepts..."
            else:
                return "Data query detected. Retrieving and analyzing results..."
        else:
            return "Processing your question..."


def create_query_processor() -> QueryProcessor:
    """Factory function to create a query processor."""
    return QueryProcessor()
