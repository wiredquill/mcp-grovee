# Development Guidelines for AI Assistants

This document provides guidelines for AI assistants (like Claude) working on the MCP Govee Controller project.

---

## ⚠️ CRITICAL PLATFORM REQUIREMENTS ⚠️

**THIS PROJECT USES SUSE BCI (Base Container Images) - NOT Debian/Ubuntu**

Before writing ANY system-level commands:
1. ✅ **Verify commands are SUSE/openSUSE compatible**
2. ✅ **Use `zypper` (NOT `apt` or `apt-get`)**
3. ✅ **Use SUSE package names** (e.g., `python311-devel` NOT `python3-dev`)
4. ✅ **Create groups before users** (SUSE's `useradd` doesn't auto-create groups)
5. ✅ **Test on actual SUSE BCI image**

**See the "SUSE/openSUSE Platform Requirements" section below for complete details.**

---

## Package Version Policy

**IMPORTANT: Always use the latest available package versions unless there is a specific reason not to.**

### When to Use Latest Versions

- By default, always specify the latest stable version for all dependencies
- Use `>=` constraints to allow patch and minor version updates
- Check PyPI or the package repository for the actual latest version before specifying

### When NOT to Use Latest Versions

Only pin to older versions when:

1. **Breaking API Changes**: The latest version has breaking changes that require significant refactoring
2. **Dependency Conflicts**: The latest version conflicts with other required dependencies
3. **Known Bugs**: The latest version has critical bugs that affect our use case
4. **Platform Incompatibility**: The latest version doesn't support our target platforms (Python 3.11+, SUSE BCI)

### Version Verification Process

Before updating or adding dependencies:

1. Check the actual latest version on PyPI: `pip index versions <package-name>`
2. Review the package's changelog for breaking changes
3. Test that the version works with our code
4. Document any version constraints and the reason in requirements.txt comments

### Current Dependencies

```python
# requirements.txt
fastmcp>=0.2.0              # MCP framework - use latest stable
govee-api-laggat>=0.2.2     # Govee API - latest available (verified 2026-01)
python-dotenv>=1.0.0        # Env var management - stable API
httpx>=0.27.0               # HTTP client - use latest
pydantic>=2.0.0             # Data validation - v2 required for modern features
```

### Example: govee-api-laggat Version Issue

Initial specification was `govee-api-laggat>=0.3.0`, but the latest available version is 0.2.2.

**Corrected to**: `govee-api-laggat>=0.2.2`

**Lesson**: Always verify the actual latest version exists before specifying it.

## SUSE/openSUSE Platform Requirements

**CRITICAL: This project uses SUSE BCI (Base Container Images). Always verify commands are compatible with openSUSE and SUSE Enterprise Linux (SLE).**

### Platform Differences from Debian/Ubuntu

SUSE-based systems have significant differences from Debian/Ubuntu that you MUST account for:

| Area | Debian/Ubuntu | SUSE/openSUSE | Impact |
|------|---------------|---------------|--------|
| **Package Manager** | `apt`, `apt-get` | `zypper` | All package operations different |
| **User Management** | `useradd` auto-creates group | `useradd` requires explicit group | User creation fails without group |
| **Python Executable** | `python` or `python3` | `python3` only | CMD/scripts using `python` fail |
| **System Packages** | `python3-dev` | `python311-devel` | Build dependencies have different names |
| **Init System** | systemd (standard) | systemd (similar) | Mostly compatible |
| **Package Names** | Often `-dev` suffix | Often `-devel` suffix | Must translate package names |

### Mandatory Verification Process

**Before writing any system-level commands in Dockerfiles, scripts, or documentation:**

1. **Verify Package Names**
   ```bash
   # Search for packages in SUSE
   zypper search <package-name>

   # Get package info
   zypper info <package-name>
   ```

2. **Verify Command Syntax**
   - Don't assume commands work the same as Debian/Ubuntu
   - Check SUSE/openSUSE documentation
   - Test in a SUSE container if uncertain

3. **Test in Target Environment**
   ```bash
   # Spin up a test container
   docker run -it registry.suse.com/bci/python:3.11 /bin/bash

   # Test your commands
   zypper refresh
   zypper install -y gcc python311-devel
   groupadd -g 1000 testuser
   useradd -u 1000 -g testuser testuser
   ```

### SUSE-Specific Command Reference

#### Package Management

```bash
# Update package lists (equivalent to apt update)
zypper refresh

# Install packages (equivalent to apt install)
zypper install -y <package>

# Install without recommends (keep image small)
zypper install -y --no-recommends <package>

# Search for packages
zypper search <pattern>

# Clean package cache (reduce image size)
zypper clean -a

# List installed packages
zypper packages --installed-only
```

