import { useState, useEffect, useRef, useMemo } from 'react'
import axios from 'axios'
import FolderBrowser from './components/FolderBrowser'
import FileList from './components/FileList'
import MetadataEditor from './components/MetadataEditor'
import SearchSection from './components/SearchSection'
import TemplateHelper from './components/TemplateHelper'
import SettingsModal from './components/SettingsModal'
import EmptyFolderModal from './components/EmptyFolderModal'
import ProgressModal from './components/ProgressModal'
import CombineSuccessModal from './components/CombineSuccessModal'
import Toast, { ToastContainer } from './components/Toast'
import './App.css'

const API_URL = '/api'

const naturalSort = (a, b) => {
  // Handle invalid a or b
  if (a === undefined && b === undefined) return 0;
  if (a === undefined) return 1;
  if (b === undefined) return -1;
  return a.localeCompare(b, undefined, { numeric: true, sensitivity: 'base' })
}

const FIELD_MAPPINGS = {
  title: ['title', 'album'],
  subtitle: ['subtitle'],
  album: ['album', 'title'],
  artist: ['artist', ['authors', 0]],
  album_artist: ['album_artist', ['authors', 0]],
  composer: ['composer', 'narrator'],
  narrator: ['narrator', ['narrators', 0]],
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
  const [selectedFiles, setSelectedFiles] = useState([])
  const [combining, setCombining] = useState(false)
  const [sortBy, setSortBy] = useState('name')
  const [sidebarWidth, setSidebarWidth] = useState(400)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [metadata, setMetadata] = useState({})
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [searching, setSearching] = useState(false)
  const [preview, setPreview] = useState(null)
  const [folderBrowserOpen, setFolderBrowserOpen] = useState(false)
  const [folderBrowserField, setFolderBrowserField] = useState('')
  const [applying, setApplying] = useState(false)
  const [error, setError] = useState(null)
  const [emptyFolders, setEmptyFolders] = useState([])
  const [showEmptyFolderModal, setShowEmptyFolderModal] = useState(false)
  const [hasPreviewed, setHasPreviewed] = useState(false)
  const [templateHelperOpen, setTemplateHelperOpen] = useState(false)
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [editingTemplateType, setEditingTemplateType] = useState('filename')
  const [progressMessage, setProgressMessage] = useState('')
  const [showProgress, setShowProgress] = useState(false)
  const [progressCount, setProgressCount] = useState(0)
  const [progressTotal, setProgressTotal] = useState(0)
  const [progressStage, setProgressStage] = useState(1)
  const [progressPercent, setProgressPercent] = useState(0)
  const [combineSuccess, setCombineSuccess] = useState(null)
  const [toasts, setToasts] = useState([])
  const [selectedSubfolder, setSelectedSubfolder] = useState('')
  const pendingClear = useRef(false)

  const addToast = (message, type = 'success') => {
    const id = Date.now()
    setToasts(prev => [...prev, { id, message, type }])
  }

  const removeToast = (id) => {
    setToasts(prev => prev.filter(t => t.id !== id))
  }

  useEffect(() => {
    loadConfig()
    loadFiles()
  }, [])

  useEffect(() => {
    if (pendingClear.current) {
      setSelectedFile(null)
      setSelectedFiles([])
      setMetadata({})
      pendingClear.current = false
    }
  })

  // Clear selection when subfolder changes
  useEffect(() => {
    if (!selectedSubfolder) return
    setSelectedFile(null)
    setSelectedFiles([])
    setMetadata({})
    setPreview(null)
  }, [selectedSubfolder])

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

  // Extract unique subfolders from file paths
  const subfolders = useMemo(() => {
    const watchPath = config.watchFolder
    if (!watchPath || !Array.isArray(files)) return ['']
    const folderSet = new Set()
    files.forEach(f => {
      if (!f.path) return
      const rel = f.path.replace(watchPath, '').replace(/^\/+/, '')
      const parts = rel.split('/')
      if (parts.length > 1 && parts[0]) {
        folderSet.add(parts[0])
      }
    })
    return ['', ...Array.from(folderSet).sort()]
  }, [files, config.watchFolder])

  // Filter files by selected subfolder
  const filteredFiles = useMemo(() => {
    if (!selectedSubfolder) return files
    const watchPath = config.watchFolder
    if (!watchPath) return files
    const prefix = watchPath.endsWith('/') ? watchPath + selectedSubfolder : watchPath + '/' + selectedSubfolder
    return files.filter(f => f.path && f.path.startsWith(prefix))
  }, [files, selectedSubfolder, config.watchFolder])

const handleCombine = async () => {
    if (selectedFiles.length < 2) return
    setCombining(true)
    setShowProgress(true)
    setProgressStage(1)
    setProgressPercent(0)
    setProgressMessage('Starting combine...')
    
    const startTime = Date.now()
    const phaseTimes = {}
    
    const getElapsed = () => {
      const elapsed = Math.floor((Date.now() - startTime) / 1000)
      const mins = Math.floor(elapsed / 60)
      const secs = elapsed % 60
      return mins > 0 ? `${mins}m ${secs}s` : `${secs}s`
    }
    
    const elapsedInterval = setInterval(() => {
      setProgressMessage(`Combining... (${getElapsed()})`)
    }, 1000)
    
    const eventSource = new EventSource(`${API_URL}/progress/combine`)
    
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.percentage !== undefined) {
          setProgressPercent(data.percentage)
        }
        if (data.message) {
          const msg = data.message.toLowerCase()
          if (msg.includes('metadata') || msg.includes('tags')) {
            phaseTimes[1] = getElapsed()
            setProgressStage(2)
            setProgressMessage(`Writing Tags... (${getElapsed()})`)
          } else if (msg.includes('moving') || msg.includes('rename')) {
            phaseTimes[2] = getElapsed()
            setProgressStage(3)
            setProgressMessage(`Moving/Renaming... (${getElapsed()})`)
          } else if (msg.includes('complete')) {
            phaseTimes[3] = getElapsed()
            setProgressStage(4)
          }
        }
        if (data.done) {
          eventSource.close()
        }
      } catch (e) {
        console.error('SSE parse error:', e)
      }
    }
    
    eventSource.onerror = () => {
      eventSource.close()
    }
    
    try {
      const response = await axios.post(`${API_URL}/combine`, {
        file_ids: selectedFiles.map(f => f.id),
        output_title: selectedFiles[0]?.filename.replace(/\.[^/.]+$/, ''),
        metadata: preview?.metadata || metadata,
        new_filename: preview?.new_filename,
        new_path: preview?.new_path
      }, { timeout: 600000 })
      
      clearInterval(elapsedInterval)
      eventSource.close()
      setProgressPercent(100)
      setProgressStage(4)
      const totalTime = getElapsed()
      
      let completedMsg = 'Complete!'
      if (phaseTimes[1]) completedMsg += ` Combining: ${phaseTimes[1]}`
      if (phaseTimes[2]) completedMsg += ` | Tags: ${phaseTimes[2]}`
      if (phaseTimes[3]) completedMsg += ` | Move: ${phaseTimes[3]}`
      completedMsg += ` | Total: ${totalTime}`
      setProgressMessage(completedMsg)
      
      setTimeout(() => {
        setShowProgress(false)
        setProgressStage(1)
        setProgressPercent(0)
        if (response.data.success) {
          const emptyFolders = response.data.empty_folders || []
          if (emptyFolders.length > 0) {
            setSelectedFiles([])
            setSelectedFile(null)
            setEmptyFolders(emptyFolders)
            setShowEmptyFolderModal(true)
          } else {
            setCombineSuccess(response.data.output_path)
            setSelectedFiles([])
            loadFiles()
          }
        }
      }, 3000)
    } catch (error) {
      clearInterval(elapsedInterval)
      eventSource.close()
      setShowProgress(false)
      setProgressStage(1)
      setProgressPercent(0)
      setError('Error combining files: ' + (error.response?.data?.detail || error.message))
    } finally {
      setCombining(false)
    }
  }

  const handleFileSelect = async (file) => {
    setSelectedFile(file)
    setSearchResults([])
    setPreview(null)
    setHasPreviewed(false)
    try {
      const response = await axios.get(`${API_URL}/files/${file.id}/metadata`)
      const loadedMetadata = response.data
      setMetadata(loadedMetadata)
      
      setPreview({
        original_metadata: loadedMetadata,
        new_filename: file.filename,
        new_path: file.path,
        metadata: loadedMetadata
      })
      setHasPreviewed(true)
      
      const fileTitle = loadedMetadata.title || loadedMetadata.album || file.filename.replace(/\.[^/.]+$/, '')
      if (fileTitle) {
        setSearchQuery(fileTitle)
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

  const handleSearch = async (query = searchQuery) => {
    if (!query?.trim()) return
    try {
      setSearching(true)
      const response = await axios.post(`${API_URL}/search?q=${encodeURIComponent(query)}`)
      setSearchResults(response.data)
    } catch (error) {
      console.error('Error searching:', error)
    } finally {
      setSearching(false)
    }
  }

  const handleSelectSearchResult = (result) => {
    const newMetadata = { ...metadata }
    Object.keys(FIELD_MAPPINGS).forEach(field => {
      const mapping = FIELD_MAPPINGS[field]
      const value = getValueFromResult(mapping, result)
      if (value) {
        newMetadata[field] = value
      }
    })
    setMetadata(newMetadata)
    setSearchResults([])
    if (hasPreviewed) {
      handlePreview(newMetadata)
    }
  }

  const getValueFromResult = (mapping, result) => {
    // Single field name
    if (typeof mapping === 'string') {
      return result[mapping] || null
    }
    // Array: try each source in order (fallback chain)
    for (const source of mapping) {
      if (Array.isArray(source)) {
        // Nested [field, index] e.g. ['authors', 0]
        const arr = result[source[0]]
        if (Array.isArray(arr) && arr.length > 0 && typeof source[1] === 'number') {
          return arr[source[1]] || null
        }
      } else {
        const value = result[source]
        if (value !== undefined && value !== null && value !== '') {
          return value
        }
      }
    }
    return null
  }

  const handleApplyMetadata = (result) => {
    const newMetadata = {}
    for (const [field, mapping] of Object.entries(FIELD_MAPPINGS)) {
      newMetadata[field] = getValueFromResult(mapping, result)
    }
    if (newMetadata.release_date) {
      newMetadata.release_date = String(newMetadata.release_date)
    }
    setMetadata(newMetadata)
    handlePreview(newMetadata)
  }

  const handleMetadataChange = (field, value) => {
    const newMetadata = { ...metadata, [field]: value }
    setMetadata(newMetadata)
    if (hasPreviewed && selectedFile) {
      handlePreview(newMetadata)
    }
  }

  const handlePreview = async (metadataToUse = null) => {
    const meta = metadataToUse || metadata
    try {
      const response = await axios.post(`${API_URL}/preview`, {
        file_id: selectedFile.id,
        metadata: meta
      })
      setPreview({ ...response.data, metadata: meta })
      setHasPreviewed(true)
    } catch (error) {
      console.error('Error getting preview:', error)
    }
  }

  const handleApply = async () => {
    setApplying(true)
    setError(null)
    setShowProgress(true)
    setProgressStage(2)
    setProgressMessage('Writing metadata...')
    try {
      const response = await axios.post(`${API_URL}/apply`, {
        file_id: selectedFile.id,
        metadata: metadata
      }, { timeout: 600000 })

      setShowProgress(false)
      setProgressStage(1)
      pendingClear.current = true

      if (response.data.success) {
        const emptyFolders = response.data.empty_folders || []
        if (emptyFolders.length > 0) {
          setPreview(null)
          setEmptyFolders(emptyFolders)
          setShowEmptyFolderModal(true)
        } else {
          addToast('Changes applied successfully!')
          setPreview(null)
          loadFiles()
        }
      } else {
        setError(response.data.message || 'Error applying changes')
      }
    } catch (error) {
      setShowProgress(false)
      setProgressStage(1)
      setError(error.response?.data?.detail || 'Error applying changes')
    } finally {
      setApplying(false)
    }
  }

  const handleDeleteFolder = async (folderPath) => {
    try {
      await axios.post(`${API_URL}/delete-folder`, null, { params: { folder_path: folderPath } })
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
      setConfig(prev => ({ ...prev, [folderBrowserField]: path }))
    }
    setFolderBrowserOpen(false)
    setFolderBrowserField('')
  }

  const handleSaveConfig = async () => {
    try {
      await axios.post(`${API_URL}/config`, config)
      addToast('Config saved successfully!')
    } catch (error) {
      console.error('Error saving config:', error)
      addToast('Error saving config', 'error')
    }
  }

  const openTemplateHelper = (type) => {
    setEditingTemplateType(type)
    setTemplateHelperOpen(true)
  }

  const handleSaveHelperTemplate = (template) => {
    if (editingTemplateType === 'filename') {
      setConfig(prev => ({ ...prev, filenameTemplate: template }))
    } else {
      setConfig(prev => ({ ...prev, folderTemplate: template }))
    }
    handleSaveConfig()
  }

  return (
    <div className="app">
      <header>
        <h1>Audiobook Manager</h1>
        <button className="settings-btn" onClick={() => setSettingsOpen(true)} title="Settings">⚙</button>
      </header>

      <div className="container">
        {!sidebarCollapsed && (
          <>
            <div className="sidebar" style={{ width: sidebarWidth }}>
              <FileList
                files={filteredFiles}
                selectedFile={selectedFile}
                onSelect={handleFileSelect}
                onRefresh={loadFiles}
                selectedFiles={selectedFiles}
                onToggleSelect={(file) => {
                  handleFileSelect(file)
                  setSelectedFiles(prev => {
                    const isSelected = prev.some(f => f.id === file.id)
                    if (isSelected) {
                      return prev.filter(f => f.id !== file.id)
                    } else {
                      return [...prev, file]
                    }
                  })
                }}
                onSelectAll={() => {
                  if (selectedFiles && filteredFiles.length === selectedFiles.length) {
                    setSelectedFiles([])
                    setSelectedFile(null)
                    setMetadata({})
                    setPreview(null)
                  } else {
                    const allFiles = [...filteredFiles]
                    setSelectedFiles(allFiles)
                    if (allFiles.length > 0) {
                      handleFileSelect(allFiles[0])
                    }
                  }
                }}
                onCombine={handleCombine}
                sortBy={sortBy}
                onSortChange={setSortBy}
                subfolders={subfolders}
                selectedSubfolder={selectedSubfolder}
                onSubfolderChange={setSelectedSubfolder}
              />
            </div>
            
            <div
              className="resize-handle"
              onMouseDown={(e) => {
                e.preventDefault()
                const startX = e.clientX
                const startWidth = sidebarWidth
                const onMouseMove = (e) => {
                  const newWidth = startWidth + (e.clientX - startX)
                  if (newWidth >= 200 && newWidth <= 800) {
                    setSidebarWidth(newWidth)
                  }
                }
                const onMouseUp = () => {
                  document.removeEventListener('mousemove', onMouseMove)
                  document.removeEventListener('mouseup', onMouseUp)
                }
                document.addEventListener('mousemove', onMouseMove)
                document.addEventListener('mouseup', onMouseUp)
              }}
            />
          </>
        )}
        
        <div className="resize-handle">
          <button className="collapse-btn" onClick={() => setSidebarCollapsed(!sidebarCollapsed)} title={sidebarCollapsed ? "Expand" : "Collapse"}>
            {sidebarCollapsed ? '\u00BB' : '\u00AB'}
          </button>
        </div>
        
        <div className="main-content">
          {selectedFile ? (
            <>
              <MetadataEditor
                selectedFile={selectedFile}
                selectedFiles={selectedFiles}
                metadata={metadata}
                preview={preview}
                onChange={handleMetadataChange}
                onApply={handleApply}
                onCombine={handleCombine}
                onPreview={() => handlePreview()}
                onOpenTemplate={openTemplateHelper}
                applying={applying}
                error={error}
                onSearchClick={(field, value) => {
                  if (value && value !== '-' && value !== selectedFile?.filename && value !== selectedFile?.path) {
                    const query = String(value)
                    setSearchQuery(query)
                    setSearchResults([])
                    handleSearch(query)
                  }
                }}
              />
              <SearchSection
                searchQuery={searchQuery}
                onSearchChange={setSearchQuery}
                onSearch={handleSearch}
                results={searchResults}
                onSelectResult={handleSelectSearchResult}
                metadata={metadata}
              />
            </>
          ) : (
            <div className="placeholder">
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

      <EmptyFolderModal
        isOpen={showEmptyFolderModal}
        folders={emptyFolders}
        onDeleteAll={handleDeleteAllEmptyFolders}
        onSkip={handleSkipDeleteFolders}
      />

      <CombineSuccessModal
        isOpen={!!combineSuccess}
        outputPath={combineSuccess}
        onClose={() => setCombineSuccess(null)}
      />

      <TemplateHelper
        isOpen={templateHelperOpen}
        onClose={() => setTemplateHelperOpen(false)}
        template={editingTemplateType === 'filename' ? config.filenameTemplate : config.folderTemplate}
        onSave={handleSaveHelperTemplate}
        type={editingTemplateType}
      />

      <SettingsModal
        isOpen={settingsOpen}
        onClose={() => setSettingsOpen(false)}
        config={config}
        onSave={setConfig}
        onBrowse={handleFolderSelect}
        onSaveAndClose={async () => {
          try {
            await axios.post(`${API_URL}/config`, config)
            setSettingsOpen(false)
          } catch (error) {
            console.error('Error saving config:', error)
            addToast('Error saving config', 'error')
          }
        }}
      />

      <ProgressModal 
        message={progressMessage} 
        isOpen={showProgress} 
        progress={progressCount} 
        total={progressTotal}
        stage={progressStage}
        totalStages={4}
        percentage={progressPercent}
      />

      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </div>
  )
}

export default App