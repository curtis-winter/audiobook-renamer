export const calculateMatch = (fileMetadata, searchResult) => {
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
    let fileVal = fileMetadata[key]
    let resultVal = searchResult[key]
    if (fileVal && typeof fileVal === 'object') fileVal = JSON.stringify(fileVal)
    if (resultVal && typeof resultVal === 'object') resultVal = JSON.stringify(resultVal)
    fileVal = String(fileVal || '').toLowerCase().trim()
    resultVal = String(resultVal || '').toLowerCase().trim()

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

export const getMatchColor = (match) => {
  if (match >= 80) return 'green'
  if (match >= 50) return 'orange'
  return 'red'
}