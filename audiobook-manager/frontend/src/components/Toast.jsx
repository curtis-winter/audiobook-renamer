import { useEffect } from 'react'

export default function Toast({ message, type = 'success', onClose, duration = 3000 }) {
  useEffect(() => {
    if (duration && onClose) {
      const timer = setTimeout(onClose, duration)
      return () => clearTimeout(timer)
    }
  }, [duration, onClose])

  const bgColor = type === 'success' ? '#4ade80' : type === 'error' ? '#f87171' : '#fbbf24'

  return (
    <div className="toast-overlay">
      <div className={`toast toast-${type}`} style={{ borderLeft: `4px solid ${bgColor}` }}>
        <span className="toast-message">{message}</span>
        <button className="toast-close" onClick={onClose}>&times;</button>
      </div>
    </div>
  )
}

export function ToastContainer({ toasts, onRemove }) {
  if (!toasts || toasts.length === 0) return null

  return (
    <div className="toast-container">
      {toasts.map((toast, index) => (
        <Toast
          key={toast.id}
          message={toast.message}
          type={toast.type}
          onClose={() => onRemove(toast.id)}
        />
      ))}
    </div>
  )
}