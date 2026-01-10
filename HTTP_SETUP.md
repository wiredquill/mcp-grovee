# HTTP/SSE Transport Setup

This guide explains how to use the MCP Govee server with HTTP/SSE transport for remote access. This is the **recommended approach** for accessing the server from a different machine than where it's deployed.

## Why HTTP/SSE Transport?

**Advantages over SSH:**
- ✅ Simpler configuration
- ✅ No SSH key management required
- ✅ Better performance over network
- ✅ Works through firewalls more easily
- ✅ Can use reverse proxy/load balancer
- ✅ Native MCP protocol support

**When to use SSH instead:**
- You don't want to expose a port
- You already have SSH configured
- Security is paramount and you don't want HTTP exposed

## Quick Start

### Option 1: Docker Compose (Easiest)

**On the remote machine:**

```bash
# Build and start the HTTP server
docker-compose -f docker-compose-http.yml up -d

# Check it's running
curl http://localhost:8080/health
```

**On your laptop (Claude Desktop config):**

```json
{
  "mcpServers": {
    "govee": {
      "url": "http://192.168.1.100:8080/sse",
      "transport": "sse"
    }
  }
}
```

Replace `192.168.1.100` with your remote machine's IP address.

### Option 2: Docker Run

**On the remote machine:**

```bash
# Build the HTTP image
docker build -f Dockerfile.http -t mcp-govee-http:latest .

# Run the container
docker run -d \
  --name mcp-govee-http \
  -p 8080:8080 \
  --env-file .env \
  --restart unless-stopped \
  mcp-govee-http:latest
```

### Option 3: Python Directly

**On the remote machine:**

```bash
# Set environment variable for HTTP transport
export MCP_TRANSPORT=sse
export MCP_HOST=0.0.0.0
export MCP_PORT=8080

# Run the server
python3 -m src.server --sse
```

Or add to your `.env` file:

```bash
MCP_TRANSPORT=sse
MCP_HOST=0.0.0.0
MCP_PORT=8080
```

## Claude Desktop Configuration

Edit your Claude Desktop config file:
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

### Basic Configuration

```json
{
  "mcpServers": {
    "govee": {
      "url": "http://remote-machine-ip:8080/sse",
      "transport": "sse"
    }
  }
}
```

### With Custom Port

```json
{
  "mcpServers": {
    "govee": {
      "url": "http://192.168.1.100:8888/sse",
      "transport": "sse"
    }
  }
}
```

## Firewall Configuration

You need to open port 8080 (or your custom port) on the remote machine.

### SUSE/openSUSE (firewalld)

```bash
# Open port 8080
sudo firewall-cmd --permanent --add-port=8080/tcp
sudo firewall-cmd --reload

# Verify
sudo firewall-cmd --list-ports
```

### Ubuntu (ufw)

```bash
# Open port 8080
sudo ufw allow 8080/tcp
sudo ufw reload
```

### Restrict to Specific IP (Recommended)

```bash
# SUSE/openSUSE - Only allow from your laptop's IP
sudo firewall-cmd --permanent --add-rich-rule='rule family="ipv4" source address="YOUR_LAPTOP_IP" port protocol="tcp" port="8080" accept'
sudo firewall-cmd --reload

# Ubuntu - Only allow from your laptop's IP
sudo ufw allow from YOUR_LAPTOP_IP to any port 8080 proto tcp
```

## Security Best Practices

### 1. Use HTTPS with Reverse Proxy

For production or internet-facing deployments, use a reverse proxy with TLS:

```nginx
# nginx configuration
server {
    listen 443 ssl http2;
    server_name mcp.yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location /sse {
        proxy_pass http://localhost:8080/sse;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 86400;
    }

    location /health {
        proxy_pass http://localhost:8080/health;
    }
}
```

Then in Claude Desktop config:

```json
{
  "mcpServers": {
    "govee": {
      "url": "https://mcp.yourdomain.com/sse",
      "transport": "sse"
    }
  }
}
```

### 2. Use Authentication (Future Enhancement)

Currently, the server doesn't have built-in authentication. For now:
- Only expose on trusted networks
- Use firewall rules to restrict access
- Use SSH tunneling for untrusted networks

### 3. Use VPN/Tailscale

For remote access over the internet:

```bash
# Install Tailscale on both machines
# Access via Tailscale IP: http://100.x.x.x:8080/sse
```

