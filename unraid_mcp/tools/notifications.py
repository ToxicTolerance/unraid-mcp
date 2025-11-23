"""Notification management tools.

This module provides tools for retrieving, listing, and sending system notifications.
"""

from typing import Any

from fastmcp import FastMCP

from ..config.logging import logger
from ..core.client import make_graphql_request
from ..core.exceptions import ToolError


def register_notification_tools(mcp: FastMCP) -> None:
    """Register all notification tools with the FastMCP instance.

    Args:
        mcp: FastMCP instance to register tools with
    """

    @mcp.tool()
    async def get_notifications_overview() -> dict[str, Any]:
        """Retrieves an overview of system notifications (unread and archive counts by severity)."""
        query = """
        query GetNotificationsOverview {
          notifications {
            overview {
              unread { info warning alert total }
              archive { info warning alert total }
            }
          }
        }
        """
        try:
            logger.info("Executing get_notifications_overview tool")
            response_data = await make_graphql_request(query)
            if response_data.get("notifications"):
                overview = response_data["notifications"].get("overview", {})
                return dict(overview) if isinstance(overview, dict) else {}
            return {}
        except Exception as e:
            logger.error(f"Error in get_notifications_overview: {e}", exc_info=True)
            raise ToolError(f"Failed to retrieve notifications overview: {str(e)}") from e

    @mcp.tool()
    async def list_notifications(
        type: str, offset: int, limit: int, importance: str | None = None
    ) -> list[dict[str, Any]]:
        """Lists notifications with filtering. Type: UNREAD/ARCHIVE. Importance: INFO/WARNING/ALERT."""
        query = """
        query ListNotifications($filter: NotificationFilter!) {
          notifications {
            list(filter: $filter) {
              id
              title
              subject
              description
              importance
              link
              type
              timestamp
              formattedTimestamp
            }
          }
        }
        """
        variables = {
            "filter": {
                "type": type.upper(),
                "offset": offset,
                "limit": limit,
                "importance": importance.upper() if importance else None,
            }
        }
        # Remove null importance from variables if not provided, as GraphQL might be strict
        if not importance:
            del variables["filter"]["importance"]

        try:
            logger.info(
                f"Executing list_notifications: type={type}, offset={offset}, limit={limit}, importance={importance}"
            )
            response_data = await make_graphql_request(query, variables)
            if response_data.get("notifications"):
                notifications_list = response_data["notifications"].get("list", [])
                return list(notifications_list) if isinstance(notifications_list, list) else []
            return []
        except Exception as e:
            logger.error(f"Error in list_notifications: {e}", exc_info=True)
            raise ToolError(f"Failed to list notifications: {str(e)}") from e

    @mcp.tool()
    async def send_notification(
        subject: str,
        description: str,
        importance: str = "normal",
        event: str = "Unraid MCP",
        link: str | None = None,
    ) -> dict[str, Any]:
        """
        Sends a system notification.

        Args:
            subject: Notification subject/title
            description: Notification body text
            importance: Importance level (normal, warning, alert)
            event: Event source name (default: "Unraid MCP")
            link: Optional link URL
        """
        mutation = """
        mutation SendNotification($input: SendNotificationInput!) {
          sendNotification(input: $input)
        }
        """
        variables = {
            "input": {
                "subject": subject,
                "description": description,
                "importance": importance.lower(),  # Schema might expect lowercase or uppercase, usually lowercase for this input type in Unraid
                "event": event,
                "link": link,
            }
        }
        try:
            logger.info(f"Executing send_notification: {subject}")
            response_data = await make_graphql_request(mutation, variables)
            success = response_data.get("sendNotification", False)
            return {
                "success": success,
                "message": (
                    "Notification sent successfully" if success else "Failed to send notification"
                ),
            }
        except Exception as e:
            logger.error(f"Error in send_notification: {e}", exc_info=True)
            raise ToolError(f"Failed to send notification: {str(e)}") from e

    logger.info("Notification tools registered successfully")
