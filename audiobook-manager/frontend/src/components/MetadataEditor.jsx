const safeValue = (val) => {
  if (val === null || val === undefined) return '-';
  if (typeof val === 'object') return JSON.stringify(val);
  return String(val);
}

const getFieldDiffClass = (field, preview) => {
  if (!preview?.original_metadata) return '';
  const original = preview.original_metadata[field];
  const newValue = preview.metadata?.[field];
  if (original === undefined || original === null || original === '') return '';
  if (String(original) !== String(newValue || '')) return 'has-change';
  return '';
}

const MetadataRow = ({ label, field, preview, metadata, onChange, templateButton, onSearchClick }) => (
  <tr>
    <td>
      {label}
      {templateButton}
    </td>
    <td 
      className="clickable-value" 
      onClick={() => onSearchClick && onSearchClick(field, metadata[field] || preview?.original_metadata?.[field])}
    >
      {safeValue(preview?.original_metadata?.[field]) || metadata[field] || '-'}
    </td>
    <td>
      <input
        type="text"
        className={getFieldDiffClass(field, preview) ? 'changed-input' : ''}
        value={metadata[field] || ''}
        onChange={(e) => onChange(field, e.target.value)}
      />
    </td>
  </tr>
)

export default function MetadataEditor({ selectedFile, selectedFiles, preview, metadata, onChange, onApply, onCombine, applying, error, onOpenTemplate, onSearchClick }) {
  const hasMultiSelect = selectedFiles && selectedFiles.length > 1
  const buttonText = hasMultiSelect ? `Combine ${selectedFiles.length} Files and Apply Changes` : 'Apply Changes'
  
  return (
    <div className="metadata-editor">
      <h2><button onClick={hasMultiSelect ? onCombine : onApply} className="apply" disabled={applying}>{applying ? 'Applying...' : buttonText}</button></h2>
      {error && <div className="error-message">{error}</div>}
      <table className="metadata-table">
        <colgroup>
          <col />
          <col />
          <col />
        </colgroup>
        <thead>
          <tr>
            <th>Field</th>
            <th>Current</th>
            <th>New Value</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>File Name <button className="template-btn" onClick={() => onOpenTemplate('filename')} title="Edit filename template">⚙</button></td>
            <td className="clickable-value" onClick={() => onSearchClick && onSearchClick('filename', selectedFile?.filename)}>{selectedFile?.filename}</td>
            <td className={preview?.new_filename ? 'has-change' : ''}>{preview?.new_filename || '-'}</td>
          </tr>
          <tr>
            <td>File Location <button className="template-btn" onClick={() => onOpenTemplate('folder')} title="Edit folder template">⚙</button></td>
            <td className="clickable-value" onClick={() => onSearchClick && onSearchClick('path', selectedFile?.path)}>{selectedFile?.path}</td>
            <td className={preview?.new_path ? 'has-change' : ''}>{preview?.new_path || '-'}</td>
          </tr>
          <MetadataRow label="Title (ALBUM)" field="title" preview={preview} metadata={metadata} onChange={onChange} onSearchClick={onSearchClick} />
          <MetadataRow label="Subtitle" field="subtitle" preview={preview} metadata={metadata} onChange={onChange} onSearchClick={onSearchClick} />
          <MetadataRow label="Author (ARTIST)" field="artist" preview={preview} metadata={metadata} onChange={onChange} onSearchClick={onSearchClick} />
          <MetadataRow label="Album Artist (ALBUMARTIST)" field="album_artist" preview={preview} metadata={metadata} onChange={onChange} onSearchClick={onSearchClick} />
          <MetadataRow label="Narrator (COMPOSER)" field="composer" preview={preview} metadata={metadata} onChange={onChange} onSearchClick={onSearchClick} />
          <MetadataRow label="Year (YEAR)" field="year" preview={preview} metadata={metadata} onChange={onChange} onSearchClick={onSearchClick} />
          <MetadataRow label="Series (SERIES)" field="series" preview={preview} metadata={metadata} onChange={onChange} onSearchClick={onSearchClick} />
          <MetadataRow label="Series Part (SERIES-PART)" field="series_part" preview={preview} metadata={metadata} onChange={onChange} onSearchClick={onSearchClick} />
          <MetadataRow label="Content Group" field="content_group" preview={preview} metadata={metadata} onChange={onChange} onSearchClick={onSearchClick} />
          <MetadataRow label="Publisher (PUBLISHER)" field="publisher" preview={preview} metadata={metadata} onChange={onChange} onSearchClick={onSearchClick} />
          <MetadataRow label="Copyright (COPYRIGHT)" field="copyright" preview={preview} metadata={metadata} onChange={onChange} onSearchClick={onSearchClick} />
          <MetadataRow label="Format (FORMAT)" field="format" preview={preview} metadata={metadata} onChange={onChange} onSearchClick={onSearchClick} />
          <MetadataRow label="Language (LANGUAGE)" field="language" preview={preview} metadata={metadata} onChange={onChange} onSearchClick={onSearchClick} />
          <MetadataRow label="ASIN" field="asin" preview={preview} metadata={metadata} onChange={onChange} onSearchClick={onSearchClick} />
          <MetadataRow label="ISBN" field="isbn" preview={preview} metadata={metadata} onChange={onChange} onSearchClick={onSearchClick} />
          <MetadataRow label="Genre (GENRE)" field="genre" preview={preview} metadata={metadata} onChange={onChange} onSearchClick={onSearchClick} />
        </tbody>
      </table>
    </div>
  )
}