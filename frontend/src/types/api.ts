// Document types
export interface Document {
  id: string;
  filename: string;
  original_filename: string;
  file_path: string;
  file_size: number;
  mime_type: string;
  file_extension: string;
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'uploaded' | 'extracting_text' | 'text_extracted' | 'extracting_metadata' | 'metadata_extracted' | 'deleted';
  uploaded_at: string;
  updated_at: string;
  deleted_at?: string;
  processing_started_at?: string;
  processing_completed_at?: string;
  processing_error?: string;
}

export interface DocumentMetadata {
  id: string;
  document_id: string;
  agreement_type?: string;
  jurisdiction?: string;
  governing_law?: string;
  geography?: string;
  industry_sector?: string;
  parties?: string[];
  effective_date?: string;
  expiration_date?: string;
  contract_value?: number;
  currency?: string;
  keywords?: string[];
  tags?: string[];
  summary?: string;
  extraction_confidence?: number;
  extraction_method?: 'ai_powered' | 'rule_based';
  extracted_at: string;
}

export interface DocumentContent {
  id: string;
  document_id: string;
  text_content: string;
  word_count: number;
  character_count: number;
  sections?: any[];
  paragraphs?: any[];
  tables?: any[];
  extraction_method: string;
  extraction_timestamp: string;
  confidence_score?: number;
  language_detected?: string;
}

// Query types
export interface QueryRequest {
  query: string;
  filters?: any;
  limit?: number;
  offset?: number;
}

export interface DocumentQueryRequest {
  query: string;
  filters?: any;
  limit?: number;
  offset?: number;
}

export interface DocumentQueryResponse {
  query: string;
  results: DocumentResult[];
  total_results: number;
  processing_time: number;
  confidence_score: number;
}

export interface SimpleQueryRequest {
  query: string;
}

export interface SimpleQueryResponse {
  query: string;
  parsed_criteria?: any;
  total_results: number;
  results: DocumentResult[];
  query_type?: string;
}

export interface QuerySuggestion {
  query: string;
  suggestions: string[];
  total_suggestions: number;
}

export interface DocumentResult {
  document_id: string;
  filename: string;
  status: string;
  uploaded_at?: string;
  file_size?: number;
  file_extension?: string;
  agreement_type?: string;
  jurisdiction?: string;
  governing_law?: string;
  geography?: string;
  industry_sector?: string;
  parties?: string[];
  effective_date?: string;
  expiration_date?: string;
  contract_value?: number;
  currency?: string;
  keywords?: string[];
  tags?: string[];
  summary?: string;
  extraction_confidence?: number;
  extraction_method?: string;
  word_count?: number;
  character_count?: number;
  content_preview?: string;
}

// Dashboard types
export interface DashboardData {
  agreement_types: Record<string, number>;
  jurisdictions: Record<string, number>;
  industries: Record<string, number>;
  geography: Record<string, number>;
  document_statistics: {
    total_documents: number;
    status_breakdown: Record<string, number>;
    file_size_statistics: {
      average_size_bytes: number;
      min_size_bytes: number;
      max_size_bytes: number;
      total_size_bytes: number;
      average_size_mb: number;
      total_size_mb: number;
    };
    recent_uploads_30_days: number;
    upload_rate_per_day: number;
  };
  recent_uploads: Array<{
    id: string;
    filename: string;
    uploaded_at: string;
    status: string;
    file_size: number;
    file_extension: string;
    agreement_type?: string;
    jurisdiction?: string;
    industry_sector?: string;
  }>;
  processing_statistics: {
    processing_status: Record<string, number>;
    success_rate_percentage: number;
    total_processed: number;
    total_documents: number;
  };
  generated_at: string;
}

export interface ProcessingOverview {
  system_overview: {
    total_documents: number;
    total_processing_jobs: number;
    active_workers: number;
    success_rate_percentage: number;
  };
  document_status_breakdown: Record<string, number>;
  job_status_breakdown: Record<string, number>;
  recent_processing_jobs: Array<{
    job_id: string;
    document_id: string;
    job_type: string;
    status: string;
    created_at: string;
    started_at?: string;
    completed_at?: string;
  }>;
  processing_metrics: {
    successful_jobs: number;
    failed_jobs: number;
    pending_jobs: number;
    processing_jobs: number;
  };
  timestamp: string;
}

// Upload types
export interface UploadResponse {
  id: string;
  filename: string;
  status: string;
  file_size: number;
  message: string;
}

// Error types
export interface ApiError {
  detail: string;
  status_code?: number;
}

// Processing Job types
export interface DocumentProcessingJob {
  id: string;
  document_id: string;
  job_type: string;
  status: string;
  priority: number;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  result_data?: any;
  error_message?: string;
  retry_count: number;
  max_retries: number;
}

export interface ProcessingJobResponse {
  job_id: string;
  status: string;
  message: string;
}

// Health check types
export interface HealthCheckResponse {
  status: string;
  timestamp: string;
  services: {
    database: string;
    redis: string;
    minio: string;
    celery: string;
  };
} 