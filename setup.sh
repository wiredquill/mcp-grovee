#!/bin/bash
set -e

echo "🚀 Setting up MCP Govee Controller..."
echo ""

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
REQUIRED_VERSION="3.11"

if [[ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]]; then
    echo "❌ Error: Python 3.11 or higher is required (found $PYTHON_VERSION)"
    exit 1
fi

echo "✓ Python version: $PYTHON_VERSION"

# Create virtual environment
echo ""
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo ""
echo "⬆️  Upgrading pip..."
pip install --upgrade pip --quiet

# Install dependencies
echo ""
echo "📥 Installing dependencies..."
pip install -r requirements.txt --quiet

echo ""
echo "✓ Dependencies installed"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo ""
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "✓ Created .env file"
    echo ""
    echo "⚠️  IMPORTANT: Please edit .env and add your Govee API key"
    echo "   Get your API key from: https://developer.govee.com/"
else
    echo ""
    echo "✓ .env file already exists"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Edit .env and add your GOVEE_API_KEY"
echo "  2. Activate the virtual environment: source venv/bin/activate"
echo "  3. Run the server: python -m src.server"
echo ""
echo "For Claude Desktop integration, see README.md"
echo ""
