import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';
import { TrendingUp, Users, MessageSquare, Target, Download, RefreshCw } from 'lucide-react';
import toast from 'react-hot-toast';
import { apiService } from '../services/api';
import { formatNumber, downloadJSON } from '../utils/helpers';

const SENTIMENT_COLORS = {
  positive: '#22c55e',
  negative: '#ef4444',
  neutral: '#6b7280'
};

function Analytics() {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      const response = await apiService.getAnalytics();
      setAnalytics(response.data);
    } catch (error) {
      console.error('Analytics fetch error:', error);
      if (error.response?.status === 404) {
        toast.error('No data available. Please process some comments first.');
      } else {
        toast.error('Failed to load analytics');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleExport = () => {
    if (!analytics) {
      toast.error('No data to export');
      return;
    }

    downloadJSON(analytics, 'analytics-report.json');
    toast.success('Analytics exported successfully');
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="loading-spinner h-8 w-8"></div>
      </div>
    );
  }

  if (!analytics) {
    return (
      <div className="text-center py-12">
        <MessageSquare className="h-16 w-16 text-gray-400 mx-auto mb-4" />
        <h2 className="text-xl font-semibold text-gray-900 mb-2">No Analytics Data</h2>
        <p className="text-gray-600 mb-6">
          Upload a draft document and process some comments to see analytics.
        </p>
        <button
          onClick={fetchAnalytics}
          className="btn btn-primary"
        >
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </button>
      </div>
    );
  }

  // Prepare chart data
  const sentimentData = Object.entries(analytics.sentiment_distribution).map(([sentiment, count]) => ({
    sentiment: sentiment.charAt(0).toUpperCase() + sentiment.slice(1),
    count,
    color: SENTIMENT_COLORS[sentiment]
  }));

  const clauseData = analytics.top_clauses.slice(0, 10).map(clause => ({
    clause: clause.clause.length > 20 ? clause.clause.substring(0, 20) + '...' : clause.clause,
    mentions: clause.mentions
  }));

  const stats = [
    {
      name: 'Total Comments',
      value: analytics.total_comments,
      icon: MessageSquare,
      color: 'text-primary-600',
      bgColor: 'bg-primary-50'
    },
    {
      name: 'Processed',
      value: analytics.processed_comments,
      icon: Target,
      color: 'text-success-600',
      bgColor: 'bg-success-50'
    },
    {
      name: 'Avg Confidence',
      value: `${(analytics.average_confidence * 100).toFixed(1)}%`,
      icon: TrendingUp,
      color: 'text-warning-600',
      bgColor: 'bg-warning-50'
    },
    {
      name: 'Unique Clauses',
      value: analytics.top_clauses.length,
      icon: Users,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50'
    }
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Analytics Dashboard</h1>
          <p className="text-gray-600">Comprehensive analysis of public comments</p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={fetchAnalytics}
            className="btn btn-secondary btn-sm"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </button>
          <button
            onClick={handleExport}
            className="btn btn-primary btn-sm"
          >
            <Download className="h-4 w-4 mr-2" />
            Export Report
          </button>
        </div>
      </div>

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
            </div>
          </div>
        ))}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Sentiment Distribution */}
        <div className="card">
          <div className="card-header">
            <h2 className="text-lg font-semibold text-gray-900">Sentiment Distribution</h2>
          </div>
          <div className="card-body">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={sentimentData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ sentiment, count, percent }) => 
                    `${sentiment}: ${count} (${(percent * 100).toFixed(0)}%)`
                  }
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="count"
                >
                  {sentimentData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Top Mentioned Clauses */}
        <div className="card">
          <div className="card-header">
            <h2 className="text-lg font-semibold text-gray-900">Most Mentioned Clauses</h2>
          </div>
          <div className="card-body">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={clauseData} layout="horizontal">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis dataKey="clause" type="category" width={80} />
                <Tooltip />
                <Bar dataKey="mentions" fill="#3b82f6" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Detailed Analysis */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Processing Summary */}
        <div className="card">
          <div className="card-header">
            <h2 className="text-lg font-semibold text-gray-900">Processing Summary</h2>
          </div>
          <div className="card-body space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Model Type</span>
              <span className="text-sm font-medium text-gray-900 capitalize">
                {analytics.processing_summary.sentiment_model}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Clauses Extracted</span>
              <span className="text-sm font-medium text-gray-900">
                {analytics.processing_summary.clauses_extracted}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Current Draft</span>
              <span className="text-sm font-medium text-gray-900">
                {analytics.processing_summary.current_draft || 'None'}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Processing Rate</span>
              <span className="text-sm font-medium text-success-600">
                {analytics.processed_comments === analytics.total_comments ? '100%' : 
                 `${((analytics.processed_comments / analytics.total_comments) * 100).toFixed(1)}%`}
              </span>
            </div>
          </div>
        </div>

        {/* Top Clauses List */}
        <div className="card">
          <div className="card-header">
            <h2 className="text-lg font-semibold text-gray-900">Clause Details</h2>
          </div>
          <div className="card-body">
            <div className="space-y-3 max-h-80 overflow-y-auto scrollbar-thin">
              {analytics.top_clauses.map((clause, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900">{clause.clause}</p>
                    <p className="text-xs text-gray-600">{clause.mentions} mentions</p>
                  </div>
                  <div className="ml-4">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-primary-100 text-primary-800">
                      #{index + 1}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Insights */}
      <div className="card">
        <div className="card-header">
          <h2 className="text-lg font-semibold text-gray-900">Key Insights</h2>
        </div>
        <div className="card-body">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-success-600 mb-2">
                {((analytics.sentiment_distribution.positive / analytics.total_comments) * 100).toFixed(1)}%
              </div>
              <p className="text-sm text-gray-600">Comments are positive</p>
            </div>
            
            <div className="text-center">
              <div className="text-2xl font-bold text-primary-600 mb-2">
                {analytics.top_clauses.length > 0 ? analytics.top_clauses[0].clause : 'N/A'}
              </div>
              <p className="text-sm text-gray-600">Most discussed clause</p>
            </div>
            
            <div className="text-center">
              <div className="text-2xl font-bold text-warning-600 mb-2">
                {(analytics.average_confidence * 100).toFixed(1)}%
              </div>
              <p className="text-sm text-gray-600">Average confidence</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Analytics;
