import { ChevronDown, ChevronRight, File, Folder, FolderOpen } from 'lucide-react';
import { useState } from 'react';

export interface FileNode {
  id: string;
  name: string;
  type: 'file' | 'directory';
  path: string;
  children?: FileNode[];
  language?: 'python' | 'cpp' | 'text';
}

interface FileTreeProps {
  files: FileNode[];
  selectedFile: string | null;
  onFileSelect: (file: FileNode) => void;
  onCreateFile?: (parentPath: string, name: string, type: 'file' | 'directory') => void;
}

export const FileTree = ({ files, selectedFile, onFileSelect, onCreateFile }: FileTreeProps) => {
  return (
    <div className="file-tree" style={{ display: 'flex', flexDirection: 'column', gap: '0.15rem' }}>
      {files.map(node => (
        <TreeNode
          key={node.id}
          node={node}
          level={0}
          selectedFile={selectedFile}
          onFileSelect={onFileSelect}
          onCreateFile={onCreateFile}
        />
      ))}
    </div>
  );
};

interface TreeNodeProps {
  node: FileNode;
  level: number;
  selectedFile: string | null;
  onFileSelect: (file: FileNode) => void;
  onCreateFile?: (parentPath: string, name: string, type: 'file' | 'directory') => void;
}

const TreeNode = ({ node, level, selectedFile, onFileSelect, onCreateFile }: TreeNodeProps) => {
  const [isExpanded, setIsExpanded] = useState(level === 0);
  const [isHovered, setIsHovered] = useState(false);
  const isSelected = node.path === selectedFile;
  const hasChildren = node.children && node.children.length > 0;

  const handleClick = () => {
    if (node.type === 'directory') {
      setIsExpanded(!isExpanded);
    } else {
      onFileSelect(node);
    }
  };

  const getFileIcon = () => {
    if (node.type === 'directory') {
      return isExpanded ? <FolderOpen size={16} /> : <Folder size={16} />;
    }
    return <File size={16} />;
  };

  const getFileColor = () => {
    if (node.type === 'directory') return '#90caf9';
    if (node.language === 'python') return '#ffd166';
    if (node.language === 'cpp') return '#6ee7b7';
    return '#a6accd';
  };

  const backgroundColor = isSelected ? '#37373d' : isHovered ? 'rgba(42, 45, 46, 0.75)' : 'transparent';
  const textColor = isSelected ? '#f3f4f6' : '#d4d4d8';

  return (
    <div>
      <div
        onClick={handleClick}
        className={`tree-node ${isSelected ? 'selected' : ''}`}
        style={{
          paddingLeft: `${level * 14 + 10}px`,
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          padding: '0.32rem 0.5rem',
          cursor: 'pointer',
          userSelect: 'none',
          backgroundColor,
          borderLeft: isSelected ? '2px solid #007acc' : '2px solid transparent',
          transition: 'background-color 0.15s ease'
        }}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        {node.type === 'directory' && (
          <span style={{ display: 'flex', alignItems: 'center', color: '#9da5b4' }}>
            {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
          </span>
        )}
        {node.type === 'file' && <span style={{ width: '14px' }} />}
        <span style={{ color: getFileColor(), display: 'flex', alignItems: 'center' }}>
          {getFileIcon()}
        </span>
        <span
          style={{
            fontSize: '0.85rem',
            color: textColor,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap'
          }}
        >
          {node.name}
        </span>
      </div>
      {node.type === 'directory' && isExpanded && hasChildren && (
        <div>
          {node.children!.map(child => (
            <TreeNode
              key={child.id}
              node={child}
              level={level + 1}
              selectedFile={selectedFile}
              onFileSelect={onFileSelect}
              onCreateFile={onCreateFile}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default FileTree;
