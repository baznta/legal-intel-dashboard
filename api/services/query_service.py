"""
Query service for natural language document interrogation.
"""

import re
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, exists
from sqlalchemy.orm import selectinload
import structlog
from difflib import SequenceMatcher

from models.document import Document, DocumentMetadata, DocumentContent
from services.llm_service import LLMService

logger = structlog.get_logger()


def fuzzy_match(query_word: str, target_words: List[str], threshold: float = 0.8) -> Optional[str]:
    """
    Fuzzy match a query word against a list of target words.
    
    Args:
        query_word: The word from the user query
        target_words: List of target words to match against
        threshold: Similarity threshold (0.0 to 1.0)
        
    Returns:
        The best matching target word or None if no match above threshold
    """
    best_match = None
    best_score = 0.0
    
    for target in target_words:
        # Exact match
        if query_word.lower() == target.lower():
            return target
        
        # Fuzzy match using sequence matcher
        score = SequenceMatcher(None, query_word.lower(), target.lower()).ratio()
        if score > best_score and score >= threshold:
            best_score = score
            best_match = target
    
    return best_match


def normalize_query(query: str) -> str:
    """
    Normalize query text for better matching.
    
    Args:
        query: Raw query string
        
    Returns:
        Normalized query string
    """
    # Convert to lowercase
    query = query.lower()
    
    # Common misspellings and variations
    misspellings = {
        'teck': 'tech',
        'technolgy': 'technology',
        'agrement': 'agreement',
        'agreemnt': 'agreement',
        'contrat': 'contract',
        'contrats': 'contracts',
        'jurisdicton': 'jurisdiction',
        'industy': 'industry',
        'sectr': 'sector',
        'realestate': 'real estate',
        'oilandgas': 'oil & gas',
        'oil&gas': 'oil & gas',
        'healthcare': 'healthcare',
        'health care': 'healthcare',
        'ecommerce': 'e-commerce',
        'e-commerce': 'e-commerce',
        'jointventure': 'joint venture',
        'joint-venture': 'joint venture',
        'masteragreement': 'master agreement',
        'master-agreement': 'master agreement',
        'nondisclosure': 'nda',
        'non-disclosure': 'nda',
        'confidentiality': 'nda',
        'employment': 'employment',
        'employement': 'employment',
        'partnership': 'partnership',
        'partnershp': 'partnership',
        'franchise': 'franchise',
        'franchisee': 'franchise',
        'license': 'license',
        'licence': 'license',
        'purchase': 'purchase',
        'purchse': 'purchase',
        'sales': 'purchase',
        'tenancy': 'tenancy',
        'tennancy': 'tenancy',
        'lease': 'tenancy',
        'shareholders': 'shareholders',
        'shareholder': 'shareholders',
        'litigation': 'litigation',
        'litigaton': 'litigation',
        'consulting': 'consulting',
        'consultancy': 'consulting',
        'service': 'service',
        'servce': 'service'
    }
    
    # Apply misspelling corrections
    for misspelling, correction in misspellings.items():
        query = query.replace(misspelling, correction)
    
    return query


