#!/bin/bash
# Setup MemPalace API

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Setting up MemPalace API..."

# Check Python version
PYTHON_CMD=""
for py in python3.12 python3.11 python3; do
    if command -v $py &> /dev/null; then
        PYTHON_CMD=$py
        break
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo "Error: Python 3.11+ not found"
    exit 1
fi

echo "Using Python: $PYTHON_CMD"

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    $PYTHON_CMD -m venv .venv
fi

# Activate venv and install dependencies
source .venv/bin/activate
pip install -r requirements.txt

echo ""
echo "Setup complete!"
echo ""
echo "To start the server:"
echo "  ./start.sh"
echo ""
echo "Or manually:"
echo "  source .venv/bin/activate"
echo "  python main.py"
