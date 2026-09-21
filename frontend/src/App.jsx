import React, { useState } from 'react';
import {
  BarChart3,
  Bell,
  ClipboardList,
  FilePlus2,
  Camera,
  ShieldCheck,
  Wrench,
} from 'lucide-react';

import ReportPage from './pages/ReportPage';
import MyReportsPage from './pages/MyReportsPage';
import CampusAlertsPage from './pages/CampusAlertsPage';
import MaintenancePage from './pages/MaintenancePage';
import AdminPage from './pages/AdminPage';

const NAV_ITEMS = [
  {
    id: 'report',
    label: 'Report Issue',
    icon: FilePlus2,
  },
  {
    id: 'reports',
    label: 'My Reports',
    icon: ClipboardList,
  },
  {
    id: 'alerts',
    label: 'Campus Alerts',
    icon: Bell,
  },
  {
    id: 'maintenance',
    label: 'Maintenance',
    icon: Wrench,
  },
  {
    id: 'admin',
    label: 'Admin',
    icon: BarChart3,
  },
];

const PAGE_TITLES = {
  report: 'Report an Issue',
  reports: 'My Reports',
  alerts: 'Campus Alerts',
  maintenance: 'Maintenance',
  admin: 'Operations Analytics',
};

export default function App() {
  const [activeTab, setActiveTab] = useState('report');

  const handleNavigation = (tab) => {
    setActiveTab(tab);
  };

  return (
    <div className="app-container">
{/* Sidebar */}
<aside className="sidebar">
<div className="sidebar-header">
  <div className="brand-copy">

    <span className="brand-badge">
      Campus Operations
    </span>

    <div className="brand-row">
      <div className="brand-mark">
        <Camera size={22} strokeWidth={2.1} />
      </div>

      <div className="brand-text">
        <h1 className="app-title">
          SnapAct
        </h1>

        <p className="app-subtitle">
          Spot it. Report it. Act on it.
        </p>
      </div>
    </div>

  </div>
</div>

        <nav aria-label="Main navigation">
          <div className="nav-section-label">Workspace</div>

          <ul className="nav-list">
            {NAV_ITEMS.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;

              return (
                <li key={item.id}>
                  <button
                    type="button"
                    className={`nav-item-btn ${isActive ? 'active' : ''}`}
                    onClick={() => handleNavigation(item.id)}
                    aria-current={isActive ? 'page' : undefined}
                  >
                    <Icon
                      size={18}
                      strokeWidth={isActive ? 2.2 : 1.9}
                      aria-hidden="true"
                    />

                    <span>{item.label}</span>
                  </button>
                </li>
              );
            })}
          </ul>
        </nav>

        <div className="sidebar-footer">
          <div className="system-status">
            <span className="status-dot" />
            <span>System connected</span>
          </div>

          <div className="system-description">
            Campus issue response platform
          </div>
        </div>
      </aside>

      {/* Main application */}
      <div className="main-content">
        <header className="top-bar">
          <div className="top-bar-title">
            <span className="mobile-brand-icon">
              <ShieldCheck size={17} />
            </span>

            <h2 className="page-title">
              {PAGE_TITLES[activeTab]}
            </h2>
          </div>

          <div className="top-bar-status">
            <span className="status-dot" />
            <span>Operational</span>
          </div>
        </header>

        <main className="content-body">
          {activeTab === 'report' && (
            <ReportPage onReportSubmitted={() => {}} />
          )}

          {activeTab === 'reports' && <MyReportsPage />}

          {activeTab === 'alerts' && <CampusAlertsPage />}

          {activeTab === 'maintenance' && <MaintenancePage />}

          {activeTab === 'admin' && <AdminPage />}
        </main>
      </div>
    </div>
  );
}