#### User Management

```bash
# CORRECT: Create group first, then user
groupadd -g 1000 username
useradd -m -u 1000 -g username username

# WRONG: This fails on SUSE (works on Debian/Ubuntu)
useradd -m -u 1000 username  # Error: group doesn't exist

# WRONG: -U flag may not work as expected
useradd -m -u 1000 -U username  # Unreliable across SUSE versions
```

#### Python Executable Path

```bash
# CORRECT: Use python3 in SUSE BCI images
CMD ["python3", "-m", "src.server"]
python3 --version

# WRONG: Using "python" directly (not available by default)
CMD ["python", "-m", "src.server"]  # Error: executable file not found in $PATH
python --version  # Command not found

# Note: pip, pip3 are typically available
pip install package
pip3 install package
```

**Why**: SUSE BCI Python images provide `python3` and `python3.11` but not a `python` symlink by default.

#### Common Package Name Translations

| Purpose | Debian/Ubuntu | SUSE/openSUSE |
|---------|---------------|---------------|
| Python dev headers | `python3-dev` | `python311-devel` |
| C compiler | `build-essential` | `gcc`, `make` |
| SSL/TLS | `libssl-dev` | `libopenssl-devel` |
| SQLite | `libsqlite3-dev` | `sqlite3-devel` |
| PostgreSQL | `libpq-dev` | `postgresql-devel` |
| MySQL | `libmysqlclient-dev` | `libmysqlclient-devel` |

### Dockerfile Best Practices for SUSE

```dockerfile
# Use SUSE BCI base image
FROM registry.suse.com/bci/python:3.11

# Package installation pattern
RUN zypper refresh && \
    zypper install -y --no-recommends \
    gcc \
    python311-devel \
    make && \
    zypper clean -a  # Always clean cache

# User creation pattern (CRITICAL)
RUN groupadd -g 1000 appuser && \
    useradd -m -u 1000 -g appuser appuser && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Run application (use python3, not python)
CMD ["python3", "-m", "src.server"]
```

### Testing Checklist

Before committing Dockerfile or system-level changes:

- [ ] Verified package names exist in SUSE repositories
- [ ] Tested zypper commands work (not apt commands)
- [ ] User/group creation uses explicit group creation
- [ ] Package names use SUSE naming conventions (-devel not -dev)
- [ ] Cleaned package cache with `zypper clean -a`
- [ ] Tested build on actual SUSE BCI image
- [ ] Verified non-root user creation works

### Common Mistakes to Avoid

❌ **WRONG - Using Debian/Ubuntu commands:**
```dockerfile
RUN apt update && apt install -y python3-dev
RUN useradd -m appuser  # Fails on SUSE
```

✅ **CORRECT - Using SUSE commands:**
```dockerfile
RUN zypper refresh && zypper install -y --no-recommends python311-devel
RUN groupadd -g 1000 appuser && useradd -m -u 1000 -g appuser appuser
```

❌ **WRONG - Assuming package names:**
```dockerfile
RUN zypper install -y python3-dev  # Doesn't exist on SUSE
```

✅ **CORRECT - Using actual SUSE package names:**
```dockerfile
RUN zypper install -y python311-devel  # Correct SUSE package
```

❌ **WRONG - Using `python` executable:**
```dockerfile
CMD ["python", "-m", "src.server"]  # Error: executable file not found in $PATH
```

✅ **CORRECT - Using `python3` executable:**
```dockerfile
CMD ["python3", "-m", "src.server"]  # Works on SUSE BCI
```

### When in Doubt

If you're unsure about a command or package name:

1. **Check the SUSE BCI documentation**: https://registry.suse.com/
2. **Test in a container**: `docker run -it registry.suse.com/bci/python:3.11 /bin/bash`
3. **Search SUSE packages**: https://software.opensuse.org/
4. **Consult openSUSE docs**: https://doc.opensuse.org/
5. **Ask the user** if verification isn't possible

### Real-World Example: User Creation Issue

**Problem encountered:**
```dockerfile
RUN useradd -m -u 1000 mcp && chown -R mcp:mcp /app
# Error: chown: invalid group: 'mcp:mcp'
```

**Root cause:** SUSE's `useradd` doesn't auto-create matching group

**Solution:**
```dockerfile
RUN groupadd -g 1000 mcp && \
    useradd -m -u 1000 -g mcp mcp && \
    chown -R mcp:mcp /app
```

**Prevention:** Always verify user management commands on target platform

## Code Maintenance Guidelines

### Python Version

