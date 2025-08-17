import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, CheckCircle, AlertCircle } from 'lucide-react';
import { uploadDocument } from '../services/api';
import toast from 'react-hot-toast';

const UploadPage: React.FC = () => {
  const [uploadedFiles, setUploadedFiles] = useState<Array<{
    name: string;
    status: 'uploading' | 'success' | 'error';
    message?: string;
  }>>([]);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const newFiles = acceptedFiles.map(file => ({
      name: file.name,
      status: 'uploading' as const,
      message: 'Uploading...'
    }));
    
    setUploadedFiles(prev => [...prev, ...newFiles]);
    
    for (let i = 0; i < acceptedFiles.length; i++) {
      const file = acceptedFiles[i];
      const fileIndex = uploadedFiles.length + i;
      
      try {
        await uploadDocument(file);
        setUploadedFiles(prev => prev.map((f, idx) => 
          idx === fileIndex 
            ? { ...f, status: 'success', message: 'Upload successful!' }
            : f
        ));
        toast.success(`${file.name} uploaded successfully!`);
      } catch (error) {
        console.error('Upload failed:', error);
        setUploadedFiles(prev => prev.map((f, idx) => 
          idx === fileIndex 
            ? { ...f, status: 'error', message: 'Upload failed' }
            : f
        ));
        toast.error(`${file.name} upload failed`);
      }
    }
  }, [uploadedFiles.length]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/msword': ['.doc']
    },
    multiple: true
  });

  const getStatusIcon = (status: 'uploading' | 'success' | 'error') => {
    switch (status) {
      case 'uploading':
        return <Upload className="h-5 w-5 text-blue-500 animate-pulse" />;
      case 'success':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'error':
        return <AlertCircle className="h-5 w-5 text-red-500" />;
      default:
        return null;
    }
  };

  const getStatusText = (status: 'uploading' | 'success' | 'error') => {
    switch (status) {
      case 'uploading':
        return 'Uploading...';
      case 'success':
        return 'Uploaded';
      case 'error':
        return 'Failed';
      default:
        return '';
    }
  };

  const getStatusColor = (status: 'uploading' | 'success' | 'error') => {
    switch (status) {
      case 'uploading':
        return 'text-blue-600 bg-blue-50 border-blue-200';
      case 'success':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'error':
        return 'text-red-600 bg-red-50 border-red-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Upload Legal Documents</h1>
        <p className="text-gray-600">
          Upload PDF and DOCX files to extract metadata and enable intelligent querying
        </p>
      </div>

      {/* Upload Zone */}
      <div className="bg-white rounded-lg shadow-sm p-8">
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors cursor-pointer ${
            isDragActive
              ? 'border-primary-400 bg-primary-50'
              : 'border-gray-300 hover:border-primary-400 hover:bg-gray-50'
          }`}
        >
          <input {...getInputProps()} />
          <Upload className="h-16 w-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            {isDragActive ? 'Drop files here' : 'Drag & drop files here'}
          </h3>
          <p className="text-gray-600 mb-4">
            or click to select files
          </p>
          <p className="text-sm text-gray-500">
            Supports PDF, DOCX, and DOC files
          </p>
        </div>
      </div>

      {/* Upload Status */}
      {uploadedFiles.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Upload Status</h3>
          <div className="space-y-3">
            {uploadedFiles.map((file, index) => (
              <div
                key={index}
                className={`flex items-center justify-between p-4 rounded-lg border ${getStatusColor(file.status)}`}
              >
                <div className="flex items-center space-x-3">
                  {getStatusIcon(file.status)}
                  <div>
                    <p className="font-medium">{file.name}</p>
                    <p className="text-sm opacity-75">
                      {getStatusText(file.status)}
                    </p>
                  </div>
                </div>
                {file.message && (
                  <p className="text-sm text-gray-600">{file.message}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Instructions */}
      <div className="bg-blue-50 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-blue-900 mb-3">How it works</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-blue-800">
          <div className="flex items-start space-x-2">
            <div className="w-6 h-6 bg-blue-200 rounded-full flex items-center justify-center text-blue-800 font-semibold text-xs">
              1
            </div>
            <p>Upload your legal documents (PDF, DOCX, DOC)</p>
          </div>
          <div className="flex items-start space-x-2">
            <div className="w-6 h-6 bg-blue-200 rounded-full flex items-center justify-center text-blue-800 font-semibold text-xs">
              2
            </div>
            <p>AI automatically extracts metadata and text content</p>
          </div>
          <div className="flex items-start space-x-2">
            <div className="w-6 h-6 bg-blue-200 rounded-full flex items-center justify-center text-blue-800 font-semibold text-xs">
              3
            </div>
            <p>Query your documents using natural language</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UploadPage; 