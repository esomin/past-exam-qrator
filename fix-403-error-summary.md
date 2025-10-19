# Fix for 403 Error in Markdown Download

## Problem
When trying to download markdown files, a 403 error was occurring because the frontend was trying to fetch JSON data from the `/api/download/<download_id>` endpoint, which is designed to trigger file downloads, not return JSON data for processing.

## Root Cause
The `/api/download/<download_id>` endpoint in the Python backend uses `send_file()` with `as_attachment=True`, which:
1. Sets headers for file download (`Content-Disposition: attachment`)
2. Expects the response to be handled as a file download by the browser
3. Is not suitable for fetching JSON data programmatically with axios

## Solution
### 1. Added New Backend Endpoint
Created a new endpoint `/api/data/<download_id>` in `python/app.py`:
- Returns JSON data directly using `jsonify()`
- Does not trigger file download
- Suitable for programmatic data fetching
- Maintains the same security checks as the download endpoint

### 2. Updated Frontend API Service
Modified `src/services/api.ts`:
- Added new `fetchJsonData()` function
- Uses the new `/data/` endpoint instead of `/download/`
- Includes proper error handling and retry logic
- Added debugging logs for troubleshooting

### 3. Updated Download Logic
Modified `src/pages/FileProcessorPage.tsx`:
- Uses the new `fetchJsonData()` function for markdown conversion
- Maintains existing download logic for JSON files
- Added better error handling and logging

## Files Changed
1. `python/app.py` - Added `/api/data/<download_id>` endpoint
2. `src/services/api.ts` - Added `fetchJsonData()` function
3. `src/pages/FileProcessorPage.tsx` - Updated download logic

## How It Works Now
1. User selects markdown format option
2. Processing creates both JSON and markdown result entries
3. For JSON downloads: Uses existing `/api/download/<download_id>` endpoint
4. For markdown downloads:
   - Calls `/api/data/<download_id>` to fetch JSON data
   - Converts JSON to markdown using `convertJsonToMarkdown()`
   - Creates blob and triggers local download

## Testing
- JSON downloads should work as before
- Markdown downloads should now work without 403 errors
- Error handling should provide clear messages for debugging
- Console logs help track the conversion process

## Benefits
- Separates concerns: data fetching vs file downloading
- Maintains backward compatibility for JSON downloads
- Provides better error messages and debugging
- Follows RESTful API design principles