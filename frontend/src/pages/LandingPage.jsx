import React from 'react';
import { 
  FileText, 
  MessageSquare, 
  BarChart3, 
  Download, 
  ArrowRight, 
  Users, 
  TrendingUp, 
  Eye,
  Upload,
  Brain,
  Shield,
  Globe
} from 'lucide-react';
import PlaceholderImage from '../components/PlaceholderImage';

const LandingPage = ({ onNavigate }) => {
  const quickAccessCards = [
    {
      title: 'Upload Draft Documents',
      description: 'Upload policy drafts for analysis and public review',
      icon: Upload,
      action: () => onNavigate('/draft-upload'),
      color: 'bg-blue-50 border-blue-200 hover:bg-blue-100'
    },
    {
      title: 'Analyze Comments',
      description: 'Process and analyze public comments with AI',
      icon: Brain,
      action: () => onNavigate('/comments'),
      color: 'bg-green-50 border-green-200 hover:bg-green-100'
    },
    {
      title: 'View Analytics',
      description: 'Explore sentiment analysis and insights',
      icon: BarChart3,
      action: () => onNavigate('/analytics'),
      color: 'bg-orange-50 border-orange-200 hover:bg-orange-100'
    },
    {
      title: 'Dashboard Overview',
      description: 'Access comprehensive policy insights',
      icon: Eye,
      action: () => onNavigate('/dashboard'),
      color: 'bg-purple-50 border-purple-200 hover:bg-purple-100'
    },
  ];

  const impactHighlights = [
    { label: 'Drafts Analyzed', value: '24', icon: FileText },
    { label: 'Comments Processed', value: '1,547', icon: MessageSquare },
    { label: 'AI Insights Generated', value: '892', icon: Brain },
    { label: 'Policy Improvements', value: '156', icon: TrendingUp },
  ];

  const features = [
    {
      title: 'AI-Powered Sentiment Analysis',
      description: 'Advanced machine learning models analyze public sentiment on policy drafts with high accuracy.',
      icon: Brain,
      color: 'text-blue-600'
    },
    {
      title: 'Automated Clause Linking',
      description: 'Intelligent system links public comments to specific clauses in policy documents.',
      icon: FileText,
      color: 'text-green-600'
    },
    {
      title: 'Real-time Analytics',
      description: 'Live dashboards provide instant insights into public opinion and engagement trends.',
      icon: BarChart3,
      color: 'text-orange-600'
    },
    {
      title: 'Secure & Compliant',
      description: 'Government-grade security ensuring data protection and regulatory compliance.',
      icon: Shield,
      color: 'text-red-600'
    },
  ];

  const recentUpdates = [
    {
      title: 'Companies (Amendment) Rules, 2024',
      date: '2 days ago',
      status: 'Active',
      comments: 42
    },
    {
      title: 'Digital Privacy Protection Framework',
      date: '5 days ago',
      status: 'Under Review',
      comments: 128
    },
    {
      title: 'Environmental Compliance Guidelines',
      date: '1 week ago',
      status: 'Completed',
      comments: 89
    },
    {
      title: 'Financial Services Reform Draft',
      date: '2 weeks ago',
      status: 'Published',
      comments: 203
    },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header with Government Branding - Exact Match */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-8 py-4">
          <div className="flex items-center justify-between">
            {/* Left Section - Government Logo Only */}
            <div className="flex items-center w-1/4">
              <img 
                src="/images/government-logo.png" 
                alt="Government of India" 
                className="h-24 w-40 object-contain"
                onError={(e) => {
                  // Fallback to placeholder if image not found
                  e.target.style.display = 'none';
                  e.target.nextSibling.style.display = 'block';
                }}
              />
              <PlaceholderImage 
                width={160} 
                height={96}
                alt="Government of India"
                className="hidden"
              />
            </div>

            {/* Center Section - NEETI MANTHAN */}
            <div className="flex-1 flex flex-col items-center justify-center text-center w-1/2">
              <h1 className="text-4xl font-black text-blue-900 tracking-wide">NEETI MANTHAN</h1>
              <p className="text-sm text-green-600 font-medium">EMPOWERING OFFICIALS, ENABLING POLICY</p>
              <p className="text-xs text-gray-500">REGULATION • INTEGRATION • FACILITATOR • EDUCATOR</p>
            </div>

            {/* Right Section - Search and User */}
            <div className="flex items-center justify-end space-x-3 w-1/4">
              <div className="relative">
                <input
                  type="text"
                  placeholder="Search policies, documents..."
                  className="w-64 px-3 py-2 border border-gray-300 rounded text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                />
                <button className="absolute right-2 top-1/2 transform -translate-y-1/2">
                  <svg className="h-4 w-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                </button>
              </div>
              <button
                onClick={() => onNavigate('/dashboard')}
                className="p-2 hover:bg-gray-50 rounded"
              >
                <svg className="h-5 w-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Banner */}
      <section className="relative bg-gradient-to-r from-blue-900 via-blue-800 to-blue-900 text-white">
        <div 
          className="absolute inset-0 bg-cover bg-center bg-no-repeat"
          style={{
            backgroundImage: `url('https://images.unsplash.com/photo-1647326520048-21dc3f07a9f2?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxpbmRpYW4lMjBwYXJsaWFtZW50JTIwZ292ZXJubWVudCUyMGJ1aWxkaW5nfGVufDF8fHx8MTc1NzEwMjA4N3ww&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral')`
          }}
        ></div>
        <div className="absolute inset-0 bg-blue-900 opacity-75"></div>
        <div className="relative z-10 max-w-7xl mx-auto px-4 py-20 text-center">
          <h1 className="text-5xl font-bold mb-6">Welcome to Neeti Manthan</h1>
          <p className="text-xl mb-8 max-w-3xl mx-auto leading-relaxed">
            A comprehensive AI-powered platform for analyzing public comments on policy drafts. 
            Leverage advanced sentiment analysis and intelligent insights to enhance policy-making through transparent, data-driven governance.
          </p>
          <div className="flex justify-center space-x-4">
            <button
              onClick={() => onNavigate('/dashboard')}
              className="bg-orange-500 hover:bg-orange-600 text-white px-8 py-3 rounded-lg font-medium text-lg transition-colors flex items-center"
            >
              Get Started
              <ArrowRight className="ml-2 h-5 w-5" />
            </button>
            <button
              onClick={() => onNavigate('/analytics')}
              className="border-2 border-white text-white hover:bg-white hover:text-blue-900 px-8 py-3 rounded-lg font-medium text-lg transition-colors"
            >
              View Demo
            </button>
          </div>
        </div>
      </section>

      {/* Quick Access Cards */}
      <section className="max-w-7xl mx-auto px-4 py-16">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold mb-4 text-blue-900">Quick Access</h2>
          <p className="text-gray-600 max-w-2xl mx-auto">
            Navigate directly to the tools and features you need for effective policy analysis and engagement
          </p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {quickAccessCards.map((card, index) => {
            const Icon = card.icon;
            return (
              <div
                key={index}
                className={`${card.color} border-2 rounded-xl p-6 cursor-pointer transition-all duration-200 transform hover:scale-105 hover:shadow-lg`}
                onClick={card.action}
              >
                <div className="text-center">
                  <Icon className="h-12 w-12 mx-auto mb-4 text-blue-900" />
                  <h3 className="text-lg font-semibold text-blue-900 mb-2">{card.title}</h3>
                  <p className="text-gray-600 text-sm mb-4">{card.description}</p>
                  <ArrowRight className="h-5 w-5 mx-auto text-green-600" />
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* Impact Highlights */}
      <section className="bg-white py-16">
        <div className="max-w-7xl mx-auto px-4">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold mb-4 text-blue-900">Platform Impact</h2>
            <p className="text-gray-600">Real-time statistics showing AI-powered policy analysis capabilities</p>
          </div>
          
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
            {impactHighlights.map((item, index) => {
              const Icon = item.icon;
              return (
                <div key={index} className="text-center bg-gray-50 rounded-xl p-6 border-2 border-gray-100 hover:border-orange-300 transition-colors">
                  <Icon className="h-8 w-8 mx-auto mb-3 text-green-600" />
                  <div className="text-3xl font-bold text-blue-900 mb-2">{item.value}</div>
                  <div className="text-gray-600 font-medium">{item.label}</div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Key Features */}
      <section className="bg-gray-50 py-16">
        <div className="max-w-7xl mx-auto px-4">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold mb-4 text-blue-900">Key Features</h2>
            <p className="text-gray-600 max-w-2xl mx-auto">
              Advanced AI capabilities designed specifically for government policy analysis and public engagement
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {features.map((feature, index) => {
              const Icon = feature.icon;
              return (
                <div key={index} className="bg-white rounded-xl p-6 shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
                  <div className="flex items-start space-x-4">
                    <Icon className={`h-10 w-10 ${feature.color} flex-shrink-0 mt-1`} />
                    <div>
                      <h3 className="text-xl font-semibold text-blue-900 mb-2">{feature.title}</h3>
                      <p className="text-gray-600">{feature.description}</p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Recent Activity & Featured Content */}
      <section className="max-w-7xl mx-auto px-4 py-16">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
          <div>
            <h2 className="text-3xl font-bold mb-6 text-blue-900">Recent Analysis</h2>
            <div className="space-y-4">
              {recentUpdates.map((update, index) => (
                <div key={index} className="bg-white rounded-lg p-4 shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="text-lg font-medium text-blue-900">{update.title}</h3>
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                      update.status === 'Active' ? 'bg-green-100 text-green-800' :
                      update.status === 'Under Review' ? 'bg-yellow-100 text-yellow-800' :
                      update.status === 'Completed' ? 'bg-blue-100 text-blue-800' :
                      'bg-purple-100 text-purple-800'
                    }`}>
                      {update.status}
                    </span>
                  </div>
                  <div className="flex justify-between items-center text-sm text-gray-600">
                    <span>{update.date}</span>
                    <span className="flex items-center">
                      <MessageSquare className="h-4 w-4 mr-1" />
                      {update.comments} comments analyzed
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
          
          <div>
            <h2 className="text-3xl font-bold mb-6 text-blue-900">AI Analytics Hub</h2>
            <div className="bg-gradient-to-br from-blue-900 to-blue-800 text-white rounded-xl p-8 h-80 flex flex-col justify-center">
              <Brain className="h-16 w-16 mb-6 text-orange-400" />
              <h3 className="text-2xl font-bold mb-4">Advanced Policy Insights</h3>
              <p className="text-blue-100 mb-8 leading-relaxed">
                Harness the power of AI to understand public sentiment, identify key concerns, 
                and generate actionable insights from policy feedback. Our advanced analytics 
                provide comprehensive understanding of citizen engagement.
              </p>
              <button
                onClick={() => onNavigate('/analytics')}
                className="bg-orange-500 hover:bg-orange-600 text-white px-6 py-3 rounded-lg font-medium w-fit transition-colors flex items-center"
              >
                Explore AI Analytics
                <ArrowRight className="ml-2 h-5 w-5" />
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-blue-900 text-white py-8">
        <div className="max-w-7xl mx-auto px-4 text-center">
          <div className="flex items-center justify-center space-x-3 mb-4">
            <PlaceholderImage 
              width={32} 
              height={32}
              alt="Government of India" 
            />
            <span className="text-lg font-semibold">Ministry of Corporate Affairs</span>
          </div>
          <p className="text-blue-200 mb-2">Government of India</p>
          <p className="text-blue-300 text-sm">
            Empowering policy-making through AI-driven insights and transparent governance
          </p>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
