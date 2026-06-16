import httpx
from typing import Optional, Dict, Any, List
import os

class ApiService:
    def __init__(self):
        self.audible_api_url = "https://api.audible.com/1.0/catalog/products"
        self.google_books_url = "https://www.googleapis.com/books/v1/volumes"
        self.open_library_url = "https://openlibrary.org/search.json"
    
    async def search_audiobook(self, query: str, search_type: str = "all") -> list:
        """Search for audiobook metadata from multiple sources"""
        results = []
        errors = []

        # Try all sources and combine results
        audible_results = await self._search_audible(query)
        if audible_results:
            results.extend(audible_results)
        else:
            errors.append("audible")

        # Always try Open Library as additional source
        openlib_results = await self._search_open_library(query)
        if openlib_results:
            results.extend(openlib_results)
        else:
            errors.append("openlibrary")

        # Always try Google Books as additional source
        google_results = await self._search_google_books(query)
        if google_results:
            results.extend(google_results)
        else:
            errors.append("google")

        # If all sources failed, return empty with info
        if not results:
            return []

        # Deduplicate by title+author combination
        seen = set()
        unique_results = []
        for r in results:
            key = f"{r.get('title', '')}|{r.get('artist', '')}"
            if key not in seen:
                seen.add(key)
                unique_results.append(r)

        return unique_results[:30]
    
    async def _search_audible(self, query: str) -> list:
        """Search Audible API (public, no auth required)"""
        try:
            params = {
                'keywords': query,
                'response_groups': 'contributors,media,product_desc,product_attrs,product_extended_attrs,series,category_ladders,rating',
                'image_sizes': '500,1000,2400',
                'num_results': 15,
                'products_sort_by': 'Relevance',
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.audible_api_url, params=params, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                results = []
                
                for item in data.get('products', []):
                    # Get series info
                    series = item.get('series', [])
                    series_name = series[0].get('title') if series else None
                    series_part = series[0].get('sequence') if series else None
                    
                    # Get narrators
                    narrators = item.get('narrators', [])
                    narrator = narrators[0].get('name') if narrators else None
                    narrators_list = [n.get('name') for n in narrators if n.get('name')]
                    
                    # Get authors
                    authors = item.get('authors', [])
                    author_names = [a.get('name') for a in authors if a.get('name')]
                    
                    # Get cover - try different sizes
                    images = item.get('product_images', {})
                    cover = images.get('2400') or images.get('1000') or images.get('500') or images.get('100')
                    
                    # Get rating
                    rating_data = item.get('rating', {})
                    rating = rating_data.get('display_average_rating') if rating_data else None
                    
                    # Get genre from category ladders
                    genre_list = []
                    category_ladders = item.get('category_ladders', [])
                    for ladder in category_ladders:
                        for cat in ladder.get('ladder', []):
                            cat_name = cat.get('name')
                            if cat_name and cat_name not in genre_list:
                                genre_list.append(cat_name)
                    
                    # Get explicit flag
                    is_explicit = item.get('is_adult_product', False)
                    
                    # Get release date/time
                    release_date = item.get('release_date')
                    
                    # Build complete results with all MP3Tag fields
                    results.append({
                        # Basic fields (MP3Tag -> Audible mapping)
                        'source': 'audible',
                        'id': item.get('asin'),
                        'asin': item.get('asin'),
                        
                        # ALBUM -> Title
                        'album': item.get('title'),
                        'title': item.get('title'),
                        
                        # SUBTITLE
                        'subtitle': item.get('subtitle'),
                        
                        # ALBUMARTIST / ARTIST -> Author
                        'album_artist': author_names[0] if author_names else None,
                        'album_artists': author_names,  # List of all authors
                        'artist': ', '.join(author_names) if author_names else None,
                        'authors': author_names,
                        
                        # COMPOSER -> Narrator
                        'composer': narrator,
                        'narrator': narrator,
                        'narrators': narrators_list,
                        
                        # YEAR / RELEASETIME
                        'year': (release_date[:4]) if release_date and len(release_date) >= 4 else None,
                        'release_date': release_date,
                        
                        # COMMENT / DESCRIPTION -> Publisher's Summary
                        'comment': item.get('publisher_summary'),
                        'description': item.get('publisher_summary'),
                        
                        # SERIES / SERIES-PART
                        'series': series_name,
                        'series_part': series_part,
                        
                        # CONTENTGROUP / MOVEMENTNAME -> Series, Book #
                        'content_group': f"{series_name}, Book #{series_part}" if series_name and series_part else series_name,
                        'movement_name': series_name,
                        'movement': series_part,
                        'show_movement': '1' if series_name else None,
                        
                        # ALBUMSORT - Complex logic
                        'album_sort': self._build_album_sort(item.get('title'), item.get('subtitle'), series_name, series_part),
                        
                        # PUBLISHER
                        'publisher': item.get('publisher_name'),
                        
                        # COPYRIGHT
                        'copyright': item.get('copyright'),
                        
                        # RATING / RATING WMP
                        'rating': rating,
                        'rating_wmp': rating,
                        
                        # COVER
                        'cover': cover,
                        
                        # FORMAT (e.g., "unabridged")
                        'format': item.get('format_type'),
                        
                        # LANGUAGE
                        'language': item.get('language'),
                        
                        # GENRE
                        'genre': '/'.join(genre_list[:2]) if genre_list else None,
                        'genre_list': genre_list,
                        
                        # EXPLICIT / ITUNESADVISORY
                        'explicit': '1' if is_explicit else None,
                        'itunes_advisory': '1' if is_explicit else '2',
                        
                        # ITUNESGAPLESS
                        'itunes_gapless': '1',
                        
                        # ITUNESMEDIATYPE
                        'itunes_mediatype': 'Audiobook',
                        
                        # ISBN
                        'isbn': item.get('isbn'),
                        
                        # WWWAUDIOFILE - Audible product URL
                        'www_audio_file': f"https://www.audible.com/pd/{item.get('asin')}",
                        
                        # Additional fields
                        'runtime': item.get('runtime_length_min'),
                        'content_type': item.get('content_type'),
                        'merchandising_summary': item.get('merchandising_summary'),
                    })
                
                return results
            return []
        except Exception as e:
            print(f"Audible search error: {e}")
            return []
    
    def _build_album_sort(self, title: str, subtitle: str, series: str, series_part: str) -> str:
        """Build ALBUMSORT based on MP3Tag logic"""
        if series:
            if series_part:
                return f"{series} {series_part} - {title}"
            return f"{series} - {title}"
        elif subtitle:
            return f"{title} - {subtitle}"
        return title
    
    async def _search_open_library(self, query: str) -> list:
        """Search Open Library API"""
        try:
            params = {'q': query, 'limit': 10}
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.open_library_url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                results = []
                for doc in data.get('docs', [])[:10]:
                    cover_id = doc.get('cover_i')
                    cover_url = f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg" if cover_id else None
                    
                    results.append({
                        'source': 'openlibrary',
                        'id': doc.get('key', '').replace('/works/', ''),
                        'title': doc.get('title'),
                        'album': doc.get('title'),
                        'subtitle': None,
                        'authors': doc.get('author_name', []),
                        'artist': ', '.join(doc.get('author_name', [])) if doc.get('author_name') else None,
                        'album_artist': doc.get('author_name', [None])[0] if doc.get('author_name') else None,
                        'publisher': (doc.get('publisher') or [None])[0] if doc.get('publisher') else None,
                        'year': str(doc.get('first_publish_year', '')) if doc.get('first_publish_year') else None,
                        'comment': (doc.get('first_sentence') or [None])[0] if doc.get('first_sentence') else None,
                        'description': (doc.get('first_sentence') or [None])[0] if doc.get('first_sentence') else None,
                        'cover': cover_url,
                    })
                return results
            return []
        except Exception as e:
            print(f"Open Library search error: {e}")
            return []
    
    async def _search_google_books(self, query: str) -> list:
        """Search Google Books API (fallback)"""
        try:
            params = {'q': query, 'maxResults': 10}
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(self.google_books_url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                results = []
                for item in data.get('items', []):
                    info = item.get('volumeInfo', {})
                    results.append({
                        'source': 'google',
                        'id': item.get('id'),
                        'title': info.get('title'),
                        'album': info.get('title'),
                        'subtitle': info.get('subtitle'),
                        'authors': info.get('authors', []),
                        'artist': ', '.join(info.get('authors', [])) if info.get('authors') else None,
                        'album_artist': info.get('authors', [None])[0] if info.get('authors') else None,
                        'publisher': info.get('publisher'),
                        'year': (info.get('publishedDate') or '')[:4] if info.get('publishedDate') else None,
                        'comment': info.get('description'),
                        'description': info.get('description'),
                        'cover': info.get('imageLinks', {}).get('thumbnail'),
                    })
                return results
            return []
        except Exception as e:
            print(f"Google Books search error: {e}")
            return []
    
    async def get_book_metadata(self, source: str, book_id: str) -> Optional[Dict[str, Any]]:
        if source == 'audible':
            return await self._get_audible_metadata(book_id)
        elif source == 'openlibrary':
            return await self._get_openlibrary_metadata(book_id)
        elif source == 'google':
            return await self._get_google_metadata(book_id)
        return None

    async def _get_audible_metadata(self, asin: str) -> Optional[Dict[str, Any]]:
        """Get detailed metadata from Audible by ASIN"""
        try:
            url = f"https://api.audible.com/1.0/catalog/products/{asin}"
            params = {
                'response_groups': 'contributors,media,product_desc,product_attrs,product_extended_attrs,series,rating,category_ladders'
            }
            headers = {'User-Agent': 'Mozilla/5.0'}
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                product = data.get('product', {})
                
                series = product.get('series', [])
                series_name = series[0].get('title') if series else None
                series_part = series[0].get('sequence') if series else None
                
                authors = product.get('authors', [])
                author_names = [a.get('name') for a in authors if a.get('name')]
                
                narrators = product.get('narrators', [])
                narrator = narrators[0].get('name') if narrators else None
                narrators_list = [n.get('name') for n in narrators if n.get('name')]
                
                images = product.get('product_images', {})
                cover = images.get('2400') or images.get('1000') or images.get('500')
                
                rating_data = product.get('rating', {})
                rating = rating_data.get('display_average_rating') if rating_data else None
                
                release_date = product.get('release_date')
                
                return {
                    'title': product.get('title'),
                    'album': product.get('title'),
                    'subtitle': product.get('subtitle'),
                    'authors': author_names,
                    'artist': ', '.join(author_names) if author_names else None,
                    'album_artist': author_names[0] if author_names else None,
                    'album_artists': author_names,
                    'narrator': narrator,
                    'composer': narrator,
                    'narrators': narrators_list,
                    'publisher': product.get('publisher_name'),
                    'year': (release_date[:4]) if release_date and len(release_date) >= 4 else None,
                    'release_date': release_date,
                    'description': product.get('publisher_summary'),
                    'comment': product.get('publisher_summary'),
                    'series': series_name,
                    'series_part': series_part,
                    'content_group': f"{series_name}, Book #{series_part}" if series_name and series_part else series_name,
                    'movement_name': series_name,
                    'movement': series_part,
                    'show_movement': '1' if series_name else None,
                    'album_sort': self._build_album_sort(product.get('title'), product.get('subtitle'), series_name, series_part),
                    'cover': cover,
                    'format': product.get('format_type'),
                    'language': product.get('language'),
                    'copyright': product.get('copyright'),
                    'rating': rating,
                    'rating_wmp': rating,
                    'asin': product.get('asin'),
                    'isbn': product.get('isbn'),
                    'explicit': '1' if product.get('is_adult_product') else None,
                    'itunes_advisory': '1' if product.get('is_adult_product') else '2',
                    'itunes_gapless': '1',
                    'itunes_mediatype': 'Audiobook',
                    'www_audio_file': f"https://www.audible.com/pd/{product.get('asin')}",
                    'runtime': product.get('runtime_length_min'),
                }
            return None
        except Exception as e:
            print(f"Audible metadata error: {e}")
            return None

    async def _get_google_metadata(self, book_id: str) -> Optional[Dict[str, Any]]:
        try:
            url = f"{self.google_books_url}/{book_id}"
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                info = data.get('volumeInfo', {})
                return {
                    'title': info.get('title'),
                    'album': info.get('title'),
                    'subtitle': info.get('subtitle'),
                    'authors': info.get('authors', []),
                    'artist': ', '.join(info.get('authors', [])) if info.get('authors') else None,
                    'album_artist': info.get('authors', [None])[0] if info.get('authors') else None,
                    'publisher': info.get('publisher'),
                    'year': (info.get('publishedDate') or '')[:4] if info.get('publishedDate') else None,
                    'description': info.get('description'),
                    'comment': info.get('description'),
                    'cover': info.get('imageLinks', {}).get('thumbnail'),
                }
            return None
        except Exception as e:
            print(f"Error getting Google metadata: {e}")
            return None

    async def _get_openlibrary_metadata(self, book_id: str) -> Optional[Dict[str, Any]]:
        try:
            url = f"https://openlibrary.org/works/{book_id}.json"
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                covers = data.get('covers', [])
                cover_url = f"https://covers.openlibrary.org/b/id/{covers[0]}-M.jpg" if covers else None
                
                author_names = []
                async with httpx.AsyncClient(timeout=3.0) as client:
                    for author in data.get('authors', [])[:3]:
                        if isinstance(author, dict) and author.get('author'):
                            author_id = author['author'].get('key')
                            if author_id:
                                try:
                                    author_resp = await client.get(f"https://openlibrary.org{author_id}.json")
                                    if author_resp.status_code == 200:
                                        author_names.append(author_resp.json().get('name', ''))
                                except:
                                    continue
                
                desc = data.get('description')
                description = desc.get('value', '') if isinstance(desc, dict) else desc
                
                return {
                    'title': data.get('title'),
                    'album': data.get('title'),
                    'subtitle': None,
                    'authors': author_names,
                    'artist': ', '.join(author_names) if author_names else None,
                    'album_artist': author_names[0] if author_names else None,
                    'publisher': (data.get('publishers') or [None])[0] if data.get('publishers') else None,
                    'year': (data.get('first_publish_date') or '')[:4] if data.get('first_publish_date') else None,
                    'description': description,
                    'comment': description,
                    'cover': cover_url,
                }
            return None
        except Exception as e:
            print(f"Error getting Open Library metadata: {e}")
            return None

api_service = ApiService()