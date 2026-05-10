import {useState} from 'react';
import UploadZone from '../components/UploadZone';
import FileTree from '../components/FileTree';
import HistoryList from '../components/HistoryList';

export default function DashboardPage({onLogout}) {
  const [tab, setTab] = useState('upload');
  const [trees, setTrees] = useState([]);

  const handleUploaded = (tree) => {
    setTrees((prev) => [tree, ...prev]);
  };

  return (
    <div className="container">
      <header className="dashboard-header">
        <h1>Archive Explorer</h1>
        <button onClick={onLogout}>Log Out</button>
      </header>

      <nav className="tabs">
        <button
          className={`tab ${tab === 'upload' ? 'tab-active' : ''}`}
          onClick={() => setTab('upload')}
        >
          Upload
        </button>
        <button
          className={`tab ${tab === 'history' ? 'tab-active' : ''}`}
          onClick={() => setTab('history')}
        >
          History
        </button>
      </nav>

      {tab === 'upload' && (
        <div>
          <UploadZone onUploaded={handleUploaded} />

          {trees.length === 0 && (
            <p className="empty">No archives extracted yet. Upload one above.</p>
          )}

          {trees.map((tree) => (
            <FileTree key={tree.archive_id} tree={tree} />
          ))}
        </div>
      )}

      {tab === 'history' && <HistoryList />}
    </div>
  );
}
