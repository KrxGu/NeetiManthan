import React, { useState, useEffect } from 'react';
import { Upload, FileText, AlertCircle, CheckCircle, Loader, Info } from 'lucide-react';
import toast from 'react-hot-toast';
import { apiService } from '../services/api';

function DraftUpload() {
  const [draft, setDraft] = useState({ title: '', content: '' });
  const [loading, setLoading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [currentDraft, setCurrentDraft] = useState(null);
  const [loadingCurrent, setLoadingCurrent] = useState(true);

  useEffect(() => {
    fetchCurrentDraft();
  }, []);

  const fetchCurrentDraft = async () => {
    try {
      setLoadingCurrent(true);
      const response = await apiService.getCurrentDraft();
      setCurrentDraft(response.data);
    } catch (error) {
      // No draft exists yet - this is normal
      setCurrentDraft(null);
    } finally {
      setLoadingCurrent(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!draft.title.trim() || !draft.content.trim()) {
      toast.error('Please provide both title and content');
      return;
    }

    try {
      setLoading(true);
      const response = await apiService.uploadDraft(draft);
      setUploadResult(response.data);
      toast.success('Draft uploaded successfully!');
      
      // Clear form and refresh current draft
      setDraft({ title: '', content: '' });
      await fetchCurrentDraft();
    } catch (error) {
      console.error('Draft upload error:', error);
      toast.error('Failed to upload draft');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setDraft({ title: '', content: '' });
    setUploadResult(null);
  };

  const sampleDraft = {
    title: "Companies (Amendment) Rules, 2024",
    content: `DRAFT NOTIFICATION

Ministry of Corporate Affairs
Government of India

COMPANIES (AMENDMENT) RULES, 2024

1. Short title and commencement
(1) These rules may be called the Companies (Amendment) Rules, 2024.
(2) They shall come into force on the date of their publication in the Official Gazette.

2. Definitions
In these rules, unless the context otherwise requires:
(a) "digital signature" means authentication of any electronic record.

3. Application for incorporation
(1) Every application shall be made in Form INC-32.

4. Processing timeline
(1) The Registrar shall process applications within 15 working days.

5. Digital compliance
(1) All forms shall be filed electronically through the MCA portal.`
  };

  const loadSample = () => {
    setDraft(sampleDraft);
    toast.success('Sample draft loaded');
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-2xl font-bold text-gray-900">Upload Draft Document</h1>
        <p className="mt-2 text-gray-600">
          Upload a draft law document to extract clauses and enable comment analysis
        </p>
      </div>

      {/* Current Draft Status */}
      {!loadingCurrent && currentDraft && (
        <div className="card bg-blue-50 border-blue-200">
          <div className="card-header">
            <div className="flex items-center">
              <Info className="h-5 w-5 text-blue-600 mr-2" />
              <h2 className="text-lg font-semibold text-blue-900">Current Draft</h2>
            </div>
          </div>
          <div className="card-body">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <dt className="text-sm font-medium text-blue-700">Title:</dt>
                <dd className="text-sm text-blue-900 mt-1">{currentDraft.title}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-blue-700">Clauses Extracted:</dt>
                <dd className="text-sm text-blue-900 mt-1">{currentDraft.clauses_extracted} clauses</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-blue-700">Created:</dt>
                <dd className="text-sm text-blue-900 mt-1">
                  {new Date(currentDraft.created_at).toLocaleString()}
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-blue-700">Document ID:</dt>
                <dd className="text-sm font-mono text-blue-700 mt-1">{currentDraft.id}</dd>
              </div>
            </div>
            <div className="mt-4">
              <p className="text-sm text-blue-700">
                <strong>Note:</strong> Uploading a new draft will replace the current one and clear all associated comments.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Upload Form */}
      <div className="card">
        <div className="card-header">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <FileText className="h-5 w-5 text-primary-600 mr-2" />
              <h2 className="text-lg font-semibold text-gray-900">Draft Information</h2>
            </div>
            <button
              type="button"
              onClick={loadSample}
              className="btn btn-secondary btn-sm"
            >
              Load Sample
            </button>
          </div>
        </div>
        
        <div className="card-body">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Title */}
            <div>
              <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-2">
                Document Title *
              </label>
              <input
                type="text"
                id="title"
                value={draft.title}
                onChange={(e) => setDraft({ ...draft, title: e.target.value })}
                className="form-input"
                placeholder="e.g., Companies (Amendment) Rules, 2024"
                required
              />
            </div>

            {/* Content */}
            <div>
              <label htmlFor="content" className="block text-sm font-medium text-gray-700 mb-2">
                Document Content *
              </label>
              <textarea
                id="content"
                value={draft.content}
                onChange={(e) => setDraft({ ...draft, content: e.target.value })}
                rows={15}
                className="form-textarea"
                placeholder="Paste the full text of the draft document here..."
                required
              />
              <p className="mt-2 text-sm text-gray-500">
                Paste the complete draft document text. The system will automatically extract clauses and sections.
              </p>
            </div>

            {/* Actions */}
            <div className="flex items-center justify-between">
              <button
                type="button"
                onClick={handleReset}
                className="btn btn-secondary"
                disabled={loading}
              >
                Reset
              </button>
              
              <button
                type="submit"
                className="btn btn-primary"
                disabled={loading || !draft.title.trim() || !draft.content.trim()}
              >
                {loading ? (
                  <>
                    <Loader className="h-4 w-4 mr-2 animate-spin" />
                    Uploading...
                  </>
                ) : (
                  <>
                    <Upload className="h-4 w-4 mr-2" />
                    Upload Draft
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>

      {/* Upload Result */}
      {uploadResult && (
        <div className="card animate-slide-up">
          <div className="card-header">
            <div className="flex items-center">
              <CheckCircle className="h-5 w-5 text-success-600 mr-2" />
              <h2 className="text-lg font-semibold text-gray-900">Upload Successful</h2>
            </div>
          </div>
          
          <div className="card-body">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="text-sm font-medium text-gray-900 mb-2">Document Details</h3>
                <dl className="space-y-2">
                  <div>
                    <dt className="text-sm text-gray-600">Title:</dt>
                    <dd className="text-sm font-medium text-gray-900">{uploadResult.title}</dd>
                  </div>
                  <div>
                    <dt className="text-sm text-gray-600">Document ID:</dt>
                    <dd className="text-sm font-mono text-gray-700">{uploadResult.id}</dd>
                  </div>
                  <div>
                    <dt className="text-sm text-gray-600">Clauses Extracted:</dt>
                    <dd className="text-sm font-medium text-success-600">
                      {uploadResult.clauses_extracted} clauses
                    </dd>
                  </div>
                </dl>
              </div>
              
              <div>
                <h3 className="text-sm font-medium text-gray-900 mb-2">Extracted Clauses</h3>
                <div className="space-y-1 max-h-32 overflow-y-auto scrollbar-thin">
                  {uploadResult.clauses?.map((clause, index) => (
                    <div key={index} className="text-sm text-gray-700 p-2 bg-gray-50 rounded">
                      {clause}
                    </div>
                  ))}
                </div>
              </div>
            </div>
            
            <div className="mt-6 p-4 bg-primary-50 rounded-lg">
              <div className="flex items-start">
                <AlertCircle className="h-5 w-5 text-primary-600 mt-0.5 mr-2 flex-shrink-0" />
                <div>
                  <h4 className="text-sm font-medium text-primary-900">Next Steps</h4>
                  <p className="text-sm text-primary-700 mt-1">
                    Your draft has been processed successfully. You can now upload and analyze public comments 
                    related to this draft document.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Help Section */}
      <div className="card">
        <div className="card-header">
          <h2 className="text-lg font-semibold text-gray-900">Upload Guidelines</h2>
        </div>
        
        <div className="card-body">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="text-sm font-medium text-gray-900 mb-2">Supported Formats</h3>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Plain text content</li>
                <li>• Structured legal documents</li>
                <li>• Draft rules and regulations</li>
                <li>• Policy documents</li>
              </ul>
            </div>
            
            <div>
              <h3 className="text-sm font-medium text-gray-900 mb-2">Best Practices</h3>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Use clear, descriptive titles</li>
                <li>• Include section numbering (1., 2., etc.)</li>
                <li>• Maintain consistent formatting</li>
                <li>• Include complete document text</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default DraftUpload;