class QueryService:
    """Service for natural language document queries."""
    
    def __init__(self):
        self.llm_service = LLMService()
    
    async def query_documents(
        self,
        db: AsyncSession,
        query: str,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Process natural language query and return structured results.
        
        Args:
            db: Database session
            query: Natural language query
            limit: Maximum number of results to return
            
        Returns:
            Dictionary with query results and metadata
        """
        try:
            # Parse the natural language query
            parsed_query = self._parse_natural_language_query(query.lower())
            
            if not parsed_query:
                suggestions = self._get_query_suggestions(query)
                return {
                    "error": "Could not understand query",
                    "suggestions": suggestions,
                    "query": query,
                    "note": "Try rephrasing your query or use one of the suggestions below."
                }
            
            # Build database query based on parsed criteria
            results = await self._execute_structured_query(db, parsed_query, limit)
            
            # If no results found, provide helpful suggestions
            if not results:
                suggestions = self._get_query_suggestions(query)
                return {
                    "query": query,
                    "parsed_criteria": parsed_query,
                    "total_results": 0,
                    "results": [],
                    "query_type": parsed_query.get("query_type", "unknown"),
                    "note": "No documents found matching your criteria. Try these suggestions:",
                    "suggestions": suggestions
                }
            
            # Format results for API response
            formatted_results = self._format_query_results(results, parsed_query)
            
            return {
                "query": query,
                "parsed_criteria": parsed_query,
                "total_results": len(formatted_results),
                "results": formatted_results,
                "query_type": parsed_query.get("query_type", "unknown")
            }
            
        except Exception as e:
            logger.error(f"Query processing failed: {e}")
            suggestions = self._get_query_suggestions(query)
            return {
                "error": f"Query processing failed: {str(e)}",
                "query": query,
                "suggestions": suggestions,
                "note": "Something went wrong. Try these alternative queries:"
            }
    
    def _parse_natural_language_query(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Parse natural language query into structured criteria with fuzzy matching.
        
        Args:
            query: Natural language query string
            
        Returns:
            Dictionary with parsed query criteria
        """
        # Normalize the query first
        normalized_query = normalize_query(query)
        criteria = {}
        
        # Agreement type queries with fuzzy matching
        agreement_patterns = {
            "nda": ["nda", "non.?disclosure", "confidentiality", "non disclosure", "nondisclosure"],
            "msa": ["msa", "master.?services", "master.?agreement", "master services", "master agreement"],
            "franchise": ["franchise", "franchising", "franchisee"],
            "employment": ["employment", "employment.?contract", "employement", "employ"],
            "service": ["service", "consulting", "professional.?services", "servce", "serv"],
            "license": ["license", "licensing", "software.?license", "licence"],
            "partnership": ["partnership", "joint.?venture", "collaboration", "partnershp"],
            "purchase": ["purchase", "sales", "acquisition", "purchse", "buy"],
            "tenancy": ["tenancy", "lease", "rental", "tennancy", "tenent"],
            "shareholders": ["shareholders", "shareholder", "stockholders", "stockholder"],
            "litigation": ["litigation", "legal memo", "memo", "litigaton", "dispute"],
            "consultancy": ["consultancy", "consulting", "consultant", "advisory"],
            "contracts": ["\\bcontracts?\\b", "\\bagreements?\\b", "\\bdocuments?\\b", "contract", "agreement"]
        }
        
        # Try fuzzy matching for agreement types
        for agreement_type, patterns in agreement_patterns.items():
            if any(re.search(pattern, normalized_query) for pattern in patterns):
                criteria["agreement_type"] = agreement_type.upper()
                break
        
        # If no exact match found, try fuzzy matching
        if "agreement_type" not in criteria:
            query_words = normalized_query.split()
            for word in query_words:
                if len(word) > 3:  # Only try to match words longer than 3 characters
                    matched_type = fuzzy_match(word, list(agreement_patterns.keys()))
                    if matched_type:
                        criteria["agreement_type"] = matched_type.upper()
                        break
        
        # Jurisdiction queries with fuzzy matching
        jurisdiction_patterns = {
            "UAE": ["uae", "united.?arab.?emirates", "dubai", "abudhabi", "abu.?dhabi", "emirates"],
            "UK": ["uk", "united.?kingdom", "england", "wales", "british", "britain"],
            "USA": ["\\busa\\b", "\\bunited.?states\\b", "\\bus\\b", "\\bamerican\\b", "america"],
            "Delaware": ["\\bdelaware\\b", "de"],
            "California": ["\\bcalifornia\\b", "\\bcal\\b", "cali"],
            "New York": ["\\bnew.?york\\b", "\\bny\\b", "nyc"],
            "Singapore": ["\\bsingapore\\b", "\\bsg\\b", "sing"],
            "Hong Kong": ["\\bhong.?kong\\b", "\\bhk\\b", "hongkong"],
            "Germany": ["\\bgermany\\b", "\\bgerman\\b", "deutschland"],
            "France": ["\\bfrance\\b", "\\bfrench\\b", "france"]
        }
        
        for jurisdiction, patterns in jurisdiction_patterns.items():
            if any(re.search(pattern, normalized_query) for pattern in patterns):
                criteria["jurisdiction"] = jurisdiction
                break
        
        # Industry sector queries with fuzzy matching
        industry_patterns = {
            "Technology": ["technology", "tech", "software", "it", "digital", "teck", "technolgy"],
            "Healthcare": ["healthcare", "medical", "pharmaceutical", "biotech", "health care", "medicine"],
            "Oil & Gas": ["oil", "gas", "petroleum", "energy", "hydrocarbon", "oilandgas", "oil&gas"],
            "Finance": ["finance", "banking", "investment", "financial", "finacial", "bank"],
            "Real Estate": ["real.?estate", "property", "construction", "realestate", "realestate"],
            "Manufacturing": ["manufacturing", "industrial", "production", "manufacture", "factory"],
            "Retail": ["retail", "e.?commerce", "consumer", "ecommerce", "e-commerce", "shopping"],
            "Energy": ["energy", "renewable", "solar", "wind", "nuclear", "power"],
            "Consulting": ["consulting", "consultancy", "advisory", "professional services"],
            "Transportation": ["transportation", "transport", "logistics", "shipping", "delivery"],
            "Telecommunications": ["telecommunications", "telecom", "communications", "phone", "internet"]
        }
        
        for industry, patterns in industry_patterns.items():
            if any(re.search(pattern, normalized_query) for pattern in patterns):
                criteria["industry_sector"] = industry
                break
        
        # If no exact match found, try fuzzy matching for industry
        if "industry_sector" not in criteria:
            query_words = normalized_query.split()
            for word in query_words:
                if len(word) > 3:
                    matched_industry = fuzzy_match(word, list(industry_patterns.keys()))
                    if matched_industry:
                        criteria["industry_sector"] = matched_industry
                        break
        
        # Date queries
        date_patterns = {
            "recent": ["recent", "latest", "new", "this.?year", "2025", "current"],
            "old": ["old", "previous", "last.?year", "2024", "2023", "past"],
            "expiring": ["expiring", "expiration", "ending", "due", "expire", "expiry"],
            "effective": ["effective", "start", "commencement", "begin", "started"]
        }
        
        for date_type, patterns in date_patterns.items():
            if any(re.search(pattern, normalized_query) for pattern in patterns):
                criteria["date_filter"] = date_type
                break
        
        # Confidence queries
        if re.search(r"high.?confidence|accurate|reliable|good", normalized_query):
            criteria["min_confidence"] = 0.8
        elif re.search(r"low.?confidence|uncertain|poor|bad", normalized_query):
            criteria["max_confidence"] = 0.5
        
        # Keyword searches with fuzzy matching
        keyword_patterns = [
            r"mention[s]?\s+(\w+)",
            r"contain[s]?\s+(\w+)",
            r"with\s+(\w+)",
            r"about\s+(\w+)",
            r"related\s+to\s+(\w+)",
            r"involving\s+(\w+)"
        ]
        
        for pattern in keyword_patterns:
            match = re.search(pattern, normalized_query)
            if match:
                keyword = match.group(1).lower()
                # Try to correct common misspellings in keywords
                corrected_keyword = normalize_query(keyword)
                criteria["keywords"] = [corrected_keyword]
                break
        
        # Query type classification
        if "governed by" in normalized_query or "jurisdiction" in normalized_query:
            criteria["query_type"] = "jurisdiction_search"
        elif "show" in normalized_query or "find" in normalized_query or "which" in normalized_query:
            criteria["query_type"] = "document_search"
        elif "confidence" in normalized_query or "accurate" in normalized_query:
            criteria["query_type"] = "quality_search"
        else:
            criteria["query_type"] = "general_search"
        
        return criteria if criteria else None
    
    async def _execute_structured_query(
        self,
        db: AsyncSession,
        criteria: Dict[str, Any],
        limit: int
    ) -> List[Document]:
        """
        Execute structured database query based on parsed criteria.
        
        Args:
            db: Database session
            criteria: Parsed query criteria
            limit: Maximum results to return
            
        Returns:
            List of matching documents
        """
        # Build base query with proper joins
        query = select(Document).options(
            selectinload(Document.document_metadata),
            selectinload(Document.content)
        )
        
        # Add filters based on criteria
        filters = []
        
        if "agreement_type" in criteria:
            # Special handling for "contracts" - it should match all agreement types
            if criteria["agreement_type"] == "CONTRACTS":
                # Don't filter by agreement_type when user asks for "contracts"
                # This allows finding all types of contracts/agreements
                pass
            else:
                # Use exists() for relationship filtering for specific agreement types
                filters.append(
                    exists().where(
                        and_(
                            DocumentMetadata.document_id == Document.id,
                            DocumentMetadata.agreement_type == criteria["agreement_type"]
                        )
                    )
                )
        
        if "jurisdiction" in criteria:
            filters.append(
                exists().where(
                    and_(
                        DocumentMetadata.document_id == Document.id,
                        or_(
                            DocumentMetadata.jurisdiction == criteria["jurisdiction"],
                            DocumentMetadata.governing_law == criteria["jurisdiction"]
                        )
                    )
                )
            )
        
        if "industry_sector" in criteria:
            filters.append(
                exists().where(
                    and_(
                        DocumentMetadata.document_id == Document.id,
                        DocumentMetadata.industry_sector == criteria["industry_sector"]
                    )
                )
            )
        
        if "min_confidence" in criteria:
            filters.append(
                exists().where(
                    and_(
                        DocumentMetadata.document_id == Document.id,
                        DocumentMetadata.extraction_confidence >= criteria["min_confidence"]
                    )
                )
            )
        
        if "max_confidence" in criteria:
            filters.append(
                exists().where(
                    and_(
                        DocumentMetadata.document_id == Document.id,
                        DocumentMetadata.extraction_confidence <= criteria["max_confidence"]
                    )
                )
            )
        
        if "keywords" in criteria:
            for keyword in criteria["keywords"]:
                filters.append(
                    exists().where(
                        and_(
                            DocumentMetadata.document_id == Document.id,
                            or_(
                                DocumentMetadata.keywords.contains([keyword]),
                                DocumentMetadata.tags.contains([keyword]),
                                DocumentMetadata.summary.ilike(f"%{keyword}%")
                            )
                        )
                    )
                )
        
        # Apply filters
        if filters:
            query = query.where(and_(*filters))
        
        # Add ordering
        if "date_filter" in criteria:
            if criteria["date_filter"] == "recent":
                query = query.order_by(Document.uploaded_at.desc())
            elif criteria["date_filter"] == "old":
                query = query.order_by(Document.uploaded_at.asc())
            elif criteria["date_filter"] == "expiring":
                # For expiration date ordering, we'll order by document upload date as fallback
                query = query.order_by(Document.uploaded_at.desc())
        else:
            # Default ordering by document upload date (most recent first)
            query = query.order_by(Document.uploaded_at.desc())
        
        # Add limit
        query = query.limit(limit)
        
        # Execute query
        result = await db.execute(query)
        documents = result.scalars().all()
        
        return documents
    
    def _format_query_results(
        self,
        documents: List[Document],
        criteria: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Format query results for API response.
        
        Args:
            documents: List of document objects
            criteria: Original query criteria
            
        Returns:
            List of formatted result dictionaries
        """
        results = []
        
        for doc in documents:
            # Get metadata if available
            metadata = None
            if hasattr(doc, 'document_metadata') and doc.document_metadata:
                # Handle both list and single object cases
                if isinstance(doc.document_metadata, list) and len(doc.document_metadata) > 0:
                    metadata = doc.document_metadata[0]
                elif hasattr(doc.document_metadata, 'agreement_type'):
                    metadata = doc.document_metadata
            
            result = {
                "document_id": str(doc.id),
                "filename": doc.original_filename,
                "status": doc.status,
                "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
                "file_size": doc.file_size,
                "file_type": doc.file_extension
            }
            
            if metadata:
                result.update({
                    "agreement_type": metadata.agreement_type,
                    "jurisdiction": metadata.jurisdiction,
                    "governing_law": metadata.governing_law,
                    "geography": metadata.geography,
                    "industry_sector": metadata.industry_sector,
                    "parties": metadata.parties,
                    "effective_date": metadata.effective_date.isoformat() if metadata.effective_date else None,
                    "expiration_date": metadata.expiration_date.isoformat() if metadata.expiration_date else None,
                    "contract_value": metadata.contract_value,
                    "currency": metadata.currency,
                    "keywords": metadata.keywords,
                    "tags": metadata.tags,
                    "summary": metadata.summary,
                    "extraction_confidence": metadata.extraction_confidence,
                    "extraction_method": metadata.extraction_method
                })
            
            results.append(result)
        
        return results
    
    async def get_query_suggestions(self) -> List[str]:
        """Get suggested queries for users."""
        return [
            "Which agreements are governed by UAE law?",
            "Show me all NDA documents",
            "Find contracts in the technology sector",
            "Which documents mention confidentiality?",
            "Show agreements with high confidence scores",
            "Find recent employment contracts",
            "Show documents expiring this year",
            "Which agreements are in the healthcare industry?",
            "Find contracts with TechCorp Solutions",
            "Show documents with jurisdiction in Delaware"
        ] 

    def _get_query_suggestions(self, failed_query: str) -> List[str]:
        """
        Get helpful suggestions when a query fails or returns no results.
        
        Args:
            failed_query: The query that failed
            
        Returns:
            List of suggested queries
        """
        suggestions = []
        normalized_query = normalize_query(failed_query.lower())
        
        # Check what the user was trying to find
        if any(word in normalized_query for word in ["tech", "technology", "software", "it"]):
            suggestions.extend([
                "Technology industry contracts",
                "Software development agreements",
                "IT service contracts",
                "Tech company NDAs"
            ])
        
        if any(word in normalized_query for word in ["contract", "agreement", "document"]):
            suggestions.extend([
                "Show me all contracts",
                "Find agreements by type",
                "Search documents by jurisdiction"
            ])
        
        if any(word in normalized_query for word in ["uae", "dubai", "emirates"]):
            suggestions.extend([
                "UAE jurisdiction contracts",
                "Contracts governed by UAE law",
                "Documents in Dubai"
            ])
        
        if any(word in normalized_query for word in ["nda", "confidentiality"]):
            suggestions.extend([
                "Non-disclosure agreements",
                "Confidentiality contracts",
                "NDA documents by jurisdiction"
            ])
        
        if any(word in normalized_query for word in ["employment", "work", "job"]):
            suggestions.extend([
                "Employment contracts",
                "Work agreements",
                "Employment documents"
            ])
        
        # Add general suggestions
        suggestions.extend([
            "Try: 'Show me all contracts'",
            "Try: 'Find NDA documents'",
            "Try: 'Technology industry agreements'",
            "Try: 'UAE jurisdiction contracts'",
            "Try: 'High confidence documents'"
        ])
        
        return suggestions[:8]  # Limit to 8 suggestions 