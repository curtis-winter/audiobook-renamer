const naturalSort = (a, b) => {
  return a.localeCompare(b, undefined, { numeric: true, sensitivity: 'base' })
}

export default function FileList({ files, selectedFile, onSelect, onRefresh, selectedFiles, onToggleSelect, onCombine, sortBy, onSortChange, onSelectAll, subfolders, selectedSubfolder, onSubfolderChange }) {
  // Ensure files is an array
  const filesArray = Array.isArray(files) ? files : [];
  const isMultiSelect = selectedFiles && selectedFiles.length >= 2
  const allSelected = filesArray.length > 0 && selectedFiles && filesArray.every(f => selectedFiles.some(sf => sf.id === f.id))
   
  // Filter out files without valid IDs to prevent React key warnings
  const validFiles = filesArray.filter(file => file && file.id);
  const sortedFiles = [...validFiles].sort((a, b) => {
    // Handle invalid a or b
    if (!a && !b) return 0;
    if (!a) return 1;
    if (!b) return -1;
    const filenameA = a?.filename || '';
    const filenameB = b?.filename || '';
    if (sortBy === 'track') {
      const getTrackNum = (filename) => {
        const match = filename.match(/(\d+)\./)
        return match ? parseInt(match[1], 10) : Infinity
      }
      return getTrackNum(filenameA) - getTrackNum(filenameB);
    }
    return naturalSort(filenameA, filenameB);
  })

  return (
    <div className="files-section">
      <div className="files-header">
        <h2>Files</h2>
      </div>
      <>
        <button onClick={onRefresh}>Refresh</button>
        {subfolders && subfolders.length > 1 && (
          <div className="folder-filter">
            <label>Folder:</label>
            <select value={selectedSubfolder || ''} onChange={(e) => onSubfolderChange(e.target.value)}>
              <option value="">All Files</option>
              {subfolders.filter(f => f).map(folder => (
                <option key={folder} value={folder}>{folder}</option>
              ))}
            </select>
          </div>
        )}
        <label className="select-all-label">
          <input
            type="checkbox"
            checked={allSelected}
            onChange={() => onSelectAll()}
          />
          Select All
        </label>
        {sortBy !== undefined && (
          <div className="sort-controls">
            <label>Sort by:</label>
            <select value={sortBy || 'name'} onChange={(e) => onSortChange(e.target.value)}>
              <option value="name">Name</option>
              <option value="track">Track #</option>
            </select>
          </div>
        )}
        <div className="file-list">
          {sortedFiles.map(file => (
            <div
              key={file.id}
              className={`file-item ${selectedFile?.id === file.id ? 'selected' : ''} ${selectedFiles?.some(f => f.id === file.id) ? 'multi-selected' : ''}`}
              onClick={() => onToggleSelect(file)}
            >
              <span className="file-checkbox">
                {selectedFiles?.some(f => f.id === file.id) ? '✓' : ''}
              </span>
              {file.filename}
            </div>
          ))}
        </div>
      </>
    </div>
  )
}