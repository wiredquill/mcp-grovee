# Remote MCP Server Setup

This guide explains how to use the MCP Govee server running on a remote machine with Claude Desktop on your local laptop.

## Overview

The MCP server is deployed on a remote machine (different IP than Claude Desktop). Since MCP uses stdio transport, we need to use SSH to connect Claude Desktop to the remote server.

## Prerequisites

- MCP server deployed and working on remote machine
- SSH access from your laptop to the remote machine
- SSH key-based authentication configured (passwordless)

## Option 1: SSH + Docker (Recommended)

This runs the Docker container on the remote machine via SSH.

### Step 1: Configure SSH Key-Based Authentication

On your laptop:

```bash
# Generate SSH key if you don't have one
ssh-keygen -t ed25519 -C "your_email@example.com"

# Copy your public key to the remote machine
ssh-copy-id user@remote-machine-ip

# Test passwordless SSH
ssh user@remote-machine-ip "echo SSH works"
```

**CRITICAL**: SSH must work without password prompts, or Claude Desktop won't be able to connect.

### Step 2: Configure Claude Desktop

Edit your Claude Desktop configuration file:
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

Add this configuration:

```json
{
  "mcpServers": {
    "govee": {
      "command": "ssh",
      "args": [
        "user@192.168.1.100",
        "docker",
        "run",
        "-i",
        "--rm",
        "--env-file",
        "/data/mcp-grovee/.env",
        "mcp-govee:latest"
      ]
    }
  }
}
```

**Replace:**
- `user` with your SSH username on the remote machine
- `192.168.1.100` with the actual IP address of the remote machine
- `/data/mcp-grovee/.env` with the actual path to your .env file on the remote machine

### Step 3: Test the Connection

1. Test SSH works from terminal:
   ```bash
   ssh user@remote-machine-ip "docker run -i --rm --env-file /data/mcp-grovee/.env mcp-govee:latest"
   ```

2. Restart Claude Desktop

3. Open Claude Desktop and try:
   - "Turn on my Govee lamp"
   - "List my Govee devices"

## Option 2: SSH + Python Directly

If you want to run Python directly instead of Docker:

```json
{
  "mcpServers": {
    "govee": {
      "command": "ssh",
      "args": [
        "user@remote-machine-ip",
        "cd /data/mcp-grovee && python3 -m src.server"
      ],
      "env": {
        "GOVEE_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

**Note**: Environment variables passed from Claude Desktop may not work over SSH. Use the .env file on the remote machine instead.

## Option 3: SSH with Custom Script (Most Reliable)

Create a wrapper script on the remote machine for easier management.

### On the Remote Machine:

Create `/usr/local/bin/mcp-govee.sh`:

```bash
#!/bin/bash
# MCP Govee Server Launcher
cd /data/mcp-grovee
docker run -i --rm --env-file .env mcp-govee:latest
```

Make it executable:

```bash
chmod +x /usr/local/bin/mcp-govee.sh
```

### On Your Laptop (Claude Desktop Config):

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

This is cleaner and easier to debug.

## Troubleshooting

### Issue: "Permission denied (publickey)"

**Problem**: SSH key authentication not set up

**Solution**:
```bash
ssh-copy-id user@remote-machine-ip
# Or manually copy your public key to remote ~/.ssh/authorized_keys
```

### Issue: "Connection refused"

**Problem**: SSH not running on remote machine or firewall blocking

**Solution**:
```bash
# On remote machine, check SSH is running
sudo systemctl status sshd

# Check if SSH port (22) is open
sudo firewall-cmd --list-all  # SUSE/openSUSE
```

### Issue: Claude Desktop shows "Server not responding"

**Problem**: SSH command failing or Docker image not found

**Solution**:
```bash
# Test the exact command manually
ssh user@remote-machine-ip "docker images | grep mcp-govee"
ssh user@remote-machine-ip "docker run -i --rm --env-file /data/mcp-grovee/.env mcp-govee:latest"
```

### Issue: "Permission denied" for .env file

**Problem**: SSH user can't read the .env file

**Solution**:
```bash
# On remote machine
sudo chown user:user /data/mcp-grovee/.env
chmod 600 /data/mcp-grovee/.env
```

### Issue: Claude Desktop freezes or hangs

**Problem**: SSH is prompting for password (can't be interactive)

**Solution**:
- Ensure SSH key-based authentication works
- Test: `ssh user@remote-machine-ip "echo test"` should work without password prompt

### Issue: "docker: command not found"

**Problem**: Docker not in PATH for non-interactive SSH sessions

**Solution**:
```bash
# On remote machine, add to ~/.bashrc or ~/.bash_profile
export PATH=$PATH:/usr/bin:/usr/local/bin

