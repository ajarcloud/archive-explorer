import {useRef, useState} from 'react';
import api from '../api';

export default function UploadZone({onUploaded}) {
  const [dragOver, setDragOver] = useState(false);
  const [progress, setProgress] = useState(null);
  const inputRef = useRef(null);

  const upload = async (file) => {
    setProgress({filename: file.name, stage: 'uploading'});

    const form = new FormData();
    form.append('file', file);

    let tree;
    try {
      tree = await api.post('/archives/upload', form);
    } catch (err) {
      setProgress((p) => p && {
        ...p, stage: 'error', error: err.message || 'Upload failed',
      });
      return;
    }

    setProgress((p) => p && {...p, stage: 'complete'});
    onUploaded(tree);
  };

  const onDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) upload(file);
  };

  const onFileChange = (e) => {
    const file = e.target.files[0];
    if (file) upload(file);
  };

  return (
    <div className="upload-section">
      <div
        className={`dropzone ${dragOver ? 'drag-over' : ''}`}
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={onDrop}
        onClick={() => inputRef.current?.click()}
      >
        <p>Drop a .zip or .tar.zst file here, or click to browse</p>
      </div>
      <input
        ref={inputRef}
        type="file"
        accept=".zip,.tar.zst,.zst"
        onChange={onFileChange}
        style={{display: 'none'}}
      />

      {progress && (
        <div
          className={
            'progress-panel' +
            (progress.stage === 'error' ? ' progress-error' : '')
          }
        >
          <div className="progress-head">
            <span className="progress-filename">{progress.filename}</span>
            <span className="progress-stage">
              {progress.stage === 'uploading' && 'Uploading…'}
              {progress.stage === 'complete' && 'Done'}
              {progress.stage === 'error' && 'Failed'}
            </span>
          </div>
          {progress.stage === 'uploading' && <progress />}
          {progress.stage === 'complete' && (
            <progress max="100" value="100" />
          )}
          {progress.stage === 'error' && (
            <p className="progress-msg">{progress.error}</p>
          )}
        </div>
      )}
    </div>
  );
}