## Kubernetes Deployment with HTTP

Update the Kubernetes service to expose HTTP:

```yaml
# k8s/service-http.yaml
apiVersion: v1
kind: Service
metadata:
  name: mcp-govee-http
  namespace: mcp-govee
spec:
  type: LoadBalancer  # or NodePort for local cluster
  selector:
    app: mcp-govee
    component: server
  ports:
  - name: http
    port: 8080
    targetPort: 8080
    protocol: TCP
```

Update deployment environment:

```yaml
# k8s/deployment.yaml
env:
- name: MCP_TRANSPORT
  value: "sse"
- name: MCP_HOST
  value: "0.0.0.0"
- name: MCP_PORT
  value: "8080"
```

## Testing

### 1. Test Health Endpoint

```bash
# From the remote machine
curl http://localhost:8080/health

# From your laptop
curl http://remote-machine-ip:8080/health
```

### 2. Test SSE Endpoint

```bash
# This should return SSE headers
curl -N http://remote-machine-ip:8080/sse
```

### 3. Test with Claude Desktop

1. Restart Claude Desktop
2. Open Claude
3. Try: "List my Govee devices"

## Troubleshooting

### Issue: "Connection refused"

**Problem**: Port not open or service not running

**Solutions:**
```bash
# Check if port is listening
sudo netstat -tlnp | grep 8080

# Check Docker container is running
docker ps | grep mcp-govee

# Check firewall
sudo firewall-cmd --list-all
```

### Issue: "Timeout" or "Cannot connect"

**Problem**: Firewall blocking connection

**Solutions:**
```bash
# Check firewall allows port 8080
sudo firewall-cmd --list-ports

# Add port if missing
sudo firewall-cmd --permanent --add-port=8080/tcp
sudo firewall-cmd --reload
```

### Issue: Claude Desktop shows "Server not responding"

**Problem**: Wrong URL or SSE endpoint not working

**Solutions:**
```bash
# Test SSE endpoint
curl -v http://remote-machine-ip:8080/sse

# Check Claude Desktop config has correct URL
# Should be: "url": "http://IP:8080/sse"

# Check logs
docker logs mcp-govee-http
```

### Issue: "Health check failing"

**Problem**: Health endpoint not implemented

**Note**: The basic health check is simple. If it fails:

```bash
# Check the server is running
docker exec mcp-govee-http python3 -c "print('Server is up')"

# Check logs
docker logs mcp-govee-http
```

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `sse` |
| `MCP_HOST` | `0.0.0.0` | Host to bind (0.0.0.0 for all interfaces) |
| `MCP_PORT` | `8080` | Port to listen on |
| `GOVEE_API_KEY` | (required) | Your Govee API key |
| `GOVEE_DEVICE_ADDRESS` | (optional) | Specific device address |
| `GOVEE_DEVICE_MODEL` | (optional) | Specific device model |

## Performance Notes

### Latency

- Local network: ~10-30ms
- Internet: Depends on connection, typically 50-200ms
- Keep-alive connections reduce overhead

### Connection Pooling

SSE maintains a persistent connection, which is more efficient than SSH for repeated commands.

### Scaling

For multiple clients or high load, consider:
- Using a load balancer
- Running multiple replicas in Kubernetes
- Implementing connection pooling

## Comparison: SSH vs HTTP

| Feature | SSH | HTTP/SSE |
|---------|-----|----------|
| Setup complexity | Medium | Easy |
| Performance | Good | Better |
| Firewall friendly | Medium | High |
| Authentication | SSH keys | None (add reverse proxy) |
| Multiple clients | One per SSH | Multiple per server |
| Load balancing | No | Yes |
| HTTPS support | Via tunnel | Native with proxy |

## Next Steps

After setting up HTTP transport:

1. Test locally first: `http://localhost:8080/sse`
2. Open firewall port carefully
3. Consider using HTTPS with nginx/caddy
4. Monitor logs: `docker logs -f mcp-govee-http`
5. Set up monitoring/alerts for production

## Related Documentation

- [README.md](README.md) - Main documentation
- [REMOTE_SETUP.md](REMOTE_SETUP.md) - SSH-based setup
- [BUILD_FROM_SCRATCH.md](BUILD_FROM_SCRATCH.md) - Development guide
