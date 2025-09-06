import React from 'react';
import { BrowserRouter as Router, Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';

// Import pages
import LandingPage from './pages/LandingPage';
import Dashboard from './pages/Dashboard';
import DraftUpload from './pages/DraftUpload';
import CommentsAnalysis from './pages/CommentsAnalysis';
import Analytics from './pages/Analytics';

// Import components
import Layout from './components/Layout';

// Wrapper component to handle navigation
function AppContent() {
  const navigate = useNavigate();
  const location = useLocation();
  const isLandingPage = location.pathname === '/';

  const handleNavigate = (path) => {
    navigate(path);
  };

  return (
    <div className="App min-h-screen flex flex-col">
      {isLandingPage ? (
        <LandingPage onNavigate={handleNavigate} />
      ) : (
        <Layout>
          <Routes>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/draft-upload" element={<DraftUpload />} />
            <Route path="/comments" element={<CommentsAnalysis />} />
            <Route path="/analytics" element={<Analytics />} />
          </Routes>
        </Layout>
      )}
    </div>
  );
}

function App() {
  return (
    <Router>
      <AppContent />
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
    </Router>
  );
}

export default App;
