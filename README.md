# Audiobook Manager

A web-based audiobook management tool similar to Filebot for movies and TV shows. This application helps you organize, rename, and tag your audiobook collection with metadata from Audible and Google Books.

## Features

- **Watch Folder**: Monitor a folder for new audiobook files with folder browser dialog
- **Metadata Lookup**: Search and fetch metadata from Google Books
- **Tag Editing**: Edit ID3 tags for MP3, M4A, M4B, FLAC, and other formats
- **Customizable Templates**: Flexible filename and folder path templates
- **Batch Processing**: Process multiple files at once
- **Preview Changes**: See what changes will be made before applying
- **Folder Browser**: Native folder selection dialog for easy path configuration

## Project Structure

```
audiobook-manager/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── models.py            # Pydantic models
│   ├── services/
│   │   ├── metadata_service.py  # Read/write audio metadata
│   │   ├── file_service.py      # File operations
│   │   ├── watch_service.py     # Folder watching
│   │   └── api_service.py       # External API calls
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx              # Main React component
│   │   ├── App.css              # Styles
│   │   └── components/
│   │       ├── FolderBrowser.jsx    # Folder selection dialog
│   │       └── FolderBrowser.css    # Folder browser styles
│   └── package.json
├── README.md
└── start.sh                   # Startup script
```

## Installation

### Backend

1. Navigate to the backend directory:
```bash
cd audiobook-manager/backend
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the backend:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### Frontend

1. Navigate to the frontend directory:
```bash
cd audiobook-manager/frontend
```

2. Install dependencies:
```bash
npm install
```

3. Run the development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:5173`

## Usage

1. **Configure Folders**: 
   - Click "Browse..." next to Watch Folder to select where your audiobooks are stored
   - Click "Browse..." next to Output Folder to select where organized files should go
   
2. **Select a File**: Choose an audiobook from the file list

3. **Search Metadata**: Search for the book title/author to fetch metadata from Google Books

4. **Edit Metadata**: Review and modify the metadata as needed using the Audible mapping

5. **Preview**: Click "Preview Changes" to see the new filename and location

6. **Apply**: Click "Apply Changes" to update tags and move the file

## Filename Templates

Use these placeholders in your templates:

- `%album%` - Book title
- `%year%` - Publication year
- `%track%` - Track number
- `%title%` - Track title
- `%artist%` - Author/Narrator
- `%albumartist%` - Album artist
- `%series%` - Series name
- `%series-part%` - Series part number

### Example Templates

**Filename**: `%album% (%year%) - Pt%track%`
- Result: `Harry Potter and the Philosopher's Stone (1997) - Pt01.mp3`

**Folder Path**: `%albumartist%/%series%/%year% - %album%`
- Result: `J.K. Rowling/Harry Potter/1997 - Harry Potter and the Philosopher's Stone/`

## Audible Metadata Mapping

| MP3Tag Tag     | Audible.com Value    |
|----------------|----------------------|
| ALBUM          | Title                |
| SUBTITLE       | Subtitle             |
| ARTIST         | Author               |
| ALBUMARTIST    | Author               |
| COMPOSER       | Narrator             |
| YEAR           | Original Year        |
| COMMENT        | Publisher's Summary  |
| SERIES         | Series               |
| SERIES-PART    | Series Book #        |
| ALBUMSORT      | %series% %series-part% - %album% |
| PUBLISHER      | Publisher            |
| COPYRIGHT      | Copyright holder     |
| RATING WMP     | Audible Rating       |
| COVER          | Cover Art            |

## API Endpoints

- `GET /api/config` - Get configuration
- `POST /api/config` - Update configuration
- `GET /api/files` - List files in watch folder
- `GET /api/files/{file_id}/metadata` - Get file metadata
- `GET /api/folders` - Browse folders (for folder selection dialog)
- `POST /api/search` - Search for book metadata
- `POST /api/preview` - Preview changes
- `POST /api/apply` - Apply metadata changes
- `GET /api/watch/status` - Get watch status
- `POST /api/watch/start` - Start watching folder
- `POST /api/watch/stop` - Stop watching folder

## Supported Formats

- MP3
- M4A/M4B (Audible)
- FLAC
- OGG
- WAV
- WMA

## Quick Start

Use the provided startup script to run both backend and frontend:

```bash
cd audiobook-manager
./start.sh
```

Then open http://localhost:5173 in your browser.

## License

MIT
