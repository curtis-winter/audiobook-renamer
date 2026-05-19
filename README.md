# Audiobook Manager

A web-based audiobook management tool similar to Filebot for organizing and tagging audiobook collections with metadata from Audible and other sources.

## Features

### Core Functionality
- **Watch Folder Monitoring**: Automatically detect and process new audiobook files
- **Metadata Search**: Search and fetch metadata from Audible, Google Books, and Open Library
- **Smart Matching**: Automatic match percentage calculation with auto-preview for high-confidence matches (80%+)
- **Tag Editing**: Edit ID3 tags for MP3, M4A, M4B, FLAC, and other audio formats
- **Customizable Templates**: Flexible filename and folder path templates with advanced functions
- **Batch Processing**: Process multiple files efficiently
- **Live Preview**: See changes before applying them
- **Folder Browser**: Native folder selection dialog for easy path configuration
- **Config Persistence**: Settings automatically save and persist across sessions

### Template Helper Modal
- **Click to Insert**: Click any tag or function to insert at cursor position in the template
- **Live Preview**: See real-time preview with two sample books:
  - **Standalone Book**: "1984" by George Orwell (no series)
  - **Book in Series**: "The Hobbit" by J.R.R. Tolkien (Middle Earth series)
- **Sample Book Selector**: Switch between sample books to see how templates render different scenarios
- **Smart Functions**:
  - `{{if_field:%series%:[%series% %series_part%]}}` - Show content only if field exists
  - `{{pad_left:%series_part%:2}}` - Zero-pad numbers (e.g., 1 → "01")
  - `{{uppercase:%title%}}` - Convert to uppercase
  - `{{lowercase:%title%}}` - Convert to lowercase
  - `{{default:%title%:Unknown}}` - Provide default value if empty
- **Save & Apply**: Save template and persist config in one click

### UI Workflow

The app is designed for efficient workflow:

1. **Select a file** from the file list on the left
2. **Search for metadata** using the search box (searches Audible, Google Books, Open Library)
3. **Select a result** - metadata auto-fills AND preview auto-generates simultaneously
4. **Edit as needed** - any field changes trigger instant preview update
5. **Apply Changes** - green button at top of metadata section
6. **Template editing** - click the ⚙ cog icon next to "File Name" or "File Location" to edit templates

### Template Editing

Templates are now edited via the ⚙ icons next to File Name and File Location in the metadata table, not in the config sidebar. This keeps templates context-aware and easy to access while working with a specific file.

### Change Highlighting

When viewing metadata, fields that differ from the original file are highlighted:
- **Bold red text** in input fields indicates the value has been changed from the original
- This applies when: selecting a search result, manually editing a field, or any field differs from what's on the file

### Path Sanitization
Automatically removes or replaces invalid characters for cross-platform compatibility:
- Windows: `< > : " / \ | ? *`
- macOS: `:`
- Linux: `/`

### Validation & Error Handling
The app includes robust validation and error handling:
- **Required field validation**: Title must be filled before applying changes
- **Conflict detection**: Prevents overwriting existing files (returns error if target already exists)
- **Path traversal protection**: Blocks attempts to escape the output directory
- **User-friendly errors**: Errors display in red below the Apply button instead of alert dialogs

## Installation

### Docker (Recommended)

```bash
# Production build (with nginx frontend)
docker compose -f docker-compose.prod.yml up --build -d

# View logs
docker logs audiobook-manager-backend
docker logs audiobook-manager-frontend

# Stop
docker compose -f docker-compose.prod.yml down
```

The application will be available at `http://localhost`

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CONFIG_PATH` | `/config/config.json` | Path to config file |
| `ALLOWED_ORIGINS` | `http://localhost:3000,http://localhost:5173` | CORS origins |

### Manual Installation

#### Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Usage

1. **Configure Folders**:
   - Click "Browse..." next to Watch Folder to select your audiobook source
   - Click "Browse..." next to Output Folder for organized files destination

2. **Select a File**: Choose an audiobook from the file list

3. **Search Metadata**: 
   - Search automatically triggers when you select a file
   - Match percentage shows on each result (green = 80%+, orange = 50-79%, red = <50%)
   - High matches (80%+) automatically preview

4. **Edit Metadata**: Review and modify metadata as needed

5. **Customize Templates**:
   - Click "Tags" button next to Filename or Folder Template
   - Use drag-and-drop or click to insert tags
   - Add functions for advanced templating
   - Preview with sample books
   - Click "OK" to save (auto-saves config)

6. **Preview Changes**: Click "Preview Changes" to see new filename and location

7. **Apply**: Click "Apply Changes" to update tags and move the file

## Template Tags

