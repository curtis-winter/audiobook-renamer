# Quick Start Guide

## Servers are Running

Both backend and frontend servers are now running:
- **Backend API**: http://localhost:8000
- **Frontend**: http://localhost:5173

## What's Working

✅ Backend API with CORS enabled
✅ Frontend React app with Vite
✅ Folder browser dialog for selecting watch/output folders
✅ Google Books API integration for metadata search
✅ ID3 tag reading/writing for MP3, M4A, M4B, FLAC
✅ Customizable filename and folder templates
✅ Preview changes before applying

## How to Use

1. Open http://localhost:5173 in your browser

2. **Configure Folders**:
   - Click "Browse..." next to Watch Folder
   - Navigate to your audiobook folder (e.g., `/home/curtis/audiobooks/input`)
   - Click "Select Folder"
   - Do the same for Output Folder

3. **Select a File**:
   - Files from the watch folder will appear in the sidebar
   - Click on a file to view/edit its metadata

4. **Search for Metadata**:
   - Enter the book title or author in the search box
   - Click "Search"
   - Click on a search result to apply the metadata

5. **Edit Metadata**:
   - Review and modify fields as needed
   - All Audible tags are supported

6. **Preview & Apply**:
   - Click "Preview Changes" to see the new filename and location
   - Click "Apply Changes" to update tags and move the file

## Restarting the Servers

If you need to restart:

```bash
# Kill existing servers
pkill -f "uvicorn"
pkill -f "vite"

# Start backend
cd audiobook-manager/backend
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 &

# Start frontend (new terminal)
cd audiobook-manager/frontend
npm run dev
```

Or use the startup script:
```bash
cd audiobook-manager
./start.sh
```

## Testing the Folder Browser

1. Click "Browse..." button
2. You should see folders like: bin, boot, dev, etc, home, lib, opt, usr, var
3. Click on "home" then "curtis" to navigate
4. Click "Select Folder" to choose it

## API Endpoints Available

- `GET /api/config` - Get current configuration
- `GET /api/folders?path=/home` - List folders
- `GET /api/files` - List audio files in watch folder
- `POST /api/search?q=harry+potter` - Search Google Books
- `POST /api/preview` - Preview changes
- `POST /api/apply` - Apply changes

## Troubleshooting

**CORS errors in console**: Make sure backend is running on port 8000

**Folder browser shows no folders**: Check that the path is valid and you have permissions

**Files not loading**: Ensure the watch folder path is correct and contains audio files (.mp3, .m4b, .m4a, .flac, etc.)
