#!/usr/bin/env python3
"""
Test script for AI-powered metadata extraction using OpenAI GPT-4o Mini.
"""

import os
import sys
import json
from pathlib import Path

# Add the api directory to the path
sys.path.append(str(Path(__file__).parent / "api"))

def test_ai_extraction():
    """Test the AI metadata extraction service."""
    
    print("🤖 Testing AI-Powered Metadata Extraction")
    print("=" * 50)
    
    try:
        # Import the AI service
        from services.ai_metadata_service import AIMetadataService
        
        # Initialize the service
        ai_service = AIMetadataService()
        
        if not ai_service.client:
            print("❌ OpenAI client not configured")
            print("💡 Set OPENAI_API_KEY in your .env file")
            return
        
        print("✅ OpenAI client configured successfully")
        print(f"📋 Model: {ai_service.model}")
        print(f"🔢 Max tokens: {ai_service.max_tokens}")
        print(f"🌡️  Temperature: {ai_service.temperature}")
        
        # Test with sample legal document content
        test_content = """
        NON-DISCLOSURE AGREEMENT (NDA)
        
        This Non-Disclosure Agreement ("Agreement") is made on this 17th day of August, 2025, by and between:
        
        1. Disclosing Party: TechCorp Solutions LLC, a Delaware limited liability company with its principal place of business at 123 Innovation Drive, San Francisco, California 94105 ("Disclosing Party")
        
        2. Receiving Party: Bright Horizon Marketing FZ-LLC, a UAE limited liability company with its principal place of business at Sheikh Zayed Road, Dubai, United Arab Emirates ("Receiving Party")
        
        WHEREAS, the parties wish to explore a potential business relationship in the technology and marketing sectors;
        
        WHEREAS, the Disclosing Party may disclose confidential information to the Receiving Party;
        
        NOW, THEREFORE, in consideration of the mutual promises and covenants contained herein, the parties agree as follows:
        
        1. CONFIDENTIAL INFORMATION: "Confidential Information" means any information disclosed by the Disclosing Party to the Receiving Party, either directly or indirectly, in writing, orally or by inspection of tangible objects, which is designated as "Confidential," "Proprietary" or some similar designation.
        
        2. NON-DISCLOSURE: The Receiving Party agrees not to disclose any Confidential Information to any third party without the prior written consent of the Disclosing Party.
        
        3. TERM: This Agreement shall remain in effect for a period of three (3) years from the date of execution.
        
        4. GOVERNING LAW: This Agreement shall be governed by and construed in accordance with the laws of the State of Delaware, United States of America.
        
        5. JURISDICTION: Any disputes arising out of or relating to this Agreement shall be subject to the exclusive jurisdiction of the courts of the State of Delaware.
        
        6. CONFIDENTIALITY OBLIGATIONS: The Receiving Party shall use the Confidential Information solely for the purpose of evaluating the potential business relationship and shall not use such information for any other purpose.
        
        7. RETURN OF MATERIALS: Upon the termination of this Agreement, the Receiving Party shall return all Confidential Information to the Disclosing Party or destroy such information.
        
        IN WITNESS WHEREOF, the parties have executed this Agreement as of the date first above written.
        
        Disclosing Party:
        _________________________
        TechCorp Solutions LLC
        Date: 17/08/2025
        
        Receiving Party:
        _________________________
        Bright Horizon Marketing FZ-LLC
        Date: 17/08/2025
        """
        
        print("\n📄 Testing with sample NDA document...")
        print("=" * 50)
        
        # Extract metadata using AI
        metadata = ai_service.extract_metadata_with_ai(test_content, "NDA_UAE_Tech_Marketing.docx")
        
        if metadata:
            print("✅ AI metadata extraction successful!")
            print("\n📊 Extracted Metadata:")
            print(json.dumps(metadata, indent=2, ensure_ascii=False))
            
            # Validate the metadata
            if ai_service.validate_metadata(metadata):
                print("\n✅ Metadata validation passed")
                
                # Enhance the metadata
                enhanced = ai_service.enhance_metadata(metadata)
                print("\n🚀 Enhanced Metadata:")
                print(json.dumps(enhanced, indent=2, ensure_ascii=False))
            else:
                print("\n❌ Metadata validation failed")
        else:
            print("❌ AI metadata extraction failed")
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure you're running this from the project root directory")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Check your OpenAI API key and configuration")

if __name__ == "__main__":
    test_ai_extraction() 