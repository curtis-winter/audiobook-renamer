# Quick Start Guide

## Installation

```bash
# Clone and run
docker compose up --build -d

# Open browser
http://localhost:8080
```

## Basic Workflow

1. **Select File** → Choose audiobook from file list
2. **Auto-Search** → Metadata search happens automatically
3. **Match Check** → Look for green badges (80%+ match)
4. **Auto-Preview** → High matches preview automatically
5. **Apply** → Click "Apply Changes" to process

## Template Quick Reference

### Common Tags
- `%title%` - Book title
- `%artist%` - Author
- `%year%` - Year
- `%series%` - Series name
- `%series_part%` - Part number

### Example Templates

**Filename**: `%title% (%year%)`
- Result: `The Hobbit (1937)`

**Folder**: `%artist%/%series%/%year% - %title%`
- Result: `J.R.R. Tolkien/Middle Earth/1937 - The Hobbit/`

### Advanced Functions

**Conditional Series**:
```
%title%%if_field:%series%: [%series% %series_part%]%
```
- With series: `The Hobbit [Middle Earth 1]`
- No series: `1984`

**Zero-Pad Track**:
```
{{pad_left:track:2}}
```
- Result: `01`, `02`, `10`, etc.

## Tips

- **Match %**: Green = good match (auto-preview)
- **Templates**: Click "Tags" button for helper modal
- **Drag & Drop**: Drag tags into template fields
- **Functions**: Click functions to insert template code
- **Preview**: Always preview before applying
- **Save**: Templates auto-save when you click OK

## Common Issues

**File not found**: Check watch folder path
**Slow processing**: Large files take time (timeout: 300s)
**Invalid chars**: Automatically sanitized (`:` → `-`)

## Need Help?

See full README.md for detailed documentation.