# Or use full path in Claude config
"args": ["user@remote-ip", "/usr/bin/docker", "run", ...]
```

## SSH Configuration Tips

### Use SSH Config File

Create or edit `~/.ssh/config` on your laptop:

```ssh-config
Host govee-server
    HostName 192.168.1.100
    User your-username
    IdentityFile ~/.ssh/id_ed25519
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
```

Then in Claude Desktop config:

```json
{
  "mcpServers": {
    "govee": {
      "command": "ssh",
      "args": [
        "govee-server",
        "/usr/local/bin/mcp-govee.sh"
      ]
    }
  }
}
```

This is cleaner and easier to manage.

## Security Considerations

### SSH Key Security

- Use strong SSH keys (ed25519 or RSA 4096)
- Protect your private key with a passphrase (optional, but may complicate Claude Desktop usage)
- Restrict SSH key to specific commands if possible

### Firewall Configuration

Only allow SSH from your laptop's IP:

```bash
# On remote machine (SUSE/openSUSE)
sudo firewall-cmd --permanent --add-rich-rule='rule family="ipv4" source address="YOUR_LAPTOP_IP" service name="ssh" accept'
sudo firewall-cmd --reload
```

### Environment Variables

- Store API keys in .env file on remote machine (not in Claude Desktop config)
- Protect .env file: `chmod 600 /data/mcp-grovee/.env`
- Never commit .env to git

## Performance Notes

### Latency

- SSH adds ~10-50ms latency per command
- Local network: minimal impact
- Internet/VPN: may be noticeable

### Connection Pooling

- SSH connection is created for each MCP request
- Consider keeping container running if performance is an issue

## Alternative: HTTP Transport (Future)

For better performance over network, consider implementing HTTP/WebSocket transport:

1. Modify the MCP server to support HTTP transport
2. Use nginx or similar as reverse proxy
3. Add TLS/SSL for security
4. Configure Claude Desktop to use HTTP endpoint

This is not currently implemented but would be better for remote access.

## Testing Checklist

Before using with Claude Desktop:

- [ ] SSH works without password: `ssh user@remote-ip "echo test"`
- [ ] Docker is accessible: `ssh user@remote-ip "docker ps"`
- [ ] Image exists: `ssh user@remote-ip "docker images | grep mcp-govee"`
- [ ] Container runs: `ssh user@remote-ip "docker run -i --rm --env-file /path/.env mcp-govee:latest"`
- [ ] .env file is readable by SSH user
- [ ] GOVEE_API_KEY is set in remote .env file
- [ ] Claude Desktop config updated with correct paths
- [ ] Claude Desktop restarted

## Example Complete Setup

### Remote Machine (192.168.1.100)

```bash
# Build image
cd /data/mcp-grovee
docker build -t mcp-govee:latest .

# Create .env
cat > .env <<EOF
GOVEE_API_KEY=your_actual_api_key_here
GOVEE_DEVICE_ADDRESS=
GOVEE_DEVICE_MODEL=
EOF

chmod 600 .env

# Create launcher script
sudo tee /usr/local/bin/mcp-govee.sh > /dev/null <<'EOF'
#!/bin/bash
cd /data/mcp-grovee
docker run -i --rm --env-file .env mcp-govee:latest
EOF

sudo chmod +x /usr/local/bin/mcp-govee.sh

# Test it works
/usr/local/bin/mcp-govee.sh
```

### Your Laptop

```bash
# Set up SSH key
ssh-copy-id user@192.168.1.100

# Test SSH
ssh user@192.168.1.100 "/usr/local/bin/mcp-govee.sh"

# Edit Claude Desktop config
# macOS:
code ~/Library/Application\ Support/Claude/claude_desktop_config.json

# Add:
{
  "mcpServers": {
    "govee": {
      "command": "ssh",
      "args": [
        "user@192.168.1.100",
        "/usr/local/bin/mcp-govee.sh"
      ]
    }
  }
}

# Restart Claude Desktop
```

## Questions?

If you encounter issues:

1. Test each component separately (SSH, Docker, .env)
2. Check logs on remote machine: `journalctl -xe`
3. Verify Claude Desktop logs (if available)
4. Test the exact SSH command manually first

## Next Steps

Once working:
- Consider setting up the Kubernetes deployment for production
- Implement proper logging on the remote server
- Set up monitoring for the container
- Configure automatic container restart policies
