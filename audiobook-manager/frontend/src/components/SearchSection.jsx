import SearchResults from './SearchResults'

export default function SearchSection({ searchQuery, onSearchChange, onSearch, results, metadata, onSelectResult }) {
  return (
    <div className="search-section">
      <h2>Search Metadata</h2>
      <div className="search-box">
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          placeholder="Search for audiobook..."
        />
        <button onClick={() => onSearch()}>Search</button>
      </div>
      <SearchResults results={results} metadata={metadata} onSelect={onSelectResult} searchQuery={searchQuery} />
    </div>
  )
}