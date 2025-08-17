import React, { useState, useEffect } from 'react';
import { FileText, Eye, RefreshCw, Play, PlayCircle } from 'lucide-react';
import { 
  getDocuments,
  deleteDocument, 
  bulkDeleteDocuments, 
  processDocument, 
  processAllDocuments, 
  getDocumentMetadata, 
  getDocumentContent,
  reprocessDocument
} from '../services/api';
import { Document, DocumentMetadata, DocumentContent } from '../types/api';
import toast from 'react-hot-toast';

const DocumentsPage: React.FC = () => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);
  const [documentMetadata, setDocumentMetadata] = useState<DocumentMetadata | null>(null);
  const [documentContent, setDocumentContent] = useState<DocumentContent | null>(null);
  const [showDetails, setShowDetails] = useState(false);
  const [isBatchProcessing, setIsBatchProcessing] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [documentToDelete, setDocumentToDelete] = useState<{ id: string; filename: string } | null>(null);
  const [selectedDocuments, setSelectedDocuments] = useState<Set<string>>(new Set());
  const [showBulkDeleteConfirm, setShowBulkDeleteConfirm] = useState(false);

  useEffect(() => {
    loadDocuments();
  }, []);

  const loadDocuments = async () => {
    try {
      setLoading(true);
      const docs = await getDocuments();
      setDocuments(docs);
    } catch (error) {
      console.error('Failed to load documents:', error);
      toast.error('Failed to load documents');
    } finally {
      setLoading(false);
    }
  };

  const handleProcessAllDocuments = async () => {
    try {
      const docsToProcess = documents.filter(doc => 
        doc.status === 'pending' || doc.status === 'uploaded'
      );
      
      if (docsToProcess.length === 0) {
        toast('No documents to process', { icon: 'ℹ️' });
        return;
      }

      toast.loading(`Starting batch processing for ${docsToProcess.length} documents...`);
      const result = await processAllDocuments();
      
      toast.dismiss();
      
      if (result.status === 'NO_DOCUMENTS_TO_PROCESS') {
        toast.success('No documents to process');
        return;
      }
      
      toast.success(`Batch processing started! Task ID: ${result.task_id}`);
      
      // Start polling for status updates
      startStatusPolling();
      
    } catch (error) {
      console.error('Failed to start batch processing:', error);
      toast.error('Failed to start batch processing');
    }
  };

  const startStatusPolling = () => {
    setIsBatchProcessing(true);
    
    // Poll every 3 seconds for status updates
    const pollInterval = setInterval(async () => {
      try {
        await loadDocuments();
        
        // Check if all documents are processed
        const allProcessed = documents.every(doc => 
          doc.status === 'completed' || doc.status === 'failed' || doc.status === 'deleted'
        );
        
        if (allProcessed) {
          clearInterval(pollInterval);
          setIsBatchProcessing(false);
          toast.success('Batch processing completed!');
        }
      } catch (error) {
        console.error('Failed to poll for status updates:', error);
      }
    }, 3000);
    
    // Stop polling after 5 minutes (300 seconds)
    setTimeout(() => {
      clearInterval(pollInterval);
      setIsBatchProcessing(false);
    }, 300000);
  };

  const handleProcessDocument = async (documentId: string, event: React.MouseEvent) => {
    event.stopPropagation(); // Prevent opening document details
    
    try {
      toast.loading('Starting document processing...');
      await processDocument(documentId);
      
      toast.dismiss();
      toast.success('Document processing started!');
      
      // Refresh the documents list after a short delay
      setTimeout(() => {
        loadDocuments();
      }, 2000);
      
    } catch (error) {
      console.error('Failed to start document processing:', error);
      toast.error('Failed to start document processing');
    }
  };

  const handleReprocessDocument = async (documentId: string, filename: string, event: React.MouseEvent) => {
    event.stopPropagation();
    
    try {
      toast.loading(`Reprocessing ${filename}...`);
      await reprocessDocument(documentId);
      
      toast.dismiss();
      toast.success(`${filename} reprocessing started successfully`);
      
      // Refresh the documents list
      loadDocuments();
      
    } catch (error) {
      toast.dismiss();
      console.error('Failed to reprocess document:', error);
      toast.error(`Failed to reprocess ${filename}`);
    }
  };

  const handleDeleteDocument = async (documentId: string, filename: string, event: React.MouseEvent) => {
    event.stopPropagation(); // Prevent opening document details
    
    setDocumentToDelete({ id: documentId, filename });
    setShowDeleteConfirm(true);
  };

  const confirmDelete = async () => {
    if (!documentToDelete) return;
    
    try {
      toast.loading('Deleting document...');
      await deleteDocument(documentToDelete.id);
      
      toast.dismiss();
      toast.success('Document deleted successfully');
      
      // Close modals and refresh
      setShowDeleteConfirm(false);
      setDocumentToDelete(null);
      setShowDetails(false);
      setSelectedDocument(null);
      
      // Refresh the documents list
      await loadDocuments();
      
    } catch (error) {
      console.error('Failed to delete document:', error);
      toast.error('Failed to delete document');
    }
  };

  const handleBulkDelete = async () => {
    if (selectedDocuments.size === 0) return;
    
    // Filter out documents that are currently processing
    const processingDocs = documents.filter(doc => 
      selectedDocuments.has(doc.id) && doc.status === 'processing'
    );
    
    if (processingDocs.length > 0) {
      toast.error(`Cannot delete ${processingDocs.length} document(s) that are currently being processed`);
      return;
    }
    
    setShowBulkDeleteConfirm(true);
  };

  const confirmBulkDelete = async () => {
    if (selectedDocuments.size === 0) return;
    
    try {
      const documentIds = Array.from(selectedDocuments);
      toast.loading(`Deleting ${documentIds.length} documents...`);
      
      const result = await bulkDeleteDocuments(documentIds);
      
      toast.dismiss();
      
      if (result.failed_count > 0) {
        toast.success(`Bulk delete completed. Deleted: ${result.deleted_count}, Failed: ${result.failed_count}`);
        if (result.errors) {
          console.error('Bulk delete errors:', result.errors);
        }
      } else {
        toast.success(`Successfully deleted ${result.deleted_count} documents`);
      }
      
      // Close modal and refresh
      setShowBulkDeleteConfirm(false);
      setSelectedDocuments(new Set());
      
      // Refresh the documents list
      await loadDocuments();
      
    } catch (error) {
      console.error('Failed to bulk delete documents:', error);
      toast.error('Failed to bulk delete documents');
    }
  };

  const toggleDocumentSelection = (documentId: string) => {
    const newSelection = new Set(selectedDocuments);
    if (newSelection.has(documentId)) {
      newSelection.delete(documentId);
    } else {
      newSelection.add(documentId);
    }
    setSelectedDocuments(newSelection);
  };

  const handleDocumentClick = async (document: Document) => {
    setSelectedDocument(document);
    setShowDetails(true);
    
    try {
      const [metadata, content] = await Promise.all([
        getDocumentMetadata(document.id),
        getDocumentContent(document.id)
      ]);
      setDocumentMetadata(metadata);
      setDocumentContent(content);
    } catch (error) {
      console.error('Failed to load document details:', error);
      toast.error('Failed to load document details');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'processing':
        return 'bg-yellow-100 text-yellow-800';
      case 'pending':
        return 'bg-blue-100 text-blue-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Documents</h1>
            <p className="text-gray-600">
              View and manage your uploaded legal documents
            </p>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={loadDocuments}
              className="flex items-center space-x-2 bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 transition-colors"
            >
              <RefreshCw className="h-4 w-4" />
              <span>Refresh</span>
            </button>
            <button
              onClick={handleProcessAllDocuments}
              disabled={isBatchProcessing}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors ${
                isBatchProcessing 
                  ? 'bg-gray-400 cursor-not-allowed text-white' 
                  : 'bg-green-600 hover:bg-green-700 text-white'
              }`}
            >
              {isBatchProcessing ? (
                <>
                  <RefreshCw className="h-4 w-4 animate-spin" />
                  <span>Processing...</span>
                </>
              ) : (
                <>
                  <Play className="h-4 w-4" />
                  <span>Process All</span>
                </>
              )}
            </button>
            {selectedDocuments.size > 0 && (
              <button
                onClick={handleBulkDelete}
                className="flex items-center space-x-2 bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors"
              >
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
                <span>Delete Selected ({selectedDocuments.size})</span>
              </button>
            )}
          </div>
        </div>
        
        {/* Batch Processing Status */}
        {isBatchProcessing && (
          <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-md">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <RefreshCw className="w-4 h-4 text-blue-600 mr-2 animate-spin" />
                <span className="text-blue-800 font-medium">
                  Batch processing in progress... Documents are being updated automatically.
                </span>
              </div>
              <div className="text-sm text-blue-600">
                Refreshing every 3 seconds
              </div>
            </div>
            
            {/* Progress Bar */}
            <div className="mt-3 w-full bg-blue-200 rounded-full h-2">
              <div className="bg-blue-600 h-2 rounded-full animate-pulse" style={{ width: '100%' }}></div>
            </div>
          </div>
        )}
      </div>

      {/* Documents List */}
      <div className="bg-white rounded-lg shadow-sm">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">
              All Documents ({documents.length})
            </h2>
            {documents.length > 0 && (
              <div className="flex items-center space-x-3">
                <label className="flex items-center space-x-2 text-sm text-gray-600">
                  <input
                    type="checkbox"
                    checked={selectedDocuments.size === documents.length && documents.length > 0}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedDocuments(new Set(documents.map(doc => doc.id)));
                      } else {
                        setSelectedDocuments(new Set());
                      }
                    }}
                    className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                  />
                  <span>Select All</span>
                </label>
                {selectedDocuments.size > 0 && (
                  <span className="text-sm text-gray-500">
                    {selectedDocuments.size} selected
                  </span>
                )}
              </div>
            )}
          </div>
        </div>
        
        {documents.length === 0 ? (
          <div className="p-8 text-center">
            <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No documents found</h3>
            <p className="text-gray-600">
              Upload some documents to get started.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {documents.map((document) => (
              <div
                key={document.id}
                className="p-6 hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className="flex-shrink-0">
                      <input
                        type="checkbox"
                        checked={selectedDocuments.has(document.id)}
                        onChange={(e) => {
                          e.stopPropagation();
                          toggleDocumentSelection(document.id);
                        }}
                        className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                      />
                    </div>
                    <div className="flex-shrink-0">
                      <FileText className="h-8 w-8 text-primary-600" />
                    </div>
                    <div 
                      className="cursor-pointer"
                      onClick={() => handleDocumentClick(document)}
                    >
                      <h3 className="text-lg font-medium text-gray-900">
                        {document.original_filename}
                      </h3>
                      <div className="flex items-center space-x-4 text-sm text-gray-500 mt-1">
                        <span>{formatFileSize(document.file_size)}</span>
                        <span>•</span>
                        <span>{document.file_extension.toUpperCase()}</span>
                        <span>•</span>
                        <span>Uploaded {formatDate(document.uploaded_at)}</span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-4">
                    <span className={`px-3 py-1 text-sm font-medium rounded-full ${getStatusColor(document.status)}`}>
                      {document.status}
                    </span>
                    {document.status === 'pending' && (
                      <button
                        onClick={(e) => handleProcessDocument(document.id, e)}
                        className="flex items-center space-x-1 bg-green-600 text-white px-2 py-1 rounded text-xs hover:bg-green-700 transition-colors"
                        title="Process Document"
                      >
                        <PlayCircle className="h-3 w-3" />
                        <span>Process</span>
                      </button>
                    )}
                    {(document.status === 'completed' || document.status === 'failed') && (
                      <button
                        onClick={(e) => handleReprocessDocument(document.id, document.original_filename, e)}
                        className="flex items-center space-x-1 bg-blue-600 text-white px-2 py-1 rounded text-xs hover:bg-blue-700 transition-colors"
                        title="Reprocess Document"
                      >
                        <RefreshCw className="h-3 w-3" />
                        <span>Reprocess</span>
                      </button>
                    )}
                    <button
                      onClick={(e) => handleDeleteDocument(document.id, document.original_filename, e)}
                      disabled={document.status === 'processing'}
                      className={`flex items-center space-x-1 px-2 py-1 rounded text-xs transition-colors ${
                        document.status === 'processing'
                          ? 'bg-gray-400 cursor-not-allowed text-white'
                          : 'bg-red-600 hover:bg-red-700 text-white'
                      }`}
                      title={document.status === 'processing' ? 'Cannot delete while processing' : 'Delete Document'}
                    >
                      <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                      <span>Delete</span>
                    </button>
                    <Eye className="h-5 w-5 text-gray-400" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Document Details Modal */}
      {showDetails && selectedDocument && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold text-gray-900">
                  Document Details
                </h2>
                <div className="flex items-center space-x-3">
                  {selectedDocument.status === 'pending' && (
                    <button
                      onClick={(e) => handleProcessDocument(selectedDocument.id, e)}
                      className="flex items-center space-x-2 bg-green-600 text-white px-3 py-2 rounded-md text-sm hover:bg-green-700 transition-colors"
                    >
                      <PlayCircle className="h-4 w-4" />
                      <span>Process</span>
                    </button>
                  )}
                  {(selectedDocument.status === 'completed' || selectedDocument.status === 'failed') && (
                    <button
                      onClick={(e) => handleReprocessDocument(selectedDocument.id, selectedDocument.original_filename, e)}
                      className="flex items-center space-x-2 bg-blue-600 text-white px-3 py-2 rounded-md text-sm hover:bg-blue-700 transition-colors"
                    >
                      <RefreshCw className="h-4 w-4" />
                      <span>Reprocess</span>
                    </button>
                  )}
                  <button
                    onClick={(e) => handleDeleteDocument(selectedDocument.id, selectedDocument.original_filename, e)}
                    className="flex items-center space-x-2 bg-red-600 text-white px-3 py-2 rounded-md text-sm hover:bg-red-700 transition-colors"
                  >
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                    <span>Delete</span>
                  </button>
                  <button
                    onClick={() => setShowDetails(false)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>

            <div className="p-6 space-y-6">
              {/* Basic Info */}
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-3">Basic Information</h3>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="font-medium text-gray-600">Filename:</span>
                    <p className="text-gray-900">{selectedDocument.original_filename}</p>
                  </div>
                  <div>
                    <span className="font-medium text-gray-600">File Size:</span>
                    <p className="text-gray-900">{formatFileSize(selectedDocument.file_size)}</p>
                  </div>
                  <div>
                    <span className="font-medium text-gray-600">Status:</span>
                    <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(selectedDocument.status)}`}>
                      {selectedDocument.status}
                    </span>
                  </div>
                  <div>
                    <span className="font-medium text-gray-600">Uploaded:</span>
                    <p className="text-gray-900">{formatDate(selectedDocument.uploaded_at)}</p>
                  </div>
                </div>
              </div>

              {/* Metadata */}
              {documentMetadata && (
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-3">Extracted Metadata</h3>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="font-medium text-gray-600">Agreement Type:</span>
                      <p className="text-gray-900">
                        {documentMetadata.agreement_type || <span className="text-gray-400 italic">Not specified</span>}
                      </p>
                    </div>
                    <div>
                      <span className="font-medium text-gray-600">Jurisdiction:</span>
                      <p className="text-gray-900">
                        {documentMetadata.jurisdiction || <span className="text-gray-400 italic">Not specified</span>}
                      </p>
                    </div>
                    <div>
                      <span className="font-medium text-gray-600">Industry Sector:</span>
                      <p className="text-gray-900">
                        {documentMetadata.industry_sector || <span className="text-gray-400 italic">Not specified</span>}
                      </p>
                    </div>
                    <div>
                      <span className="font-medium text-gray-600">Confidence:</span>
                      <p className="text-gray-900">
                        {documentMetadata.extraction_confidence ? 
                          `${Math.round(documentMetadata.extraction_confidence * 100)}%` : 
                          <span className="text-gray-400 italic">Not available</span>
                        }
                      </p>
                    </div>
                    <div>
                      <span className="font-medium text-gray-600">Extraction Method:</span>
                      <p className="text-gray-900 capitalize">
                        {documentMetadata.extraction_method ? 
                          documentMetadata.extraction_method.replace('_', ' ') : 
                          <span className="text-gray-400 italic">Not specified</span>
                        }
                      </p>
                    </div>
                    {documentMetadata.contract_value && (
                      <div>
                        <span className="font-medium text-gray-600">Contract Value:</span>
                        <p className="text-gray-900">
                          {documentMetadata.contract_value} {documentMetadata.currency || ''}
                        </p>
                      </div>
                    )}
                  </div>

                  {documentMetadata.summary && (
                    <div className="mt-4">
                      <span className="font-medium text-gray-600">Summary:</span>
                      <p className="text-gray-900 mt-1">{documentMetadata.summary}</p>
                    </div>
                  )}
                </div>
              )}

              {/* Content Preview */}
              {documentContent && (
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-3">Content Preview</h3>
                  <div className="bg-gray-50 rounded-lg p-4 max-h-64 overflow-y-auto">
                    <p className="text-sm text-gray-700 whitespace-pre-wrap">
                      {documentContent.text_content ? (
                        <>
                          {documentContent.text_content.substring(0, 1000)}
                          {documentContent.text_content.length > 1000 && '...'}
                        </>
                      ) : (
                        'No text content available'
                      )}
                    </p>
                  </div>
                  <div className="mt-2 text-sm text-gray-500">
                    {documentContent.word_count || 0} words • {documentContent.character_count || 0} characters
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && documentToDelete && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-md w-full p-6">
            <div className="flex items-center mb-4">
              <div className="flex-shrink-0">
                <svg className="h-6 w-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-lg font-medium text-gray-900">Delete Document</h3>
                <p className="text-sm text-gray-500">
                  Are you sure you want to delete "{documentToDelete.filename}"?
                </p>
              </div>
            </div>
            
            <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                  </svg>
                </div>
                <div className="ml-3">
                  <h4 className="text-sm font-medium text-red-800">Warning</h4>
                  <p className="text-sm text-red-700 mt-1">
                    This action cannot be undone. The document and all its extracted data will be permanently removed.
                  </p>
                </div>
              </div>
            </div>
            
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => {
                  setShowDeleteConfirm(false);
                  setDocumentToDelete(null);
                }}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
              >
                Cancel
              </button>
              <button
                onClick={confirmDelete}
                className="px-4 py-2 text-sm font-medium text-white bg-red-600 border border-transparent rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
              >
                Delete Document
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Bulk Delete Confirmation Modal */}
      {showBulkDeleteConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-md w-full p-6">
            <div className="flex items-center mb-4">
              <div className="flex-shrink-0">
                <svg className="h-6 w-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-lg font-medium text-gray-900">Delete Multiple Documents</h3>
                <p className="text-sm text-gray-500">
                  Are you sure you want to delete {selectedDocuments.size} documents?
                </p>
              </div>
            </div>
            
            <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                  </svg>
                </div>
                <div className="ml-3">
                  <h4 className="text-sm font-medium text-red-800">Warning</h4>
                  <p className="text-sm text-red-700 mt-1">
                    This action cannot be undone. All selected documents and their extracted data will be permanently removed.
                  </p>
                </div>
              </div>
            </div>
            
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setShowBulkDeleteConfirm(false)}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
              >
                Cancel
              </button>
              <button
                onClick={confirmBulkDelete}
                className="px-4 py-2 text-sm font-medium text-white bg-red-600 border border-transparent rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
              >
                Delete {selectedDocuments.size} Documents
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DocumentsPage; 