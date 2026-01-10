#!/bin/bash
# Remote Server Setup Script for MCP Govee Controller
# This script sets up the MCP server on a remote machine

set -e

echo "🚀 MCP Govee Remote Server Setup"
echo "================================="
echo ""

# Check if running on SUSE/openSUSE
if [ -f /etc/os-release ]; then
    . /etc/os-release
    if [[ "$ID" != "sles" && "$ID" != "opensuse-leap" && "$ID" != "opensuse-tumbleweed" ]]; then
        echo "⚠️  Warning: This script is optimized for SUSE/openSUSE"
        echo "   Current OS: $PRETTY_NAME"
        read -p "Continue anyway? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
fi

# Check Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed"
    echo "   Install Docker first: https://docs.docker.com/engine/install/"
    exit 1
fi

echo "✓ Docker is installed: $(docker --version)"

# Check current directory
if [ ! -f "Dockerfile" ] || [ ! -f "requirements.txt" ]; then
    echo "❌ Error: Must run this script from the mcp-grovee directory"
    echo "   Current directory: $(pwd)"
    exit 1
fi

echo "✓ Running in correct directory: $(pwd)"
echo ""

# Get Govee API key
echo "📝 Govee API Configuration"
echo "=========================="
echo ""

if [ -f ".env" ]; then
    echo "⚠️  .env file already exists"
    read -p "Overwrite it? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Keeping existing .env file"
    else
        rm .env
    fi
fi

if [ ! -f ".env" ]; then
    echo "Get your Govee API key from: https://developer.govee.com/"
    echo ""
    read -p "Enter your Govee API key: " api_key

    if [ -z "$api_key" ]; then
        echo "❌ API key cannot be empty"
        exit 1
    fi

    cat > .env <<EOF
GOVEE_API_KEY=$api_key
GOVEE_DEVICE_ADDRESS=
GOVEE_DEVICE_MODEL=
EOF

    chmod 600 .env
    echo "✓ Created .env file"
fi

echo ""

# Build Docker image
echo "🐳 Building Docker Image"
echo "======================="
echo ""

docker build -t mcp-govee:latest .

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Docker image built successfully"
else
    echo ""
    echo "❌ Docker build failed"
    exit 1
fi

echo ""

# Test the container
echo "🧪 Testing Container"
echo "==================="
echo ""

echo "Starting container (will exit after a few seconds)..."
timeout 5 docker run -i --rm --env-file .env mcp-govee:latest || true

echo ""
echo "✓ Container test completed"
echo ""

# Create launcher script
echo "📜 Creating Launcher Script"
echo "=========================="
echo ""

INSTALL_DIR=$(pwd)

read -p "Install launcher script to /usr/local/bin/mcp-govee.sh? (Y/n) " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
    sudo tee /usr/local/bin/mcp-govee.sh > /dev/null <<EOF
#!/bin/bash
# MCP Govee Server Launcher
cd $INSTALL_DIR
docker run -i --rm --env-file .env mcp-govee:latest
EOF

    sudo chmod +x /usr/local/bin/mcp-govee.sh
    echo "✓ Launcher script installed to /usr/local/bin/mcp-govee.sh"
    LAUNCHER_PATH="/usr/local/bin/mcp-govee.sh"
else
    # Create local launcher
    cat > ./mcp-govee.sh <<EOF
#!/bin/bash
# MCP Govee Server Launcher
cd $INSTALL_DIR
docker run -i --rm --env-file .env mcp-govee:latest
EOF

    chmod +x ./mcp-govee.sh
    echo "✓ Launcher script created: ./mcp-govee.sh"
    LAUNCHER_PATH="$INSTALL_DIR/mcp-govee.sh"
fi

echo ""

# Get IP address
echo "🌐 Network Information"
echo "====================="
echo ""

# Try to get IP address
IP_ADDR=$(hostname -I | awk '{print $1}')

if [ -z "$IP_ADDR" ]; then
    echo "⚠️  Could not detect IP address automatically"
    read -p "Enter this server's IP address: " IP_ADDR
fi

echo "Server IP Address: $IP_ADDR"
echo ""

# Display SSH setup instructions
echo "🔑 SSH Setup Required"
echo "===================="
echo ""
echo "On your laptop, run:"
echo ""
echo "  ssh-copy-id $(whoami)@$IP_ADDR"
echo ""
echo "Then test passwordless SSH:"
echo ""
echo "  ssh $(whoami)@$IP_ADDR \"echo SSH works\""
echo ""

# Display Claude Desktop configuration
echo "⚙️  Claude Desktop Configuration"
echo "================================"
echo ""
echo "Add this to your Claude Desktop config on your laptop:"
echo ""
echo "{"
echo "  \"mcpServers\": {"
echo "    \"govee\": {"
echo "      \"command\": \"ssh\","
echo "      \"args\": ["
echo "        \"$(whoami)@$IP_ADDR\","
echo "        \"$LAUNCHER_PATH\""
echo "      ]"
echo "    }"
echo "  }"
echo "}"
echo ""

# Save config to file
cat > claude-desktop-remote-config.json <<EOF
{
  "mcpServers": {
    "govee": {
      "command": "ssh",
      "args": [
        "$(whoami)@$IP_ADDR",
        "$LAUNCHER_PATH"
      ]
    }
  }
}
EOF

echo "✓ Configuration saved to: claude-desktop-remote-config.json"
echo ""

# Final summary
echo "✅ Setup Complete!"
echo "================="
echo ""
echo "Next steps:"
echo ""
echo "1. On your laptop, set up SSH key authentication:"
echo "   ssh-copy-id $(whoami)@$IP_ADDR"
echo ""
echo "2. Test the SSH connection:"
echo "   ssh $(whoami)@$IP_ADDR \"$LAUNCHER_PATH\""
echo ""
echo "3. Copy the configuration from:"
echo "   $INSTALL_DIR/claude-desktop-remote-config.json"
echo "   to your Claude Desktop config on your laptop"
echo ""
echo "4. Restart Claude Desktop on your laptop"
echo ""
echo "5. Test by asking Claude to control your Govee lamp!"
echo ""
echo "For detailed instructions, see REMOTE_SETUP.md"
echo ""
