import axios from 'axios';
import { 
  Document, 
  DocumentMetadata, 
  DocumentContent, 
  DashboardData, 
  DocumentQueryRequest, 
  DocumentQueryResponse, 
  QuerySuggestion, 
  UploadResponse,
  ProcessingOverview
} from '../types/api';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Health check
export const checkHealth = async (): Promise<boolean> => {
  try {
    const response = await api.get('/health');
    return response.status === 200;
  } catch (error) {
    console.error('Health check failed:', error);
    return false;
  }
};

// Document upload
export const uploadDocument = async (file: File): Promise<UploadResponse> => {
  const formData = new FormData();
  formData.append('files', file);
  
  const response = await api.post('/api/v1/documents/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  
  // Backend returns an array of responses, but we're uploading one file
  // so we return the first (and only) response
  return response.data[0];
};

// Document processing
export const processDocument = async (documentId: string): Promise<any> => {
  const response = await api.post(`/api/v1/documents/${documentId}/process`);
  return response.data;
};

// Get document status
export const getDocumentStatus = async (documentId: string): Promise<any> => {
  const response = await api.get(`/api/v1/documents/${documentId}/status`);
  return response.data;
};

// Get document metadata
export const getDocumentMetadata = async (documentId: string): Promise<DocumentMetadata> => {
  const response = await api.get(`/api/v1/documents/${documentId}/metadata`);
  return response.data;
};

// Get document content
export const getDocumentContent = async (documentId: string): Promise<DocumentContent> => {
  const response = await api.get(`/api/v1/documents/${documentId}/content`);
  return response.data;
};

// Get all documents
export const getDocuments = async (): Promise<Document[]> => {
  const response = await api.get('/api/v1/documents');
  return response.data;
};

// Query documents (main endpoint)
export const queryDocuments = async (request: DocumentQueryRequest): Promise<DocumentQueryResponse> => {
  const response = await api.post('/api/v1/query', request);
  return response.data;
};

// Simple query endpoint
export const simpleQuery = async (request: DocumentQueryRequest): Promise<DocumentQueryResponse> => {
  const response = await api.post('/api/v1/query/simple', request);
  return response.data;
};

// Get query examples
export const getQueryExamples = async (): Promise<any> => {
  const response = await api.get('/api/v1/query/examples');
  return response.data;
};

// Get query suggestions
export const getQuerySuggestions = async (query: string): Promise<QuerySuggestion> => {
  const response = await api.get(`/api/v1/query/suggestions?query=${encodeURIComponent(query)}`);
  return response.data;
};

// Get dashboard data
export const getDashboardData = async (): Promise<DashboardData> => {
  const response = await api.get('/api/v1/dashboard');
  return response.data;
};

// Get processing overview
export const getProcessingOverview = async (): Promise<ProcessingOverview> => {
  const response = await api.get('/api/v1/dashboard/processing-overview');
  return response.data;
};

// Error interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.data?.detail) {
      console.error('API Error:', error.response.data.detail);
    } else {
      console.error('API Error:', error.message);
    }
    return Promise.reject(error);
  }
);

export default api; 

export const resetDocumentStatus = async (documentId: string): Promise<void> => {
  await api.post(`/api/v1/documents/${documentId}/reset`);
};

export const processAllDocuments = async (): Promise<{ 
  task_id: string; 
  status: string; 
  message: string;
  pending_count?: number;
}> => {
  const response = await api.post('/api/v1/process-all');
  return response.data;
};

// Delete document
export const deleteDocument = async (documentId: string): Promise<{ message: string }> => {
  const response = await api.delete(`/api/v1/documents/${documentId}`);
  return response.data;
};

// Bulk delete documents
export const bulkDeleteDocuments = async (documentIds: string[]): Promise<{
  message: string;
  deleted_count: number;
  failed_count: number;
  total_requested: number;
  errors?: string[];
}> => {
  const response = await api.delete('/api/v1/documents/bulk', { 
    data: { document_ids: documentIds }
  });
  return response.data;
}; 

export const reprocessDocument = async (documentId: string): Promise<any> => {
  try {
    const response = await fetch(`${API_BASE_URL}/documents/${documentId}/reprocess`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error reprocessing document:', error);
    throw error;
  }
}; 