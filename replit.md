# Flask Webhook Receiver

## Overview
A Python Flask web server designed to receive and log webhook data. The server provides endpoints for receiving webhooks via POST requests, viewing webhook history, and monitoring incoming data.

## Features
- **Webhook Endpoint**: `/webhook` - Receives POST requests with JSON or form data
- **History View**: `/history` - Returns all received webhooks as JSON
- **Clear History**: `/clear` - Clears the webhook history (POST request)
- **Home Page**: `/` - Simple web interface showing server status

## Project Structure
- `app.py` - Main Flask application with webhook endpoints
- `requirements.txt` - Python dependencies
- `.gitignore` - Git ignore patterns for Python projects

## How to Use
1. The server runs on port 5000
2. Send POST requests to `/webhook` to receive webhook data
3. View received webhooks at `/history`
4. The server logs all incoming webhooks to console and keeps the last 100 in memory

## Recent Changes
- Initial setup (November 19, 2025)
- Created Flask webhook receiver with endpoints for receiving, viewing, and clearing webhooks
- Added request logging and data storage
