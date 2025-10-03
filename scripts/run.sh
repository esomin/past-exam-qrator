#!/bin/bash

echo "🚀 Starting Q&A Processing Pipeline"

# 의존성 설치 확인
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# TypeScript 빌드 및 실행
echo "🔨 Building TypeScript..."
npm run build

echo "▶️  Running pipeline..."
npm start

echo "✅ Pipeline completed!"
echo "📁 Check output files in ./data directory"