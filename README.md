# MCP Govee Controller

A Model Context Protocol (MCP) server for controlling Govee RGBIC smart lighting devices. This server enables AI assistants like Claude to control your Govee lights through natural language commands.

## Features

- Control Govee RGBIC cylinder floor lamp (and other Govee devices)
- Turn lights on/off
- Adjust brightness (0-100%)
- Set RGB colors
- Set color temperature
- Use preset colors (red, green, blue, yellow, cyan, magenta, white, warm_white, orange, purple, pink)
- Query device state
- List all available Govee devices

## Prerequisites

- Govee API Key ([Get one here](https://developer.govee.com/))
- Python 3.11+ OR Docker
- Your Govee device(s) set up in the Govee Home app

## Quick Start

### Option 1: Using Docker (Recommended)

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/mcp-grovee.git
   cd mcp-grovee
   ```

2. Create a `.env` file:
   ```bash
   cp .env.example .env
   ```

3. Edit `.env` and add your Govee API key:
   ```bash
   GOVEE_API_KEY=your_govee_api_key_here
   ```

4. Build the Docker image:
   ```bash
   docker build -t mcp-govee:latest .
   ```

5. Test the server:
   ```bash
   docker run -i --rm --env-file .env mcp-govee:latest
   ```

### Option 2: Using Python Virtual Environment

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/mcp-grovee.git
   cd mcp-grovee
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file:
   ```bash
   cp .env.example .env
   ```

5. Edit `.env` and add your Govee API key:
   ```bash
   GOVEE_API_KEY=your_govee_api_key_here
   ```

6. Run the server:
   ```bash
   python -m src.server
   ```

## Configuration

### Environment Variables

- `GOVEE_API_KEY` (required): Your Govee API key from https://developer.govee.com/
- `GOVEE_DEVICE_ADDRESS` (optional): Specific device MAC address (without colons) to control
- `GOVEE_DEVICE_MODEL` (optional): Specific device model to control

If device address and model are not specified, the server will control the first available device.

## Integration

### Claude Desktop

To use this MCP server with Claude Desktop:

#### Local Setup (Server on Same Machine)

1. Locate your Claude Desktop configuration file:
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
   - Linux: `~/.config/Claude/claude_desktop_config.json`

2. Add the MCP server configuration:

   **Using Python directly:**
   ```json
   {
     "mcpServers": {
       "govee": {
         "command": "python3",
         "args": ["-m", "src.server"],
         "cwd": "/absolute/path/to/mcp-grovee",
         "env": {
           "GOVEE_API_KEY": "your_govee_api_key_here"
         }
       }
     }
   }
   ```

   **Using Docker:**
   ```json
   {
     "mcpServers": {
       "govee": {
         "command": "docker",
         "args": [
           "run",
           "-i",
           "--rm",
           "--env-file",
           "/absolute/path/to/mcp-grovee/.env",
           "mcp-govee:latest"
         ]
       }
     }
   }
   ```

#### Remote Setup (Server on Different Machine)

**If the MCP server is deployed on a remote machine**, you have two options:

##### Option 1: HTTP/SSE Transport (Recommended ⭐)

The cleanest way to access a remote MCP server. See [HTTP_SETUP.md](HTTP_SETUP.md) for detailed instructions.

**On remote machine:**
```bash
docker-compose -f docker-compose-http.yml up -d
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

**Advantages:**
- ✅ Simpler setup
- ✅ Better performance
- ✅ No SSH key management
- ✅ Works through firewalls easily

See [HTTP_SETUP.md](HTTP_SETUP.md) for complete HTTP/SSE setup guide.

##### Option 2: SSH Transport

Alternative method using SSH. See [REMOTE_SETUP.md](REMOTE_SETUP.md) for detailed instructions.

```json
{
  "mcpServers": {
    "govee": {
      "command": "ssh",
      "args": [
        "user@remote-machine-ip",
        "/usr/local/bin/mcp-govee.sh"
      ]
    }
  }
}
```

**When to use SSH:**
- You don't want to expose an HTTP port
- You already have SSH configured
- See [REMOTE_SETUP.md](REMOTE_SETUP.md) for complete SSH setup guide

3. Restart Claude Desktop

4. Start a conversation and try commands like:
   - "Turn on my Govee lamp"
   - "Set the lamp to blue"
   - "Set brightness to 50%"
   - "What's the current state of my lamp?"

### n8n Integration

To use with n8n:

1. Deploy the MCP server to a Kubernetes cluster (see Kubernetes Deployment section)
2. In n8n, use the HTTP Request node to communicate with the MCP server
3. The server exposes MCP tools that can be called via HTTP (future enhancement)

For now, n8n integration requires implementing an HTTP/WebSocket transport layer for the MCP server.

## Available Tools

The MCP server provides the following tools:

| Tool | Description | Parameters |
|------|-------------|------------|
| `turn_on` | Turn on the Govee lamp | None |
| `turn_off` | Turn off the Govee lamp | None |
| `set_brightness` | Set brightness level | `brightness` (0-100) |
| `set_color` | Set RGB color | `red`, `green`, `blue` (0-255) |
| `set_color_temperature` | Set color temperature | `temperature` (2000-9000K) |
| `set_preset_color` | Set a preset color | `color_name` (red, green, blue, etc.) |
| `get_device_state` | Get current device state | None |
| `list_devices` | List all Govee devices | None |

## Kubernetes Deployment

For production deployment to Kubernetes:

1. Build and push the Docker image:
   ```bash
   docker build -t your-registry.com/mcp-govee:latest .
   docker push your-registry.com/mcp-govee:latest
   ```

2. Update `k8s/secret.yaml` with your Govee API key

3. Update `k8s/kustomization.yaml` with your image registry

4. Deploy using kubectl:
   ```bash
   kubectl apply -k k8s/
   ```

Or using kustomize:
   ```bash
   kustomize build k8s/ | kubectl apply -f -
   ```

5. Verify the deployment:
   ```bash
   kubectl get pods -n mcp-govee
   kubectl logs -n mcp-govee deployment/mcp-govee-server
   ```

## Troubleshooting

### "GOVEE_API_KEY not found"
Make sure you've created a `.env` file with your API key or set the environment variable.

### "No Govee devices found"
- Verify your API key is correct
- Ensure your Govee devices are set up in the Govee Home app
- Check that your devices support the Govee API (most newer devices do)

### "Failed to turn on lamp"
- Check that the device is online
- Verify the device is controllable via the Govee API
- Some devices may have rate limiting - wait a few seconds between commands

### Device not responding
- Ensure your device has a stable internet connection
- Check the Govee API status
- Verify the device is controllable through the official Govee app

## Development

To modify or extend this MCP server:

1. Fork this repository
2. Make your changes to `src/server.py`
3. Test locally using the Quick Start instructions
4. Submit a pull request

See [BUILD_FROM_SCRATCH.md](BUILD_FROM_SCRATCH.md) for detailed development instructions.

## Security Notes

- Never commit your `.env` file or API keys to version control
- In production, use Kubernetes Secrets or a secret management solution
- The Docker container runs as a non-root user for security
- Consider using network policies in Kubernetes to restrict access

## License

MIT License - See LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and questions:
- Open an issue on GitHub
- Check the [BUILD_FROM_SCRATCH.md](BUILD_FROM_SCRATCH.md) guide for development details

## Acknowledgments

- Built with [FastMCP](https://github.com/jlowin/fastmcp)
- Uses [govee-api-laggat](https://github.com/LaggAt/python-govee-api) for Govee API integration
- Follows the [Model Context Protocol](https://modelcontextprotocol.io/) specification
