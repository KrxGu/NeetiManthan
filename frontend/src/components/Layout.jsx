import React, { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, 
  FileText, 
  MessageSquare, 
  BarChart3, 
  Menu, 
  X,
  Settings,
  HelpCircle
} from 'lucide-react';

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Draft Upload', href: '/draft', icon: FileText },
  { name: 'Comments', href: '/comments', icon: MessageSquare },
  { name: 'Analytics', href: '/analytics', icon: BarChart3 },
];

function SidebarContent({ onClose }) {
    const location = useLocation();
    return (
        <div className="flex grow flex-col gap-y-5 overflow-y-auto bg-white border-r border-gray-200 px-6 pb-4">
            <div className="flex h-16 shrink-0 items-center">
              <div className="flex items-center">
                  <div className="flex-shrink-0">
                      <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
                          <span className="text-white font-bold text-sm">NM</span>
                      </div>
                  </div>
                  <div className="ml-3">
                      <h1 className="text-lg font-semibold text-gray-900">NeetiManthan</h1>
                      <p className="text-xs text-gray-500">AI Comment Analysis</p>
                  </div>
              </div>
            </div>
            <nav className="flex flex-1 flex-col">
                <ul role="list" className="flex flex-1 flex-col gap-y-7">
                    <li>
                        <ul role="list" className="-mx-2 space-y-1">
                            {navigation.map((item) => {
                                const isActive = location.pathname === item.href;
                                return (
                                    <li key={item.name}>
                                        <NavLink
                                            to={item.href}
                                            onClick={onClose}
                                            className={`group flex gap-x-3 rounded-md p-2 text-sm leading-6 font-semibold ${
                                                isActive
                                                ? 'bg-gray-50 text-primary-600'
                                                : 'text-gray-700 hover:text-primary-600 hover:bg-gray-50'
                                            }`}
                                        >
                                            <item.icon
                                                className={`h-6 w-6 shrink-0 ${
                                                    isActive ? 'text-primary-600' : 'text-gray-400 group-hover:text-primary-600'
                                                }`}
                                                aria-hidden="true"
                                            />
                                            {item.name}
                                        </NavLink>
                                    </li>
                                );
                            })}
                        </ul>
                    </li>
                    <li className="mt-auto">
                        <NavLink
                            to="#"
                            className="group -mx-2 flex gap-x-3 rounded-md p-2 text-sm font-semibold leading-6 text-gray-700 hover:bg-gray-50 hover:text-primary-600"
                        >
                            <Settings
                                className="h-6 w-6 shrink-0 text-gray-400 group-hover:text-primary-600"
                                aria-hidden="true"
                            />
                            Settings
                        </NavLink>
                    </li>
                </ul>
            </nav>
        </div>
    );
}

function Layout({ children }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();

  const currentPage = navigation.find(item => item.href === location.pathname)?.name || 'Dashboard';

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Static sidebar for desktop */}
      <div className="hidden lg:flex lg:flex-shrink-0">
        <div className="flex flex-col w-64">
          <SidebarContent onClose={() => {}} />
        </div>
      </div>

      {/* Mobile sidebar */}
      {sidebarOpen && (
        <div className="relative z-50 lg:hidden" onClose={setSidebarOpen}>
          <div className="fixed inset-0 bg-gray-900/80" />
          <div className="fixed inset-0 flex">
            <div className="relative mr-16 flex w-full max-w-xs flex-1">
              <div className="absolute left-full top-0 flex w-16 justify-center pt-5">
                <button type="button" className="-m-2.5 p-2.5" onClick={() => setSidebarOpen(false)}>
                  <span className="sr-only">Close sidebar</span>
                  <X className="h-6 w-6 text-white" aria-hidden="true" />
                </button>
              </div>
              <SidebarContent onClose={() => setSidebarOpen(false)} />
            </div>
          </div>
        </div>
      )}

      <div className="flex flex-col flex-1 w-0 overflow-hidden">
        <div className="relative z-10 flex-shrink-0 flex h-16 bg-white shadow">
          <button
            type="button"
            className="px-4 border-r border-gray-200 text-gray-500 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-primary-500 lg:hidden"
            onClick={() => setSidebarOpen(true)}
          >
            <span className="sr-only">Open sidebar</span>
            <Menu className="h-6 w-6" aria-hidden="true" />
          </button>
          <div className="flex-1 px-4 flex justify-between">
            <div className="flex-1 flex">
               <h1 className="my-auto text-xl font-semibold text-gray-900">{currentPage}</h1>
            </div>
            <div className="ml-4 flex items-center md:ml-6">
                <div className="flex items-center space-x-2">
                  <div className="w-2.5 h-2.5 bg-success-500 rounded-full animate-pulse-soft"></div>
                  <span className="text-sm text-gray-600">System Online</span>
                </div>
            </div>
          </div>
        </div>

        <main className="flex-1 relative overflow-y-auto focus:outline-none">
          <div className="py-6">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              {children}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

export default Layout;
