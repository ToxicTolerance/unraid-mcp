"""Plugin management tools.

This module provides tools for listing, installing, and removing Unraid plugins.
"""

from typing import Any

from fastmcp import FastMCP

from ..config.logging import logger
from ..core.client import make_graphql_request
from ..core.exceptions import ToolError


def register_plugin_tools(mcp: FastMCP) -> None:
    """Register all plugin tools with the FastMCP instance.

    Args:
        mcp: FastMCP instance to register tools with
    """

    @mcp.tool()
    async def list_plugins() -> list[dict[str, Any]]:
        """Lists all installed plugins on the Unraid system."""
        query = """
        query ListPlugins {
          plugins {
            name
            version
            hasApiModule
            hasCliModule
          }
        }
        """
        try:
            logger.info("Executing list_plugins tool")
            response_data = await make_graphql_request(query)
            plugins = response_data.get("plugins", [])
            return list(plugins) if isinstance(plugins, list) else []
        except Exception as e:
            logger.error(f"Error in list_plugins: {e}", exc_info=True)
            raise ToolError(f"Failed to list plugins: {str(e)}") from e

    @mcp.tool()
    async def add_plugin(names: list[str], restart: bool = True) -> dict[str, Any]:
        """
        Installs one or more plugins.

        Args:
            names: List of plugin package names (URLs or filenames) to install
            restart: Whether to restart the API after installation (default: True)
        """
        mutation = """
        mutation AddPlugin($input: PluginManagementInput!) {
          addPlugin(input: $input)
        }
        """
        variables = {
            "input": {
                "names": names,
                "restart": restart,
                "bundled": False,  # Assuming we are adding external plugins usually
            }
        }
        try:
            logger.info(f"Executing add_plugin for {names}")
            response_data = await make_graphql_request(mutation, variables)
            result = response_data.get("addPlugin")
            return {
                "success": True,  # If no error raised, it succeeded
                "manual_restart_required": result,  # Returns true if manual restart required
                "message": f"Plugins {names} added successfully."
                + (
                    " Manual restart required."
                    if result
                    else " API restarting automatically." if restart else ""
                ),
            }
        except Exception as e:
            logger.error(f"Error in add_plugin: {e}", exc_info=True)
            raise ToolError(f"Failed to add plugins: {str(e)}") from e

    @mcp.tool()
    async def remove_plugin(names: list[str], restart: bool = True) -> dict[str, Any]:
        """
        Removes one or more plugins.

        Args:
            names: List of plugin package names to remove
            restart: Whether to restart the API after removal (default: True)
        """
        mutation = """
        mutation RemovePlugin($input: PluginManagementInput!) {
          removePlugin(input: $input)
        }
        """
        variables = {"input": {"names": names, "restart": restart, "bundled": False}}
        try:
            logger.info(f"Executing remove_plugin for {names}")
            response_data = await make_graphql_request(mutation, variables)
            result = response_data.get("removePlugin")
            return {
                "success": True,
                "manual_restart_required": result,
                "message": f"Plugins {names} removed successfully."
                + (
                    " Manual restart required."
                    if result
                    else " API restarting automatically." if restart else ""
                ),
            }
        except Exception as e:
            logger.error(f"Error in remove_plugin: {e}", exc_info=True)
            raise ToolError(f"Failed to remove plugins: {str(e)}") from e

    logger.info("Plugin tools registered successfully")
