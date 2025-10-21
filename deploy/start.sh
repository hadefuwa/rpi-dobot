#!/bin/bash
# Start script for PWA Dobot-PLC Control

cd "$(dirname "$0")/.."

echo "🚀 Starting PWA Dobot-PLC Control..."

# Load environment variables
if [ -f backend/.env ]; then
    export $(grep -v '^#' backend/.env | xargs)
fi

# Start the Flask application
cd backend
python3 app.py