- **Target**: Python 3.11+
- **Rationale**: Modern async features, performance improvements, type hinting enhancements
- Update to newer Python versions as they become stable and are supported by SUSE BCI

### Container Base Image

- **Current**: `registry.suse.com/bci/python:3.11`
- **Policy**: Use the latest Python version available in SUSE BCI registry
- **Check**: Regularly verify if Python 3.12 or 3.13 images are available

### Async/Await Patterns

- Always use async/await for I/O operations (API calls, file operations)
- Use `asyncio` best practices from the latest Python version
- Leverage modern async context managers and iterators

### Type Hints

- Use modern type hinting syntax (Python 3.11+ features)
- Prefer `|` union syntax over `Union[]`
- Use `Self` type for return types
- Leverage `TypedDict`, `Protocol`, and other modern typing features

### Error Handling

- Return user-friendly error messages from MCP tools
- Log detailed errors for debugging
- Never expose sensitive information in error messages
- Use structured logging (future enhancement)

### Security Best Practices

1. **Never commit secrets**: Use environment variables or secret management
2. **Run as non-root**: All containers must run as non-root users
3. **Minimal permissions**: Apply principle of least privilege
4. **Regular updates**: Keep dependencies updated for security patches
5. **Input validation**: Validate all user inputs (brightness, RGB values, etc.)

## Testing Requirements

### Before Committing Changes

1. **Local Testing**: Test with `python -m src.server`
2. **Docker Build**: Ensure `docker build .` succeeds
3. **MCP Inspector**: Test tools with MCP Inspector if available
4. **Claude Desktop**: Test integration with Claude Desktop if possible

### Test Checklist

- [ ] All MCP tools work as expected
- [ ] Error handling works correctly
- [ ] Docker image builds successfully
- [ ] Kubernetes manifests are valid (`kubectl apply --dry-run=client`)
- [ ] Documentation is updated
- [ ] No secrets or credentials in code

## Documentation Standards

### Code Comments

- Use docstrings for all public functions
- Include type hints for all parameters and return values
- Document error conditions and edge cases
- Keep comments up-to-date with code changes

### README Updates

When adding features:

1. Update the tools table in README.md
2. Add usage examples if the feature is significant
3. Update BUILD_FROM_SCRATCH.md if the implementation pattern changes
4. Update CONTRIBUTING.md if the development workflow changes

### Changelog (Future)

- Document all user-facing changes
- Use semantic versioning
- Include migration guides for breaking changes

## Adding New Features

### New MCP Tools

When adding a new tool:

```python
@mcp.tool()
async def new_tool_name(param: int) -> str:
    """
    Brief description of what this tool does.

    Args:
        param: Description of the parameter and valid range

    Returns:
        Success or error message in user-friendly format
    """
    try:
        # Input validation
        if param < 0 or param > 100:
            return "✗ Error: param must be between 0 and 100"

        # Get device and client
        device = await get_target_device()
        govee = await get_govee_client()

        # Execute operation
        success, _ = await govee.some_operation(device, param)

        # Return user-friendly result
        if success:
            return f"✓ Operation completed: {param}"
        else:
            return "✗ Failed to complete operation"

    except Exception as e:
        return f"✗ Error: {str(e)}"
```

### New Dependencies

Before adding a new dependency:

1. Verify it's necessary (avoid dependency bloat)
2. Check license compatibility (prefer MIT, Apache 2.0, BSD)
3. Verify maintenance status (recent commits, active issues)
4. Use the latest stable version
5. Add to requirements.txt with explanation comment
6. Update Dockerfile if system dependencies needed

## Kubernetes Configuration

### Resource Limits

- **Requests**: Conservative estimates (current: 128Mi RAM, 100m CPU)
- **Limits**: Reasonable maximums (current: 256Mi RAM, 500m CPU)
- **Rationale**: Prevent resource exhaustion, allow for bursts

### Security Context

Always include:
- `runAsNonRoot: true`
- `runAsUser: 1000`
- `allowPrivilegeEscalation: false`
- `readOnlyRootFilesystem: true`
- `capabilities.drop: [ALL]`

### Replica Count

- **Production**: 1 replica (avoid conflicting device commands)
- **Strategy**: Recreate (no overlap)
- **Future**: Consider leader election for HA

## Common Issues and Solutions

### Issue: Package Version Not Found

**Problem**: Specified version doesn't exist on PyPI

**Solution**:
1. Check actual available versions: `pip index versions package-name`
2. Update requirements.txt to use latest available
3. Test that the available version works
4. Update documentation

### Issue: Docker Build Fails

**Problem**: System dependencies missing or wrong

