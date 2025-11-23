"""Unraid Connect and Remote Access management tools.

This module provides tools for managing Unraid Connect integration,
Remote Access settings, and dynamic remote access configuration.
"""

from typing import Any

from fastmcp import FastMCP

from ..config.logging import logger
from ..core.client import make_graphql_request
from ..core.exceptions import ToolError


def register_connect_tools(mcp: FastMCP) -> None:
    """Register all Connect tools with the FastMCP instance.

    Args:
        mcp: FastMCP instance to register tools with
    """

    @mcp.tool()
    async def get_connect_status() -> dict[str, Any]:
        """Retrieves current Unraid Connect and Remote Access status."""
        query = """
        query GetConnectStatus {
          connect {
            dynamicRemoteAccess {
              enabledType
              runningType
              error
            }
            settings {
              values {
                accessType
                forwardType
                port
              }
            }
          }
          remoteAccess {
            accessType
            forwardType
            port
          }
        }
        """
        try:
            logger.info("Executing get_connect_status tool")
            response_data = await make_graphql_request(query)
            return {
                "connect": response_data.get("connect", {}),
                "remote_access": response_data.get("remoteAccess", {}),
            }
        except Exception as e:
            logger.error(f"Error in get_connect_status: {e}", exc_info=True)
            raise ToolError(f"Failed to retrieve Connect status: {str(e)}") from e

    @mcp.tool()
    async def update_connect_settings(
        access_type: str | None = None, forward_type: str | None = None, port: int | None = None
    ) -> dict[str, Any]:
        """
        Update Unraid Connect settings.

        Args:
            access_type: WAN access type (DYNAMIC, ALWAYS, DISABLED)
            forward_type: Port forwarding type (UPNP, STATIC)
            port: Port number for STATIC forwarding
        """
        mutation = """
        mutation UpdateApiSettings($input: ConnectSettingsInput!) {
          updateApiSettings(input: $input) {
            accessType
            forwardType
            port
          }
        }
        """
        variables: dict[str, Any] = {"input": {}}
        if access_type:
            variables["input"]["accessType"] = access_type
        if forward_type:
            variables["input"]["forwardType"] = forward_type
        if port is not None:
            variables["input"]["port"] = port

        try:
            logger.info(f"Executing update_connect_settings: {variables}")
            response_data = await make_graphql_request(mutation, variables)
            result = response_data.get("updateApiSettings", {})
            return dict(result) if isinstance(result, dict) else {}
        except Exception as e:
            logger.error(f"Error in update_connect_settings: {e}", exc_info=True)
            raise ToolError(f"Failed to update Connect settings: {str(e)}") from e

    @mcp.tool()
    async def sign_in_connect(
        api_key: str, username: str, email: str, avatar: str | None = None
    ) -> dict[str, Any]:
        """
        Sign in to Unraid Connect.

        Args:
            api_key: The API key for authentication
            username: Preferred username
            email: User email
            avatar: Optional avatar URL
        """
        mutation = """
        mutation ConnectSignIn($input: ConnectSignInInput!) {
          connectSignIn(input: $input)
        }
        """
        variables = {
            "input": {
                "apiKey": api_key,
                "userInfo": {"preferred_username": username, "email": email, "avatar": avatar},
            }
        }
        try:
            logger.info("Executing sign_in_connect")
            response_data = await make_graphql_request(mutation, variables)
            success = response_data.get("connectSignIn", False)
            return {
                "success": success,
                "message": "Signed in to Connect" if success else "Failed to sign in",
            }
        except Exception as e:
            logger.error(f"Error in sign_in_connect: {e}", exc_info=True)
            raise ToolError(f"Failed to sign in to Connect: {str(e)}") from e

    @mcp.tool()
    async def sign_out_connect() -> dict[str, Any]:
        """Sign out of Unraid Connect."""
        mutation = """
        mutation ConnectSignOut {
          connectSignOut
        }
        """
        try:
            logger.info("Executing sign_out_connect")
            response_data = await make_graphql_request(mutation)
            success = response_data.get("connectSignOut", False)
            return {
                "success": success,
                "message": "Signed out of Connect" if success else "Failed to sign out",
            }
        except Exception as e:
            logger.error(f"Error in sign_out_connect: {e}", exc_info=True)
            raise ToolError(f"Failed to sign out of Connect: {str(e)}") from e

    logger.info("Connect tools registered successfully")
