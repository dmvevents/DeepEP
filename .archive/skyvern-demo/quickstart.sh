#!/bin/bash

# Skyvern Quick Start Script
# Automated setup for Mortgage Qualification System demo

set -e

echo "=========================================="
echo "Skyvern Setup for Mortgage System Demo"
echo "=========================================="
echo ""

# Check Python version
echo "1. Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | grep -oP '\d+\.\d+')
if [[ $(echo "$PYTHON_VERSION >= 3.11" | bc) -eq 1 ]]; then
    echo "   ✓ Python $PYTHON_VERSION detected"
else
    echo "   ✗ Python 3.11+ required. You have: $PYTHON_VERSION"
    exit 1
fi

# Check if OLLAMA is running
echo ""
echo "2. Checking OLLAMA service..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "   ✓ OLLAMA is running"
else
    echo "   ✗ OLLAMA is not running"
    echo "   Starting OLLAMA..."
    ollama serve > /tmp/ollama.log 2>&1 &
    sleep 3
    echo "   ✓ OLLAMA started"
fi

# Check if granite3.2-vision model is available
echo ""
echo "3. Checking vision model..."
if ollama list | grep -q "granite3.2-vision"; then
    echo "   ✓ granite3.2-vision model available"
else
    echo "   ✗ granite3.2-vision not found"
    echo "   Pulling model..."
    ollama pull granite3.2-vision
    echo "   ✓ Model downloaded"
fi

# Install Skyvern
echo ""
echo "4. Installing Skyvern..."
if python3 -c "import skyvern" 2>/dev/null; then
    echo "   ✓ Skyvern already installed"
else
    echo "   Installing Skyvern..."
    pip3 install skyvern
    echo "   ✓ Skyvern installed"
fi

# Initialize Skyvern if not already done
echo ""
echo "5. Initializing Skyvern..."
if [ ! -f ".env" ]; then
    echo "   Creating configuration..."
    skyvern quickstart

    # Configure for OLLAMA
    echo "" >> .env
    echo "# OLLAMA Configuration" >> .env
    echo "LLM_PROVIDER=ollama" >> .env
    echo "OLLAMA_BASE_URL=http://localhost:11434" >> .env
    echo "LLM_MODEL=granite3.2-vision" >> .env

    echo "   ✓ Configuration created"
else
    echo "   ✓ Configuration already exists"
fi

# Check if OCR service is running
echo ""
echo "6. Checking OCR service..."
if curl -s http://localhost:8003/health > /dev/null 2>&1; then
    echo "   ✓ OCR service is running"
else
    echo "   ⚠ OCR service not running (required for document upload tests)"
    echo "   Start it with: cd ../ocr-service && docker-compose up -d"
fi

# Create sample workflow script
echo ""
echo "7. Creating sample workflow..."
cat > workflows/hello_world.py << 'EOF'
#!/usr/bin/env python3
"""
Simple Skyvern test - Opens qualification workflow page
"""

from skyvern import Skyvern
import asyncio

async def test_basic():
    skyvern = Skyvern()

    result = await skyvern.run_task(
        url="file:///Users/antonalexander/Github/real_estate_app/frontend/qualification_workflow.html",
        prompt="Take a screenshot of the page"
    )

    print("✅ Skyvern is working!")
    print(f"Screenshot saved to: {result.get('screenshot_path', 'N/A')}")

if __name__ == '__main__':
    asyncio.run(test_basic())
EOF

chmod +x workflows/hello_world.py
echo "   ✓ Sample workflow created: workflows/hello_world.py"

# All done
echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Start Skyvern:"
echo "   skyvern run all"
echo ""
echo "2. Access UI at:"
echo "   http://localhost:3000"
echo ""
echo "3. Run sample workflow:"
echo "   python3 workflows/hello_world.py"
echo ""
echo "4. View full documentation:"
echo "   cat ../SKYVERN_DEPLOYMENT_GUIDE.md"
echo ""
echo "=========================================="
