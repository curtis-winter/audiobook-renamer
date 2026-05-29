export default function CombineSuccessModal({ isOpen, outputPath, onClose }) {
  if (!isOpen) return null

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal success-modal" onClick={(e) => e.stopPropagation()}>
        <h2>Combine Complete</h2>
        <p>Files combined successfully!</p>
        <div className="output-path">
          <label>Output:</label>
          <span>{outputPath}</span>
        </div>
        <div className="modal-actions">
          <button onClick={onClose} className="btn-primary">OK</button>
        </div>
      </div>
    </div>
  )
}