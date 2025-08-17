# 🏛️ Legal Intelligence Dashboard

A powerful, AI-powered legal document management and analysis platform built with FastAPI, React, and OpenAI. Extract metadata, classify documents, and query your legal documents using natural language.

## ✨ Features

### 🔍 **Intelligent Document Processing**
- **AI-Powered Metadata Extraction**: Uses OpenAI GPT to automatically extract key information from legal documents
- **Multi-Format Support**: Handles PDF, DOCX, TXT, and other common document formats
- **Smart Classification**: Automatically categorizes documents by type, jurisdiction, industry, and more
- **Batch Processing**: Process multiple documents simultaneously with progress tracking

### 🎯 **Advanced Query System**
- **Natural Language Queries**: Ask questions like "Show me tech industry contracts" or "Find NDA documents in UAE"
- **Fuzzy Matching**: Handles misspellings and typos intelligently (e.g., "teck industy" → "Technology Industry")
- **Multi-Criteria Search**: Filter by agreement type, jurisdiction, industry sector, dates, and more
- **Smart Suggestions**: Get helpful query suggestions when searches fail

### 📊 **Comprehensive Dashboard**
- **Real-time Analytics**: View document counts, processing status, and metadata distribution
- **Interactive Charts**: Visualize data by agreement type, jurisdiction, industry, and geography
- **Document Management**: Upload, delete, reprocess, and manage documents with ease
- **Status Tracking**: Monitor document processing from upload to completion

### 🚀 **Enterprise Features**
- **Scalable Architecture**: Built with Docker, Celery, and Redis for production readiness
- **Secure Storage**: MinIO object storage with proper access controls
- **Background Processing**: Asynchronous document processing with Celery workers
- **RESTful API**: Clean, documented API endpoints for integration

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   FastAPI       │    │   Celery        │
│   (React/TS)    │◄──►│   Backend       │◄──►│   Workers       │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   PostgreSQL    │    │   MinIO         │
                       │   Database      │    │   Storage       │
                       └─────────────────┘    └─────────────────┘
```

## 🛠️ Prerequisites

- **Docker & Docker Compose** (v2.0+)
- **OpenAI API Key** (for AI-powered metadata extraction)
- **Git** (for cloning the repository)
- **4GB+ RAM** (recommended for smooth operation)

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd legal-intel-dashboard
```

### 2. Set Up Environment
```bash
# Copy environment template
cp env.example .env

# Edit environment variables
nano .env
```

**Required Environment Variables:**
```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini

# Database Configuration
POSTGRES_DB=legal_intel
POSTGRES_USER=legal_user
POSTGRES_PASSWORD=secure_password

# MinIO Configuration
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin123

# API Configuration
API_SECRET_KEY=your_secret_key_here
```

### 3. Start the Application
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

### 4. Access the Application
- **Frontend**: http://localhost:3000
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin123)

## 📋 Detailed Setup

### Database Initialization
The application automatically creates the database schema on first run. If you need to manually initialize:

```bash
# Access the API container
docker-compose exec api bash

# Run database initialization
python manage.py init-db
```

### MinIO Bucket Setup
MinIO automatically creates the required bucket (`legal-documents`) on startup.

