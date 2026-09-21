import React, { useEffect, useMemo, useState } from 'react';
import {
  AlertTriangle,
  BarChart3,
  CheckCircle2,
  Clock3,
  FileText,
  RefreshCw,
  ShieldAlert,
} from 'lucide-react';

import { getIssues } from '../api';

export default function AdminPage() {
  const [issues, setIssues] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchIssues = async () => {
    setLoading(true);
    setError('');

    try {
      const data = await getIssues();
      setIssues(data.issues || []);
    } catch (err) {
      setError(
        err.message || 'Failed to load admin metrics'
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIssues();
  }, []);

  const totalReports = issues.length;

  const openCount = issues.filter(
    (issue) => issue.status === 'open'
  ).length;

  const inProgressCount = issues.filter(
    (issue) => issue.status === 'in_progress'
  ).length;

  const resolvedCount = issues.filter(
    (issue) => issue.status === 'resolved'
  ).length;

  const criticalCount = issues.filter(
    (issue) =>
      issue.priority?.priority === 'critical' ||
      issue.safety?.is_safety_critical
  ).length;

  const categoryCounts = useMemo(() => {
    return issues.reduce((acc, issue) => {
      const category =
        (issue.category || 'other').toLowerCase();

      acc[category] = (acc[category] || 0) + 1;
      return acc;
    }, {});
  }, [issues]);

  const priorityCounts = useMemo(() => {
    return issues.reduce((acc, issue) => {
      const priority =
        (issue.priority?.priority || 'low').toLowerCase();

      acc[priority] = (acc[priority] || 0) + 1;
      return acc;
    }, {});
  }, [issues]);

  const recentIssues = useMemo(() => {
    return [...issues]
      .sort(
        (a, b) =>
          new Date(b.created_at || 0) -
          new Date(a.created_at || 0)
      )
      .slice(0, 5);
  }, [issues]);

  return (
    <div className="admin-page">

      {/* Header */}
      <div className="admin-header">
        <div>
          <div className="page-eyebrow">
            <BarChart3 size={15} />
            ADMINISTRATION
          </div>

          <h2 className="admin-title">
            Campus Operations Overview
          </h2>

          <p className="admin-description">
            Monitor issue volume, priority distribution, safety
            conditions, and resolution activity.
          </p>
        </div>

        <button
          className="btn btn-secondary refresh-admin"
          onClick={fetchIssues}
          disabled={loading}
        >
          <RefreshCw
            size={16}
            className={loading ? 'spin' : ''}
          />
          Refresh
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="admin-error" role="alert">
          <AlertTriangle size={18} />
          <span>{error}</span>
        </div>
      )}

      {/* KPIs */}
      <div className="admin-kpi-grid">

        <div className="admin-kpi-card">
          <div className="admin-kpi-icon">
            <FileText size={19} />
          </div>

          <span>Total Reports</span>
          <strong>{totalReports}</strong>
        </div>

        <div className="admin-kpi-card">
          <div className="admin-kpi-icon blue">
            <Clock3 size={19} />
          </div>

          <span>Open Issues</span>
          <strong>{openCount}</strong>
        </div>

        <div className="admin-kpi-card">
          <div className="admin-kpi-icon amber">
            <RefreshCw size={19} />
          </div>

          <span>In Progress</span>
          <strong>{inProgressCount}</strong>
        </div>

        <div className="admin-kpi-card">
          <div className="admin-kpi-icon green">
            <CheckCircle2 size={19} />
          </div>

          <span>Resolved</span>
          <strong>{resolvedCount}</strong>
        </div>

        <div
          className={`admin-kpi-card ${
            criticalCount > 0 ? 'critical-kpi' : ''
          }`}
        >
          <div className="admin-kpi-icon red">
            <ShieldAlert size={19} />
          </div>

          <span>Critical Hazards</span>
          <strong>{criticalCount}</strong>
        </div>

      </div>

      {/* Analytics */}
      <div className="admin-analytics-grid">

        {/* Categories */}
        <section className="admin-panel">
          <div className="admin-panel-heading">
            <div>
              <h3>Category Distribution</h3>
              <span>
                What types of issues are being reported?
              </span>
            </div>

            <BarChart3 size={18} />
          </div>

          {Object.keys(categoryCounts).length === 0 ? (
            <div className="admin-empty">
              No category data available.
            </div>
          ) : (
            <div className="admin-bars">
              {Object.entries(categoryCounts).map(
                ([category, count]) => {
                  const percentage =
                    totalReports > 0
                      ? Math.round(
                          (count / totalReports) * 100
                        )
                      : 0;

                  return (
                    <div
                      className="admin-bar-row"
                      key={category}
                    >
                      <div className="admin-bar-label">
                        <span>
                          {category.replace('_', ' ')}
                        </span>

                        <strong>
                          {count} · {percentage}%
                        </strong>
                      </div>

                      <div className="admin-bar-track">
                        <div
                          className="admin-bar-fill"
                          style={{
                            width: `${percentage}%`,
                          }}
                        />
                      </div>
                    </div>
                  );
                }
              )}
            </div>
          )}
        </section>

        {/* Priority */}
        <section className="admin-panel">
          <div className="admin-panel-heading">
            <div>
              <h3>Priority Overview</h3>
              <span>
                Distribution of operational urgency.
              </span>
            </div>

            <ShieldAlert size={18} />
          </div>

          <div className="admin-bars">
            {['critical', 'high', 'medium', 'low'].map(
              (priority) => {
                const count =
                  priorityCounts[priority] || 0;

                const percentage =
                  totalReports > 0
                    ? Math.round(
                        (count / totalReports) * 100
                      )
                    : 0;

                return (
                  <div
                    className="admin-bar-row"
                    key={priority}
                  >
                    <div className="admin-bar-label">
                      <span className="priority-name">
                        {priority}
                      </span>

                      <strong>
                        {count} · {percentage}%
                      </strong>
                    </div>

                    <div className="admin-bar-track">
                      <div
                        className={`admin-bar-fill priority-fill-${priority}`}
                        style={{
                          width: `${percentage}%`,
                        }}
                      />
                    </div>
                  </div>
                );
              }
            )}
          </div>
        </section>

      </div>

      {/* Recent Issues */}
      <section className="admin-panel admin-recent-panel">

        <div className="admin-panel-heading">
          <div>
            <h3>Recent Issues</h3>
            <span>
              Latest five reports entering the system.
            </span>
          </div>

          <FileText size={18} />
        </div>

        {recentIssues.length === 0 ? (
          <div className="admin-empty">
            No issues logged yet.
          </div>
        ) : (
          <div className="admin-table-wrapper">
            <table className="admin-table">

              <thead>
                <tr>
                  <th>Issue</th>
                  <th>Location</th>
                  <th>Category</th>
                  <th>Priority</th>
                  <th>Status</th>
                </tr>
              </thead>

              <tbody>
                {recentIssues.map((issue) => (
                  <tr key={issue.id}>

                    <td>
                      <strong>{issue.id}</strong>
                    </td>

                    <td>
                      {issue.location || 'Not specified'}
                    </td>

                    <td>
                      {issue.category?.replace('_', ' ')}
                    </td>

                    <td>
                      <span
                        className={`priority-pill priority-${
                          issue.priority?.priority || 'low'
                        }`}
                      >
                        {issue.priority?.priority || 'low'}
                      </span>
                    </td>

                    <td>
                      <span
                        className={`status-pill status-${issue.status}`}
                      >
                        {issue.status?.replace('_', ' ')}
                      </span>
                    </td>

                  </tr>
                ))}
              </tbody>

            </table>
          </div>
        )}

      </section>

    </div>
  );
}