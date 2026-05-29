export default function EmptyFolderModal({ isOpen, folders, onDeleteAll, onSkip }) {
  if (!isOpen) return null

  return (
    <div className="modal-overlay">
      <div className="modal">
        <h3>Empty Folders Detected</h3>
        <p>The following folders are now empty after moving the file:</p>
        <ul className="empty-folder-list">
          {folders.map((folder, index) => (
            <li key={index}>{folder}</li>
          ))}
        </ul>
        <p>Would you like to delete these empty folders?</p>
        <div className="modal-actions">
          <button onClick={onSkip} className="btn-secondary">
            Keep Folders
          </button>
          <button onClick={onDeleteAll} className="btn-primary">
            Delete Folders
          </button>
        </div>
      </div>
    </div>
  )
}