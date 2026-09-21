import React, { useEffect, useMemo, useState } from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  Clock3,
  MapPin,
  RefreshCw,
  ShieldAlert,
  Wrench,
} from 'lucide-react';

import { getIssues, updateIssueStatus } from '../api';

const PRIORITY_ORDER = {
  critical: 4,
  high: 3,
  medium: 2,
  low: 1,
};

export default function MaintenancePage() {
  const [issues, setIssues] = useState([]);
  const [loading, setLoading] = useState(true);
  const [updatingId, setUpdatingId] = useState(null);
  const [error, setError] = useState('');

  const fetchIssues = async () => {
    setLoading(true);
    setError('');

    try {
      const data = await getIssues();
      setIssues(data.issues || []);
    } catch (err) {
      setError(err.message || 'Failed to load maintenance queue');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIssues();
  }, []);

  const handleStatusChange = async (issueId, newStatus) => {
    setUpdatingId(issueId);
    setError('');

    try {
      await updateIssueStatus(issueId, newStatus);
      await fetchIssues();
    } catch (err) {
      setError(err.message || `Failed to update status`);
    } finally {
      setUpdatingId(null);
    }
  };

  const sortedIssues = useMemo(() => {
    return [...issues].sort((a, b) => {
      const priorityA =
        PRIORITY_ORDER[(a.priority?.priority || 'low').toLowerCase()] || 0;

      const priorityB =
        PRIORITY_ORDER[(b.priority?.priority || 'low').toLowerCase()] || 0;

      if (priorityB !== priorityA) {
        return priorityB - priorityA;
      }

      if (a.status === 'resolved' && b.status !== 'resolved') return 1;
      if (a.status !== 'resolved' && b.status === 'resolved') return -1;

      return 0;
    });
  }, [issues]);

  const activeCount = issues.filter(
    (issue) => issue.status !== 'resolved'
  ).length;

  const criticalCount = issues.filter(
    (issue) =>
      issue.priority?.priority === 'critical' ||
      issue.safety?.is_safety_critical
  ).length;

  const inProgressCount = issues.filter(
    (issue) => issue.status === 'in_progress'
  ).length;

  return (
    <div className="maintenance-page">

      {/* Header */}
      <div className="maintenance-header">
        <div>
          <div className="page-eyebrow">
            <Wrench size={15} />
            OPERATIONS
          </div>

          <h2 className="maintenance-title">
            Maintenance Queue
          </h2>

          <p className="maintenance-description">
            Work items are ordered by deterministic priority so critical
            safety issues receive attention first.
          </p>
        </div>

        <button
          className="btn btn-secondary refresh-maintenance"
          onClick={fetchIssues}
          disabled={loading}
        >
          <RefreshCw size={16} className={loading ? 'spin' : ''} />
          Refresh
        </button>
      </div>

      {/* Summary */}
      <div className="maintenance-summary-grid">

        <div className="maintenance-summary-card">
          <div className="maintenance-summary-icon">
            <Wrench size={19} />
          </div>

          <div>
            <span>Active Work</span>
            <strong>{activeCount}</strong>
          </div>
        </div>

        <div className="maintenance-summary-card critical-summary">
          <div className="maintenance-summary-icon">
            <ShieldAlert size={19} />
          </div>

          <div>
            <span>Critical</span>
            <strong>{criticalCount}</strong>
          </div>
        </div>

        <div className="maintenance-summary-card">
          <div className="maintenance-summary-icon">
            <Clock3 size={19} />
          </div>

          <div>
            <span>In Progress</span>
            <strong>{inProgressCount}</strong>
          </div>
        </div>

      </div>

      {/* Error */}
      {error && (
        <div className="maintenance-error" role="alert">
          <AlertTriangle size={18} />
          <span>{error}</span>
        </div>
      )}

      {/* Queue */}
      {loading && issues.length === 0 ? (
        <div className="maintenance-empty">
          <RefreshCw size={26} className="spin" />
          <strong>Loading maintenance queue</strong>
          <span>Checking current campus work items...</span>
        </div>
      ) : sortedIssues.length === 0 ? (
        <div className="maintenance-empty">
          <CheckCircle2 size={30} />
          <strong>No issues in the maintenance queue</strong>
          <span>All campus issues are currently clear.</span>
        </div>
      ) : (
        <div className="maintenance-list">

          {sortedIssues.map((issue) => {
            const isCritical =
              issue.priority?.priority === 'critical' ||
              issue.safety?.is_safety_critical;

            const priority =
              issue.priority?.priority || 'low';

            const dateStr = issue.created_at
              ? new Date(issue.created_at).toLocaleString()
              : 'N/A';

            return (
              <article
                key={issue.id}
                className={`maintenance-card ${
                  isCritical ? 'critical' : ''
                }`}
              >

                <div className="maintenance-card-icon">
                  {isCritical ? (
                    <ShieldAlert size={21} />
                  ) : (
                    <Wrench size={21} />
                  )}
                </div>

                <div className="maintenance-card-content">

                  <div className="maintenance-card-top">

                    <div>
                      <div className="maintenance-id">
                        {issue.id}
                      </div>

                      <h3>
                        {issue.category?.replace('_', ' ') || 'Other issue'}
                      </h3>
                    </div>

                    <div className="maintenance-badges">
                      <span
                        className={`priority-pill priority-${priority}`}
                      >
                        {priority}
                      </span>

                      <span
                        className={`status-pill status-${issue.status}`}
                      >
                        {issue.status?.replace('_', ' ')}
                      </span>

                      {issue.report_count > 1 && (
                        <span className="report-count-pill">
                          {issue.report_count} reports
                        </span>
                      )}
                    </div>

                  </div>

                  <div className="maintenance-location">
                    <MapPin size={14} />
                    {issue.location || 'Location not specified'}
                  </div>

                  <p className="maintenance-description-text">
                    {issue.description}
                  </p>

                  <div className="maintenance-meta">
                    <span>
                      <strong>Severity:</strong>{' '}
                      {issue.severity || 'low'}
                    </span>

                    <span>
                      <strong>Created:</strong>{' '}
                      {dateStr}
                    </span>
                  </div>

                  {issue.safety?.message && (
                    <div
                      className={`maintenance-guidance ${
                        isCritical ? 'critical-guidance' : ''
                      }`}
                    >
                      {isCritical ? (
                        <ShieldAlert size={17} />
                      ) : (
                        <AlertTriangle size={17} />
                      )}

                      <div>
                        <strong>
                          {isCritical
                            ? 'Safety instruction'
                            : 'Safety note'}
                        </strong>

                        <span>
                          {issue.safety.message}
                        </span>
                      </div>
                    </div>
                  )}

                  {/* Actions */}
                  <div className="maintenance-actions">

                    {issue.status === 'open' && (
                      <button
                        className="btn btn-primary btn-sm"
                        onClick={() =>
                          handleStatusChange(
                            issue.id,
                            'in_progress'
                          )
                        }
                        disabled={updatingId === issue.id}
                      >
                        <Wrench size={15} />
                        {updatingId === issue.id
                          ? 'Updating...'
                          : 'Start Work'}
                      </button>
                    )}

                    {issue.status === 'in_progress' && (
                      <button
                        className="btn btn-primary btn-sm"
                        onClick={() =>
                          handleStatusChange(
                            issue.id,
                            'resolved'
                          )
                        }
                        disabled={updatingId === issue.id}
                      >
                        <CheckCircle2 size={15} />
                        {updatingId === issue.id
                          ? 'Updating...'
                          : 'Mark Resolved'}
                      </button>
                    )}

                    {issue.status === 'resolved' && (
                      <button
                        className="btn btn-secondary btn-sm"
                        onClick={() =>
                          handleStatusChange(
                            issue.id,
                            'open'
                          )
                        }
                        disabled={updatingId === issue.id}
                      >
                        Re-open
                      </button>
                    )}

                  </div>

                </div>

              </article>
            );
          })}

        </div>
      )}

    </div>
  );
}