**Solution**:
1. Check base image has required compilers (gcc, python-devel)
2. Clean zypper cache to reduce image size
3. Use `--no-cache-dir` for pip to avoid cache issues

### Issue: User Creation Fails in Docker (SUSE)

**Problem**: `chown: invalid group: 'mcp:mcp'` error during build

**Root Cause**: SUSE's `useradd` doesn't automatically create a matching group like some other distributions

**Solution**:
```dockerfile
# Create group first, then user
RUN groupadd -g 1000 mcp && \
    useradd -m -u 1000 -g mcp mcp && \
    chown -R mcp:mcp /app
```

**Key Points**:
- Always create the group explicitly before the user on SUSE systems
- Use matching GID and UID for consistency (1000 is common for first user)
- The `-g` flag specifies the primary group for the user

### Issue: Govee API Rate Limiting

**Problem**: Too many API calls in short time

**Solution**:
1. Implement exponential backoff
2. Cache device state
3. Batch operations when possible
4. Document rate limits in tool descriptions

## Performance Considerations

### Async Client Reuse

- Initialize Govee client once, reuse across calls
- Use lazy initialization pattern
- Clean up connections on shutdown (future enhancement)

### Caching

Consider caching:
- Device list (refresh periodically)
- Device state (short TTL)
- API responses (with invalidation)

### Connection Pooling

- httpx handles connection pooling automatically
- Verify pool settings for production use

## Future Enhancements

### Planned Features

1. **HTTP/WebSocket Transport**: For n8n and other integrations
2. **Multi-Device Support**: Control multiple devices simultaneously
3. **Scene Support**: Govee scenes and DIY modes
4. **Schedule Support**: Time-based automations
5. **Music Mode**: Sync lights to music
6. **Device Groups**: Group control for multiple devices

### Infrastructure Improvements

1. **CI/CD Pipeline**: Automated testing and deployment
2. **Helm Chart**: Easier Kubernetes deployment
3. **Monitoring**: Prometheus metrics, Grafana dashboards
4. **Logging**: Structured logging with log levels
5. **Tracing**: OpenTelemetry integration

### Code Quality

1. **Unit Tests**: pytest-based test suite
2. **Integration Tests**: Test against Govee API sandbox
3. **Type Checking**: mypy static analysis
4. **Linting**: pylint or ruff for code quality
5. **Formatting**: black for consistent style

## Git Workflow

### Commit Messages

Use conventional commits:
- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation only
- `refactor:` - Code refactoring
- `test:` - Adding tests
- `chore:` - Maintenance tasks
- `perf:` - Performance improvements

### Branch Naming

- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring

### Pull Request Requirements

- Clear description of changes
- Updated documentation
- Tested locally and with Docker
- No breaking changes without major version bump
- Follows coding standards

## Questions to Ask

When uncertain about implementation:

1. **Does this follow the MCP specification?**
2. **Are we using the latest compatible versions?**
3. **Are all commands verified for SUSE/openSUSE compatibility?**
   - Using `zypper` instead of `apt`?
   - Using correct package names (e.g., `-devel` not `-dev`)?
   - Creating groups before users?
   - Testing on actual SUSE BCI image?
4. **Is this secure by default?**
5. **Will this work in Kubernetes?**
6. **Is the error handling user-friendly?**
7. **Is the documentation updated?**
8. **Can this be tested easily?**

## Resources

### Project-Specific
- [MCP Specification](https://modelcontextprotocol.io/)
- [FastMCP Repository](https://github.com/jlowin/fastmcp)
- [Govee API Docs](https://developer.govee.com/)
- [govee-api-laggat GitHub](https://github.com/LaggAt/python-govee-api)

### SUSE/openSUSE (CRITICAL - Review Before Any System Commands)
- [SUSE BCI Registry](https://registry.suse.com/)
- [SUSE BCI Documentation](https://documentation.suse.com/container/)
- [openSUSE Documentation](https://doc.opensuse.org/)
- [openSUSE Package Search](https://software.opensuse.org/)
- [Zypper Command Reference](https://en.opensuse.org/SDB:Zypper_usage)
- [SUSE vs Debian Command Comparison](https://en.opensuse.org/SDB:SuSE_vs_Debian)

### General Development
- [Python Async Best Practices](https://docs.python.org/3/library/asyncio.html)
- [Kubernetes Best Practices](https://kubernetes.io/docs/concepts/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)

## Contact and Support

For questions or clarifications:
- Review existing documentation (README.md, BUILD_FROM_SCRATCH.md)
- Check GitHub issues
- Consult the MCP and Govee API documentation
- Follow security best practices
- When in doubt, ask the user for guidance

---

**Remember: Quality over speed. Secure by default. User-friendly always.**
