"""Security and access control tools.

This module provides tools for managing API keys and access controls.
"""

from typing import Any

from fastmcp import FastMCP

from ..config.logging import logger
from ..core.client import make_graphql_request
from ..core.exceptions import ToolError


def register_security_tools(mcp: FastMCP) -> None:
    """Register all security tools with the FastMCP instance.

    Args:
        mcp: FastMCP instance to register tools with
    """

    @mcp.tool()
    async def get_api_keys() -> list[dict[str, Any]]:
        """Retrieves a list of all API keys."""
        query = """
        query GetApiKeys {
          apiKeys {
            id
            name
            key
            scope
            createdAt
            lastUsedAt
          }
        }
        """
        try:
            logger.info("Executing get_api_keys tool")
            response_data = await make_graphql_request(query)
            api_keys = response_data.get("apiKeys", [])
            return list(api_keys) if isinstance(api_keys, list) else []
        except Exception as e:
            logger.error(f"Error in get_api_keys: {e}", exc_info=True)
            raise ToolError(f"Failed to retrieve API keys: {str(e)}") from e

    @mcp.tool()
    async def create_api_key(name: str, scope: str = "READ_ONLY") -> dict[str, Any]:
        """
        Creates a new API key.

        Args:
            name: Name/description for the API key
            scope: Permission scope (READ_ONLY, READ_WRITE, ADMIN)
        """
        mutation = """
        mutation CreateApiKey($input: CreateApiKeyInput!) {
          createApiKey(input: $input) {
            id
            name
            key
            scope
            createdAt
          }
        }
        """
        variables = {"input": {"name": name, "scope": scope}}
        try:
            logger.info(f"Executing create_api_key: {name}")
            response_data = await make_graphql_request(mutation, variables)
            api_key = response_data.get("createApiKey", {})
            return dict(api_key) if isinstance(api_key, dict) else {}
        except Exception as e:
            logger.error(f"Error in create_api_key: {e}", exc_info=True)
            raise ToolError(f"Failed to create API key: {str(e)}") from e

    @mcp.tool()
    async def delete_api_key(key_id: str) -> dict[str, Any]:
        """
        Deletes an API key.

        Args:
            key_id: ID of the API key to delete
        """
        mutation = """
        mutation DeleteApiKey($input: DeleteApiKeyInput!) {
          deleteApiKey(input: $input)
        }
        """
        variables = {"input": {"id": key_id}}
        try:
            logger.info(f"Executing delete_api_key: {key_id}")
            response_data = await make_graphql_request(mutation, variables)
            success = response_data.get("deleteApiKey", False)
            return {
                "success": success,
                "message": (
                    "API key deleted successfully" if success else "Failed to delete API key"
                ),
            }
        except Exception as e:
            logger.error(f"Error in delete_api_key: {e}", exc_info=True)
            raise ToolError(f"Failed to delete API key: {str(e)}") from e

    @mcp.tool()
    async def update_api_key(
        key_id: str, name: str | None = None, scope: str | None = None
    ) -> dict[str, Any]:
        """
        Updates an existing API key.

        Args:
            key_id: ID of the API key to update
            name: New name (optional)
            scope: New scope (optional)
        """
        mutation = """
        mutation UpdateApiKey($input: UpdateApiKeyInput!) {
          updateApiKey(input: $input) {
            id
            name
            scope
          }
        }
        """
        variables = {"input": {"id": key_id}}
        if name:
            variables["input"]["name"] = name
        if scope:
            variables["input"]["scope"] = scope

        try:
            logger.info(f"Executing update_api_key: {key_id}")
            response_data = await make_graphql_request(mutation, variables)
            api_key = response_data.get("updateApiKey", {})
            return dict(api_key) if isinstance(api_key, dict) else {}
        except Exception as e:
            logger.error(f"Error in update_api_key: {e}", exc_info=True)
            raise ToolError(f"Failed to update API key: {str(e)}") from e

    logger.info("Security tools registered successfully")
