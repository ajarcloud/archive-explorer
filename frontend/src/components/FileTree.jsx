import {useState} from 'react';

function formatSize(bytes) {
  if (bytes === 0) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB'];
  const i = Math.min(
    Math.floor(Math.log(bytes) / Math.log(1024)),
    units.length - 1
  );
  return (bytes / Math.pow(1024, i)).toFixed(i === 0 ? 0 : 1) + ' ' + units[i];
}

function TreeNode({node}) {
  const [open, setOpen] = useState(false);
  const isDir = node.is_dir;

  return (
    <li>
      <div
        className={`tree-row ${isDir ? 'dir' : 'file'}`}
        onClick={() => isDir && setOpen(!open)}
      >
        <span className="tree-icon">
          {isDir ? (open ? '▼' : '▶') : '⁣'}
        </span>
        <span className="tree-name">{node.name}</span>
        <span className="tree-size">{formatSize(node.size)}</span>
      </div>
      {isDir && open && node.children && (
        <ul>
          {node.children.map((child) => (
            <TreeNode key={child.path} node={child} />
          ))}
        </ul>
      )}
    </li>
  );
}

export default function FileTree({tree}) {
  if (!tree) return null;

  return (
    <div className="file-tree">
      <h3>{tree.name}</h3>
      <ul>
        {tree.children?.map((child) => (
          <TreeNode key={child.path} node={child} />
        ))}
      </ul>
    </div>
  );
}
