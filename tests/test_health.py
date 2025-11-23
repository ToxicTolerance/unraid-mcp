from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from unraid_mcp.tools.health import register_health_tools


@pytest.mark.asyncio
async def test_health_check() -> None:
    # Mock FastMCP
    mock_mcp = MagicMock()

    # Capture the decorated function
    health_check_func = None

    def tool_decorator(*args: Any, **kwargs: Any) -> Any:
        def wrapper(func: Any) -> Any:
            nonlocal health_check_func
            health_check_func = func
            return func

        return wrapper

    mock_mcp.tool.side_effect = tool_decorator

    # Register tools
    register_health_tools(mock_mcp)

    assert health_check_func is not None

    # Mock make_graphql_request
    with patch(
        "unraid_mcp.tools.health.make_graphql_request", new_callable=AsyncMock
    ) as mock_request:
        # Mock successful response
        mock_request.return_value = {
            "info": {
                "machineId": "test-id",
                "time": "2023-01-01T00:00:00Z",
                "versions": {"core": {"unraid": "6.12.0"}},
                "os": {"uptime": 1000},
            },
            "array": {"state": "STARTED"},
            "notifications": {"overview": {"unread": {"alert": 0, "warning": 0, "total": 0}}},
            "docker": {"containers": []},
        }

        # Run health check
        result = await health_check_func()

        assert result["status"] == "healthy"
        assert result["unraid_system"]["version"] == "6.12.0"
        assert result["array_status"]["state"] == "STARTED"
