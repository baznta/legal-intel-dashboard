import React, { useState, useEffect } from 'react';
import { Search, FileText, Calendar, MapPin, Building, Users, Tag } from 'lucide-react';
import { simpleQuery, getQueryExamples, getQuerySuggestions } from '../services/api';
import { SimpleQueryResponse, DocumentResult } from '../types/api';
import toast from 'react-hot-toast';

const QueryPage: React.FC = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<DocumentResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [examples, setExamples] = useState<any[]>([]);
  const [suggestions, setSuggestions] = useState<string[]>([]);

  useEffect(() => {
    const loadExamples = async () => {
      try {
        const examplesData = await getQueryExamples();
        setExamples(examplesData.examples || []);
      } catch (error) {
        console.error('Failed to load examples:', error);
      }
    };

    loadExamples();
  }, []);

  useEffect(() => {
    if (query.length > 3) {
      const loadSuggestions = async () => {
        try {
          const suggestionsData = await getQuerySuggestions(query);
          setSuggestions(suggestionsData.suggestions || []);
        } catch (error) {
          console.error('Failed to load suggestions:', error);
        }
      };

      const timeoutId = setTimeout(loadSuggestions, 500);
      return () => clearTimeout(timeoutId);
    } else {
      setSuggestions([]);
    }
  }, [query]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    try {
      const response: SimpleQueryResponse = await simpleQuery({ query: query.trim() });
      setResults(response.results || []);
      toast.success(`Found ${response.total_results} documents`);
    } catch (error) {
      console.error('Query error:', error);
      toast.error('Failed to execute query');
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleExampleClick = (exampleQuery: string) => {
    setQuery(exampleQuery);
  };

  const handleSuggestionClick = (suggestion: string) => {
    setQuery(suggestion);
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A';
    try {
      return new Date(dateString).toLocaleDateString();
    } catch {
      return 'Invalid Date';
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Natural Language Query</h1>
        <p className="text-gray-600">
          Ask questions about your legal documents using natural language
        </p>
      </div>

      {/* Query Form */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="query" className="block text-sm font-medium text-gray-700 mb-2">
              What would you like to know?
            </label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
              <input
                type="text"
                id="query"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="e.g., Which agreements are governed by UAE law?"
                className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
          </div>

          {/* Suggestions */}
          {suggestions.length > 0 && (
            <div className="space-y-2">
              <p className="text-sm text-gray-600">Suggestions:</p>
              <div className="flex flex-wrap gap-2">
                {suggestions.map((suggestion, index) => (
                  <button
                    key={index}
                    type="button"
                    onClick={() => handleSuggestionClick(suggestion)}
                    className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded-full transition-colors"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          )}

          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="w-full bg-primary-600 text-white py-3 px-6 rounded-lg font-medium hover:bg-primary-700 focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? 'Searching...' : 'Search Documents'}
          </button>
        </form>
      </div>

      {/* Examples */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Example Queries</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {examples.map((example, index) => (
            <button
              key={index}
              onClick={() => handleExampleClick(example.query)}
              className="text-left p-4 border border-gray-200 rounded-lg hover:border-primary-300 hover:bg-primary-50 transition-colors"
            >
              <p className="font-medium text-gray-900 mb-1">{example.query}</p>
              <p className="text-sm text-gray-600">{example.description}</p>
              <span className="inline-block mt-2 px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded">
                {example.category}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Results */}
      {results.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Results ({results.length} documents)
          </h3>
          <div className="space-y-4">
            {results.map((result, index) => (
              <div key={index} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center space-x-2">
                    <FileText className="h-5 w-5 text-primary-600" />
                    <h4 className="font-medium text-gray-900">{result.filename}</h4>
                  </div>
                  <span className={`px-2 py-1 text-xs rounded-full ${
                    result.status === 'completed' ? 'bg-green-100 text-green-800' :
                    result.status === 'processing' ? 'bg-yellow-100 text-yellow-800' :
                    result.status === 'failed' ? 'bg-red-100 text-red-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {result.status}
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 text-sm">
                  {result.agreement_type && (
                    <div className="flex items-center space-x-2">
                      <Tag className="h-4 w-4 text-gray-400" />
                      <span className="text-gray-600">Type:</span>
                      <span className="font-medium">{result.agreement_type}</span>
                    </div>
                  )}

                  {result.jurisdiction && (
                    <div className="flex items-center space-x-2">
                      <MapPin className="h-4 w-4 text-gray-400" />
                      <span className="text-gray-600">Jurisdiction:</span>
                      <span className="font-medium">{result.jurisdiction}</span>
                    </div>
                  )}

                  {result.industry_sector && (
                    <div className="flex items-center space-x-2">
                      <Building className="h-4 w-4 text-gray-400" />
                      <span className="text-gray-600">Industry:</span>
                      <span className="font-medium">{result.industry_sector}</span>
                    </div>
                  )}

                  {result.parties && result.parties.length > 0 && (
                    <div className="flex items-center space-x-2">
                      <Users className="h-4 w-4 text-gray-400" />
                      <span className="text-gray-600">Parties:</span>
                      <span className="font-medium">{result.parties.join(', ')}</span>
                    </div>
                  )}

                  {result.effective_date && (
                    <div className="flex items-center space-x-2">
                      <Calendar className="h-4 w-4 text-gray-400" />
                      <span className="text-gray-600">Effective:</span>
                      <span className="font-medium">{formatDate(result.effective_date)}</span>
                    </div>
                  )}

                  {result.extraction_confidence && (
                    <div className="flex items-center space-x-2">
                      <div className="w-4 h-4 rounded-full bg-gray-200 flex items-center justify-center">
                        <span className="text-xs font-bold text-gray-600">
                          {Math.round(result.extraction_confidence * 100)}%
                        </span>
                      </div>
                      <span className="text-gray-600">Confidence</span>
                    </div>
                  )}
                </div>

                {result.summary && (
                  <div className="mt-3 pt-3 border-t border-gray-200">
                    <p className="text-sm text-gray-600">
                      <span className="font-medium">Summary:</span> {result.summary}
                    </p>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* No Results */}
      {results.length === 0 && !loading && query && (
        <div className="bg-white rounded-lg shadow-sm p-6 text-center">
          <Search className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No documents found</h3>
          <p className="text-gray-600">
            Try adjusting your query or check if documents have been uploaded and processed.
          </p>
        </div>
      )}
    </div>
  );
};

export default QueryPage; 