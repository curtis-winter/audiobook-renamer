import SearchResults from './SearchResults'

export default function SearchSection({ searchQuery, onSearchChange, onSearch, results, metadata, onSelectResult, searching }) {
  return (
    <div className="search-section">
      <h2>Search Metadata</h2>
      <div className="search-box">
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && onSearch()}
          placeholder="Search for audiobook..."
          disabled={searching}
        />
        <button onClick={() => onSearch()} disabled={searching}>
          {searching ? 'Searching…' : 'Search'}
        </button>
      </div>
      <SearchResults
        results={results}
        metadata={metadata}
        onSelect={onSelectResult}
        searchQuery={searchQuery}
        searching={searching}
      />
    </div>
  )
}