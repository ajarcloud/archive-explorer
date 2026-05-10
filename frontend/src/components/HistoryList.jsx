import {useEffect, useState} from 'react';
import api from '../api';
import FileTree from './FileTree';

export default function HistoryList() {
  const [jobs, setJobs] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.get('/archives/history')
      .then(setJobs)
      .catch((err) => setError(err.message || 'Failed to load history'));
  }, []);

  if (error) {
    return <p className="error">{error}</p>;
  }

  if (jobs === null) {
    return <p className="empty">Loading…</p>;
  }

  if (jobs.length === 0) {
    return <p className="empty">No archives uploaded yet.</p>;
  }

  return (
    <div>
      {jobs.map((job) => (
        <div key={job.archive_id} className="history-entry">
          <div className="history-meta">
            <span className="history-name">{job.archive_name}</span>
            <span className="history-time">
              {new Date(job.created_at).toLocaleString()}
            </span>
          </div>
          <FileTree tree={job.tree} />
        </div>
      ))}
    </div>
  );
}
