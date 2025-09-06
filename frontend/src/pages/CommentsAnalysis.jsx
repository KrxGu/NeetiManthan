import React, { useState, useEffect } from 'react';
import { Upload, MessageSquare, Filter, Download, Plus, Loader } from 'lucide-react';
import toast from 'react-hot-toast';
import { useDropzone } from 'react-dropzone';
import { apiService } from '../services/api';
import { getSentimentBadge, getConfidenceLevel, truncateText, formatDateTime, downloadCSV } from '../utils/helpers';

function CommentsAnalysis() {
  const [comments, setComments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploadLoading, setUploadLoading] = useState(false);
  const [filter, setFilter] = useState('all');
  const [singleComment, setSingleComment] = useState({
    text: '',
    user_type: '',
    organization: '',
    state: ''
  });
  const [showSingleForm, setShowSingleForm] = useState(false);
  const [currentDraft, setCurrentDraft] = useState(null);

  useEffect(() => {
    fetchComments();
    fetchCurrentDraft();
  }, []);

  const fetchCurrentDraft = async () => {
    try {
      const response = await apiService.getCurrentDraft();
      setCurrentDraft(response.data);
    } catch (error) {
      // No draft exists yet
      setCurrentDraft(null);
    }
  };

  const fetchComments = async () => {
    try {
      setLoading(true);
      const response = await apiService.getAllComments();
      setComments(response.data.comments || []);
    } catch (error) {
      console.error('Fetch comments error:', error);
      // Don't show error toast if no comments exist yet
    } finally {
      setLoading(false);
    }
  };

  const onDrop = async (acceptedFiles) => {
    const file = acceptedFiles[0];
    if (!file) return;

    if (!file.name.endsWith('.csv')) {
      toast.error('Please upload a CSV file');
      return;
    }

    try {
      setUploadLoading(true);
      const response = await apiService.uploadCommentsCSV(file);
      toast.success(`Successfully processed ${response.data.total_comments} comments`);
      await fetchComments();
    } catch (error) {
      console.error('CSV upload error:', error);
      toast.error('Failed to upload CSV file');
    } finally {
      setUploadLoading(false);
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv']
    },
    maxFiles: 1
  });

  const handleSingleCommentSubmit = async (e) => {
    e.preventDefault();
    
    if (!singleComment.text.trim()) {
      toast.error('Please enter comment text');
      return;
    }

    try {
      setLoading(true);
      await apiService.processSingleComment(singleComment);
      toast.success('Comment processed successfully');
      setSingleComment({ text: '', user_type: '', organization: '', state: '' });
      setShowSingleForm(false);
      await fetchComments();
    } catch (error) {
      console.error('Single comment error:', error);
      toast.error('Failed to process comment');
    } finally {
      setLoading(false);
    }
  };

  const filteredComments = comments.filter(comment => {
    if (filter === 'all') return true;
    return comment.sentiment === filter;
  });

  const handleExport = () => {
    if (comments.length === 0) {
      toast.error('No comments to export');
      return;
    }

    const exportData = comments.map(comment => ({
      text: comment.text,
      sentiment: comment.sentiment,
      confidence: comment.confidence,
      clause_mentioned: comment.clause_mentioned || '',
      user_type: comment.user_type || '',
      organization: comment.organization || '',
      state: comment.state || '',
      processed_at: comment.processed_at
    }));

    downloadCSV(exportData, 'comments-analysis.csv');
    toast.success('Comments exported successfully');
  };

  const sentimentCounts = comments.reduce((acc, comment) => {
    acc[comment.sentiment] = (acc[comment.sentiment] || 0) + 1;
    return acc;
  }, {});

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Comments Analysis</h1>
          <p className="text-gray-600">Process and analyze public comments with AI</p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={() => setShowSingleForm(!showSingleForm)}
            className="btn btn-secondary btn-sm"
          >
            <Plus className="h-4 w-4 mr-2" />
            Add Single Comment
          </button>
          <button
            onClick={handleExport}
            className="btn btn-primary btn-sm"
            disabled={comments.length === 0}
          >
            <Download className="h-4 w-4 mr-2" />
            Export CSV
          </button>
        </div>
      </div>

      {/* Current Draft Info */}
      {currentDraft && (
        <div className="card bg-blue-50 border-blue-200">
          <div className="card-body">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-blue-900">Current Draft</h3>
                <p className="text-blue-700 mt-1">{currentDraft.title}</p>
              </div>
              <div className="text-right">
                <div className="text-sm text-blue-600">
                  {currentDraft.clauses_extracted} clauses extracted
                </div>
                <div className="text-xs text-blue-500 mt-1">
                  Updated: {new Date(currentDraft.updated_at).toLocaleDateString()}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {!currentDraft && (
        <div className="card bg-amber-50 border-amber-200">
          <div className="card-body text-center">
            <p className="text-amber-800">
              No draft document uploaded yet. 
              <a href="/draft" className="font-medium text-amber-900 hover:text-amber-700 ml-1">
                Upload a draft document
              </a> to enable comment analysis.
            </p>
          </div>
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div className="card">
          <div className="card-body text-center">
            <div className="text-2xl font-bold text-gray-900">{comments.length}</div>
            <div className="text-sm text-gray-600">Total Comments</div>
          </div>
        </div>
        <div className="card">
          <div className="card-body text-center">
            <div className="text-2xl font-bold text-success-600">{sentimentCounts.positive || 0}</div>
            <div className="text-sm text-gray-600">Positive</div>
          </div>
        </div>
        <div className="card">
          <div className="card-body text-center">
            <div className="text-2xl font-bold text-danger-600">{sentimentCounts.negative || 0}</div>
            <div className="text-sm text-gray-600">Negative</div>
          </div>
        </div>
        <div className="card">
          <div className="card-body text-center">
            <div className="text-2xl font-bold text-gray-600">{sentimentCounts.neutral || 0}</div>
            <div className="text-sm text-gray-600">Neutral</div>
          </div>
        </div>
      </div>

      {/* Single Comment Form */}
      {showSingleForm && (
        <div className="card animate-slide-up">
          <div className="card-header">
            <h2 className="text-lg font-semibold text-gray-900">Add Single Comment</h2>
          </div>
          <div className="card-body">
            <form onSubmit={handleSingleCommentSubmit} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    User Type
                  </label>
                  <input
                    type="text"
                    value={singleComment.user_type}
                    onChange={(e) => setSingleComment({ ...singleComment, user_type: e.target.value })}
                    className="form-input"
                    placeholder="e.g., Individual, Legal Professional"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Organization
                  </label>
                  <input
                    type="text"
                    value={singleComment.organization}
                    onChange={(e) => setSingleComment({ ...singleComment, organization: e.target.value })}
                    className="form-input"
                    placeholder="e.g., NASSCOM, Bar Association"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    State
                  </label>
                  <input
                    type="text"
                    value={singleComment.state}
                    onChange={(e) => setSingleComment({ ...singleComment, state: e.target.value })}
                    className="form-input"
                    placeholder="e.g., Maharashtra, Delhi"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Comment Text *
                </label>
                <textarea
                  value={singleComment.text}
                  onChange={(e) => setSingleComment({ ...singleComment, text: e.target.value })}
                  rows={4}
                  className="form-textarea"
                  placeholder="Enter the comment text here..."
                  required
                />
              </div>
              <div className="flex items-center justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => setShowSingleForm(false)}
                  className="btn btn-secondary"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={loading}
                >
                  {loading ? (
                    <>
                      <Loader className="h-4 w-4 mr-2 animate-spin" />
                      Processing...
                    </>
                  ) : (
                    'Process Comment'
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* CSV Upload */}
      <div className="card">
        <div className="card-header">
          <div className="flex items-center">
            <Upload className="h-5 w-5 text-primary-600 mr-2" />
            <h2 className="text-lg font-semibold text-gray-900">Upload Comments CSV</h2>
          </div>
        </div>
        <div className="card-body">
          <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
              isDragActive
                ? 'border-primary-500 bg-primary-50'
                : 'border-gray-300 hover:border-primary-400'
            }`}
          >
            <input {...getInputProps()} />
            {uploadLoading ? (
              <div className="flex items-center justify-center">
                <Loader className="h-8 w-8 text-primary-600 animate-spin mr-3" />
                <span className="text-lg text-primary-600">Processing comments...</span>
              </div>
            ) : (
              <>
                <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-lg font-medium text-gray-900 mb-2">
                  {isDragActive ? 'Drop your CSV file here' : 'Upload CSV file'}
                </p>
                <p className="text-sm text-gray-600">
                  Drag and drop your comments CSV file, or click to select
                </p>
                <p className="text-xs text-gray-500 mt-2">
                  CSV should have columns: text, user_type, organization, state
                </p>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Comments List */}
      <div className="card">
        <div className="card-header">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <MessageSquare className="h-5 w-5 text-primary-600 mr-2" />
              <h2 className="text-lg font-semibold text-gray-900">
                Processed Comments ({filteredComments.length})
              </h2>
            </div>
            <div className="flex items-center space-x-3">
              <Filter className="h-4 w-4 text-gray-400" />
              <select
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                className="form-select text-sm"
              >
                <option value="all">All Sentiments</option>
                <option value="positive">Positive</option>
                <option value="negative">Negative</option>
                <option value="neutral">Neutral</option>
              </select>
            </div>
          </div>
        </div>

        <div className="card-body">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader className="h-6 w-6 animate-spin mr-2" />
              <span>Loading comments...</span>
            </div>
          ) : filteredComments.length === 0 ? (
            <div className="text-center py-8">
              <MessageSquare className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-lg font-medium text-gray-900 mb-2">No comments yet</p>
              <p className="text-gray-600">Upload a CSV file or add single comments to get started</p>
            </div>
          ) : (
            <div className="space-y-4">
              {filteredComments.map((comment) => {
                const confidence = getConfidenceLevel(comment.confidence);
                return (
                  <div key={comment.id} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center space-x-3">
                        <span className={`badge ${getSentimentBadge(comment.sentiment)}`}>
                          {comment.sentiment}
                        </span>
                        <span className={`text-sm font-medium ${confidence.color}`}>
                          {confidence.text} Confidence ({(comment.confidence * 100).toFixed(1)}%)
                        </span>
                        {comment.clause_mentioned && (
                          <span className="badge badge-gray text-xs">
                            {comment.clause_mentioned}
                          </span>
                        )}
                      </div>
                      <span className="text-xs text-gray-500">
                        {formatDateTime(comment.processed_at)}
                      </span>
                    </div>
                    
                    <p className="text-gray-900 mb-3">{comment.text}</p>
                    
                    {(comment.user_type || comment.organization || comment.state) && (
                      <div className="flex items-center space-x-4 text-sm text-gray-600">
                        {comment.user_type && (
                          <span><strong>Type:</strong> {comment.user_type}</span>
                        )}
                        {comment.organization && (
                          <span><strong>Org:</strong> {comment.organization}</span>
                        )}
                        {comment.state && (
                          <span><strong>State:</strong> {comment.state}</span>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default CommentsAnalysis;
