import { useState, useEffect } from 'react'
import axios from 'axios'
import FolderBrowser from './components/FolderBrowser'
import './App.css'

// Use relative path for API - works with nginx proxy in production
const API_URL = '/api'

const calculateMatch = (fileMetadata, searchResult) => {
  if (!fileMetadata || !searchResult) return 0

  let matches = 0
  let total = 0

  const fields = [
    { key: 'title', weight: 3 },
    { key: 'artist', weight: 2 },
    { key: 'album_artist', weight: 2 },
    { key: 'album', weight: 2 },
    { key: 'year', weight: 1 },
    { key: 'series', weight: 2 },
    { key: 'series_part', weight: 1 },
    { key: 'narrator', weight: 1 },
  ]

  fields.forEach(({ key, weight }) => {
    const fileVal = (fileMetadata[key] || '').toLowerCase().trim()
    const resultVal = (searchResult[key] || '').toLowerCase().trim()

    if (fileVal && resultVal) {
      total += weight
      if (fileVal === resultVal || resultVal.includes(fileVal) || fileVal.includes(resultVal)) {
        matches += weight
      }
    }
  })

  if (total === 0) return 0
  return Math.round((matches / total) * 100)
}

const getMatchColor = (match) => {
  if (match >= 80) return 'green'
  if (match >= 50) return 'orange'
  return 'red'
}

