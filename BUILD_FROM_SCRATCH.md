# Building MCP Govee Controller from Scratch

This guide walks through building this MCP server project from scratch, explaining each component and decision along the way.

## Table of Contents

1. [Project Overview](#project-overview)
2. [Prerequisites](#prerequisites)
3. [Step 1: Project Initialization](#step-1-project-initialization)
4. [Step 2: Understanding MCP](#step-2-understanding-mcp)
5. [Step 3: Govee API Integration](#step-3-govee-api-integration)
6. [Step 4: Building the MCP Server](#step-4-building-the-mcp-server)
7. [Step 5: Containerization](#step-5-containerization)
8. [Step 6: Kubernetes Deployment](#step-6-kubernetes-deployment)
9. [Step 7: Client Integration](#step-7-client-integration)
10. [Testing and Debugging](#testing-and-debugging)

## Project Overview

We're building an MCP (Model Context Protocol) server that allows AI assistants to control Govee smart lighting devices. The project uses:

- **Python 3.11+**: Core programming language
- **FastMCP**: Framework for building MCP servers
- **govee-api-laggat**: Python library for Govee API
- **SUSE BCI**: Base container image
- **Docker**: Containerization
- **Kubernetes**: Production deployment

## Prerequisites

Before starting, ensure you have:

- Python 3.11 or higher
- Docker Desktop or Docker Engine
- kubectl (for Kubernetes)
- A Govee API key from https://developer.govee.com/
- Basic understanding of Python, async/await, and containerization

## Step 1: Project Initialization

### 1.1 Create Project Structure

```bash
# Create project directory
mkdir mcp-grovee
cd mcp-grovee

# Initialize git repository
git init

# Create directory structure
mkdir -p src k8s
touch src/__init__.py
```

### 1.2 Create .gitignore

Create a `.gitignore` file to exclude sensitive and generated files:

```gitignore
# Python
__pycache__/
*.py[cod]
venv/
*.egg-info/

# Environment
.env

# IDE
.vscode/
.idea/

# OS
.DS_Store
```

### 1.3 Create .gitattributes

Ensure consistent line endings:

```gitattributes
* text=auto
```

## Step 2: Understanding MCP

### 2.1 What is MCP?

The Model Context Protocol (MCP) is a standard for connecting AI assistants to external data and tools. Key concepts:

- **Servers**: Provide tools and resources to clients
- **Tools**: Functions that AI assistants can call
- **Transport**: Communication layer (stdio, HTTP, WebSocket)
- **Resources**: Data that clients can access

### 2.2 Why FastMCP?

FastMCP is a Python framework that simplifies MCP server development:

- Decorator-based tool registration
- Automatic schema generation
- Built-in stdio transport
- Type safety with Python type hints

## Step 3: Govee API Integration

### 3.1 Understanding Govee API

Govee provides an API for controlling their smart devices:

- RESTful HTTP API
- Requires API key authentication
- Supports device discovery, state queries, and control
- Rate limiting applies

### 3.2 Choosing a Python Library

We use `govee-api-laggat` because:

- Active maintenance
- Async/await support
- Clean, Pythonic API
- Handles authentication and rate limiting

### 3.3 Creating requirements.txt

Create `requirements.txt` with dependencies:

```text
fastmcp>=0.2.0
govee-api-laggat>=0.2.2
python-dotenv>=1.0.0
httpx>=0.27.0
pydantic>=2.0.0
```

**Why these versions?**
- `fastmcp>=0.2.0`: Latest stable MCP implementation
- `govee-api-laggat>=0.2.2`: Latest available version with async support
- `python-dotenv`: Environment variable management
- `httpx`: Modern async HTTP client
- `pydantic`: Data validation

## Step 4: Building the MCP Server

### 4.1 Environment Configuration

Create `.env.example`:

```bash
GOVEE_API_KEY=your_govee_api_key_here
GOVEE_DEVICE_ADDRESS=
GOVEE_DEVICE_MODEL=
```

This allows users to configure:
- API authentication
- Specific device targeting (optional)

### 4.2 Core Server Implementation

Create `src/server.py`:

```python
#!/usr/bin/env python3
from fastmcp import FastMCP

# Initialize MCP server
mcp = FastMCP("govee-controller")

@mcp.tool()
async def turn_on() -> str:
    """Turn on the Govee lamp."""
    # Implementation here
    pass

if __name__ == "__main__":
    mcp.run()
```

**Key Design Decisions:**

1. **Async/await**: Govee API is async, so we use async tools
2. **Lazy initialization**: Create Govee client on first use
3. **Error handling**: Return user-friendly error messages
4. **Type hints**: Enable better tooling and validation

### 4.3 Implementing Tools

Each tool should:

1. Have a clear, descriptive name
2. Include a docstring (becomes tool description)
3. Use type hints for parameters
4. Return human-readable strings
5. Handle errors gracefully

Example tool:

```python
@mcp.tool()
async def set_brightness(brightness: int) -> str:
    """
    Set the brightness of the Govee lamp.

    Args:
        brightness: Brightness level from 0 to 100
    """
    try:
        # Validate input
        if not 0 <= brightness <= 100:
            return "✗ Error: Brightness must be between 0 and 100"

        # Get device and client
        device = await get_target_device()
        govee = await get_govee_client()

        # Execute command
        success, _ = await govee.set_brightness(device, brightness)

        # Return result
        if success:
            return f"✓ Brightness set to {brightness}%"
        else:
            return f"✗ Failed to set brightness"
    except Exception as e:
        return f"✗ Error: {str(e)}"
```

### 4.4 Device Discovery

Implement device selection logic:

```python
async def get_target_device() -> GoveeDevice:
    """Get device based on env config or first available."""
    govee = await get_govee_client()
    devices, _ = await govee.get_devices()

    # Filter by address/model if specified
    target_address = os.getenv("GOVEE_DEVICE_ADDRESS")
    target_model = os.getenv("GOVEE_DEVICE_MODEL")

    # Return matching device or first device
    # ... filtering logic ...
```

## Step 5: Containerization

### 5.1 Why SUSE BCI?

SUSE Base Container Images (BCI) offer:

- Minimal size
- Enterprise support
- Regular security updates
- Python 3.11 preinstalled

### 5.2 Dockerfile Design

Create `Dockerfile`:

```dockerfile
FROM registry.suse.com/bci/python:3.11

WORKDIR /app

# Install system dependencies
RUN zypper refresh && \
    zypper install -y --no-recommends gcc python311-devel && \
    zypper clean -a

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY src/ ./src/

# Create non-root user (SUSE-specific: create group first)
RUN groupadd -g 1000 mcp && \
    useradd -m -u 1000 -g mcp mcp && \
    chown -R mcp:mcp /app
USER mcp

# Run server
CMD ["python", "-m", "src.server"]
```

**Best Practices Applied:**

1. **Layer caching**: Dependencies before code
2. **Security**: Non-root user
3. **Minimal size**: Clean package cache
4. **Build dependencies**: gcc for compiling Python packages
5. **SUSE compatibility**: Explicitly create group before user (SUSE's useradd doesn't auto-create matching group)

### 5.3 Docker Compose for Testing

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  mcp-govee:
    build: .
    env_file: .env
    stdin_open: true  # Required for stdio transport
    tty: true
```

**Why stdin_open and tty?**
MCP uses stdio (standard input/output) for communication, so we need interactive mode.

## Step 6: Kubernetes Deployment

### 6.1 Namespace

Create `k8s/namespace.yaml`:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: mcp-govee
```

Namespaces provide:
- Resource isolation
- Access control boundaries
- Organization

### 6.2 Secrets Management

Create `k8s/secret.yaml`:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: govee-credentials
  namespace: mcp-govee
type: Opaque
stringData:
  GOVEE_API_KEY: "your_key_here"
```

**Production Considerations:**
- Use external secret management (Vault, AWS Secrets Manager)
- Implement secret rotation
- Never commit secrets to git

### 6.3 Deployment

Create `k8s/deployment.yaml`:

Key features:
- **Single replica**: Avoid conflicting commands to device
- **Recreate strategy**: No overlap between old/new pods
- **Resource limits**: Prevent resource exhaustion
- **Security context**: Non-root, read-only filesystem
- **Health checks**: Liveness and readiness probes

```yaml
spec:
  replicas: 1
  strategy:
    type: Recreate
  template:
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
```

### 6.4 Service

Create `k8s/service.yaml`:

- **ClusterIP**: Internal cluster access
- **NodePort**: External access for testing
- **Session affinity**: Maintain connection state

### 6.5 Kustomize

Create `k8s/kustomization.yaml` for:
- Image management
- Environment-specific configs
- Label management

## Step 7: Client Integration

### 7.1 Claude Desktop

Configuration location:
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

Configuration format:

```json
{
  "mcpServers": {
    "govee": {
      "command": "python",
      "args": ["-m", "src.server"],
      "cwd": "/absolute/path/to/mcp-grovee",
      "env": {
        "GOVEE_API_KEY": "your_key_here"
      }
    }
  }
}
```

### 7.2 n8n Integration

For n8n, you'll need to:

1. Expose HTTP/WebSocket transport (future enhancement)
2. Deploy to accessible endpoint
3. Use HTTP Request nodes in n8n workflows

## Testing and Debugging

### Local Testing

1. **Direct Python execution:**
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   python -m src.server
   ```

2. **Docker testing:**
   ```bash
   docker build -t mcp-govee:latest .
   docker run -i --rm --env-file .env mcp-govee:latest
   ```

3. **MCP Inspector:**
   ```bash
   npx @modelcontextprotocol/inspector python -m src.server
   ```

### Kubernetes Testing

1. **Deploy to cluster:**
   ```bash
   kubectl apply -k k8s/
   ```

2. **Check logs:**
   ```bash
   kubectl logs -n mcp-govee deployment/mcp-govee-server -f
   ```

3. **Test connectivity:**
   ```bash
   kubectl exec -n mcp-govee deployment/mcp-govee-server -- python -c "import src.server"
   ```

### Common Issues

**"No module named 'fastmcp'"**
- Ensure dependencies are installed
- Check virtual environment is activated

**"GOVEE_API_KEY not found"**
- Verify .env file exists
- Check environment variables are loaded

**"No devices found"**
- Verify API key is correct
- Check devices are set up in Govee app

**Kubernetes pod CrashLoopBackOff**
- Check logs: `kubectl logs -n mcp-govee <pod-name>`
- Verify secrets are created
- Check image is available

## Advanced Topics

### Adding New Tools

1. Define async function with `@mcp.tool()` decorator
2. Add type hints and docstring
3. Implement error handling
4. Test with MCP Inspector

### HTTP Transport

To add HTTP/WebSocket support:

1. Install additional dependencies (uvicorn, websockets)
2. Implement transport layer
3. Update Kubernetes service for HTTP
4. Add Ingress/LoadBalancer

### Multi-Device Support

To control multiple devices:

1. Add device parameter to tools
2. Implement device caching
3. Update Kubernetes for horizontal scaling
4. Add device discovery tools

### Monitoring

Add observability:

1. Prometheus metrics
2. Structured logging
3. Tracing (OpenTelemetry)
4. Health check endpoints

## Production Checklist

Before deploying to production:

- [ ] Use external secret management
- [ ] Implement proper logging
- [ ] Add monitoring and alerting
- [ ] Set up CI/CD pipeline
- [ ] Configure resource limits
- [ ] Implement rate limiting
- [ ] Add authentication/authorization
- [ ] Set up backup and disaster recovery
- [ ] Document runbooks
- [ ] Configure network policies
- [ ] Set up TLS/SSL
- [ ] Implement graceful shutdown

## Resources

- [MCP Specification](https://modelcontextprotocol.io/)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [Govee API Documentation](https://developer.govee.com/)
- [SUSE BCI Documentation](https://registry.suse.com/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)

## Next Steps

1. Extend with more Govee features (scenes, schedules)
2. Add support for other Govee device types
3. Implement HTTP/WebSocket transport
4. Create web UI for device management
5. Add integration tests
6. Set up CI/CD pipeline
7. Publish to container registry
8. Create Helm chart

## Contributing

To contribute to this project:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Update documentation
6. Submit a pull request

## Support

For questions or issues:
- Check existing GitHub issues
- Review the main README.md
- Consult MCP and Govee API documentation
