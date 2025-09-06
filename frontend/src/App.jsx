import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';

// Import pages
import Dashboard from './pages/Dashboard';
import DraftUpload from './pages/DraftUpload';
import CommentsAnalysis from './pages/CommentsAnalysis';
import Analytics from './pages/Analytics';

// Import components
import Layout from './components/Layout';

function App() {
  return (
    <Router>
      <div className="App min-h-screen flex flex-col">
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/draft" element={<DraftUpload />} />
            <Route path="/comments" element={<CommentsAnalysis />} />
            <Route path="/analytics" element={<Analytics />} />
          </Routes>
        </Layout>
        
        {/* Toast notifications */}
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: '#363636',
              color: '#fff',
            },
            success: {
              duration: 3000,
              theme: {
                primary: '#22c55e',
                secondary: '#f0fdf4',
              },
            },
            error: {
              duration: 5000,
              theme: {
                primary: '#ef4444',
                secondary: '#fef2f2',
              },
            },
          }}
        />
      </div>
    </Router>
  );
}

export default App;
