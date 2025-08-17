"""
Query routes for natural language document interrogation.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, exists
from typing import List, Dict, Any
import structlog
import time
import re
from sqlalchemy.orm import selectinload

from core.database import get_db
from models.document import Document, DocumentMetadata, DocumentContent
from schemas.document import DocumentQueryRequest, DocumentQueryResponse
from services.llm_service import LLMService
from services.query_service import QueryService

logger = structlog.get_logger()
router = APIRouter()

# Initialize LLM service
llm_service = LLMService()


@router.post("/query", response_model=DocumentQueryResponse)
async def query_documents(
    request: DocumentQueryRequest,
    db: AsyncSession = Depends(get_db)
):
    """Query documents using natural language."""
    
    start_time = time.time()
    
    try:
        logger.info(f"Processing query: {request.query}")
        
        # Parse query using LLM service
        parsed_query = await llm_service.parse_query(request.query)
        
        # Build database query based on parsed information
        query_results = await _execute_document_query(
            db, parsed_query, request.filters, request.limit, request.offset
        )
        
        # Process results
        processed_results = await _process_query_results(query_results, request.query)
        
        processing_time = time.time() - start_time
        
        response = DocumentQueryResponse(
            query=request.query,
            results=processed_results,
            total_results=len(processed_results),
            processing_time=processing_time,
            confidence_score=parsed_query.get("confidence", 0.8)
        )
        
        logger.info(
            f"Query completed successfully",
            query=request.query,
            results_count=len(processed_results),
            processing_time=processing_time
        )
        
        return response
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Query processing failed: {e}", query=request.query)
        
        raise HTTPException(
            status_code=500,
            detail=f"Query processing failed: {str(e)}"
        )


async def _execute_document_query(
    db: AsyncSession,
    parsed_query: Dict[str, Any],
    filters: Any,
    limit: int,
    offset: int
) -> List[Document]:
    """Execute the document query based on parsed query."""
    
    # Build base query with proper eager loading
    query = select(Document).options(
        selectinload(Document.document_metadata),
        selectinload(Document.content)
    )
    
    # Apply query-specific filters
    query_filters = []
    
    # Agreement type filter
    if parsed_query.get("agreement_type"):
        query_filters.append(
            exists().where(
                and_(
                    DocumentMetadata.document_id == Document.id,
                    DocumentMetadata.agreement_type.ilike(f"%{parsed_query['agreement_type']}%")
                )
            )
        )
    
    # Jurisdiction filter
    if parsed_query.get("jurisdiction"):
        query_filters.append(
            exists().where(
                and_(
                    DocumentMetadata.document_id == Document.id,
                    or_(
                        DocumentMetadata.jurisdiction.ilike(f"%{parsed_query['jurisdiction']}%"),
                        DocumentMetadata.governing_law.ilike(f"%{parsed_query['jurisdiction']}%")
                    )
                )
            )
        )
    
    # Industry filter
    if parsed_query.get("industry"):
        query_filters.append(
            exists().where(
                and_(
                    DocumentMetadata.document_id == Document.id,
                    DocumentMetadata.industry_sector.ilike(f"%{parsed_query['industry']}%")
                )
            )
        )
    
    # Geography filter
    if parsed_query.get("geography"):
        query_filters.append(
            exists().where(
                and_(
                    DocumentMetadata.document_id == Document.id,
                    DocumentMetadata.geography.ilike(f"%{parsed_query['geography']}%")
                )
            )
        )
    
    # Text content search
    if parsed_query.get("search_terms"):
        search_terms = parsed_query["search_terms"]
        content_query = select(Document).options(
            selectinload(Document.document_metadata),
            selectinload(Document.content)
        ).join(DocumentContent)
        
        for term in search_terms:
            content_query = content_query.filter(
                DocumentContent.text_content.ilike(f"%{term}%")
            )
        
        # Execute content search
        content_results = await db.execute(content_query.limit(limit).offset(offset))
        content_docs = content_results.scalars().all()
        
        # If we have content results, return them
        if content_docs:
            return content_docs
    
    # Apply filters if any
    if query_filters:
        query = query.where(and_(*query_filters))
    
    # Apply pagination
    query = query.limit(limit).offset(offset)
    
    # Execute query
    result = await db.execute(query)
    documents = result.scalars().all()
    
    return documents


async def _process_query_results(
    documents: List[Document],
    original_query: str
) -> List[Dict[str, Any]]:
    """Process and format query results."""
    
    results = []
    
    for doc in documents:
        # Extract relevant information based on query
        result_data = {
            "document_id": str(doc.id),
            "filename": doc.original_filename,
            "status": doc.status,
            "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
            "file_size": doc.file_size,
            "file_extension": doc.file_extension
        }
        
        # Add metadata if available (handle list properly)
        if hasattr(doc, 'document_metadata') and doc.document_metadata:
            # Handle both single and list cases
            metadata = doc.document_metadata[0] if isinstance(doc.document_metadata, list) else doc.document_metadata
            if metadata:
                result_data.update({
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
                    "tags": metadata.tags
                })
        
        # Add content summary if available (handle list properly)
        if hasattr(doc, 'content') and doc.content:
            # Handle both single and list cases
            content = doc.content[0] if isinstance(doc.content, list) else doc.content
            if content:
                result_data.update({
                    "word_count": content.word_count,
                    "character_count": content.character_count,
                    "content_preview": content.text_content[:200] + "..." if len(content.text_content) > 200 else content.text_content
                })
        
        results.append(result_data)
    
    return results


@router.get("/query/examples")
async def get_query_examples():
    """Get example queries for users."""
    
    examples = [
        {
            "query": "Which agreements are governed by UAE law?",
            "description": "Find all documents with UAE jurisdiction or governing law",
            "category": "jurisdiction"
        },
        {
            "query": "Show me all NDA contracts",
            "description": "Find all Non-Disclosure Agreements",
            "category": "agreement_type"
        },
        {
            "query": "Contracts in the technology industry",
            "description": "Find documents related to technology sector",
            "category": "industry"
        },
        {
            "query": "Agreements mentioning Middle East",
            "description": "Find documents with Middle East geography",
            "category": "geography"
        },
        {
            "query": "Contracts with termination clauses",
            "description": "Find documents containing termination-related text",
            "category": "content_search"
        },
        {
            "query": "MSA contracts in Europe",
            "description": "Find Master Service Agreements in European jurisdictions",
            "category": "combined"
        }
    ]
    
    return {
        "examples": examples,
        "total_examples": len(examples),
        "note": "These are example queries to help you get started. Use natural language to describe what you're looking for."
    }


@router.post("/query/simple")
async def simple_query_documents(
    request: Dict[str, str],
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Simple query endpoint for natural language document interrogation.
    
    Args:
        query: Natural language question (e.g., "Which agreements are governed by UAE law?")
        
    Returns:
        Structured JSON response with rows and columns based on the user's query
    """
    try:
        query = request.get("query", "")
        if not query:
            raise HTTPException(status_code=400, detail="Query field is required")
            
        query_service = QueryService()
        results = await query_service.query_documents(db, query)
        
        return results
        
    except Exception as e:
        logger.error(f"Simple query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@router.get("/query/suggestions")
async def get_query_suggestions(query: str):
    """Get query suggestions based on partial input."""
    
    # Simple keyword-based suggestions
    suggestions = []
    
    # Jurisdiction suggestions
    if "uae" in query.lower() or "dubai" in query.lower():
        suggestions.extend([
            "Which agreements are governed by UAE law?",
            "Show me contracts in Dubai",
            "UAE jurisdiction contracts"
        ])
    
    # Agreement type suggestions
    if "nda" in query.lower() or "nda" in query.upper():
        suggestions.extend([
            "Show me all NDA contracts",
            "Non-disclosure agreements",
            "NDA contracts by jurisdiction"
        ])
    
    # Industry suggestions
    if "tech" in query.lower() or "technology" in query.lower():
        suggestions.extend([
            "Technology industry contracts",
            "Tech company agreements",
            "Software development contracts"
        ])
    
    # Default suggestions
    if not suggestions:
        suggestions = [
            "Which agreements are governed by UAE law?",
            "Show me all NDA contracts",
            "Contracts in the technology industry",
            "Agreements mentioning Middle East"
        ]
    
    return {
        "query": query,
        "suggestions": suggestions[:5],  # Limit to 5 suggestions
        "total_suggestions": len(suggestions)
    } 