### OpenAI API Key Setup
1. Get your API key from [OpenAI Platform](https://platform.openai.com/api-keys)
2. Add it to your `.env` file
3. Restart the API service: `docker-compose restart api`

## 🎯 Usage Guide

### 📤 Uploading Documents

1. **Navigate to Documents Page**: Click "Documents" in the sidebar
2. **Upload Files**: Drag & drop or click to select documents
3. **Supported Formats**: PDF, DOCX, TXT, RTF
4. **Auto-Processing**: Documents are automatically queued for processing

### 🔍 Querying Documents

#### Natural Language Queries
Use plain English to search your documents:

```
✅ "Show me all NDA documents"
✅ "Find contracts in the technology sector"
✅ "Which agreements are governed by UAE law?"
✅ "Show documents with high confidence scores"
✅ "Find recent employment contracts"
```

#### Advanced Queries
```
✅ "contracts in tech industry" (handles misspellings)
✅ "agreemnts in realestate" (corrects typos)
✅ "UAE jurisdiction contracts" (specific criteria)
✅ "documents expiring this year" (date-based)
```

#### Query Examples
| Query | What It Finds |
|-------|---------------|
| `"tech industry contracts"` | All contracts in technology sector |
| `"UAE jurisdiction"` | Documents governed by UAE law |
| `"high confidence NDAs"` | NDA documents with confidence >80% |
| `"recent agreements"` | Documents uploaded this year |
| `"partnership documents"` | Partnership agreements and joint ventures |

### 📊 Dashboard Analytics

#### Document Overview
- **Total Documents**: Count of all processed documents
- **Processing Status**: Real-time status of document pipeline
- **Storage Usage**: MinIO storage consumption

#### Metadata Charts
- **Agreement Types**: Distribution by document type (NDA, MSA, etc.)
- **Jurisdictions**: Documents by governing law
- **Industry Sectors**: Business domain classification
- **Geographic Distribution**: Regional breakdown

### 🗂️ Document Management

#### Individual Document Operations
- **View Details**: Click document name to see full metadata
- **Download**: Access original file
- **Reprocess**: Re-extract metadata if needed
- **Delete**: Remove document and all associated data

#### Bulk Operations
- **Select Multiple**: Use checkboxes for batch selection
- **Bulk Delete**: Remove multiple documents at once
- **Process All**: Queue all pending documents for processing

#### Document Statuses
- **`uploaded`**: File uploaded, waiting for processing
- **`extracting_text`**: Currently extracting text content
- **`text_extracted`**: Text extracted, ready for metadata
- **`extracting_metadata`**: AI analyzing document content
- **`metadata_extracted`**: Metadata extraction complete
- **`completed`**: Fully processed and ready for querying
- **`failed`**: Processing encountered an error
- **`deleted`**: Document marked for deletion

### 🔄 Reprocessing Documents

If metadata extraction quality is poor or you want to reclassify documents:

1. **Navigate to Documents**: Go to the Documents page
2. **Find Document**: Locate the document you want to reprocess
3. **Click Reprocess**: Use the "Reprocess" button
4. **Wait for Completion**: Monitor the processing status
5. **Verify Results**: Check the new metadata extraction

## 🧪 Testing the System

### Test Document Upload
```bash
# Create a test document
echo "This is a test NDA agreement between Company A and Company B." > test_document.txt

# Upload via API
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test_document.txt"
```

### Test Natural Language Query
```bash
# Test basic query
curl -X POST "http://localhost:8000/api/v1/query/simple" \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me all contracts"}'

# Test misspelling handling
curl -X POST "http://localhost:8000/api/v1/query/simple" \
  -H "Content-Type: application/json" \
  -d '{"query": "teck industy contracts"}'
```

### Test Document Processing
```bash
# Process all pending documents
curl -X POST "http://localhost:8000/api/v1/process-all"

# Check processing status
curl "http://localhost:8000/api/v1/documents"
```

## 🔧 Configuration

### API Configuration
```python
# api/core/config.py
API_V1_STR = "/api/v1"
PROJECT_NAME = "Legal Intelligence Dashboard"
BACKEND_CORS_ORIGINS = ["http://localhost:3000"]
```

### Celery Configuration
```python
# api/core/celery_app.py
CELERY_BROKER_URL = "redis://redis:6379//"
CELERY_RESULT_BACKEND = "redis://redis:6379/"
CELERY_TASK_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]
```

### MinIO Configuration
```python
# api/core/minio_client.py
MINIO_ENDPOINT = "minio:9000"
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin123"
MINIO_BUCKET_NAME = "legal-documents"
```

## 🚨 Troubleshooting

### Common Issues

#### 1. API Won't Start
```bash
# Check logs
docker-compose logs api

# Common causes:
# - Missing environment variables
# - Database connection issues
# - Port conflicts
```

#### 2. Document Processing Fails
```bash
# Check Celery worker logs
docker-compose logs celery

# Verify OpenAI API key
docker-compose exec api python -c "import os; print(os.getenv('OPENAI_API_KEY'))"
```

#### 3. Frontend Can't Connect to API
```bash
# Check API is running
curl http://localhost:8000/health

# Verify CORS configuration
# Check browser console for errors
```

#### 4. Database Connection Issues
```bash
# Test database connectivity
docker-compose exec api python -c "
from core.database import get_db
import asyncio
async def test():
    async for db in get_db():
        print('Database connected!')
        break
asyncio.run(test())
"
```

### Performance Optimization

#### For Large Document Collections
```bash
# Increase Celery concurrency
CELERY_CONCURRENCY=16

# Enable Redis persistence
redis:
  command: redis-server --appendonly yes
```

#### For Production Deployment
```bash
# Use external PostgreSQL
POSTGRES_HOST=your-db-host
POSTGRES_PORT=5432

# Use external Redis
REDIS_URL=redis://your-redis-host:6379

# Configure MinIO for production
MINIO_ENDPOINT=your-minio-host:9000
```

## 📚 API Reference

### Core Endpoints

#### Documents
- `POST /api/v1/documents/upload` - Upload new document
- `GET /api/v1/documents` - List all documents
- `GET /api/v1/documents/{id}` - Get document details
- `DELETE /api/v1/documents/{id}` - Delete document
- `POST /api/v1/documents/{id}/process` - Process specific document
- `POST /api/v1/documents/{id}/reprocess` - Reprocess document

#### Processing
- `POST /api/v1/process-all` - Process all pending documents
- `GET /api/v1/documents/{id}/status` - Get processing status

#### Query
- `POST /api/v1/query/simple` - Natural language query
- `POST /api/v1/query/advanced` - Structured query

#### Dashboard
- `GET /api/v1/dashboard/stats` - Get dashboard statistics
- `GET /api/v1/dashboard/charts` - Get chart data

### Response Formats

#### Query Response
```json
{
  "query": "tech industry contracts",
  "parsed_criteria": {
    "agreement_type": "CONTRACTS",
    "industry_sector": "Technology"
  },
  "total_results": 7,
  "results": [...],
  "query_type": "document_search"
}
```

#### Document Response
```json
{
  "document_id": "uuid",
  "filename": "Contract.docx",
  "status": "completed",
  "metadata": {
    "agreement_type": "Service Agreement",
    "jurisdiction": "UAE",
    "industry_sector": "Technology"
  }
}
```

## 🔒 Security Considerations

### API Security
- **Secret Keys**: Use strong, unique secret keys
- **CORS**: Configure allowed origins carefully
- **Rate Limiting**: Implement rate limiting for production

### Data Privacy
- **Document Storage**: Documents stored securely in MinIO
- **Database**: PostgreSQL with proper access controls
- **API Keys**: Store OpenAI keys securely in environment variables

### Production Deployment
- **HTTPS**: Use SSL/TLS for all communications
- **Firewall**: Restrict access to necessary ports only
- **Monitoring**: Implement logging and monitoring
- **Backups**: Regular database and document backups

## 🤝 Contributing

### Development Setup
```bash
# Clone repository
git clone <repo-url>
cd legal-intel-dashboard

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r api/requirements.txt
cd frontend && npm install

# Run locally
cd api && uvicorn main:app --reload
cd frontend && npm start
```

### Code Style
- **Python**: Follow PEP 8, use type hints
- **TypeScript**: Use strict mode, proper interfaces
- **React**: Functional components with hooks
- **API**: RESTful design, proper error handling

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Getting Help
1. **Check Logs**: Use `docker-compose logs` to debug issues
2. **API Documentation**: Visit `/docs` endpoint for interactive API docs
3. **GitHub Issues**: Report bugs and feature requests
4. **Documentation**: Refer to this README and inline code comments

### Community
- **Discussions**: Use GitHub Discussions for questions
- **Contributions**: Pull requests welcome for improvements
- **Issues**: Report bugs with detailed reproduction steps

---

**Built with ❤️ for the legal community**

*Transform your legal document management with AI-powered intelligence* 