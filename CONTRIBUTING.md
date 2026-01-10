# Contributing to MCP Govee Controller

Thank you for your interest in contributing to the MCP Govee Controller project!

## Getting Started

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/yourusername/mcp-grovee.git
   cd mcp-grovee
   ```
3. Run the setup script:
   ```bash
   ./setup.sh
   ```
4. Create a branch for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Workflow

### Local Development

1. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```

2. Make your changes to `src/server.py` or other files

3. Test your changes:
   ```bash
   python -m src.server
   ```

4. Use the MCP Inspector for interactive testing:
   ```bash
   npx @modelcontextprotocol/inspector python -m src.server
   ```

### Code Style

We follow Python best practices:

- PEP 8 style guide
- Type hints for all functions
- Docstrings for all public functions
- Maximum line length: 88 characters (Black default)

Format your code with Black:
```bash
make format
```

Check linting:
```bash
make lint
```

### Adding New Tools

To add a new MCP tool:

1. Add a new function to `src/server.py`
2. Decorate it with `@mcp.tool()`
3. Use async/await if calling Govee API
4. Add type hints and docstring
5. Include error handling
6. Return user-friendly strings

Example:
```python
@mcp.tool()
async def your_new_tool(param: int) -> str:
    """
    Brief description of what this tool does.

    Args:
        param: Description of the parameter
    """
    try:
        # Your implementation
        return "✓ Success message"
    except Exception as e:
        return f"✗ Error: {str(e)}"
```

### Testing

Currently, we don't have automated tests, but you should:

1. Test manually with Claude Desktop
2. Test with the MCP Inspector
3. Verify error handling works
4. Test with Docker container
5. Document your testing in the PR

We welcome contributions to add automated testing!

### Docker Testing

Build and test the Docker image:
```bash
make docker-build
make docker-run
```

## Submitting Changes

1. Commit your changes:
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

   Use conventional commit messages:
   - `feat:` for new features
   - `fix:` for bug fixes
   - `docs:` for documentation
   - `refactor:` for code refactoring
   - `test:` for adding tests
   - `chore:` for maintenance

2. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

3. Create a Pull Request on GitHub

## Pull Request Guidelines

Your PR should:

- Have a clear title and description
- Reference any related issues
- Include documentation updates if needed
- Pass all existing tests (when we have them)
- Follow the code style guidelines
- Be focused on a single feature/fix

## Reporting Issues

When reporting bugs, please include:

- Your operating system
- Python version
- Steps to reproduce
- Expected behavior
- Actual behavior
- Error messages and logs

## Feature Requests

We welcome feature requests! Please:

- Check if it's already requested
- Describe the use case
- Explain why it would be useful
- Consider contributing the implementation

## Code of Conduct

Be respectful and inclusive. We're all here to learn and build together.

## Questions?

Feel free to:
- Open an issue for discussion
- Ask in your pull request
- Check the BUILD_FROM_SCRATCH.md guide

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
