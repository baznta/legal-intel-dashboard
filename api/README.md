# Legal Intel Dashboard - Backend API

## Overview

This is the backend API for the Legal Intel Dashboard, a platform that allows users to upload legal documents, extract metadata, and perform natural language queries across the document dataset.

## Architecture

The backend is built with a modern, production-ready architecture:

- **FastAPI**: High-performance async web framework
- **PostgreSQL**: Primary database with SQLAlchemy ORM
- **Redis**: Caching and Celery broker
- **MinIO**: S3-compatible object storage
- **Celery**: Background task processing
- **Docker**: Containerized deployment

## Features

### Core Functionality
- Document upload and storage (PDF, DOCX)
- Text extraction and metadata analysis
- Natural language query processing
- Dashboard analytics and insights
- Background document processing

### Production Features
- Health monitoring and checks
- Structured logging
- Error handling and retry logic
- Rate limiting and security
- Async processing and scalability

## Project Structure

```
api/
├── core/                   # Core configuration and utilities
│   ├── config.py          # Application settings
│   ├── database.py        # Database connection and models
│   └── minio_client.py    # MinIO storage client
├── models/                 # SQLAlchemy database models
│   └── document.py        # Document-related models
├── schemas/                # Pydantic schemas
│   └── document.py        # API request/response schemas
├── services/               # Business logic services
│   ├── document_service.py # Document operations
│   └── llm_service.py     # LLM integration (mock)
├── routes/                 # API route handlers
│   ├── documents.py       # Document management
│   ├── health.py          # Health checks
│   ├── query.py           # Natural language queries
│   └── dashboard.py       # Analytics dashboard
├── workers/                # Celery background tasks
│   ├── celery_app.py      # Celery configuration
│   └── tasks.py           # Background task definitions
├── main.py                 # FastAPI application entry point
├── requirements.txt        # Python dependencies
├── Dockerfile             # Container configuration
└── README.md              # This file
```

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- MinIO

### 1. Clone and Setup
```bash
git clone <repository-url>
cd legal-intel-dashboard
```

### 2. Environment Configuration
```bash
cd api
cp env.example .env
# Edit .env with your configuration
```

### 3. Start Services
```bash
# From project root
docker-compose up -d
```

This will start:
- PostgreSQL database
- Redis cache
- MinIO storage
- API service
- Celery workers

### 4. Verify Setup
```bash
# Check API health
curl http://localhost:8000/health

# Check API documentation
open http://localhost:8000/docs
```

## API Endpoints

### Health Checks
- `GET /health` - Basic health check
- `GET /health/detailed` - Detailed service health
- `GET /health/ready` - Kubernetes readiness probe
- `GET /health/live` - Kubernetes liveness probe

### Document Management
- `POST /api/v1/documents/upload` - Upload documents
- `GET /api/v1/documents` - List documents
- `GET /api/v1/documents/{id}` - Get document details
- `DELETE /api/v1/documents/{id}` - Delete document
- `GET /api/v1/documents/{id}/download` - Download document
- `GET /api/v1/documents/{id}/metadata` - Get document metadata
- `GET /api/v1/documents/{id}/content` - Get document content

### Query Interface
- `POST /api/v1/query` - Natural language query
- `GET /api/v1/query/examples` - Query examples
- `GET /api/v1/query/suggestions` - Query suggestions

### Dashboard Analytics
- `GET /api/v1/dashboard` - Comprehensive dashboard data
- `GET /api/v1/dashboard/agreement-types` - Agreement type analytics
- `GET /api/v1/dashboard/jurisdictions` - Jurisdiction analytics
- `GET /api/v1/dashboard/trends` - Upload trends

## Development

### Local Development Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://legal_user:legal_pass123@localhost:5432/legal_intel"
export REDIS_URL="redis://localhost:3030"
export MINIO_ENDPOINT="localhost:9000"

# Run API
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Running Tests
```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest
```

### Code Quality
```bash
# Format code
black .
isort .

# Lint code
flake8
```

## Production Deployment

### Docker Deployment
```bash
# Build and start services
docker-compose -f docker-compose.prod.yml up -d

# Scale API services
docker-compose up -d --scale api=3
```

### Environment Variables
Set these environment variables in production:
- `DEBUG=false`
- `SECRET_KEY=<strong-secret-key>`
- `DATABASE_URL=<production-db-url>`
- `REDIS_URL=<production-redis-url>`
- `MINIO_ENDPOINT=<production-minio-url>`

### Monitoring
- Health checks: `/health/detailed`
- Metrics: Prometheus endpoints (planned)
- Logging: Structured JSON logs
- Database: Connection pooling and monitoring

## Database Schema

### Core Tables
- `documents`: Main document records
- `document_metadata`: Extracted metadata
- `document_content`: Extracted text content
- `document_processing_jobs`: Background job tracking

### Key Relationships
- One document can have one metadata record
- One document can have one content record
- One document can have multiple processing jobs

## Background Processing

### Celery Tasks
- `process_document`: Main document processing
- `extract_metadata`: Metadata extraction
- `extract_text`: Text extraction

### Task Queues
- `document_processing`: Main processing queue
- `metadata_extraction`: Metadata extraction queue
- `text_extraction`: Text extraction queue

## Security Features

- CORS configuration
- Rate limiting (planned)
- Input validation with Pydantic
- SQL injection protection
- File type validation
- Size limits

## Performance Considerations

- Async/await throughout
- Database connection pooling
- Redis caching
- Background task processing
- File streaming for large uploads
- Pagination for large result sets

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check PostgreSQL is running
   - Verify connection string in .env
   - Check network connectivity

2. **MinIO Connection Failed**
   - Verify MinIO service is running
   - Check credentials in .env
   - Ensure bucket exists

3. **Redis Connection Failed**
   - Check Redis service is running
   - Verify connection string
   - Check network connectivity

### Logs
```bash
# View API logs
docker-compose logs api

# View Celery logs
docker-compose logs celery

# View database logs
docker-compose logs postgres
```

## Contributing

1. Follow the existing code structure
2. Add tests for new functionality
3. Update documentation
4. Use type hints and docstrings
5. Follow PEP 8 style guidelines

## License

This project is licensed under the MIT License - see the LICENSE file for details. 