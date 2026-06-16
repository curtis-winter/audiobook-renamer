import { useState, useRef, useEffect } from 'react'
import { processTemplateFunctions } from '../utils/template'

const SAMPLE_BOOKS = {
  standalone: {
    name: 'Standalone Book',
    data: {
      title: '1984',
      album: '1984',
      artist: 'George Orwell',
      album_artist: 'George Orwell',
      composer: 'Simon Prebble',
      narrator: 'Simon Prebble',
      year: '1949',
      track: '1',
      series: '',
      series_part: '',
      subtitle: '',
      genre: 'Fiction',
      comment: 'Unabridged',
      publisher: 'Penguin Books',
      copyright: '1949',
      format: 'MP3',
      language: 'English',
      asin: ''
    }
  },
  series: {
    name: 'Book in Series',
    data: {
      title: 'The Hobbit',
      album: 'The Hobbit',
      artist: 'J.R.R. Tolkien',
      album_artist: 'J.R.R. Tolkien',
      composer: 'Rob Inglis',
      narrator: 'Rob Inglis',
      year: '1937',
      track: '1',
      series: 'Middle Earth',
      series_part: '1',
      subtitle: 'There and Back Again',
      genre: 'Fantasy',
      comment: 'Unabridged',
      publisher: 'George Allen & Unwin',
      copyright: '1937',
      format: 'MP3',
      language: 'English',
      asin: 'B000FC3K1A'
    }
  }
}

const TAGS = ['%title%', '%album%', '%artist%', '%albumartist%', '%narrator%', '%year%', '%series%', '%series_part%', '%genre%', '%language%', '%asin%', '%format%']

const FUNCTIONS = [
  '{{if_field:%series%: [%series% %series_part%]}}',
  '{{pad_left:%series_part%:2}}',
  '{{uppercase:%title%}}',
  '{{lowercase:%title%}}',
  '{{default:%title%:Unknown}}'
]

export default function TemplateHelper({ isOpen, onClose, template, onSave, type }) {
  const [helperTemplate, setHelperTemplate] = useState(template)
  const [helperSampleBook, setHelperSampleBook] = useState('series')
  const textareaRef = useRef(null)

  useEffect(() => {
    setHelperTemplate(template)
  }, [template])

  const insertTag = (tag) => {
    const textarea = textareaRef.current
    if (textarea) {
      const start = textarea.selectionStart
      const end = textarea.selectionEnd
      const before = helperTemplate.substring(0, start)
      const after = helperTemplate.substring(end)
      setHelperTemplate(before + tag + after)
      setTimeout(() => {
        textarea.focus()
        textarea.setSelectionRange(start + tag.length, start + tag.length)
      }, 0)
    } else {
      setHelperTemplate(prev => prev + tag)
    }
  }

  const handleSave = () => {
    onSave(helperTemplate)
    onClose()
  }

   const processedTemplate = processTemplateFunctions(helperTemplate || '', SAMPLE_BOOKS[helperSampleBook].data)
   const preview = processedTemplate.replace(/%(\w+)%/g, (m, k) => SAMPLE_BOOKS[helperSampleBook].data[k] || m)

  if (!isOpen) return null

  return (
    <div className="template-helper-modal open">
      <div className="modal-overlay" onClick={onClose}></div>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <h2>Template Helper - {type === 'filename' ? 'Filename' : 'Folder'} Template</h2>
        <div className="template-helper-content">
          <div className="template-editor-full">
            <label>Template:</label>
            <textarea
              ref={textareaRef}
              value={helperTemplate}
              onChange={(e) => setHelperTemplate(e.target.value)}
              placeholder="Enter template..."
              rows={3}
            />
          </div>
          <div className="template-tags">
            <h4>Tags</h4>
            <div className="tag-buttons">
              {TAGS.map(tag => (
                <button key={tag} className="tag-btn" onClick={() => insertTag(tag)}>{tag}</button>
              ))}
            </div>
          </div>
          <div className="template-functions">
            <h4>Functions</h4>
            <div className="tag-buttons">
              {FUNCTIONS.map(fn => (
                <button key={fn} className="tag-btn function" onClick={() => insertTag(fn)}>{fn}</button>
              ))}
            </div>
          </div>
          <div className="template-preview">
            <div className="preview-header">
              <h4>Preview</h4>
              <select value={helperSampleBook} onChange={(e) => setHelperSampleBook(e.target.value)}>
                <option value="standalone">{SAMPLE_BOOKS.standalone.name}</option>
                <option value="series">{SAMPLE_BOOKS.series.name}</option>
              </select>
            </div>
            <div className="preview-box">
              <pre>{preview}</pre>
            </div>
          </div>
        </div>
        <div className="modal-actions">
          <button onClick={onClose} className="btn-secondary">Cancel</button>
          <button onClick={handleSave} className="btn-primary">Save & Apply</button>
        </div>
      </div>
    </div>
  )
}