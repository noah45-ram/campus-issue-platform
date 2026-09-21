import React, { useEffect, useMemo, useState } from 'react';
import {
  AlertTriangle,
  Bell,
  CheckCircle2,
  Clock3,
  MapPin,
  RefreshCw,
  ShieldAlert,
} from 'lucide-react';

import { getIssues } from '../api';

const LOCATION_OPTIONS = [
  'All Locations',
  'H4 Hostel - Ground Floor',
  'H4 Hostel - First Floor',
  'H5 Hostel - Ground Floor',
  'Academic Block',
  'Library',
  'Cafeteria',
  'Sports Complex',
  'Other Campus Area',
];

export default function CampusAlertsPage() {
  const [issues, setIssues] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filterMode, setFilterMode] = useState('all');
  const [selectedArea, setSelectedArea] = useState(
    'H4 Hostel - Ground Floor'
  );

  const fetchIssues = async () => {
    setLoading(true);
    setError('');

    try {
      const data = await getIssues();
      setIssues(data.issues || []);
    } catch (err) {
      setError(err.message || 'Failed to load alerts');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIssues();
  }, []);

const activeIssues = issues.filter((issue) => {
  return (
    issue.status === 'open' ||
    issue.status === 'in_progress'
  );
});

  const criticalCount = activeIssues.filter(
    (issue) =>
      issue.safety?.is_safety_critical ||
      issue.priority?.priority === 'critical'
  ).length;

  const inProgressCount = activeIssues.filter(
    (issue) => issue.status === 'in_progress'
  ).length;

  const displayedAlerts = useMemo(() => {
    return activeIssues
      .filter((issue) => {
        const isCritical =
          issue.safety?.is_safety_critical ||
          issue.priority?.priority === 'critical';

        if (filterMode === 'critical') {
          return isCritical;
        }

        if (filterMode === 'my_area') {
          return (
            isCritical ||
            (issue.location &&
              issue.location
                .toLowerCase()
                .includes(selectedArea.toLowerCase()))
          );
        }

        return true;
      })
      .sort((a, b) => {
        const priorityOrder = {
          critical: 4,
          high: 3,
          medium: 2,
          low: 1,
        };

        return (
          (priorityOrder[b.priority?.priority] || 0) -
          (priorityOrder[a.priority?.priority] || 0)
        );
      });
  }, [activeIssues, filterMode, selectedArea]);

  const getPriorityLabel = (priority) => {
    return priority ? priority.toUpperCase() : 'LOW';
  };

  return (
    <div className="alerts-page">

      {/* Header */}
      <div className="alerts-header">
        <div>
          <div className="page-eyebrow">
            <Bell size={15} />
            CAMPUS MONITORING
          </div>

          <h2 className="alerts-title">
            Active Campus Alerts
          </h2>

          <p className="alerts-description">
            Important safety and maintenance conditions currently requiring
            attention across campus.
          </p>
        </div>

        <button
          type="button"
          className="btn btn-secondary refresh-alerts"
          onClick={fetchIssues}
          disabled={loading}
        >
          <RefreshCw size={16} className={loading ? 'spin' : ''} />
          Refresh
        </button>
      </div>

      {/* Summary */}
      <div className="alert-summary-grid">

        <div className="alert-summary-card">
          <div className="alert-summary-icon">
            <Bell size={19} />
          </div>

          <div>
            <span className="alert-summary-label">
              Active Alerts
            </span>
            <strong>{activeIssues.length}</strong>
          </div>
        </div>

        <div className="alert-summary-card critical-summary">
          <div className="alert-summary-icon">
            <ShieldAlert size={19} />
          </div>

          <div>
            <span className="alert-summary-label">
              Critical
            </span>
            <strong>{criticalCount}</strong>
          </div>
        </div>

        <div className="alert-summary-card">
          <div className="alert-summary-icon">
            <Clock3 size={19} />
          </div>

          <div>
            <span className="alert-summary-label">
              In Progress
            </span>
            <strong>{inProgressCount}</strong>
          </div>
        </div>

      </div>

      {/* Filters */}
      <div className="alerts-filter-card">

        <div className="alerts-filter-header">
          <div>
            <strong>View alerts</strong>
            <span>
              Choose which campus conditions you want to see.
            </span>
          </div>
        </div>

        <div className="alerts-filter-row">

          <div className="alerts-filter-buttons">

            <button
              type="button"
              className={`filter-chip ${
                filterMode === 'all' ? 'active' : ''
              }`}
              onClick={() => setFilterMode('all')}
            >
              <Bell size={15} />
              All Alerts
              <span>{activeIssues.length}</span>
            </button>

            <button
              type="button"
              className={`filter-chip ${
                filterMode === 'my_area' ? 'active' : ''
              }`}
              onClick={() => setFilterMode('my_area')}
            >
              <MapPin size={15} />
              My Area
            </button>

            <button
              type="button"
              className={`filter-chip critical-chip ${
                filterMode === 'critical' ? 'active' : ''
              }`}
              onClick={() => setFilterMode('critical')}
            >
              <AlertTriangle size={15} />
              Critical
              <span>{criticalCount}</span>
            </button>

          </div>

          {filterMode === 'my_area' && (
            <div className="area-selector">
              <MapPin size={15} />

              <select
                id="select-area-filter"
                value={selectedArea}
                onChange={(event) =>
                  setSelectedArea(event.target.value)
                }
              >
                {LOCATION_OPTIONS
                  .filter((location) => location !== 'All Locations')
                  .map((location) => (
                    <option key={location} value={location}>
                      {location}
                    </option>
                  ))}
              </select>
            </div>
          )}

        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="alert-error" role="alert">
          <AlertTriangle size={18} />
          <span>{error}</span>
        </div>
      )}

      {/* Loading */}
      {loading && displayedAlerts.length === 0 && (
        <div className="alerts-empty-state">
          <RefreshCw size={26} className="spin" />
          <strong>Loading alerts</strong>
          <span>Checking the latest campus conditions...</span>
        </div>
      )}

      {/* Empty */}
      {!loading && displayedAlerts.length === 0 && !error && (
        <div className="alerts-empty-state">
          <CheckCircle2 size={30} />

          <strong>
            No active alerts
          </strong>

          <span>
            There are no active safety hazards or maintenance issues
            matching this view.
          </span>
        </div>
      )}

      {/* Alerts */}
      {displayedAlerts.length > 0 && (
        <div className="alerts-list">

          {displayedAlerts.map((alert) => {
            const isCritical =
              alert.safety?.is_safety_critical ||
              alert.priority?.priority === 'critical';

            return (
              <article
                key={alert.id}
                className={`campus-alert-card ${
                  isCritical ? 'critical' : ''
                }`}
              >

                <div className="alert-card-icon">
                  {isCritical ? (
                    <ShieldAlert size={21} />
                  ) : (
                    <Bell size={21} />
                  )}
                </div>

                <div className="alert-card-content">

                  <div className="alert-card-top">

                    <div>
                      <div className="alert-card-id">
                        {alert.id}
                      </div>

                      <h3>
                        {alert.category?.replace('_', ' ')}
                      </h3>
                    </div>

                    <div className="alert-card-badges">

                      <span
                        className={`priority-pill priority-${alert.priority?.priority || 'low'}`}
                      >
                        {getPriorityLabel(
                          alert.priority?.priority
                        )}
                      </span>

                      <span
                        className={`status-pill status-${alert.status}`}
                      >
                        {alert.status?.replace('_', ' ')}
                      </span>

                    </div>

                  </div>

                  <div className="alert-location">
                    <MapPin size={14} />
                    {alert.location || 'Campus area not specified'}
                  </div>

                  <p className="alert-description">
                    {alert.description}
                  </p>

                  {alert.report_count > 1 && (
                    <div className="alert-report-count">
                      Reported {alert.report_count} times
                    </div>
                  )}

                  {alert.safety?.message && (
                    <div
                      className={`alert-guidance ${
                        isCritical ? 'critical-guidance' : ''
                      }`}
                    >
                      {isCritical ? (
                        <ShieldAlert size={17} />
                      ) : (
                        <CheckCircle2 size={17} />
                      )}

                      <div>
                        <strong>
                          {isCritical
                            ? 'Safety instruction'
                            : 'Quick advisory'}
                        </strong>

                        <span>
                          {alert.safety.message}
                        </span>
                      </div>
                    </div>
                  )}

                </div>

              </article>
            );
          })}

        </div>
      )}

    </div>
  );
}