function App() {
  const [config, setConfig] = useState({
    watchFolder: './watch',
    outputFolder: './output',
    filenameTemplate: '%album% (%year%) - Pt%track%',
    folderTemplate: '%albumartist%/%series%/%year% - %album%'
  })
  const [files, setFiles] = useState([])
  const [selectedFile, setSelectedFile] = useState(null)
  const [metadata, setMetadata] = useState({})
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [preview, setPreview] = useState(null)
  const [folderBrowserOpen, setFolderBrowserOpen] = useState(false)
  const [folderBrowserField, setFolderBrowserField] = useState('')
  const [applying, setApplying] = useState(false)
  const [emptyFolders, setEmptyFolders] = useState([])
  const [showEmptyFolderModal, setShowEmptyFolderModal] = useState(false)
  const [hasPreviewed, setHasPreviewed] = useState(false)
  const [templateHelperOpen, setTemplateHelperOpen] = useState(false)
  const [editingTemplateType, setEditingTemplateType] = useState('filename')

  useEffect(() => {
    loadConfig()
    loadFiles()
  }, [])

  const loadConfig = async () => {
    try {
      const response = await axios.get(`${API_URL}/config`)
      setConfig(response.data)
    } catch (error) {
      console.error('Error loading config:', error)
    }
  }

  const loadFiles = async () => {
    try {
      const response = await axios.get(`${API_URL}/files`)
      setFiles(response.data)
    } catch (error) {
      console.error('Error loading files:', error)
    }
  }

  const handleFileSelect = async (file) => {
    setSelectedFile(file)
    setSearchResults([])
    setPreview(null)
    setHasPreviewed(false)
    try {
      const response = await axios.get(`${API_URL}/files/${file.id}/metadata`)
      setMetadata(response.data)
      // Auto-search using the file's title if available
      const fileTitle = response.data.title || response.data.album || file.filename.replace(/\.[^/.]+$/, '')
      if (fileTitle) {
        setSearchQuery(fileTitle)
        // Auto-trigger search
        try {
          const searchResponse = await axios.post(`${API_URL}/search?q=${encodeURIComponent(fileTitle)}`)
          setSearchResults(searchResponse.data)
        } catch (error) {
          console.error('Auto-search error:', error)
        }
      }
    } catch (error) {
      console.error('Error loading metadata:', error)
    }
  }

  const handleSearch = async () => {
    try {
      const response = await axios.post(`${API_URL}/search?q=${encodeURIComponent(searchQuery)}`)
      setSearchResults(response.data)
    } catch (error) {
      console.error('Error searching:', error)
    }
  }

   const handleApplyMetadata = (result) => {
     // Define field mappings: {targetField: [sourceFields]}
     const fieldMappings = {
       title: ['title', 'album'],
       subtitle: ['subtitle'],
       album: ['album', 'title'],
       artist: ['artist', ['authors', 0]],
       album_artist: ['album_artist', ['authors', 0]],
       composer: ['composer', 'narrator'],
       narrators: ['narrators'],
       series: ['series'],
       series_part: ['series_part'],
       content_group: ['content_group'],
       movement: ['movement'],
       movement_name: ['movement_name'],
       show_movement: ['show_movement'],
       year: ['year'],
       release_date: ['release_date'],
       publisher: ['publisher'],
       copyright: ['copyright'],
       comment: ['comment', 'description'],
       description: ['description'],
       format: ['format'],
       language: ['language'],
       asin: ['asin'],
       isbn: ['isbn'],
       genre: ['genre'],
       runtime: ['runtime'],
       cover: ['cover'],
       rating: ['rating'],
       explicit: ['explicit'],
       album_sort: ['album_sort'],
       www_audio_file: ['www_audio_file']
     };
     
     // Helper function to get value from result using field mapping
     const getValueFromResult = (mapping) => {
       // Handle array mappings like ['authors', 0] for accessing nested values
       if (Array.isArray(mapping)) {
         const [field, indexOrAccessor] = mapping;
         const value = result[field];
         if (Array.isArray(value) && typeof indexOrAccessor === 'number') {
           return value[indexOrAccessor] || null;
         }
         return value;
       }
       
       // Handle string or array of strings (fallback chain)
       const sources = Array.isArray(mapping) ? mapping : [mapping];
       for (const source of sources) {
         if (result[source] !== undefined && result[source] !== null) {
           return result[source];
         }
       }
       return null;
     };
     
     setMetadata(prev => ({
       ...prev,
       title: getValueFromResult(fieldMappings.title),
       subtitle: getValueFromResult(fieldMappings.subtitle),
       album: getValueFromResult(fieldMappings.album),
       artist: getValueFromResult(fieldMappings.artist),
       album_artist: getValueFromResult(fieldMappings.album_artist),
       composer: getValueFromResult(fieldMappings.composer),
       narrators: getValueFromResult(fieldMappings.narrators),
       series: getValueFromResult(fieldMappings.series),
       series_part: getValueFromResult(fieldMappings.series_part),
       content_group: getValueFromResult(fieldMappings.content_group),
       movement: getValueFromResult(fieldMappings.movement),
       movement_name: getValueFromResult(fieldMappings.movement_name),
       show_movement: getValueFromResult(fieldMappings.show_movement),
       year: getValueFromResult(fieldMappings.year),
       release_date: getValueFromResult(fieldMappings.release_date),
       publisher: getValueFromResult(fieldMappings.publisher),
       copyright: getValueFromResult(fieldMappings.copyright),
       comment: getValueFromResult(fieldMappings.comment),
       description: getValueFromResult(fieldMappings.description),
       format: getValueFromResult(fieldMappings.format),
       language: getValueFromResult(fieldMappings.language),
       asin: getValueFromResult(fieldMappings.asin),
       isbn: getValueFromResult(fieldMappings.isbn),
       genre: getValueFromResult(fieldMappings.genre),
       runtime: getValueFromResult(fieldMappings.runtime),
       cover: getValueFromResult(fieldMappings.cover),
       rating: getValueFromResult(fieldMappings.rating),
       explicit: getValueFromResult(fieldMappings.explicit),
       album_sort: getValueFromResult(fieldMappings.album_sort),
       www_audio_file: getValueFromResult(fieldMappings.www_audio_file)
     }));
   }

  const handleMetadataChange = (field, value) => {
    setMetadata(prev => ({
      ...prev,
      [field]: value
    }))
    // Auto-recalculate preview when metadata is edited after initial preview
    if (hasPreviewed && selectedFile) {
      handlePreview()
    }
  }

  const handlePreview = async () => {
    try {
      const response = await axios.post(`${API_URL}/preview`, {
        file_id: selectedFile.id,
        metadata: metadata
      })
      setPreview(response.data)
      setHasPreviewed(true)
    } catch (error) {
      console.error('Error getting preview:', error)
    }
  }

  const handleApply = async () => {
    setApplying(true)
    try {
      const response = await axios.post(`${API_URL}/apply`, {
        file_id: selectedFile.id,
        metadata: metadata
      })
      
      if (response.data.success) {
        // Check for empty folders
        const emptyFolders = response.data.empty_folders || []
        
        if (emptyFolders.length > 0) {
          setPreview(null)
          setEmptyFolders(emptyFolders)
          setShowEmptyFolderModal(true)
        } else {
          alert('Changes applied successfully!')
          setPreview(null)
          loadFiles()
        }
      } else {
        alert('Error applying changes: ' + response.data.message)
      }
    } catch (error) {
      console.error('Error applying changes:', error)
      alert('Error applying changes')
    } finally {
      setApplying(false)
    }
  }

  const handleDeleteFolder = async (folderPath) => {
    try {
      await axios.post(`${API_URL}/delete-folder`, null, {
        params: { folder_path: folderPath }
      })
    } catch (error) {
      console.error('Error deleting folder:', error)
    }
  }

  const handleDeleteAllEmptyFolders = async () => {
    for (const folder of emptyFolders) {
      await handleDeleteFolder(folder)
    }
    setShowEmptyFolderModal(false)
    setEmptyFolders([])
    loadFiles()
  }

  const handleSkipDeleteFolders = () => {
    setShowEmptyFolderModal(false)
    setEmptyFolders([])
    loadFiles()
  }

  const handleFolderSelect = (field) => {
    setFolderBrowserField(field)
    setFolderBrowserOpen(true)
  }

  const handleFolderBrowserClose = () => {
    setFolderBrowserOpen(false)
    setFolderBrowserField('')
  }

  const handleFolderBrowserSelect = (path) => {
    if (folderBrowserField) {
      setConfig(prev => ({
        ...prev,
        [folderBrowserField]: path
      }))
    }
    setFolderBrowserOpen(false)
    setFolderBrowserField('')
  }

  const handleSaveConfig = async () => {
    try {
      await axios.post(`${API_URL}/config`, config)
      alert('Config saved successfully!')
    } catch (error) {
      console.error('Error saving config:', error)
      alert('Error saving config')
    }
  }

  const openTemplateHelper = (type) => {
    setEditingTemplateType(type)
    setTemplateHelperOpen(true)
  }

  const insertTag = (tag) => {
    if (editingTemplateType === 'filename') {
      setConfig(prev => ({
        ...prev,
        filenameTemplate: prev.filenameTemplate + tag
      }))
    } else {
      setConfig(prev => ({
        ...prev,
        folderTemplate: prev.folderTemplate + tag
      }))
    }
    setTemplateHelperOpen(false)
  }

   // Shared sample metadata for template previews
   const getSampleMetadata = () => ({
     title: 'The Hobbit',
     album: 'The Hobbit',
     artist: 'J.R.R. Tolkien',
     album_artist: 'J.R.R. Tolkien',
     composer: 'J.R.R. Tolkien',
     narrator: 'J.R.R. Tolkien',
     year: '1937',
     track: '1',
     series: 'Middle Earth',
     series_part: '1',
     subtitle: '',
     genre: 'Fantasy',
     comment: '',
     publisher: 'George Allen & Unwin',
     copyright: '1937',
     format: 'MP3',
     language: 'English',
     asin: 'B000FC3K1A'
   });
   
   // Generate sample preview for template helper
   const generateSampleFilename = (template) => {
     const sampleMetadata = getSampleMetadata();
     
     // Simple template replacement for preview
     let result = template;
     result = result.replace(/%title%/g, sampleMetadata.title || '');
     result = result.replace(/%album%/g, sampleMetadata.album || '');
     result = result.replace(/%artist%/g, sampleMetadata.artist || '');
     result = result.replace(/%album_artist%/g, sampleMetadata.album_artist || '');
     result = result.replace(/%composer%/g, sampleMetadata.composer || '');
     result = result.replace(/%narrator%/g, sampleMetadata.narrator || '');
     result = result.replace(/%year%/g, sampleMetadata.year || '');
     result = result.replace(/%track%/g, sampleMetadata.track ? String(sampleMetadata.track).padStart(2, '0') : '');
     result = result.replace(/%series%/g, sampleMetadata.series || '');
     result = result.replace(/%series_part%/g, sampleMetadata.series_part || '');
     result = result.replace(/%series-part%/g, sampleMetadata.series_part || '');
     result = result.replace(/%series_full%/g, `${sampleMetadata.series || ''} ${sampleMetadata.series_part || ''}`.trim());
     result = result.replace(/%subtitle%/g, sampleMetadata.subtitle || '');
     result = result.replace(/%genre%/g, sampleMetadata.genre || '');
     result = result.replace(/%comment%/g, sampleMetadata.comment || '');
     result = result.replace(/%publisher%/g, sampleMetadata.publisher || '');
     result = result.replace(/%copyright%/g, sampleMetadata.copyright || '');
     result = result.replace(/%format%/g, sampleMetadata.format || '');
     result = result.replace(/%language%/g, sampleMetadata.language || '');
     result = result.replace(/%asin%/g, sampleMetadata.asin || '');
     
     // Clean up extra spaces
     result = result.replace(/\s+/g, ' ').trim();
     return result || '[empty]';
   };
   
   const generateSampleFolderPath = (template) => {
     const sampleMetadata = getSampleMetadata();
     
     // Simple template replacement for preview
     let result = template;
     result = result.replace(/%title%/g, sampleMetadata.title || '');
     result = result.replace(/%album%/g, sampleMetadata.album || '');
     result = result.replace(/%artist%/g, sampleMetadata.artist || '');
     result = result.replace(/%album_artist%/g, sampleMetadata.album_artist || '');
     result = result.replace(/%composer%/g, sampleMetadata.composer || '');
     result = result.replace(/%narrator%/g, sampleMetadata.narrator || '');
     result = result.replace(/%year%/g, sampleMetadata.year || '');
     result = result.replace(/%track%/g, sampleMetadata.track ? String(sampleMetadata.track).padStart(2, '0') : '');
     result = result.replace(/%series%/g, sampleMetadata.series || '');
     result = result.replace(/%series_part%/g, sampleMetadata.series_part || '');
     result = result.replace(/%series-part%/g, sampleMetadata.series_part || '');
     result = result.replace(/%series_full%/g, `${sampleMetadata.series || ''} ${sampleMetadata.series_part || ''}`.trim());
     result = result.replace(/%subtitle%/g, sampleMetadata.subtitle || '');
     result = result.replace(/%genre%/g, sampleMetadata.genre || '');
     result = result.replace(/%comment%/g, sampleMetadata.comment || '');
     result = result.replace(/%publisher%/g, sampleMetadata.publisher || '');
     result = result.replace(/%copyright%/g, sampleMetadata.copyright || '');
     result = result.replace(/%format%/g, sampleMetadata.format || '');
     result = result.replace(/%language%/g, sampleMetadata.language || '');
     result = result.replace(/%asin%/g, sampleMetadata.asin || '');
     
     // Clean up extra spaces and slashes
     result = result.replace(/\s+/g, ' ').trim();
     result = result.replace(/\/\/+/g, '/');
     return result || '[empty]';
   };

  return (
    <div className="app">
      <header>
        <h1>Audiobook Manager</h1>
      </header>

      <div className="container">
      <div className="sidebar">
        <div className="config-section">
          <h2>Configuration</h2>
          <div className="form-group">
            <label>Watch Folder:</label>
            <div className="folder-input">
              <input
                type="text"
                value={config.watchFolder}
                onChange={(e) => setConfig({...config, watchFolder: e.target.value})}
              />
              <button onClick={() => handleFolderSelect('watchFolder')}>Browse...</button>
            </div>
          </div>
          <div className="form-group">
            <label>Output Folder:</label>
            <div className="folder-input">
              <input
                type="text"
                value={config.outputFolder}
                onChange={(e) => setConfig({...config, outputFolder: e.target.value})}
              />
              <button onClick={() => handleFolderSelect('outputFolder')}>Browse...</button>
            </div>
          </div>
          <div className="form-group">
            <label>Filename Template:</label>
            <div className="template-input">
              <input
                type="text"
                value={config.filenameTemplate}
                onChange={(e) => setConfig({...config, filenameTemplate: e.target.value})}
              />
              <button onClick={() => openTemplateHelper('filename')}>Tags</button>
            </div>
          </div>
          <div className="form-group">
            <label>Folder Template:</label>
            <div className="template-input">
              <input
                type="text"
                value={config.folderTemplate}
                onChange={(e) => setConfig({...config, folderTemplate: e.target.value})}
              />
              <button onClick={() => openTemplateHelper('folder')}>Tags</button>
            </div>
          </div>
          <button onClick={handleSaveConfig} className="save-config">Save Config</button>
        </div>

          <div className="files-section">
            <h2>Files</h2>
            <button onClick={loadFiles}>Refresh</button>
            <div className="file-list">
              {files.map(file => (
                <div
                  key={file.id}
                  className={`file-item ${selectedFile?.id === file.id ? 'selected' : ''}`}
                  onClick={() => handleFileSelect(file)}
                >
                  {file.filename}
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="main-content">
          {selectedFile ? (
            <>
              <div className="metadata-editor">
                <h2>Metadata</h2>
                <table className="metadata-table">
                  <thead>
                    <tr>
                      <th>Field</th>
                      <th>Current</th>
                      <th>New Value</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td>Title (ALBUM)</td>
                      <td>{preview?.original_metadata?.title || metadata.title || '-'}</td>
                      <td><input type="text" value={metadata.title || ''} onChange={(e) => handleMetadataChange('title', e.target.value)} /></td>
                    </tr>
                    <tr>
                      <td>Subtitle</td>
                      <td>{preview?.original_metadata?.subtitle || metadata.subtitle || '-'}</td>
                      <td><input type="text" value={metadata.subtitle || ''} onChange={(e) => handleMetadataChange('subtitle', e.target.value)} /></td>
                    </tr>
                    <tr>
                      <td>Author (ARTIST)</td>
                      <td>{preview?.original_metadata?.artist || metadata.artist || '-'}</td>
                      <td><input type="text" value={metadata.artist || ''} onChange={(e) => handleMetadataChange('artist', e.target.value)} /></td>
                    </tr>
                    <tr>
                      <td>Album Artist (ALBUMARTIST)</td>
                      <td>{preview?.original_metadata?.album_artist || metadata.album_artist || '-'}</td>
                      <td><input type="text" value={metadata.album_artist || ''} onChange={(e) => handleMetadataChange('album_artist', e.target.value)} /></td>
                    </tr>
                    <tr>
                      <td>Narrator (COMPOSER)</td>
                      <td>{preview?.original_metadata?.composer || metadata.composer || '-'}</td>
                      <td><input type="text" value={metadata.composer || ''} onChange={(e) => handleMetadataChange('composer', e.target.value)} /></td>
                    </tr>
                    <tr>
                      <td>Year (YEAR)</td>
                      <td>{preview?.original_metadata?.year || metadata.year || '-'}</td>
                      <td><input type="text" value={metadata.year || ''} onChange={(e) => handleMetadataChange('year', e.target.value)} /></td>
                    </tr>
                    <tr>
                      <td>Series (SERIES)</td>
                      <td>{preview?.original_metadata?.series || metadata.series || '-'}</td>
                      <td><input type="text" value={metadata.series || ''} onChange={(e) => handleMetadataChange('series', e.target.value)} /></td>
                    </tr>
                    <tr>
                      <td>Series Part (SERIES-PART)</td>
                      <td>{preview?.original_metadata?.series_part || metadata.series_part || '-'}</td>
                      <td><input type="text" value={metadata.series_part || ''} onChange={(e) => handleMetadataChange('series_part', e.target.value)} /></td>
                    </tr>
                    <tr>
                      <td>Content Group</td>
                      <td>{preview?.original_metadata?.content_group || metadata.content_group || '-'}</td>
                      <td><input type="text" value={metadata.content_group || ''} onChange={(e) => handleMetadataChange('content_group', e.target.value)} /></td>
                    </tr>
                    <tr>
                      <td>Publisher (PUBLISHER)</td>
                      <td>{preview?.original_metadata?.publisher || metadata.publisher || '-'}</td>
                      <td><input type="text" value={metadata.publisher || ''} onChange={(e) => handleMetadataChange('publisher', e.target.value)} /></td>
                    </tr>
                    <tr>
                      <td>Copyright (COPYRIGHT)</td>
                      <td>{preview?.original_metadata?.copyright || metadata.copyright || '-'}</td>
                      <td><input type="text" value={metadata.copyright || ''} onChange={(e) => handleMetadataChange('copyright', e.target.value)} /></td>
                    </tr>
                    <tr>
                      <td>Format (FORMAT)</td>
                      <td>{preview?.original_metadata?.format || metadata.format || '-'}</td>
                      <td><input type="text" value={metadata.format || ''} onChange={(e) => handleMetadataChange('format', e.target.value)} /></td>
                    </tr>
                    <tr>
                      <td>Language (LANGUAGE)</td>
                      <td>{preview?.original_metadata?.language || metadata.language || '-'}</td>
                      <td><input type="text" value={metadata.language || ''} onChange={(e) => handleMetadataChange('language', e.target.value)} /></td>
                    </tr>
                    <tr>
                      <td>ASIN</td>
                      <td>{preview?.original_metadata?.asin || metadata.asin || '-'}</td>
                      <td><input type="text" value={metadata.asin || ''} onChange={(e) => handleMetadataChange('asin', e.target.value)} /></td>
                    </tr>
                    <tr>
                      <td>Genre (GENRE)</td>
                      <td>{preview?.original_metadata?.genre || metadata.genre || '-'}</td>
                      <td><input type="text" value={metadata.genre || ''} onChange={(e) => handleMetadataChange('genre', e.target.value)} /></td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <div className="search-section">
                <h2>Search Metadata</h2>
                <div className="search-box">
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search for audiobook..."
                  />
                  <button onClick={handleSearch}>Search</button>
                </div>
                <div className="search-results">
                  {searchResults.length === 0 && searchQuery && (
                    <p className="no-results">No results found. Try a different search term.</p>
                  )}
                  {searchResults.map((result, index) => {
                    const match = calculateMatch(metadata, result)
                    return (
                      <div key={index} className="search-result" onClick={() => handleApplyMetadata(result)}>
                        {result.cover && <img src={result.cover} alt="cover" className="result-cover" />}
                        <div className="result-info">
                          <h3>{result.title}</h3>
                          {result.authors?.length > 0 && <p>By: {result.authors.join(', ')}</p>}
                          {result.year && <p>Year: {result.year}</p>}
                        </div>
                        <div className="result-match" style={{ color: getMatchColor(match) }}>
                          {match}%
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>

              <div className="actions">
                <button onClick={handlePreview}>Preview Changes</button>
                <button onClick={handleApply} className="apply" disabled={applying}>
                  {applying ? 'Applying...' : 'Apply Changes'}
                </button>
              </div>
              {applying && (
                <div className="progress-bar">
                  <div className="progress-bar-fill"></div>
                </div>
              )}

              {preview && (
                <div className="preview">
                  <h3>Filename Preview</h3>
                  <p><strong>Original:</strong> {preview.original_path}</p>
                  <p><strong>New Filename:</strong> {preview.new_filename}</p>
                  <p><strong>New Folder:</strong> {preview.new_path}</p>
                </div>
              )}
            </>
          ) : (
            <div className="no-selection">
              <p>Select a file from the list to begin</p>
            </div>
          )}
        </div>
      </div>
      <FolderBrowser
        isOpen={folderBrowserOpen}
        onClose={handleFolderBrowserClose}
        onSelect={handleFolderBrowserSelect}
        initialPath={folderBrowserField === 'watchFolder' ? config.watchFolder : config.outputFolder}
      />

      {/* Empty Folder Modal */}
      {showEmptyFolderModal && (
        <div className="modal-overlay">
          <div className="modal">
            <h3>Empty Folders Detected</h3>
            <p>The following folders are now empty after moving the file:</p>
            <ul className="empty-folder-list">
              {emptyFolders.map((folder, index) => (
                <li key={index}>{folder}</li>
              ))}
            </ul>
            <p>Would you like to delete these empty folders?</p>
            <div className="modal-actions">
              <button onClick={handleSkipDeleteFolders} className="btn-secondary">
                Keep Folders
              </button>
              <button onClick={handleDeleteAllEmptyFolders} className="btn-primary">
                Delete Folders
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default App
