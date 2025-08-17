#!/bin/bash

# Legal Intel Dashboard OpenAI Setup Script

echo "🤖 Legal Intel Dashboard OpenAI Setup"
echo "======================================"

# Check if .env file exists
if [ -f ".env" ]; then
    echo "✅ .env file found"
    
    # Check if OpenAI is already configured
    if grep -q "OPENAI_API_KEY" .env; then
        echo "✅ OpenAI configuration found in .env"
        echo ""
        echo "Current OpenAI settings:"
        grep "OPENAI" .env | while read line; do
            if [[ $line == *"API_KEY"* ]]; then
                echo "  API Key: ${line:0:20}..."
            else
                echo "  $line"
            fi
        done
    else
        echo "❌ OpenAI configuration not found in .env"
        echo ""
        echo "📝 Adding OpenAI configuration to .env..."
        echo "" >> .env
        echo "# OpenAI Configuration" >> .env
        echo "OPENAI_API_KEY=your-openai-api-key-here" >> .env
        echo "OPENAI_MODEL=gpt-4o-mini" >> .env
        echo "OPENAI_MAX_TOKENS=4000" >> .env
        echo "OPENAI_TEMPERATURE=0.1" >> .env
        echo "✅ OpenAI configuration added to .env"
    fi
else
    echo "❌ .env file not found"
    echo "📝 Creating .env file from template..."
    cp env.example .env
    echo "✅ .env file created from env.example"
fi

echo ""
echo "🔑 To use AI-powered metadata extraction:"
echo "   1. Get your OpenAI API key from https://platform.openai.com/api-keys"
echo "   2. Edit .env file and set OPENAI_API_KEY=your-actual-api-key"
echo "   3. Restart the services: docker-compose up -d --build"
echo ""
echo "💡 The system will automatically:"
echo "   - Use AI extraction when API key is configured"
echo "   - Fall back to rule-based extraction if AI fails"
echo "   - Provide structured JSON output with high accuracy"
echo ""
echo "🚀 Ready to test AI-powered metadata extraction!" 