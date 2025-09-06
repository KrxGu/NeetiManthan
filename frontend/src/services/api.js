import axios from 'axios';

// Create axios instance with base configuration
const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for debugging
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`, config.data);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    console.log(`API Response: ${response.status}`, response.data);
    return response;
  },
  (error) => {
    // Only log actual errors, not network issues during startup
    if (error.code !== 'ECONNRESET' && error.code !== 'ECONNREFUSED') {
      console.error('API Response Error:', error.response?.data || error.message);
    }
    return Promise.reject(error);
  }
);

// API endpoints
export const apiService = {
  // Health and status
  getHealth: () => api.get('/health').catch(err => {
    console.log('Health check failed - API might still be loading');
    return { data: { status: 'loading', message: 'API is starting up...' } };
  }),
  getStatus: () => api.get('/').catch(err => {
    console.log('Status check failed - API might still be loading');
    return { data: { message: 'NeetiManthan API (Loading)', status: 'starting' } };
  }),

  // Draft management
  uploadDraft: (draftData) => api.post('/draft/upload', draftData),
  getCurrentDraft: () => api.get('/draft'),

  // Comment processing
  processSingleComment: (commentData) => api.post('/comments/single', commentData),
  uploadCommentsCSV: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/comments/upload-csv', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
  getAllComments: () => api.get('/comments'),

  // Analytics
  getAnalytics: () => api.get('/analytics').catch(err => {
    console.log('Analytics not available - no data processed yet');
    throw err;
  }),

  // Testing
  testSentiment: () => api.post('/test-sentiment'),

  // Data management
  resetData: () => api.delete('/reset'),
};

export default api;
