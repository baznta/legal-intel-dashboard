import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { getDashboardData, getProcessingOverview } from '../services/api';
import { DashboardData, ProcessingOverview } from '../types/api';
import { FileText, CheckCircle, Clock, AlertCircle, XCircle, TrendingUp, MapPin, Building2, Globe } from 'lucide-react';

const DashboardPage: React.FC = () => {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [processingOverview, setProcessingOverview] = useState<ProcessingOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [dashboard, processing] = await Promise.all([
          getDashboardData(),
          getProcessingOverview()
        ]);
        setDashboardData(dashboard);
        setProcessingOverview(processing);
      } catch (err) {
        setError('Failed to load dashboard data');
        console.error('Dashboard error:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    
    // Set up periodic refresh every 30 seconds
    const interval = setInterval(fetchData, 30000);
    
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8">
        <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">Error Loading Dashboard</h3>
        <p className="text-gray-600">{error}</p>
      </div>
    );
  }

  if (!dashboardData || !processingOverview) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-600">No data available</p>
      </div>
    );
  }

  // Extract processing overview data from the actual API response
  const systemOverview = processingOverview.system_overview || {};
  const documentStatusBreakdown = processingOverview.document_status_breakdown || {};

  // Prepare chart data
  const agreementTypeData = Object.entries(dashboardData.agreement_types).map(([type, count]) => ({
    name: type,
    value: count,
  }));

  const jurisdictionData = Object.entries(dashboardData.jurisdictions).map(([jurisdiction, count]) => ({
    name: jurisdiction,
    value: count,
  }));

  const industryData = Object.entries(dashboardData.industries).map(([industry, count]) => ({
    name: industry,
    value: count,
  }));

  const geographyData = Object.entries(dashboardData.geography).map(([geo, count]) => ({
    name: geo,
    value: count,
  }));

  // Prepare table data for industry and geographic coverage
  const coverageTableData = Object.entries(dashboardData.industries).map(([industry, count]) => {
    const geoCount = Object.entries(dashboardData.geography).reduce((total, [geo, geoCount]) => {
      // This is a simplified mapping - in a real app you'd have industry-geography relationships
      return total + geoCount;
    }, 0);
    
    return {
      industry,
      documentCount: count,
      geographicCoverage: geoCount,
      percentage: ((count / dashboardData.document_statistics.total_documents) * 100).toFixed(1)
    };
  });

  const COLORS = ['#3b82f6', '#8b5cf6', '#06b6d4', '#10b981', '#f59e0b', '#ef4444', '#84cc16', '#f97316'];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Legal Intelligence Dashboard</h1>
        <p className="text-gray-600">Comprehensive overview of your legal document collection and processing status</p>
        <div className="mt-4 flex items-center space-x-4 text-sm text-gray-500">
          <span>Last updated: {new Date(dashboardData.generated_at).toLocaleString()}</span>
          <span>•</span>
          <span>Total Documents: {dashboardData.document_statistics.total_documents}</span>
        </div>
      </div>

      {/* Processing Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center">
            <FileText className="h-8 w-8 text-blue-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Total Documents</p>
              <p className="text-2xl font-bold text-gray-900">{systemOverview.total_documents || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center">
            <CheckCircle className="h-8 w-8 text-green-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Completed</p>
              <p className="text-2xl font-bold text-gray-900">{documentStatusBreakdown.completed || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center">
            <Clock className="h-8 w-8 text-yellow-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Processing</p>
              <p className="text-2xl font-bold text-gray-900">{documentStatusBreakdown.processing || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center">
            <AlertCircle className="h-8 w-8 text-orange-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Pending</p>
              <p className="text-2xl font-bold text-gray-900">{documentStatusBreakdown.pending || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center">
            <XCircle className="h-8 w-8 text-red-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Failed</p>
              <p className="text-2xl font-bold text-gray-900">{documentStatusBreakdown.failed || 0}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Agreement Types Bar Chart */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center mb-4">
            <FileText className="h-5 w-5 text-blue-600 mr-2" />
            <h3 className="text-lg font-semibold text-gray-900">Agreement Types Distribution</h3>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={agreementTypeData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip formatter={(value) => [value, 'Documents']} />
              <Bar dataKey="value" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Jurisdictions Pie Chart */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center mb-4">
            <Globe className="h-5 w-5 text-purple-600 mr-2" />
            <h3 className="text-lg font-semibold text-gray-900">Governing Law Breakdown</h3>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={jurisdictionData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {jurisdictionData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip formatter={(value) => [value, 'Documents']} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Industry and Geography Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Industry Sectors Bar Chart */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center mb-4">
            <Building2 className="h-5 w-5 text-green-600 mr-2" />
            <h3 className="text-lg font-semibold text-gray-900">Industry Sectors</h3>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={industryData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip formatter={(value) => [value, 'Documents']} />
              <Bar dataKey="value" fill="#10b981" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Geographic Coverage Bar Chart */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center mb-4">
            <MapPin className="h-5 w-5 text-orange-600 mr-2" />
            <h3 className="text-lg font-semibold text-gray-900">Geographic Coverage</h3>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={geographyData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip formatter={(value) => [value, 'Documents']} />
              <Bar dataKey="value" fill="#f59e0b" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Industry and Geographic Coverage Table */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex items-center mb-6">
          <TrendingUp className="h-5 w-5 text-indigo-600 mr-2" />
          <h3 className="text-lg font-semibold text-gray-900">Industry & Geographic Coverage Analysis</h3>
        </div>
        
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Industry Sector
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Document Count
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Geographic Coverage
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  % of Total
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {coverageTableData.map((row, index) => (
                <tr key={index} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">{row.industry}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">{row.documentCount}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">{row.geographicCoverage}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">{row.percentage}%</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      row.documentCount > 2 
                        ? 'bg-green-100 text-green-800' 
                        : row.documentCount > 1 
                        ? 'bg-yellow-100 text-yellow-800' 
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {row.documentCount > 2 ? 'High' : row.documentCount > 1 ? 'Medium' : 'Low'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Document Statistics Summary */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Document Processing Summary</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">
              {systemOverview.success_rate_percentage || 0}%
            </div>
            <div className="text-sm text-gray-600">Processing Success Rate</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">
              {dashboardData.document_statistics.upload_rate_per_day}
            </div>
            <div className="text-sm text-gray-600">Documents per Day</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">
              {(dashboardData.document_statistics.file_size_statistics.total_size_mb).toFixed(2)} MB
            </div>
            <div className="text-sm text-gray-600">Total Storage Used</div>
          </div>
        </div>
      </div>

      {/* System Health */}
      {processingOverview.system_overview && (
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">System Health</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {processingOverview.system_overview.active_workers || 0}
              </div>
              <div className="text-sm text-gray-600">Active Workers</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {processingOverview.system_overview.total_processing_jobs || 0}
              </div>
              <div className="text-sm text-gray-600">Total Processing Jobs</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">
                {processingOverview.processing_metrics?.successful_jobs || 0}
              </div>
              <div className="text-sm text-gray-600">Successful Jobs</div>
            </div>
          </div>
        </div>
      )}

      {/* Real-time Document Status */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Document Processing Status</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center p-4 bg-blue-50 rounded-lg">
            <div className="text-2xl font-bold text-blue-600">
              {documentStatusBreakdown.pending || 0}
            </div>
            <div className="text-sm text-gray-600">Pending</div>
            <div className="text-xs text-blue-500 mt-1">Ready to Process</div>
          </div>
          <div className="text-center p-4 bg-yellow-50 rounded-lg">
            <div className="text-2xl font-bold text-yellow-600">
              {documentStatusBreakdown.processing || 0}
            </div>
            <div className="text-sm text-gray-600">Processing</div>
            <div className="text-xs text-yellow-500 mt-1">In Progress</div>
          </div>
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <div className="text-2xl font-bold text-green-600">
              {documentStatusBreakdown.completed || 0}
            </div>
            <div className="text-sm text-gray-600">Completed</div>
            <div className="text-xs text-green-500 mt-1">Ready for Query</div>
          </div>
          <div className="text-center p-4 bg-red-50 rounded-lg">
            <div className="text-2xl font-bold text-red-600">
              {documentStatusBreakdown.failed || 0}
            </div>
            <div className="text-sm text-gray-600">Failed</div>
            <div className="text-xs text-red-500 mt-1">Needs Attention</div>
          </div>
        </div>
        
        {processingOverview.processing_metrics && (
          <div className="mt-6 p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600">Processing Queue:</span>
              <span className="font-medium">
                {processingOverview.processing_metrics.pending_jobs || 0} pending, 
                {processingOverview.processing_metrics.processing_jobs || 0} active
              </span>
            </div>
            <div className="flex items-center justify-between text-sm mt-2">
              <span className="text-gray-600">Success Rate:</span>
              <span className="font-medium text-green-600">
                {systemOverview.success_rate_percentage || 0}%
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default DashboardPage; 