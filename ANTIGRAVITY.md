# ANTIGRAVITY.md

This file provides guidance to Antigravity when working with code in this repository.

> **Note**: This is an MCP (Model Context Protocol) server project. Antigravity can interact with this server once it's running to access Unraid server management capabilities.

## Project Overview
This is an MCP (Model Context Protocol) server that provides tools to interact with an Unraid server's GraphQL API. The server is built using FastMCP with a **modular architecture** consisting of separate packages for configuration, core functionality, subscriptions, and tools.

## Development Commands

### Setup
```bash
# Initialize uv virtual environment and install dependencies
uv sync

# Install dev dependencies
uv sync --group dev
```

### Running the Server
```bash
# Local development with uv (recommended)
uv run unraid-mcp-server

# Using development script with hot reload
./dev.sh

# Direct module execution
uv run -m unraid_mcp.main
```

### Code Quality
```bash
# Format code with black
uv run black unraid_mcp/

# Lint with ruff
uv run ruff check unraid_mcp/

# Type checking with mypy
uv run mypy unraid_mcp/

# Run tests
uv run pytest
```

### Docker Development
```bash
# Build the Docker image
docker build -t unraid-mcp-server .

# Run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f unraid-mcp

# Stop service
docker-compose down
```

### Environment Setup
- Copy `.env.example` to `.env` and configure:
  - `UNRAID_API_URL`: Unraid GraphQL endpoint (required)
  - `UNRAID_API_KEY`: Unraid API key (required)
  - `UNRAID_MCP_TRANSPORT`: Transport type (default: streamable-http)
  - `UNRAID_MCP_PORT`: Server port (default: 6970)
  - `UNRAID_MCP_HOST`: Server host (default: 0.0.0.0)

## Architecture

### Core Components
- **Main Server**: `unraid_mcp/server.py` - Modular MCP server with FastMCP integration
- **Entry Point**: `unraid_mcp/main.py` - Application entry point and startup logic
- **Configuration**: `unraid_mcp/config/` - Settings management and logging configuration
- **Core Infrastructure**: `unraid_mcp/core/` - GraphQL client, exceptions, and shared types
- **Subscriptions**: `unraid_mcp/subscriptions/` - Real-time WebSocket subscriptions and diagnostics
- **Tools**: `unraid_mcp/tools/` - Domain-specific tool implementations
- **GraphQL Client**: Uses httpx for async HTTP requests to Unraid API
- **Transport Layer**: Supports streamable-http (recommended), SSE (deprecated), and stdio

### Key Design Patterns
- **Modular Architecture**: Clean separation of concerns across focused modules
- **Error Handling**: Uses ToolError for user-facing errors, detailed logging for debugging
- **Timeout Management**: Custom timeout configurations for different query types
- **Data Processing**: Tools return both human-readable summaries and detailed raw data
- **Health Monitoring**: Comprehensive health check tool for system monitoring
- **Real-time Subscriptions**: WebSocket-based live data streaming

### Tool Categories (44 Tools Total)
1. **System Information** (5 tools): `get_system_info()`, `get_array_status()`, `get_network_config()`, `get_registration_info()`, `get_unraid_variables()`
2. **Storage Management** (9 tools): `get_shares_info()`, `list_physical_disks()`, `get_disk_details()`, `list_available_log_files()`, `get_logs()`, `get_share_details()`, `get_pool_details()`, `get_cache_pool_details()`, `get_filesystem_details()`
3. **Docker Management** (3 tools): `list_docker_containers()`, `manage_docker_container()`, `get_docker_container_details()`
4. **VM Management** (3 tools): `list_vms()`, `manage_vm()`, `get_vm_details()`
5. **Cloud Storage (RClone)** (4 tools): `list_rclone_remotes()`, `get_rclone_config_form()`, `create_rclone_remote()`, `delete_rclone_remote()`
6. **Health Monitoring** (1 tool): `health_check()`
7. **Connect Management** (4 tools): `get_connect_settings()`, `get_connect_status()`, `get_connect_vpn_config()`, `update_connect_settings()`
8. **Notifications** (3 tools): `get_notifications_overview()`, `list_notifications()`, `dismiss_notification()`
9. **Plugins** (3 tools): `list_plugins()`, `get_plugin_details()`, `manage_plugin()`
10. **Security** (4 tools): `get_security_settings()`, `list_ssl_certificates()`, `get_certificate_details()`, `update_security_settings()`
11. **UPS Management** (3 tools): `get_ups_status()`, `get_ups_settings()`, `update_ups_settings()`
12. **Subscription Diagnostics** (2 tools): `test_subscription_query()`, `diagnose_subscriptions()`

### Environment Variable Hierarchy
The server loads environment variables from multiple locations in order:
1. `/app/.env.local` (container mount)
2. `../.env.local` (project root)
3. `../.env` (project root)
4. `.env` (local directory)

### Transport Configuration
- **streamable-http** (recommended): HTTP-based transport on `/mcp` endpoint
- **sse** (deprecated): Server-Sent Events transport
- **stdio**: Standard input/output for direct integration

### Error Handling Strategy
- GraphQL errors are converted to ToolError with descriptive messages
- HTTP errors include status codes and response details
- Network errors are caught and wrapped with connection context
- All errors are logged with full context for debugging

### Performance Considerations
- Increased timeouts for disk operations (90s read timeout)
- Selective queries to avoid GraphQL type overflow issues
- Optional caching controls for Docker container queries
- Rotating log files to prevent disk space issues

## Antigravity-Specific Guidance

### Working with MCP Servers
This project IS an MCP server implementation. When the user asks you to interact with their Unraid server:
1. **First ensure the server is running**: Check if `uv run unraid-mcp-server` or `./dev.sh` is active
2. **Connect via MCP**: Use the MCP tools available in your environment to connect to the server
3. **Use the tools**: Once connected, you can use any of the 44 tools listed above to interact with the Unraid server

### Development Workflow
When making changes to this codebase:
1. **Understand the modular structure**: Each tool category is in its own file under `unraid_mcp/tools/`
2. **Follow the patterns**: New tools should follow the existing decorator pattern with `@mcp.tool()`
3. **Update registration**: Add new tools to the appropriate `register_*_tools()` function
4. **Test thoroughly**: Use the health check and diagnostic tools to verify changes
5. **Check logs**: The server logs extensively - use them for debugging

### Common Tasks

#### Adding a New Tool
1. Identify the appropriate module (e.g., `storage.py`, `docker.py`)
2. Add the tool function with `@mcp.tool()` decorator
3. Implement GraphQL query and error handling
4. Update the tool count in this file
5. Test with the diagnostic tools

#### Debugging GraphQL Issues
1. Check `Schema.txt` for the current GraphQL schema
2. Use `test_subscription_query()` to test queries
3. Review error logs in `unraid_mcp/logs/`
4. Verify field types match schema (common issue: Int vs Float)

#### Updating Dependencies
```bash
# Add a new dependency
uv add package-name

# Update all dependencies
uv sync

# Update lock file
uv lock
```

### Code Style Guidelines
- **Line length**: 100 characters (enforced by black and ruff)
- **Type hints**: Required for all functions (enforced by mypy)
- **Imports**: Sorted with isort (part of ruff)
- **Docstrings**: Use for all public functions and classes
- **Error handling**: Always use `ToolError` for user-facing errors

### Testing Strategy
- **Unit tests**: Test individual tool functions
- **Integration tests**: Test GraphQL queries against live server
- **Health checks**: Use `health_check()` tool for system validation
- **Subscription tests**: Use diagnostic tools for WebSocket testing