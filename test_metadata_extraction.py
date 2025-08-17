#!/usr/bin/env python3
"""
Test script for enhanced metadata extraction capabilities.
This demonstrates the robust rule-based extraction system.
"""

import re
from datetime import datetime
from typing import Dict, Any, Optional

def extract_enhanced_metadata(text_content: str, filename: str) -> Dict[str, Any]:
    """Enhanced metadata extraction using comprehensive rule-based patterns."""
    metadata = {}
    text_lower = text_content.lower()
    filename_lower = filename.lower()
    
    # 1. AGREEMENT TYPE EXTRACTION
    agreement_type_patterns = {
        "NDA": [
            r"non.?disclosure\s+agreement",
            r"nda\s+agreement",
            r"confidentiality\s+agreement"
        ],
        "MSA": [
            r"master\s+services?\s+agreement",
            r"msa\s+agreement"
        ],
        "Franchise Agreement": [
            r"franchise\s+agreement"
        ],
        "Employment Agreement": [
            r"employment\s+agreement"
        ],
        "Tenancy Agreement": [
            r"tenancy\s+agreement"
        ]
    }
    
    for agreement_type, patterns in agreement_type_patterns.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                metadata["agreement_type"] = agreement_type
                break
        if "agreement_type" in metadata:
            break
    
    # 2. JURISDICTION & GOVERNING LAW
    jurisdiction_patterns = [
        r"governed\s+by\s+the\s+laws?\s+of\s+the\s+([A-Za-z\s]+?)(?:\s|,|\.|$)",
        r"governed\s+by\s+the\s+laws?\s+of\s+([A-Za-z\s]+?)(?:\s|,|\.|$)",
        r"jurisdiction\s+of\s+([A-Za-z\s]+?)(?:\s|,|\.|$)",
        r"([A-Za-z\s]+?)\s+law\s+shall\s+govern",
        r"laws\s+of\s+the\s+([A-Za-z\s]+?)(?:\s|,|\.|$)",
        r"courts\s+of\s+([A-Za-z\s]+?)(?:\s|,|\.|$)"
    ]
    
    jurisdiction_mapping = {
        "uae": "UAE", "united arab emirates": "UAE",
        "uk": "UK", "united kingdom": "UK", "england": "UK",
        "usa": "USA", "united states": "USA", "delaware": "Delaware, USA",
        "singapore": "Singapore", "germany": "Germany"
    }
    
    for pattern in jurisdiction_patterns:
        match = re.search(pattern, text_lower)
        if match:
            jurisdiction = match.group(1).strip().lower()
            for key, value in jurisdiction_mapping.items():
                if key in jurisdiction:
                    metadata["jurisdiction"] = value
                    metadata["governing_law"] = value
                    break
            else:
                metadata["jurisdiction"] = jurisdiction.title()
                metadata["governing_law"] = jurisdiction.title()
            break
    
    # 3. GEOGRAPHY
    geography_patterns = [
        r"(\w+(?:\s+\w+)*)\s+region",
        r"(\w+(?:\s+\w+)*)\s+territory",
        r"(\w+(?:\s+\w+)*)\s+state",
        r"(\w+(?:\s+\w+)*)\s+country",
        r"(\w+(?:\s+\w+)*)\s+valley",
        r"(\w+(?:\s+\w+)*)\s+area",
        r"(\w+(?:\s+\w+)*)\s+district"
    ]
    
    geography_mapping = {
        "middle east": "Middle East", "gulf region": "Gulf Region",
        "europe": "Europe", "european union": "European Union",
        "asia": "Asia", "asia pacific": "Asia Pacific",
        "north america": "North America", "silicon valley": "Silicon Valley, USA"
    }
    
    for pattern in geography_patterns:
        match = re.search(pattern, text_lower)
        if match:
            geography = match.group(1).strip().lower()
            # Filter out section headers and common words
            if (geography not in ["governing", "law", "and", "jurisdiction", "this", "agreement", "shall", "be", "governed", "by", "construed", "accordance", "with", "laws", "of", "the", "state", "united", "states", "america", "disputes", "arising", "out", "relating", "subject", "exclusive", "courts"] and
                len(geography) > 3):
                for key, value in geography_mapping.items():
                    if key in geography:
                        metadata["geography"] = value
                        break
                else:
                    metadata["geography"] = geography.title()
                break
    
    # 4. INDUSTRY SECTOR
    industry_patterns = {
        "Technology": [
            r"technology", r"artificial intelligence", r"cybersecurity",
            r"software", r"hardware", r"digital"
        ],
        "Healthcare": [
            r"healthcare", r"medical", r"pharmaceutical"
        ],
        "Finance": [
            r"finance", r"banking", r"investment"
        ],
        "Oil & Gas": [
            r"oil\s+and\s+gas", r"petroleum", r"hydrocarbon"
        ]
    }
    
    for industry, patterns in industry_patterns.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                metadata["industry_sector"] = industry
                break
        if "industry_sector" in metadata:
            break
    
    # 5. PARTIES
    parties_patterns = [
        r"between\s+([^:]+?)\s+and\s+([^:]+?)(?:\s|,|\.|$)",
        r"([^:]+?)\s+\(hereinafter\s+referred\s+to\s+as\s+[^)]+\)"
    ]
    
    parties = []
    for pattern in parties_patterns:
        matches = re.findall(pattern, text_content, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                parties.extend([party.strip() for party in match if party.strip()])
            else:
                parties.append(match.strip())
    
    if parties:
        metadata["parties"] = list(set(parties))
    
    # 6. DATES
    date_patterns = [
        r"effective\s+date[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
        r"(\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{4})"
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, text_lower)
        if match:
            try:
                date_str = match.group(1)
                if "effective_date" not in metadata:
                    metadata["effective_date"] = date_str
                break
            except:
                pass
    
    # 7. CONTRACT VALUE & CURRENCY
    currency_patterns = [
        r"(\$[\d,]+(?:\.\d{2})?)",
        r"(\d+(?:,\d{3})*(?:\.\d{2})?\s*(?:USD|US\s*Dollars?))"
    ]
    
    for pattern in currency_patterns:
        match = re.search(pattern, text_content, re.IGNORECASE)
        if match:
            amount_str = match.group(1)
            metadata["currency"] = "USD"
            amount_clean = re.sub(r'[^\d.]', '', amount_str)
            try:
                metadata["contract_value"] = float(amount_clean)
            except:
                pass
            break
    
    # 8. KEYWORDS
    legal_keywords = [
        "confidentiality", "termination", "liability", "indemnification",
        "force majeure", "governing law", "dispute resolution", "breach",
        "remedies", "waiver", "severability", "entire agreement"
    ]
    
    found_keywords = []
    for keyword in legal_keywords:
        if keyword in text_lower:
            found_keywords.append(keyword)
    
    if found_keywords:
        metadata["keywords"] = found_keywords
    
    # 9. TAGS
    tags = []
    if "agreement_type" in metadata:
        tags.append(metadata["agreement_type"])
    if "industry_sector" in metadata:
        tags.append(metadata["industry_sector"])
    if "jurisdiction" in metadata:
        tags.append(metadata["jurisdiction"])
    
    if tags:
        metadata["tags"] = tags
    
    # 10. CONFIDENCE SCORE
    confidence_score = 0.0
    confidence_factors = {
        "agreement_type": 0.2,
        "jurisdiction": 0.15,
        "geography": 0.1,
        "industry_sector": 0.15,
        "parties": 0.1,
        "effective_date": 0.1,
        "contract_value": 0.05,
        "currency": 0.05,
        "keywords": 0.05
    }
    
    for field, weight in confidence_factors.items():
        if field in metadata and metadata[field]:
            confidence_score += weight
    
    metadata["extraction_confidence"] = min(confidence_score, 1.0)
    
    return metadata

def main():
    """Test the enhanced metadata extraction."""
    print("🔍 Enhanced Metadata Extraction Test")
    print("=" * 50)
    
    # Read test document
    with open("test_document.txt", "r") as f:
        content = f.read()
    
    # Extract metadata
    metadata = extract_enhanced_metadata(content, "test_document.txt")
    
    # Display results
    print("\n📋 Extracted Metadata:")
    print("-" * 30)
    
    for key, value in metadata.items():
        if value is not None:
            print(f"✅ {key}: {value}")
        else:
            print(f"❌ {key}: Not found")
    
    print(f"\n🎯 Overall Confidence: {metadata.get('extraction_confidence', 0):.1%}")
    
    # Summary
    print(f"\n📊 Summary:")
    print(f"   • Agreement Type: {metadata.get('agreement_type', 'Unknown')}")
    print(f"   • Jurisdiction: {metadata.get('jurisdiction', 'Unknown')}")
    print(f"   • Industry: {metadata.get('industry_sector', 'Unknown')}")
    print(f"   • Geography: {metadata.get('geography', 'Unknown')}")
    print(f"   • Parties: {len(metadata.get('parties', []))} found")
    print(f"   • Contract Value: {metadata.get('currency', 'N/A')} {metadata.get('contract_value', 'N/A')}")
    print(f"   • Keywords: {len(metadata.get('keywords', []))} legal terms found")

if __name__ == "__main__":
    main() 