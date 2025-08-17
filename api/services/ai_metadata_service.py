"""
AI-powered metadata extraction service using OpenAI GPT-4o Mini.
"""

import json
import structlog
from typing import Dict, Any, Optional, List
from openai import OpenAI
from core.config import settings

logger = structlog.get_logger()


class AIMetadataService:
    """AI-powered metadata extraction service using OpenAI GPT-4o Mini."""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None
        self.model = settings.openai_model
        self.max_tokens = settings.openai_max_tokens
        self.temperature = settings.openai_temperature
    
    def extract_metadata_with_ai(self, text_content: str, filename: str) -> Optional[Dict[str, Any]]:
        """
        Extract metadata using OpenAI GPT-4o Mini with structured output.
        
        Args:
            text_content: The text content of the document
            filename: The original filename for context
            
        Returns:
            Dictionary containing extracted metadata or None if extraction fails
        """
        if not self.client:
            logger.warning("OpenAI client not configured, falling back to rule-based extraction")
            return None
        
        try:
            # Create a comprehensive prompt for legal document analysis
            system_prompt = self._create_system_prompt()
            user_prompt = self._create_user_prompt(text_content, filename)
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                response_format={"type": "json_object"}
            )
            
            # Parse the response
            content = response.choices[0].message.content
            metadata = json.loads(content)
            
            logger.info(f"AI metadata extraction successful for {filename}")
            return metadata
            
        except Exception as e:
            logger.error(f"AI metadata extraction failed for {filename}: {e}")
            return None
    
    async def extract_metadata_batch(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract metadata from multiple documents in batch for improved throughput.
        
        Args:
            documents: List of documents with text_content and filename
            
        Returns:
            List of extracted metadata dictionaries
        """
        if not self.client:
            logger.warning("OpenAI client not configured, cannot perform batch extraction")
            return []
        
        try:
            # Create batch prompt for multiple documents
            system_prompt = self._create_batch_system_prompt()
            user_prompt = self._create_batch_user_prompt(documents)
            
            # Call OpenAI API with batch processing
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=self.max_tokens * 2,  # Increase tokens for batch processing
                temperature=self.temperature,
                response_format={"type": "json_object"}
            )
            
            # Parse the response
            content = response.choices[0].message.content
            batch_metadata = json.loads(content)
            
            logger.info(f"Batch AI metadata extraction successful for {len(documents)} documents")
            return batch_metadata.get("documents", [])
            
        except Exception as e:
            logger.error(f"Batch AI metadata extraction failed: {e}")
            return []
    
    def _create_system_prompt(self) -> str:
        """Create the system prompt for the AI model."""
        return """You are an expert legal document analyst specializing in contract and agreement analysis. 
Your task is to extract structured metadata from legal documents and return it in a specific JSON format.

IMPORTANT: You must return ONLY valid JSON with the exact structure specified below. Do not include any explanatory text.

Extract the following fields with high accuracy:

1. agreement_type: The type of legal agreement. Classify into these specific categories:
   - "NDA" (Non-Disclosure Agreement)
   - "MSA" (Master Service Agreement) 
   - "Franchise Agreement"
   - "Employment Agreement" or "Employment Contract"
   - "Service Agreement" or "Consulting Agreement"
   - "License Agreement" or "Software License"
   - "Partnership Agreement" or "Joint Venture Agreement"
   - "Purchase Agreement" or "Sales Agreement"
   - "Tenancy Agreement" or "Lease Agreement"
   - "Shareholders Agreement"
   - "Litigation Memo" or "Legal Memo"
   - "Consultancy Agreement"

2. jurisdiction: The legal jurisdiction or governing law. Be specific:
   - "UAE" for United Arab Emirates
   - "UK" for United Kingdom
   - "Delaware, USA" for Delaware state
   - "California, USA" for California state
   - "New York, USA" for New York state
   - "Singapore"
   - "Hong Kong"
   - "Germany"
   - "France"

3. governing_law: The specific governing law mentioned (usually same as jurisdiction)

4. geography: Geographic regions mentioned:
   - "Middle East" for Middle Eastern countries
   - "Gulf Region" for GCC countries
   - "Europe" for European countries
   - "Asia Pacific" for Asian countries
   - "North America" for US/Canada
   - "Gulf Cooperation Council" for GCC

5. industry_sector: The industry sector. Classify into:
   - "Technology" for tech, software, IT, digital
   - "Healthcare" for medical, pharmaceutical, biotech
   - "Oil & Gas" for petroleum, energy, hydrocarbon
   - "Finance" for banking, investment, financial
   - "Real Estate" for property, construction, real estate
   - "Manufacturing" for industrial, production
   - "Retail" for e-commerce, consumer, retail
   - "Energy" for renewable, solar, wind, nuclear
   - "Consulting" for professional services, consulting
   - "Transportation" for logistics, transport
   - "Telecommunications" for telecom, communications

6. parties: List of parties involved (e.g., ["Company A", "Company B"])

7. effective_date: The effective/start date in YYYY-MM-DD format if found

8. expiration_date: The expiration/end date in YYYY-MM-DD format if found

9. contract_value: Numeric value of the contract if mentioned

10. currency: The currency of the contract value (e.g., "USD", "EUR", "GBP", "AED")

11. keywords: List of important legal keywords found (e.g., ["confidentiality", "termination", "liability", "indemnification", "governing law", "jurisdiction", "breach", "remedies"])

12. tags: List of relevant tags for categorization

13. summary: A comprehensive 2-3 sentence summary of the document's key terms and purpose

14. extraction_confidence: Confidence score from 0.0 to 1.0 based on clarity of information

15. document_classification: Additional classification tags:
    - "contract_type": "commercial", "employment", "real_estate", "intellectual_property", "partnership", "service"
    - "complexity": "simple", "moderate", "complex"
    - "risk_level": "low", "medium", "high"
    - "duration": "short_term", "medium_term", "long_term"

Analyze the document thoroughly and provide the most accurate classification possible. If information is unclear, use reasonable inference based on the document content and context.
"""

    def _create_user_prompt(self, text_content: str, filename: str) -> str:
        """Create the user prompt with document content."""
        # Truncate content if too long to avoid token limits
        max_chars = 8000  # Conservative limit for GPT-4o-mini
        if len(text_content) > max_chars:
            text_content = text_content[:max_chars] + "\n\n[Content truncated due to length]"
        
        return f"""Please analyze the following legal document and extract the metadata as specified.

Filename: {filename}

Document Content:
{text_content}

Please extract all relevant metadata and return it in the exact JSON format specified. Focus on accuracy and completeness."""
    
    def _create_batch_system_prompt(self) -> str:
        """Create the system prompt for batch document processing."""
        return """You are an expert legal document analyst specializing in contract and agreement analysis. 
Your task is to extract structured metadata from multiple legal documents and return it in a specific JSON format.

IMPORTANT: You must return ONLY valid JSON with the exact structure specified below. Do not include any explanatory text.

For each document, extract the following fields with high accuracy:

1. agreement_type: The type of legal agreement. Classify into these specific categories:
   - "NDA" (Non-Disclosure Agreement)
   - "MSA" (Master Service Agreement) 
   - "Franchise Agreement"
   - "Employment Agreement" or "Employment Contract"
   - "Service Agreement" or "Consulting Agreement"
   - "License Agreement" or "Software License"
   - "Partnership Agreement" or "Joint Venture Agreement"
   - "Purchase Agreement" or "Sales Agreement"
   - "Tenancy Agreement" or "Lease Agreement"
   - "Shareholders Agreement"
   - "Litigation Memo" or "Legal Memo"
   - "Consultancy Agreement"

2. jurisdiction: The legal jurisdiction or governing law. Be specific:
   - "UAE" for United Arab Emirates
   - "UK" for United Kingdom
   - "Delaware, USA" for Delaware state
   - "California, USA" for California state
   - "New York, USA" for New York state
   - "Singapore"
   - "Hong Kong"
   - "Germany"
   - "France"

3. governing_law: The specific governing law mentioned (usually same as jurisdiction)

4. geography: Geographic regions mentioned:
   - "Middle East" for Middle Eastern countries
   - "Gulf Region" for GCC countries
   - "Europe" for European countries
   - "Asia Pacific" for Asian countries
   - "North America" for US/Canada
   - "Gulf Cooperation Council" for GCC

5. industry_sector: The industry sector. Classify into:
   - "Technology" for tech, software, IT, digital
   - "Healthcare" for medical, pharmaceutical, biotech
   - "Oil & Gas" for petroleum, energy, hydrocarbon
   - "Finance" for banking, investment, financial
   - "Real Estate" for property, construction, real estate
   - "Manufacturing" for industrial, production
   - "Retail" for e-commerce, consumer, retail
   - "Energy" for renewable, solar, wind, nuclear
   - "Consulting" for professional services, consulting
   - "Transportation" for logistics, transport
   - "Telecommunications" for telecom, communications

6. parties: List of parties involved (e.g., ["Company A", "Company B"])

7. effective_date: The effective/start date in YYYY-MM-DD format if found

8. expiration_date: The expiration/end date in YYYY-MM-DD format if found

9. contract_value: Numeric value of the contract if mentioned

10. currency: The currency of the contract value (e.g., "USD", "EUR", "GBP", "AED")

11. keywords: List of important legal keywords found (e.g., ["confidentiality", "termination", "liability", "indemnification", "governing law", "jurisdiction", "breach", "remedies"])

12. tags: List of relevant tags for categorization

13. summary: A comprehensive 2-3 sentence summary of the document's key terms and purpose

14. extraction_confidence: Confidence score from 0.0 to 1.0 based on clarity of information

15. document_classification: Additional classification tags:
    - "contract_type": "commercial", "employment", "real_estate", "intellectual_property", "partnership", "service"
    - "complexity": "simple", "moderate", "complex"
    - "risk_level": "low", "medium", "high"
    - "duration": "short_term", "medium_term", "long_term"

Return the data in this exact JSON format:
{
  "documents": [
    {
      "filename": "document1.docx",
      "agreement_type": "string or null",
      "jurisdiction": "string or null", 
      "governing_law": "string or null",
      "geography": "string or null",
      "industry_sector": "string or null",
      "parties": ["array of strings or null"],
      "effective_date": "YYYY-MM-DD or null",
      "expiration_date": "YYYY-MM-DD or null", 
      "contract_value": "number or null",
      "currency": "string or null",
      "keywords": ["array of strings or null"],
      "tags": ["array of strings or null"],
      "summary": "string or null",
      "extraction_confidence": "number between 0.0 and 1.0",
      "document_classification": {
        "contract_type": "string or null",
        "complexity": "string or null",
        "risk_level": "string or null",
        "duration": "string or null"
      }
    }
  ]
}

Analyze each document thoroughly and provide the most accurate classification possible. If information is unclear, use reasonable inference based on the document content and context.
"""

    def _create_batch_user_prompt(self, documents: List[Dict[str, Any]]) -> str:
        """Create the user prompt for batch document processing."""
        prompt_parts = []
        for doc in documents:
            prompt_parts.append(f"Filename: {doc['filename']}\n")
            prompt_parts.append(f"Document Content:\n{doc['text_content']}\n")
            prompt_parts.append("Please extract all relevant metadata and return it in the exact JSON format specified.\n")
            prompt_parts.append("Focus on accuracy and completeness.\n")
        return "\n".join(prompt_parts)
    
    def validate_metadata(self, metadata: Dict[str, Any]) -> bool:
        """Validate the extracted metadata structure."""
        required_fields = [
            "agreement_type", "jurisdiction", "governing_law", "geography", 
            "industry_sector", "parties", "effective_date", "expiration_date",
            "contract_value", "currency", "keywords", "tags", 
            "extraction_confidence", "summary"
        ]
        
        for field in required_fields:
            if field not in metadata:
                logger.warning(f"Missing required field in AI metadata: {field}")
                return False
        
        # Validate confidence score
        confidence = metadata.get("extraction_confidence")
        if confidence is not None and (not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 1):
            logger.warning(f"Invalid confidence score: {confidence}")
            return False
        
        return True
    
    def enhance_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance and clean the extracted metadata."""
        enhanced = metadata.copy()
        
        # Clean up parties list
        if enhanced.get("parties"):
            enhanced["parties"] = [
                party.strip() for party in enhanced["parties"] 
                if party and isinstance(party, str) and len(party.strip()) > 2
            ]
        
        # Clean up keywords list
        if enhanced.get("keywords"):
            enhanced["keywords"] = [
                keyword.strip().lower() for keyword in enhanced["keywords"]
                if keyword and isinstance(keyword, str) and len(keyword.strip()) > 2
            ]
        
        # Clean up tags list
        if enhanced.get("tags"):
            enhanced["tags"] = [
                tag.strip() for tag in enhanced["tags"]
                if tag and isinstance(tag, str) and len(tag.strip()) > 2
            ]
        
        # Ensure dates are in correct format
        for date_field in ["effective_date", "expiration_date"]:
            if enhanced.get(date_field):
                # Try to standardize date format
                try:
                    from datetime import datetime
                    # Parse and convert to datetime object for database
                    if isinstance(enhanced[date_field], str):
                        date_obj = datetime.fromisoformat(enhanced[date_field].replace('Z', '+00:00'))
                        enhanced[date_field] = date_obj
                    elif isinstance(enhanced[date_field], datetime):
                        # Already a datetime object
                        pass
                    else:
                        enhanced[date_field] = None
                except:
                    # If parsing fails, set to None
                    enhanced[date_field] = None
        
        # Ensure numeric fields are numbers
        if enhanced.get("contract_value"):
            try:
                enhanced["contract_value"] = float(enhanced["contract_value"])
            except:
                enhanced["contract_value"] = None
        
        return enhanced 