export const processTemplateFunctions = (template, metadata) => {
  let result = template

  result = result.replace(/\{\{if_field:([^:]+):([^}]+)\}\}/g, (match, field, value) => {
    const fieldName = field.replace(/%/g, '')
    const fieldValue = metadata[fieldName] || ''
    if (!fieldValue) return ''
    return value.replace(/\{field\}/g, fieldValue)
  })

  result = result.replace(/\{\{pad_left:([^:]+):(\d+)\}\}/g, (match, field, width) => {
    const fieldName = field.replace(/%/g, '')
    const fieldValue = metadata[fieldName] || ''
    return fieldValue.toString().padStart(parseInt(width), '0')
  })

  result = result.replace(/\{\{uppercase:([^}]+)\}\}/g, (match, field) => {
    const fieldName = field.replace(/%/g, '')
    let fieldValue = metadata[fieldName]
    if (fieldValue && typeof fieldValue === 'object') fieldValue = JSON.stringify(fieldValue)
    return String(fieldValue || '').toUpperCase()
  })

  result = result.replace(/\{\{lowercase:([^}]+)\}\}/g, (match, field) => {
    const fieldName = field.replace(/%/g, '')
    let fieldValue = metadata[fieldName]
    if (fieldValue && typeof fieldValue === 'object') fieldValue = JSON.stringify(fieldValue)
    return String(fieldValue || '').toLowerCase()
  })

  result = result.replace(/\{\{default:([^:]+):([^}]+)\}\}/g, (match, field, defaultVal) => {
    const fieldName = field.replace(/%/g, '')
    let fieldValue = metadata[fieldName]
    if (fieldValue && typeof fieldValue === 'object') fieldValue = JSON.stringify(fieldValue)
    return fieldValue || defaultVal
  })

  return result
}

export const generateSampleFilename = (template) => {
  const sampleMetadata = {
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
  }
  
  let result = template
  result = result.replace(/%title%/g, sampleMetadata.title || '')
  result = result.replace(/%album%/g, sampleMetadata.album || '')
  result = result.replace(/%artist%/g, sampleMetadata.artist || '')
  result = result.replace(/%album_artist%/g, sampleMetadata.album_artist || '')
  result = result.replace(/%composer%/g, sampleMetadata.composer || '')
  result = result.replace(/%narrator%/g, sampleMetadata.narrator || '')
  result = result.replace(/%year%/g, sampleMetadata.year || '')
  result = result.replace(/%track%/g, sampleMetadata.track ? String(sampleMetadata.track).padStart(2, '0') : '')
  result = result.replace(/%series%/g, sampleMetadata.series || '')
  result = result.replace(/%series_part%/g, sampleMetadata.series_part || '')
  result = result.replace(/%series-part%/g, sampleMetadata.series_part || '')
  result = result.replace(/%series_full%/g, `${sampleMetadata.series || ''} ${sampleMetadata.series_part || ''}`.trim())
  result = result.replace(/%subtitle%/g, sampleMetadata.subtitle || '')
  result = result.replace(/%genre%/g, sampleMetadata.genre || '')
  result = result.replace(/%comment%/g, sampleMetadata.comment || '')
  result = result.replace(/%publisher%/g, sampleMetadata.publisher || '')
  result = result.replace(/%copyright%/g, sampleMetadata.copyright || '')
  result = result.replace(/%format%/g, sampleMetadata.format || '')
  result = result.replace(/%language%/g, sampleMetadata.language || '')
  result = result.replace(/%asin%/g, sampleMetadata.asin || '')
  
  result = result.replace(/\s+/g, ' ').trim()
  return result || '[empty]'
}

export const generateSampleFolderPath = (template) => {
  const sampleMetadata = {
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
  }
  
  let result = template
  result = result.replace(/%title%/g, sampleMetadata.title || '')
  result = result.replace(/%album%/g, sampleMetadata.album || '')
  result = result.replace(/%artist%/g, sampleMetadata.artist || '')
  result = result.replace(/%album_artist%/g, sampleMetadata.album_artist || '')
  result = result.replace(/%composer%/g, sampleMetadata.composer || '')
  result = result.replace(/%narrator%/g, sampleMetadata.narrator || '')
  result = result.replace(/%year%/g, sampleMetadata.year || '')
  result = result.replace(/%track%/g, sampleMetadata.track ? String(sampleMetadata.track).padStart(2, '0') : '')
  result = result.replace(/%series%/g, sampleMetadata.series || '')
  result = result.replace(/%series_part%/g, sampleMetadata.series_part || '')
  result = result.replace(/%series-part%/g, sampleMetadata.series_part || '')
  result = result.replace(/%series_full%/g, `${sampleMetadata.series || ''} ${sampleMetadata.series_part || ''}`.trim())
  result = result.replace(/%subtitle%/g, sampleMetadata.subtitle || '')
  result = result.replace(/%genre%/g, sampleMetadata.genre || '')
  result = result.replace(/%comment%/g, sampleMetadata.comment || '')
  result = result.replace(/%publisher%/g, sampleMetadata.publisher || '')
  result = result.replace(/%copyright%/g, sampleMetadata.copyright || '')
  result = result.replace(/%format%/g, sampleMetadata.format || '')
  result = result.replace(/%language%/g, sampleMetadata.language || '')
  result = result.replace(/%asin%/g, sampleMetadata.asin || '')
  
  result = result.replace(/\s+/g, ' ').trim()
  result = result.replace(/\/\/+/g, '/')
  return result || '[empty]'
}