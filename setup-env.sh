#!/bin/bash

# Legal Intel Dashboard Environment Setup Script

echo "🔧 Legal Intel Dashboard Environment Setup"
echo "=========================================="

# Check if .env file exists
if [ -f ".env" ]; then
    echo "✅ .env file found"
else
    echo "❌ .env file not found"
    echo "📝 Creating .env file from template..."
    cp env.example .env
    echo "✅ .env file created from env.example"
fi

# Check if .env file is in .gitignore
if grep -q "\.env" .gitignore; then
    echo "✅ .env file is properly ignored in .gitignore"
else
    echo "⚠️  .env file is NOT in .gitignore"
    echo "📝 Adding .env to .gitignore..."
    echo ".env" >> .gitignore
    echo "✅ .env added to .gitignore"
fi

echo ""
echo "📋 Current environment variables:"
echo "=================================="
echo "Database: ${POSTGRES_DB:-'Not set'}"
echo "Redis: ${REDIS_URL:-'Not set'}"
echo "MinIO: ${MINIO_ENDPOINT:-'Not set'}"
echo ""

echo "🚀 To start services with new environment:"
echo "   docker-compose down"
echo "   docker-compose up -d --build"
echo ""
echo "🔐 Remember to change default passwords in production!"
echo "   Current passwords are in .env file" 