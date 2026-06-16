# Frontend - Audiobook Manager

React + Vite frontend for the Audiobook Manager application.

## Development

```bash
cd frontend
npm install
npm run dev
```

## Build

```bash
npm run build
```

## Lint

```bash
npm run lint
```

## Tech Stack

- **React 19** - UI Framework
- **Vite** - Build tool and dev server
- **Axios** - HTTP client
- **ESLint** - Linting

## Project Structure

```
frontend/
├── src/
│   ├── App.jsx           # Main application component
│   ├── App.css           # Main styles
│   ├── index.css         # Global styles
│   ├── main.jsx          # Entry point
│   ├── components/       # React components
│   │   ├── FileList.jsx
│   │   ├── MetadataEditor.jsx
│   │   ├── SearchSection.jsx
│   │   ├── SearchResults.jsx
│   │   ├── TemplateHelper.jsx
│   │   ├── SettingsModal.jsx
│   │   ├── FolderBrowser.jsx
│   │   ├── ProgressModal.jsx
│   │   ├── CombineSuccessModal.jsx
│   │   ├── EmptyFolderModal.jsx
│   │   └── Toast.jsx
│   └── utils/
│       ├── template.js   # Template processing
│       └── matching.js   # Match percentage calculation
├── public/               # Static assets
├── dist/                 # Production build output
├── nginx.conf            # Nginx config for production
├── Dockerfile            # Development container
├── Dockerfile.prod       # Production container
├── package.json
└── vite.config.js
```

## Docker

### Development
```bash
docker build -f Dockerfile -t audiobook-frontend .
docker run -p 5173:5173 audiobook-frontend
```

### Production
```bash
docker build -f Dockerfile.prod -t audiobook-frontend-prod .
docker run -p 80:80 audiobook-frontend-prod
```

## Repository

https://github.com/curtis-winter/audiobook-renamer
