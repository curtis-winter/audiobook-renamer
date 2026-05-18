import { useState, useEffect } from 'react'
import './FolderBrowser.css'

const FolderBrowser = ({ isOpen, onClose, onSelect, initialPath = '' }) => {
  const [currentPath, setCurrentPath] = useState(initialPath || '/')
  const [folders, setFolders] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (isOpen) {
      // Convert relative paths like ./watch to absolute
      let absPath = initialPath || '/'
      if (initialPath && initialPath.startsWith('./')) {
        absPath = '/'
      }
      setCurrentPath(absPath)
      loadFolders(absPath)
    }
  }, [isOpen, initialPath])

  const loadFolders = async (path) => {
    setLoading(true)
    setError(null)
    try {
      const encodedPath = encodeURIComponent(path === '/' ? '/' : path)
      const response = await fetch(`/api/folders?path=${encodedPath}`)
      if (response.ok) {
        const data = await response.json()
        setFolders(data.folders)
        setCurrentPath(data.current)
      } else {
        setError('Failed to load folders')
      }
    } catch (err) {
      setError('Error connecting to server')
    }
    setLoading(false)
  }

  const handleFolderClick = (folder) => {
    const newPath = currentPath === '/' ? `/${folder}` : `${currentPath}/${folder}`
    loadFolders(newPath)
  }

  const handleSelect = () => {
    onSelect(currentPath)
    onClose()
  }

  const handleUp = () => {
    if (currentPath === '/') return
    const parts = currentPath.split('/')
    parts.pop()
    const parent = parts.join('/') || '/'
    loadFolders(parent)
  }

  if (!isOpen) return null

  return (
    <div className="folder-browser-overlay" onClick={onClose}>
      <div className="folder-browser" onClick={e => e.stopPropagation()}>
        <div className="folder-browser-header">
          <h3>Select Folder</h3>
          <button className="close-btn" onClick={onClose}>&times;</button>
        </div>
        
        <div className="folder-browser-path">
          <button onClick={handleUp} disabled={!currentPath.includes('/')}>
            ⬆ Up
          </button>
          <input
            type="text"
            value={currentPath}
            onChange={(e) => setCurrentPath(e.target.value)}
            readOnly
          />
        </div>

        <div className="folder-browser-content">
          {loading && <div className="loading">Loading...</div>}
          {error && <div className="error">{error}</div>}
          <div className="folder-list">
            {folders.map((folder, index) => (
              <div
                key={index}
                className="folder-item"
                onClick={() => handleFolderClick(folder)}
              >
                📁 {folder}
              </div>
            ))}
          </div>
        </div>

        <div className="folder-browser-footer">
          <button className="cancel-btn" onClick={onClose}>Cancel</button>
          <button className="select-btn" onClick={handleSelect}>Select Folder</button>
        </div>
      </div>
    </div>
  )
}

export default FolderBrowser
