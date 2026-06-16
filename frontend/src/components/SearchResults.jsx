import { useMemo } from 'react'
import { calculateMatch, getMatchColor } from '../utils/matching'

export default function SearchResults({ results, metadata, onSelect, searchQuery, searching }) {
  const sortedResults = useMemo(() => {
    if (!Array.isArray(results)) return []
    return [...results]
      .map((result, index) => ({ result, index, match: calculateMatch(metadata, result) }))
      .sort((a, b) => {
        if (b.match !== a.match) return b.match - a.match
        return a.index - b.index
      })
  }, [results, metadata])

  if (searching) {
    return (
      <div className="search-results">
        <div className="searching-indicator" role="status" aria-live="polite">
          <div className="spinner-small" aria-hidden="true" />
          <span>Searching for metadata…</span>
        </div>
      </div>
    )
  }

  return (
    <div className="search-results">
      {sortedResults.length === 0 && searchQuery && (
        <p className="no-results">No results found. Try a different search term.</p>
      )}
      {sortedResults.map(({ result, match, index }) => (
        <div key={index} className="search-result" onClick={() => onSelect(result)}>
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
      ))}
    </div>
  )
}