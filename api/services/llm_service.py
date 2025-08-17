"""
Mock LLM service for query parsing and document analysis.
"""

from typing import Dict, Any, List, Optional
import structlog
import re
import json

logger = structlog.get_logger()


class LLMService:
    """Mock LLM service for natural language processing."""
    
    def __init__(self):
        self.agreement_types = [
            "NDA", "MSA", "Franchise Agreement", "Employment Contract", 
            "Service Agreement", "License Agreement", "Purchase Agreement",
            "Distribution Agreement", "Joint Venture Agreement", "Merger Agreement"
        ]
        
        self.jurisdictions = [
            "UAE", "UK", "USA", "Delaware", "New York", "California",
            "Singapore", "Hong Kong", "Germany", "France", "Netherlands"
        ]
        
        self.industries = [
            "Technology", "Healthcare", "Oil & Gas", "Finance", "Real Estate",
            "Manufacturing", "Retail", "Transportation", "Energy", "Telecommunications"
        ]
        
        self.geographies = [
            "Middle East", "Europe", "North America", "Asia Pacific",
            "Latin America", "Africa", "Gulf Cooperation Council"
        ]
    
    async def parse_query(self, query: str) -> Dict[str, Any]:
        """Parse natural language query to extract structured information."""
        
        query_lower = query.lower()
        
        # Extract agreement type
        agreement_type = self._extract_agreement_type(query_lower)
        
        # Extract jurisdiction
        jurisdiction = self._extract_jurisdiction(query_lower)
        
        # Extract industry
        industry = self._extract_industry(query_lower)
        
        # Extract geography
        geography = self._extract_geography(query_lower)
        
        # Extract search terms
        search_terms = self._extract_search_terms(query_lower)
        
        # Determine query type
        query_type = self._determine_query_type(query_lower)
        
        # Calculate confidence score
        confidence = self._calculate_confidence(
            agreement_type, jurisdiction, industry, geography, search_terms
        )
        
        parsed_query = {
            "agreement_type": agreement_type,
            "jurisdiction": jurisdiction,
            "industry": industry,
            "geography": geography,
            "search_terms": search_terms,
            "query_type": query_type,
            "confidence": confidence,
            "original_query": query
        }
        
        logger.info(f"Query parsed successfully", parsed_query=parsed_query)
        return parsed_query
    
    def _extract_agreement_type(self, query: str) -> Optional[str]:
        """Extract agreement type from query."""
        
        for agreement_type in self.agreement_types:
            if agreement_type.lower() in query:
                return agreement_type
        
        # Check for variations
        if "nda" in query or "non-disclosure" in query:
            return "NDA"
        elif "msa" in query or "master service" in query:
            return "MSA"
        elif "franchise" in query:
            return "Franchise Agreement"
        elif "employment" in query or "contract" in query:
            return "Employment Contract"
        
        return None
    
    def _extract_jurisdiction(self, query: str) -> Optional[str]:
        """Extract jurisdiction from query."""
        
        for jurisdiction in self.jurisdictions:
            if jurisdiction.lower() in query:
                return jurisdiction
        
        # Check for variations
        if "uae" in query or "dubai" in query or "abudhabi" in query:
            return "UAE"
        elif "uk" in query or "british" in query or "england" in query:
            return "UK"
        elif "usa" in query or "united states" in query or "american" in query:
            return "USA"
        elif "delaware" in query:
            return "Delaware"
        
        return None
    
    def _extract_industry(self, query: str) -> Optional[str]:
        """Extract industry from query."""
        
        for industry in self.industries:
            if industry.lower() in query:
                return industry
        
        # Check for variations
        if "tech" in query or "software" in query or "digital" in query:
            return "Technology"
        elif "health" in query or "medical" in query or "pharma" in query:
            return "Healthcare"
        elif "oil" in query or "gas" in query or "petroleum" in query:
            return "Oil & Gas"
        elif "bank" in query or "financial" in query or "investment" in query:
            return "Finance"
        
        return None
    
    def _extract_geography(self, query: str) -> Optional[str]:
        """Extract geography from query."""
        
        for geography in self.geographies:
            if geography.lower() in query:
                return geography
        
        # Check for variations
        if "middle east" in query or "gulf" in query or "arab" in query:
            return "Middle East"
        elif "europe" in query or "european" in query:
            return "Europe"
        elif "north america" in query or "american" in query:
            return "North America"
        elif "asia" in query or "asian" in query or "pacific" in query:
            return "Asia Pacific"
        
        return None
    
    def _extract_search_terms(self, query: str) -> List[str]:
        """Extract search terms from query."""
        
        # Remove common words and extract meaningful terms
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "is", "are", "was", "were", "be", "been", "being",
            "have", "has", "had", "do", "does", "did", "will", "would", "could",
            "should", "may", "might", "can", "show", "me", "all", "which", "what",
            "where", "when", "who", "how", "why", "contracts", "agreements",
            "documents", "files", "that", "this", "these", "those"
        }
        
        # Split query into words and filter
        words = re.findall(r'\b\w+\b', query.lower())
        search_terms = [word for word in words if word not in stop_words and len(word) > 2]
        
        return search_terms[:5]  # Limit to 5 terms
    
    def _determine_query_type(self, query: str) -> str:
        """Determine the type of query."""
        
        if any(word in query for word in ["governed by", "jurisdiction", "law"]):
            return "jurisdiction_search"
        elif any(word in query for word in ["nda", "msa", "agreement", "contract"]):
            return "agreement_type_search"
        elif any(word in query for word in ["industry", "sector", "business"]):
            return "industry_search"
        elif any(word in query for word in ["geography", "region", "country", "city"]):
            return "geography_search"
        elif any(word in query for word in ["clause", "term", "provision", "mentioning"]):
            return "content_search"
        else:
            return "general_search"
    
    def _calculate_confidence(self, *extracted_values) -> float:
        """Calculate confidence score based on extracted values."""
        
        # Count non-None values
        extracted_count = sum(1 for value in extracted_values if value is not None)
        
        # Base confidence
        base_confidence = 0.5
        
        # Add confidence for each extracted value
        value_confidence = extracted_count * 0.1
        
        # Cap at 0.95
        confidence = min(base_confidence + value_confidence, 0.95)
        
        return round(confidence, 2)
    
    async def analyze_document_content(self, text_content: str) -> Dict[str, Any]:
        """Analyze document content to extract metadata."""
        
        # This is a mock implementation
        # In production, this would use a real LLM service
        
        analysis = {
            "agreement_type": self._classify_agreement_type(text_content),
            "jurisdiction": self._extract_jurisdiction_from_text(text_content),
            "industry_sector": self._classify_industry(text_content),
            "geography": self._extract_geography_from_text(text_content),
            "parties": self._extract_parties(text_content),
            "effective_date": self._extract_effective_date(text_content),
            "expiration_date": self._extract_expiration_date(text_content),
            "contract_value": self._extract_contract_value(text_content),
            "currency": self._extract_currency(text_content),
            "keywords": self._extract_keywords(text_content),
            "confidence_score": 0.85
        }
        
        return analysis
    
    def _classify_agreement_type(self, text: str) -> Optional[str]:
        """Classify agreement type based on text content."""
        
        text_lower = text.lower()
        
        if any(term in text_lower for term in ["non-disclosure", "nda", "confidentiality"]):
            return "NDA"
        elif any(term in text_lower for term in ["master service", "msa", "service agreement"]):
            return "MSA"
        elif "franchise" in text_lower:
            return "Franchise Agreement"
        elif any(term in text_lower for term in ["employment", "hire", "worker"]):
            return "Employment Contract"
        elif "license" in text_lower:
            return "License Agreement"
        
        return None
    
    def _extract_jurisdiction_from_text(self, text: str) -> Optional[str]:
        """Extract jurisdiction from document text."""
        
        text_lower = text.lower()
        
        if any(term in text_lower for term in ["uae", "dubai", "abudhabi", "emirates"]):
            return "UAE"
        elif any(term in text_lower for term in ["uk", "british", "england", "united kingdom"]):
            return "UK"
        elif any(term in text_lower for term in ["usa", "united states", "american"]):
            return "USA"
        elif "delaware" in text_lower:
            return "Delaware"
        
        return None
    
    def _classify_industry(self, text: str) -> Optional[str]:
        """Classify industry based on text content."""
        
        text_lower = text.lower()
        
        if any(term in text_lower for term in ["technology", "software", "digital", "tech"]):
            return "Technology"
        elif any(term in text_lower for term in ["healthcare", "medical", "pharmaceutical"]):
            return "Healthcare"
        elif any(term in text_lower for term in ["oil", "gas", "petroleum", "energy"]):
            return "Oil & Gas"
        elif any(term in text_lower for term in ["bank", "financial", "investment", "finance"]):
            return "Finance"
        
        return None
    
    def _extract_geography_from_text(self, text: str) -> Optional[str]:
        """Extract geography from document text."""
        
        text_lower = text.lower()
        
        if any(term in text_lower for term in ["middle east", "gulf", "arab"]):
            return "Middle East"
        elif any(term in text_lower for term in ["europe", "european"]):
            return "Europe"
        elif any(term in text_lower for term in ["north america", "american"]):
            return "North America"
        elif any(term in text_lower for term in ["asia", "asian", "pacific"]):
            return "Asia Pacific"
        
        return None
    
    def _extract_parties(self, text: str) -> List[str]:
        """Extract contracting parties from text."""
        
        # Mock implementation - in production this would use NER
        parties = []
        
        # Look for common patterns
        if "between" in text.lower():
            # Extract text between "between" and "and"
            between_match = re.search(r'between\s+([^.]*?)\s+and\s+([^.]*)', text, re.IGNORECASE)
            if between_match:
                parties.extend([between_match.group(1).strip(), between_match.group(2).strip()])
        
        return parties[:4]  # Limit to 4 parties
    
    def _extract_effective_date(self, text: str) -> Optional[str]:
        """Extract effective date from text."""
        
        # Look for date patterns
        date_patterns = [
            r'effective\s+date[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'commencement\s+date[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'start\s+date[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_expiration_date(self, text: str) -> Optional[str]:
        """Extract expiration date from text."""
        
        # Look for date patterns
        date_patterns = [
            r'expiration\s+date[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'end\s+date[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'termination\s+date[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_contract_value(self, text: str) -> Optional[float]:
        """Extract contract value from text."""
        
        # Look for currency patterns
        currency_patterns = [
            r'(\$[\d,]+(?:\.\d{2})?)',
            r'(\d+(?:,\d{3})*(?:\.\d{2})?\s*(?:USD|dollars?))',
            r'(\d+(?:,\d{3})*(?:\.\d{2})?\s*(?:AED|dirhams?))'
        ]
        
        for pattern in currency_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value_str = match.group(1).replace('$', '').replace(',', '')
                try:
                    return float(value_str)
                except ValueError:
                    continue
        
        return None
    
    def _extract_currency(self, text: str) -> Optional[str]:
        """Extract currency from text."""
        
        text_lower = text.lower()
        
        if "$" in text or "dollar" in text_lower or "usd" in text_lower:
            return "USD"
        elif "aed" in text_lower or "dirham" in text_lower:
            return "AED"
        elif "€" in text or "euro" in text_lower or "eur" in text_lower:
            return "EUR"
        elif "£" in text or "pound" in text_lower or "gbp" in text_lower:
            return "GBP"
        
        return None
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text."""
        
        # Mock implementation - in production this would use NLP
        keywords = []
        
        # Look for common legal terms
        legal_terms = [
            "confidentiality", "non-disclosure", "termination", "breach",
            "liability", "indemnification", "governing law", "jurisdiction",
            "arbitration", "mediation", "force majeure", "amendment"
        ]
        
        text_lower = text.lower()
        for term in legal_terms:
            if term in text_lower:
                keywords.append(term)
        
        return keywords[:10]  # Limit to 10 keywords 