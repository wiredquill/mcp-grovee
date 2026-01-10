# Use SUSE BCI Python 3.11 as base image
FROM registry.suse.com/bci/python:3.11

# Set working directory
WORKDIR /app

# Install system dependencies if needed
RUN zypper refresh && \
    zypper install -y --no-recommends \
    gcc \
    python311-devel && \
    zypper clean -a

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY src/ ./src/

# Create non-root user for security
RUN useradd -m -u 1000 mcp && \
    chown -R mcp:mcp /app

# Switch to non-root user
USER mcp

# Set Python path
ENV PYTHONPATH=/app

# Expose port (optional, for future HTTP/WebSocket support)
EXPOSE 8080

# Run the MCP server
CMD ["python", "-m", "src.server"]
