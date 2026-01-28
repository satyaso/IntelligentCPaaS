#!/bin/bash

# AWS Amplify startup script for Flask application

echo "🚀 Starting AI-CPaaS Demo on AWS Amplify..."

# Set production environment
export FLASK_ENV=production

# Start gunicorn with Flask app
exec gunicorn \
    --bind 0.0.0.0:8080 \
    --workers 4 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    "src.ai_cpaas_demo.web.app:app"
