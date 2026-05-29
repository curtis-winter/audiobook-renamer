export default function ProgressModal({ message, isOpen, stage, totalStages, percentage }) {
  if (!isOpen) return null

  const stageLabels = {
    1: 'Combining Audio',
    2: 'Writing Tags',
    3: 'Moving/Renaming',
    4: 'Complete'
  }

  const currentStage = stage || 1
  const totalStgs = totalStages || 4

  return (
    <div className="modal-overlay progress-modal">
      <div className="progress-modal-content">
        <div className="progress-header">
          <div className="spinner-large"></div>
          <h3>{message || 'Processing...'}</h3>
        </div>
        
        <div className="progress-track-container">
          <div className="progress-track">
            <div className="progress-fill" style={{ width: `${Math.min((currentStage - 1) / (totalStgs - 1) * 100, 99)}%` }}></div>
          </div>
        </div>

        <div className="progress-steps">
          {[1, 2, 3, 4].map(s => (
            <div key={s} className={`progress-step ${s < currentStage ? 'done' : ''} ${s === currentStage ? 'active' : ''}`}>
              <div className="step-connector"></div>
              <div className="step-marker">
                {s < currentStage ? (
                  <svg viewBox="0 0 24 24" fill="currentColor"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>
                ) : s}
              </div>
              <div className="step-connector"></div>
              <span className="step-label">{stageLabels[s]}</span>
            </div>
          ))}
        </div>

        <div className="progress-status">
          {currentStage < totalStgs ? stageLabels[currentStage] : 'Done!'}
        </div>
      </div>
    </div>
  )
}