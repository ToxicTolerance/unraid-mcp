"""UPS (Uninterruptible Power Supply) management tools.

This module provides tools for monitoring and configuring UPS devices connected
to the Unraid server, including battery status, power metrics, and shutdown settings.
"""

from typing import Any

from fastmcp import FastMCP

from ..config.logging import logger
from ..core.client import make_graphql_request
from ..core.exceptions import ToolError


def register_ups_tools(mcp: FastMCP) -> None:
    """Register all UPS tools with the FastMCP instance.

    Args:
        mcp: FastMCP instance to register tools with
    """

    @mcp.tool()
    async def get_ups_devices() -> list[dict[str, Any]]:
        """Retrieves a list of connected UPS devices and their status."""
        query = """
        query GetUpsDevices {
          upsDevices {
            id
            name
            model
            status
            battery {
              chargeLevel
              estimatedRuntime
              health
            }
            power {
              inputVoltage
              outputVoltage
              loadPercentage
            }
          }
        }
        """
        try:
            logger.info("Executing get_ups_devices tool")
            response_data = await make_graphql_request(query)
            ups_devices = response_data.get("upsDevices", [])
            return list(ups_devices) if isinstance(ups_devices, list) else []
        except Exception as e:
            logger.error(f"Error in get_ups_devices: {e}", exc_info=True)
            raise ToolError(f"Failed to retrieve UPS devices: {str(e)}") from e

    @mcp.tool()
    async def get_ups_config() -> dict[str, Any]:
        """Retrieves the current UPS configuration settings."""
        query = """
        query GetUpsConfiguration {
          upsConfiguration {
            service
            upsCable
            customUpsCable
            upsType
            device
            overrideUpsCapacity
            batteryLevel
            minutes
            timeout
            killUps
            nisIp
            netServer
            upsName
            modelName
          }
        }
        """
        try:
            logger.info("Executing get_ups_config tool")
            response_data = await make_graphql_request(query)
            config = response_data.get("upsConfiguration", {})
            return dict(config) if isinstance(config, dict) else {}
        except Exception as e:
            logger.error(f"Error in get_ups_config: {e}", exc_info=True)
            raise ToolError(f"Failed to retrieve UPS configuration: {str(e)}") from e

    @mcp.tool()
    async def configure_ups(config: dict[str, Any]) -> dict[str, Any]:
        """
        Updates UPS configuration settings.

        Args:
            config: Dictionary containing UPS configuration parameters.
                   Fields: service (ENABLE/DISABLE), upsCable, customUpsCable, upsType,
                   device, overrideUpsCapacity, batteryLevel, minutes, timeout, killUps (YES/NO)
        """
        mutation = """
        mutation ConfigureUps($config: UPSConfigInput!) {
          configureUps(config: $config)
        }
        """
        variables = {"config": config}
        try:
            logger.info("Executing configure_ups tool")
            response_data = await make_graphql_request(mutation, variables)
            success = response_data.get("configureUps", False)
            return {
                "success": success,
                "message": (
                    "UPS configuration updated successfully"
                    if success
                    else "Failed to update UPS configuration"
                ),
            }
        except Exception as e:
            logger.error(f"Error in configure_ups: {e}", exc_info=True)
            raise ToolError(f"Failed to configure UPS: {str(e)}") from e

    logger.info("UPS tools registered successfully")
