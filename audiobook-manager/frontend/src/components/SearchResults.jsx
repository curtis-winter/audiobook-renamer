import { calculateMatch, getMatchColor } from '../utils/matching'

export default function SearchResults({ results, metadata, onSelect, searchQuery }) {
  return (
    <div className="search-results">
      {results.length === 0 && searchQuery && (
        <p className="no-results">No results found. Try a different search term.</p>
      )}
      {results.map((result, index) => {
        const match = calculateMatch(metadata, result)
        return (
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
        )
      })}
    </div>
  )
}