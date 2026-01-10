#!/bin/bash
# HTTP/SSE Transport Setup Script for MCP Govee Controller

set -e

echo "🌐 MCP Govee HTTP/SSE Transport Setup"
echo "======================================"
echo ""

# Check Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed"
    echo "   Install Docker first: https://docs.docker.com/engine/install/"
    exit 1
fi

echo "✓ Docker is installed: $(docker --version)"

# Check current directory
if [ ! -f "Dockerfile.http" ] || [ ! -f "requirements.txt" ]; then
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
    echo "✓ .env file already exists"
    source .env
    if [ -z "$GOVEE_API_KEY" ]; then
        echo "⚠️  GOVEE_API_KEY not set in .env"
        read -p "Enter your Govee API key: " api_key
        echo "GOVEE_API_KEY=$api_key" >> .env
    fi
else
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
MCP_TRANSPORT=sse
MCP_HOST=0.0.0.0
MCP_PORT=8080
EOF

    chmod 600 .env
    echo "✓ Created .env file"
fi

echo ""

# Get port configuration
echo "🔧 HTTP Server Configuration"
echo "============================"
echo ""

DEFAULT_PORT=8080
read -p "Port to listen on [$DEFAULT_PORT]: " port
port=${port:-$DEFAULT_PORT}

# Update .env with port if changed
if [ "$port" != "8080" ]; then
    if grep -q "^MCP_PORT=" .env; then
        sed -i.bak "s/^MCP_PORT=.*/MCP_PORT=$port/" .env && rm .env.bak
    else
        echo "MCP_PORT=$port" >> .env
    fi
fi

echo "✓ Will listen on port: $port"
echo ""

# Build Docker image
echo "🐳 Building Docker Image"
echo "======================="
echo ""

docker build -f Dockerfile.http -t mcp-govee-http:latest .

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Docker image built successfully"
else
    echo ""
    echo "❌ Docker build failed"
    exit 1
fi

echo ""

# Start the container
echo "🚀 Starting HTTP Server"
echo "======================"
echo ""

# Stop existing container if running
if docker ps -a | grep -q mcp-govee-http; then
    echo "Stopping existing container..."
    docker stop mcp-govee-http 2>/dev/null || true
    docker rm mcp-govee-http 2>/dev/null || true
fi

# Start new container
docker run -d \
  --name mcp-govee-http \
  -p $port:8080 \
  --env-file .env \
  --restart unless-stopped \
  mcp-govee-http:latest

if [ $? -eq 0 ]; then
    echo "✓ HTTP server started successfully"
else
    echo "❌ Failed to start HTTP server"
    exit 1
fi

# Wait a moment for server to start
sleep 3

# Test the server
echo ""
echo "🧪 Testing Server"
echo "================"
echo ""

if curl -s -f http://localhost:$port/health > /dev/null 2>&1; then
    echo "✓ Server health check passed"
else
    echo "⚠️  Health check failed (this is normal if health endpoint not fully implemented)"
    echo "   Checking if server is running..."
    if docker ps | grep -q mcp-govee-http; then
        echo "✓ Container is running"
    else
        echo "❌ Container is not running"
        echo "   Check logs: docker logs mcp-govee-http"
        exit 1
    fi
fi

echo ""

# Get IP address
echo "🌐 Network Information"
echo "====================="
echo ""

IP_ADDR=$(hostname -I | awk '{print $1}')

if [ -z "$IP_ADDR" ]; then
    echo "⚠️  Could not detect IP address automatically"
    read -p "Enter this server's IP address: " IP_ADDR
fi

echo "Server IP Address: $IP_ADDR"
echo "SSE Endpoint: http://$IP_ADDR:$port/sse"
echo ""

# Firewall reminder
echo "🔥 Firewall Configuration"
echo "========================"
echo ""
echo "You need to open port $port in your firewall:"
echo ""
echo "For SUSE/openSUSE:"
echo "  sudo firewall-cmd --permanent --add-port=$port/tcp"
echo "  sudo firewall-cmd --reload"
echo ""
echo "For Ubuntu:"
echo "  sudo ufw allow $port/tcp"
echo ""
echo "Or restrict to your laptop's IP:"
echo "  sudo firewall-cmd --permanent --add-rich-rule='rule family=\"ipv4\" source address=\"YOUR_LAPTOP_IP\" port protocol=\"tcp\" port=\"$port\" accept'"
echo "  sudo firewall-cmd --reload"
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
echo "      \"url\": \"http://$IP_ADDR:$port/sse\","
echo "      \"transport\": \"sse\""
echo "    }"
echo "  }"
echo "}"
echo ""

# Save config to file
cat > claude-desktop-http-config.json <<EOF
{
  "mcpServers": {
    "govee": {
      "url": "http://$IP_ADDR:$port/sse",
      "transport": "sse"
    }
  }
}
EOF

echo "✓ Configuration saved to: claude-desktop-http-config.json"
echo ""

# Final summary
echo "✅ Setup Complete!"
echo "================="
echo ""
echo "Next steps:"
echo ""
echo "1. Open firewall port $port (see commands above)"
echo ""
echo "2. Test from your laptop:"
echo "   curl http://$IP_ADDR:$port/health"
echo ""
echo "3. Copy the configuration from:"
echo "   $(pwd)/claude-desktop-http-config.json"
echo "   to your Claude Desktop config on your laptop"
echo ""
echo "4. Restart Claude Desktop on your laptop"
echo ""
echo "5. Test by asking Claude to control your Govee lamp!"
echo ""
echo "Useful commands:"
echo "  View logs:    docker logs -f mcp-govee-http"
echo "  Stop server:  docker stop mcp-govee-http"
echo "  Start server: docker start mcp-govee-http"
echo "  Restart:      docker restart mcp-govee-http"
echo ""
echo "For detailed instructions, see HTTP_SETUP.md"
echo ""
