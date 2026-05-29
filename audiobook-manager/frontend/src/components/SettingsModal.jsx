export default function SettingsModal({ isOpen, onClose, config, onSave, onBrowse, onSaveAndClose }) {
  if (!isOpen) return null

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal settings-modal" onClick={(e) => e.stopPropagation()}>
        <h2>Settings</h2>
        <div className="form-group">
          <label>Watch Folder:</label>
          <div className="folder-input">
            <input
              type="text"
              value={config.watchFolder}
              onChange={(e) => onSave({ ...config, watchFolder: e.target.value })}
            />
            <button onClick={() => onBrowse('watchFolder')}>Browse...</button>
          </div>
        </div>
        <div className="form-group">
          <label>Output Folder:</label>
          <div className="folder-input">
            <input
              type="text"
              value={config.outputFolder}
              onChange={(e) => onSave({ ...config, outputFolder: e.target.value })}
            />
            <button onClick={() => onBrowse('outputFolder')}>Browse...</button>
          </div>
        </div>
        <div className="modal-actions">
          <button onClick={onClose} className="btn-secondary">Cancel</button>
          <button onClick={onSaveAndClose} className="btn-primary">Save</button>
        </div>
      </div>
    </div>
  )
}