| Tag | Description | Example |
|-----|-------------|---------|
| `%title%` | Book title | The Hobbit |
| `%album%` | Album name (same as title) | The Hobbit |
| `%artist%` | Author/Artist | J.R.R. Tolkien |
| `%albumartist%` | Album artist | J.R.R. Tolkien |
| `%composer%` | Composer/Narrator | Rob Inglis |
| `%narrator%` | Narrator | Rob Inglis |
| `%year%` | Publication year | 1937 |
| `%track%` | Track number | 01 |
| `%series%` | Series name | Middle Earth |
| `%series_part%` | Series part number | 1 |
| `%series-part%` | Series part (alternate) | 1 |
| `%series_full%` | Full series with part | Middle Earth 1 |
| `%subtitle%` | Subtitle | There and Back Again |
| `%genre%` | Genre | Fantasy |
| `%comment%` | Comment | Unabridged |
| `%publisher%` | Publisher | George Allen & Unwin |
| `%copyright%` | Copyright | 1937 |
| `%format%` | File format | MP3 |
| `%language%` | Language | English |
| `%asin%` | ASIN | B000FC3K1A |

## Template Functions

### Conditional
- `{{if_field:fieldname:value}}` - Show value if field exists
- `{{if_field:fieldname:yes:no}}` - If/else logic

### Formatting
- `{{pad_left:fieldname:2}}` - Zero-pad to width (1 → "01")
- `{{uppercase:fieldname}}` - Convert to uppercase
- `{{lowercase:fieldname}}` - Convert to lowercase
- `{{default:fieldname:Default}}` - Use default if empty
- `{{replace:fieldname:old:new}}` - Replace text

## Filename Templates

**Example 1**: `%title% (%year%)`
- Result: `The Hobbit (1937)`

**Example 2**: `%albumartist% - %album% (%year%)`
- Result: `J.R.R. Tolkien - The Hobbit (1937)`

**Example 3**: `%title%%if_field:%series%: [%series% %series_part%]%.%extension%`
- With series: `The Hobbit [Middle Earth 1].m4b`
- Without series: `1984.m4b`

## Folder Templates

**Example 1**: `%albumartist%/%series%/%year% - %album%`
- Result: `J.R.R. Tolkien/Middle Earth/1937 - The Hobbit/`

**Example 2**: `%albumartist%/%series%{{if_field:%series%:/%series% %series_part%}}`
- With series: `J.R.R. Tolkien/Middle Earth/Middle Earth 1/`
- Without series: `George Orwell/1984/`

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/config` | GET | Get configuration |
| `/api/config` | POST | Update configuration |
| `/api/files` | GET | List files in watch folder |
| `/api/files/{id}/metadata` | GET | Get file metadata |
| `/api/search` | POST | Search for book metadata |
| `/api/preview` | POST | Preview changes |
| `/api/apply` | POST | Apply metadata changes |
| `/api/watch/status` | GET | Get watch status |
| `/api/watch/start` | POST | Start watching folder |
| `/api/watch/stop` | POST | Stop watching folder |

## Supported Formats

- MP3
- M4A / M4B (Audible)
- FLAC
- OGG
- WAV
- WMA
- AAC

## Project Structure

```
audiobook-manager/
├── backend/
│   ├── main.py                 # FastAPI application
│   ├── models.py               # Pydantic models
│   ├── services/
│   │   ├── metadata_service.py # Read/write audio metadata
│   │   ├── file_service.py     # File operations & templates
│   │   ├── watch_service.py    # Folder watching
│   │   └── api_service.py      # External API calls
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx             # Main React component
│   │   ├── App.css             # Styles
│   │   └── components/
│   └── package.json
├── docker-compose.yml
├── docker-compose.single.yml
├── Dockerfile
└── README.md
```

## Configuration

Configuration is stored in `/config/config.json` and persists across deployments:

```json
{
  "watch_folder": "/mnt/watch",
  "output_folder": "/mnt/output",
  "filename_template": "%title% (%year%)",
  "folder_template": "%albumartist%/%album%"
}
```

## Troubleshooting

### Files not showing in watch folder
- Ensure the watch folder path is correct and accessible
- Check file permissions
- Verify file extensions are supported

### Template not working
- Check for invalid characters (automatically sanitized)
- Verify tag names are correct (case-sensitive)
- Test with sample books in template helper

### Slow performance
- Large files may take time to process metadata
- Network shares (SMB) may be slower
- Check nginx timeout settings (default: 300s)

## License

MIT

## Credits

Built with:
- **Backend**: FastAPI, Python
- **Frontend**: React, Vite
- **Metadata**: Mutagen, Audible API, Google Books API
- **Container**: Docker, nginx
