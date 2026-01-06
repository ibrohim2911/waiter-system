#!/bin/bash
# Build script for PyInstaller bundling
# Run this from the project root: bash build.sh

set -e

echo "=== Waiter System Build Script ==="
echo ""

# 1. Ensure frontend is built
if [ ! -d "frontend" ]; then
    echo "❌ Frontend folder not found. Please ensure your React app is in ./frontend/"
    exit 1
fi

echo "📦 Building frontend..."
cd frontend
npm run build
cd ..

# 2. Collect Django static files
echo "📦 Collecting Django static files..."
python manage.py collectstatic --noinput

# 3. Bundle with PyInstaller
echo "🚀 Building .exe with PyInstaller..."
pyinstaller waiter.spec

echo ""
echo "✅ Build complete! Executable is in: dist/Restaurant/"
echo ""
echo "To run:"
echo "  dist/Restaurant/Restaurant.exe"
