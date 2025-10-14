# React File Processor

A full-stack application for processing JSON files with multiple classification options. Built with Vite React frontend and Flask Python backend.

## Features

- Drag-and-drop JSON file upload
- Multiple processing options (Category, Institution, Year)
- Enhanced Python backend with solve field parsing
- Download processed results as JSON files
- Modern React UI with TypeScript

## Project Structure

```
├── src/                    # React frontend
│   ├── components/         # React components
│   ├── services/          # API services
│   └── types/             # TypeScript definitions
├── python/                # Flask backend
│   ├── processors/        # Processing modules
│   ├── app.py            # Flask application
│   └── requirements.txt   # Python dependencies
└── scripts/               # Setup scripts
```

## Setup Instructions

### 1. Install Node.js Dependencies

```bash
npm install
```

### 2. Setup Python Environment

```bash
npm run setup-python
```

This will:
- Create a Python virtual environment
- Install Flask and other required dependencies

### 3. Development

Start both frontend and backend:

```bash
npm run dev-full
```

Or start them separately:

```bash
# Frontend only
npm run dev

# Backend only
npm run start-backend
```

## API Endpoints

- `GET /api/health` - Health check
- `POST /api/process` - Process uploaded JSON file
- `GET /api/download/<id>` - Download processed file

## Expanding the ESLint configuration

If you are developing a production application, we recommend updating the configuration to enable type-aware lint rules:

```js
export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...

      // Remove tseslint.configs.recommended and replace with this
      tseslint.configs.recommendedTypeChecked,
      // Alternatively, use this for stricter rules
      tseslint.configs.strictTypeChecked,
      // Optionally, add this for stylistic rules
      tseslint.configs.stylisticTypeChecked,

      // Other configs...
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```

You can also install [eslint-plugin-react-x](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-x) and [eslint-plugin-react-dom](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-dom) for React-specific lint rules:

```js
// eslint.config.js
import reactX from 'eslint-plugin-react-x'
import reactDom from 'eslint-plugin-react-dom'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...
      // Enable lint rules for React
      reactX.configs['recommended-typescript'],
      // Enable lint rules for React DOM
      reactDom.configs.recommended,
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```
