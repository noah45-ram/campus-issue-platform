const API_BASE = import.meta.env.VITE_API_URL || '/api';

async function handleResponse(response) {
  const contentType = response.headers.get('content-type') || '';

  let data;

  if (contentType.includes('application/json')) {
    data = await response.json();
  } else {
    data = await response.text();
  }

  if (!response.ok) {
    const message =
      typeof data === 'string'
        ? data
        : data?.detail || data?.message || 'Request failed';

    throw new Error(message);
  }

  return data;
}

export async function analyzeIssue(payload) {
  const response = await fetch(`${API_BASE}/issues/analyze`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  return handleResponse(response);
}

export async function createIssue(payload) {
  const formData = new FormData();

  if (payload.description) {
    formData.append('description', payload.description);
  }

  if (payload.location) {
    formData.append('location', payload.location);
  }

  formData.append(
    'recurrence',
    payload.recurrence ? 'true' : 'false'
  );

  formData.append(
    'affected_area',
    payload.affectedArea || 'local'
  );

  if (payload.image) {
    formData.append('image', payload.image);
  }

  const response = await fetch(`${API_BASE}/issues`, {
    method: 'POST',
    body: formData,
  });

  return handleResponse(response);
}

/* Keep this name because the existing pages import getIssues(). */
export async function getIssues() {
  const response = await fetch(`${API_BASE}/issues`);

  return handleResponse(response);
}

export async function getIssue(issueId) {
  const response = await fetch(
    `${API_BASE}/issues/${encodeURIComponent(issueId)}`
  );

  return handleResponse(response);
}

export async function updateIssueStatus(issueId, status) {
  const response = await fetch(
    `${API_BASE}/issues/${encodeURIComponent(issueId)}/status`,
    {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ status }),
    }
  );

  return handleResponse(response);
}