import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  FileText, 
  MessageSquare, 
  BarChart3, 
  TrendingUp,
  AlertCircle,
  CheckCircle,
  Clock,
  Users
} from 'lucide-react';
import toast from 'react-hot-toast';
import { apiService } from '../services/api';
import { formatNumber, formatDateTime } from '../utils/helpers';

function Dashboard() {
  const [systemStatus, setSystemStatus] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [currentDraft, setCurrentDraft] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      
      const statusPromise = apiService.getHealth().catch(() => ({ data: { status: 'loading' } }));
      const analyticsPromise = apiService.getAnalytics().catch(error => {
        if (error.response && error.response.status === 404) {
          return { data: null }; // Gracefully handle 404
        }
        throw error; // Re-throw other errors
      });
      const draftPromise = apiService.getCurrentDraft().catch(() => ({ data: null }));

      const [statusResponse, analyticsResponse, draftResponse] = await Promise.all([statusPromise, analyticsPromise, draftPromise]);

      setSystemStatus(statusResponse.data);
      setAnalytics(analyticsResponse.data);
      setCurrentDraft(draftResponse.data);
      
    } catch (error) {
      if (error.code !== 'ECONNRESET' && error.code !== 'ECONNREFUSED') {
        console.error('Dashboard data fetch error:', error);
        toast.error('Failed to load dashboard data');
      }
    } finally {
      setLoading(false);
    }
  };

  const stats = [
    {
      name: 'Total Comments',
      value: analytics?.total_comments || 0,
      icon: MessageSquare,
      color: 'text-primary-600',
      bgColor: 'bg-primary-50',
    },
    {
      name: 'Processed',
      value: analytics?.processed_comments || 0,
      icon: CheckCircle,
      color: 'text-success-600',
      bgColor: 'bg-success-50',
    },
    {
      name: 'Avg Confidence',
      value: (analytics && analytics.average_confidence > 0) ? `${(analytics.average_confidence * 100).toFixed(1)}%` : 'N/A',
      icon: TrendingUp,
      color: 'text-warning-600',
      bgColor: 'bg-warning-50',
    },
    {
      name: 'Active Drafts',
      value: analytics ? 1 : 0,
      icon: FileText,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50',
    }
  ];

  const quickActions = [
    {
      name: 'Upload Draft',
      description: 'Upload a new draft law document',
      href: '/draft',
      icon: FileText,
      color: 'bg-primary-600 hover:bg-primary-700'
    },
    {
      name: 'Process Comments',
      description: 'Analyze public comments with AI',
      href: '/comments',
      icon: MessageSquare,
      color: 'bg-success-600 hover:bg-success-700'
    },
    {
      name: 'View Analytics',
      description: 'See detailed analysis reports',
      href: '/analytics',
      icon: BarChart3,
      color: 'bg-warning-600 hover:bg-warning-700'
    }
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="loading-spinner h-8 w-8"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Welcome Section */}
      <div className="bg-gradient-to-r from-primary-600 to-primary-700 rounded-lg shadow-lg">
        <div className="px-6 py-8 sm:px-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-white">Welcome to NeetiManthan</h1>
              <p className="mt-2 text-primary-100 text-lg">
                AI-powered public comment analysis for draft laws
              </p>
              <p className="mt-1 text-primary-200 text-sm">
                Last updated: {formatDateTime(new Date().toISOString())}
              </p>
            </div>
            <div className="hidden sm:block">
              <div className="flex items-center space-x-2 text-white">
                <div className={`w-3 h-3 rounded-full ${
                  systemStatus?.status === 'healthy' ? 'bg-success-400' : 
                  systemStatus?.status === 'loading' ? 'bg-warning-400' : 'bg-danger-400'
                }`}></div>
                <span className="text-sm font-medium">
                  {systemStatus?.status === 'healthy' ? 'System Healthy' : 
                   systemStatus?.status === 'loading' ? 'System Loading' : 'System Issues'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Current Draft Status */}
      {currentDraft && (
        <div className="card bg-blue-50 border-blue-200">
          <div className="card-body">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <FileText className="h-6 w-6 text-blue-600 mr-3" />
                <div>
                  <h3 className="text-lg font-semibold text-blue-900">Current Draft Document</h3>
                  <p className="text-blue-700 mt-1">{currentDraft.title}</p>
                </div>
              </div>
              <div className="text-right">
                <div className="text-sm text-blue-600 font-medium">
                  {currentDraft.clauses_extracted} clauses extracted
                </div>
                <div className="text-xs text-blue-500 mt-1">
                  Uploaded: {new Date(currentDraft.created_at).toLocaleDateString()}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {!currentDraft && (
        <div className="card bg-amber-50 border-amber-200">
          <div className="card-body">
            <div className="flex items-center">
              <AlertCircle className="h-6 w-6 text-amber-600 mr-3" />
              <div>
                <h3 className="text-lg font-semibold text-amber-900">No Draft Document</h3>
                <p className="text-amber-700 mt-1">
                  Upload a draft document to start analyzing public comments.
                  <Link to="/draft" className="font-medium text-amber-900 hover:text-amber-700 ml-1">
                    Upload now →
                  </Link>
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <div key={stat.name} className="card">
            <div className="card-body">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">{stat.name}</p>
                  <p className="text-2xl font-semibold text-gray-900">{formatNumber(stat.value)}</p>
                </div>
                <div className={`p-3 rounded-lg ${stat.bgColor}`}>
                  <stat.icon className={`h-6 w-6 ${stat.color}`} />
                </div>
              </div>
              <div className="mt-4 flex items-center text-sm text-gray-500">
                  {/* Placeholder for future change indicator */}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="card">
        <div className="card-header">
          <h2 className="text-lg font-semibold text-gray-900">Quick Actions</h2>
          <p className="text-sm text-gray-600">Get started with common tasks</p>
        </div>
        <div className="card-body">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            {quickActions.map((action) => (
              <Link
                key={action.name}
                to={action.href}
                className="group relative overflow-hidden rounded-lg bg-white p-6 shadow-sm border border-gray-200 hover:shadow-md transition-all duration-200"
              >
                <div className="flex items-center">
                  <div className={`p-3 rounded-lg ${action.color} text-white`}>
                    <action.icon className="h-6 w-6" />
                  </div>
                  <div className="ml-4">
                    <h3 className="text-lg font-medium text-gray-900 group-hover:text-primary-600">
                      {action.name}
                    </h3>
                    <p className="text-sm text-gray-500">{action.description}</p>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* System Status */}
        <div className="card">
          <div className="card-header">
            <h2 className="text-lg font-semibold text-gray-900">System Status</h2>
          </div>
          <div className="card-body space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <CheckCircle className="h-5 w-5 text-success-500 mr-2" />
                <span className="text-sm font-medium">API Gateway</span>
              </div>
              <span className="badge badge-success">Healthy</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <CheckCircle className="h-5 w-5 text-success-500 mr-2" />
                <span className="text-sm font-medium">Database</span>
              </div>
              <span className="badge badge-success">Connected</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                {systemStatus?.status === 'loading' ? (
                  <div className="loading-spinner h-5 w-5 mr-2"></div>
                ) : (
                  <CheckCircle className="h-5 w-5 text-success-500 mr-2" />
                )}
                <span className="text-sm font-medium">ML Models</span>
              </div>
              <span className={`badge ${systemStatus?.status === 'loading' ? 'badge-warning' : 'badge-success'}`}>
                {systemStatus?.status === 'loading' ? 'Loading...' : 
                 systemStatus?.sentiment_model === 'ml-loaded' ? 'ML Loaded' : 'Rule-based'}
              </span>
            </div>
          </div>
        </div>

        {/* Recent Insights */}
        <div className="card">
          <div className="card-header">
            <h2 className="text-lg font-semibold text-gray-900">Recent Insights</h2>
          </div>
          <div className="card-body">
            {analytics ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Sentiment Distribution</span>
                </div>
                <div className="space-y-2">
                  {Object.entries(analytics.sentiment_distribution).map(([sentiment, count]) => (
                    <div key={sentiment} className="flex items-center justify-between">
                      <span className="text-sm font-medium capitalize">{sentiment}</span>
                      <span className="text-sm text-gray-600">{count} comments</span>
                    </div>
                  ))}
                </div>
                {analytics.top_clauses?.length > 0 && (
                  <div className="mt-4">
                    <span className="text-sm text-gray-600">Most Mentioned Clause</span>
                    <p className="text-sm font-medium">{analytics.top_clauses[0].clause}</p>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-6">
                <Clock className="h-8 w-8 text-gray-400 mx-auto mb-2" />
                <p className="text-sm text-gray-600">No data available yet</p>
                <p className="text-xs text-gray-500">Upload a draft and process comments to see insights</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
