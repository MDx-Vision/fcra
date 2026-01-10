#!/bin/bash
#
# Capture SOP Screenshots
# This script starts the server, runs the Cypress screenshot tests, and copies files to the right location.
#
# Usage: ./scripts/capture-sop-screenshots.sh
#

set -e

echo "=========================================="
echo "Client Portal SOP Screenshot Capture"
echo "=========================================="
echo ""

# Create output directory
mkdir -p static/images/sop

# Check if server is running
if curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/ | grep -q "200"; then
    echo "✓ Server is already running"
else
    echo "Starting Flask server..."
    CI=true python app.py > /tmp/flask_sop.log 2>&1 &
    SERVER_PID=$!
    echo "  Server PID: $SERVER_PID"

    # Wait for server to be ready
    echo "  Waiting for server to start..."
    for i in {1..30}; do
        if curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/ | grep -q "200"; then
            echo "✓ Server is ready"
            break
        fi
        sleep 1
    done
fi

echo ""
echo "Running Cypress screenshot capture..."
echo ""

# Run Cypress test
npx cypress run --spec "cypress/e2e/capture_sop_screenshots.cy.js" --browser chrome --headless

echo ""
echo "Moving screenshots to static/images/sop/..."

# Move screenshots from Cypress folder to static folder
CYPRESS_DIR="cypress/screenshots/capture_sop_screenshots.cy.js"
if [ -d "$CYPRESS_DIR" ]; then
    find "$CYPRESS_DIR" -name "*.png" | while read file; do
        filename=$(basename "$file")
        # Extract just the screenshot name (after the last --)
        clean_name=$(echo "$filename" | sed 's/.*-- //' | sed 's/ (failed)//')
        cp "$file" "static/images/sop/$clean_name"
        echo "  ✓ $clean_name"
    done
fi

echo ""
echo "=========================================="
echo "Screenshot capture complete!"
echo "=========================================="
echo ""
echo "Screenshots saved to: static/images/sop/"
echo ""
ls -la static/images/sop/*.png 2>/dev/null | head -25 || echo "No screenshots found yet"
echo ""
echo "To view the SOP with screenshots, open CLIENT_PORTAL_SOP.md"
