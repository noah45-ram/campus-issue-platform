import React, { useState, useEffect } from 'react';
import { getIssues } from '../api';

export default function MyReportsPage() {
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
      setError(err.message || 'Failed to load issues');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIssues();
  }, []);

  return (
    <div>
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div>
            <h2 className="card-title" style={{ marginBottom: '4px' }}>My Campus Reports</h2>
            <p className="form-hint">View all reported sustainability and maintenance issues across campus.</p>
          </div>
          <button className="btn btn-secondary btn-sm" onClick={fetchIssues} disabled={loading}>
            {loading ? 'Refreshing...' : 'Refresh List'}
          </button>
        </div>

        {error && (
          <div className="banner banner-critical" role="alert">
            <div>{error}</div>
          </div>
        )}

        {loading && issues.length === 0 ? (
          <div className="empty-state">
            <span className="spinner" style={{ borderColor: 'var(--color-primary) transparent var(--color-primary) transparent', width: '28px', height: '28px' }} />
            <div style={{ marginTop: '12px' }}>Loading reports...</div>
          </div>
        ) : issues.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-title">No issues reported yet</div>
            <div>Submit your first campus issue using the Report Issue tab.</div>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table className="issues-table">
              <thead>
                <tr>
                  <th>Issue ID</th>
                  <th>Category</th>
                  <th>Location</th>
                  <th>Description</th>
                  <th>Priority</th>
                  <th>Status</th>
                  <th>Reported Date</th>
                </tr>
              </thead>
              <tbody>
                {issues.map((issue) => {
                  const dateStr = issue.created_at
                    ? new Date(issue.created_at).toLocaleString(undefined, {
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                      })
                    : 'N/A';

                  return (
                    <tr key={issue.id}>
                      <td style={{ fontWeight: 600, color: 'var(--color-primary-dark)', whiteSpace: 'nowrap' }}>
                        {issue.id}
                      </td>
                      <td style={{ textTransform: 'capitalize', whiteSpace: 'nowrap' }}>
                        {issue.category}
                      </td>
                      <td style={{ whiteSpace: 'nowrap' }}>
                        {issue.location}
                      </td>
                      <td style={{ maxWidth: '320px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {issue.description}
                      </td>
                      <td>
                        <span className={`badge badge-prio-${issue.priority?.priority || 'low'}`}>
                          {issue.priority?.priority || 'low'}
                        </span>
                      </td>
                      <td>
                        <span className={`badge badge-status-${issue.status}`}>
                          {issue.status.replace('_', ' ')}
                        </span>
                      </td>
                      <td style={{ fontSize: '12px', color: 'var(--color-text-muted)', whiteSpace: 'nowrap' }}>
                        {dateStr}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
