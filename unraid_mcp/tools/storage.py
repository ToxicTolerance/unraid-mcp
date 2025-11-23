"""Storage, disk, and notification management tools.

This module provides tools for managing user shares, notifications,
log files, physical disks with SMART data, and system storage operations
with custom timeout configurations for disk-intensive operations.
"""

from typing import Any

import httpx
from fastmcp import FastMCP

from ..config.logging import logger
from ..core.client import make_graphql_request
from ..core.exceptions import ToolError


def register_storage_tools(mcp: FastMCP) -> None:
    """Register all storage tools with the FastMCP instance.

    Args:
        mcp: FastMCP instance to register tools with
    """

    @mcp.tool()
    async def get_shares_info() -> list[dict[str, Any]]:
        """Retrieves information about user shares."""
        query = """
        query GetSharesInfo {
          shares {
            id
            name
            free
            used
            size
            include
            exclude
            cache
            nameOrig
            comment
            allocator
            splitLevel
            floor
            cow
            color
            luksStatus
          }
        }
        """
        try:
            logger.info("Executing get_shares_info tool")
            response_data = await make_graphql_request(query)
            shares = response_data.get("shares", [])
            return list(shares) if isinstance(shares, list) else []
        except Exception as e:
            logger.error(f"Error in get_shares_info: {e}", exc_info=True)
            raise ToolError(f"Failed to retrieve shares information: {str(e)}") from e

    @mcp.tool()
    async def list_available_log_files() -> list[dict[str, Any]]:
        """Lists all available log files that can be queried."""
        query = """
        query ListLogFiles {
          logFiles {
            name
            path
            size
            modifiedAt
          }
        }
        """
        try:
            logger.info("Executing list_available_log_files tool")
            response_data = await make_graphql_request(query)
            log_files = response_data.get("logFiles", [])
            return list(log_files) if isinstance(log_files, list) else []
        except Exception as e:
            logger.error(f"Error in list_available_log_files: {e}", exc_info=True)
            raise ToolError(f"Failed to list available log files: {str(e)}") from e

    @mcp.tool()
    async def get_logs(log_file_path: str, tail_lines: int = 100) -> dict[str, Any]:
        """Retrieves content from a specific log file, defaulting to the last 100 lines."""
        query = """
        query GetLogContent($path: String!, $lines: Int) {
          logFile(path: $path, lines: $lines) {
            path
            content
            totalLines
            startLine
          }
        }
        """
        variables = {"path": log_file_path, "lines": tail_lines}
        try:
            logger.info(f"Executing get_logs for {log_file_path}, tail_lines={tail_lines}")
            response_data = await make_graphql_request(query, variables)
            log_file = response_data.get("logFile", {})
            return dict(log_file) if isinstance(log_file, dict) else {}
        except Exception as e:
            logger.error(f"Error in get_logs for {log_file_path}: {e}", exc_info=True)
            raise ToolError(f"Failed to retrieve logs from {log_file_path}: {str(e)}") from e

    @mcp.tool()
    async def list_physical_disks() -> list[dict[str, Any]]:
        """Lists all physical disks recognized by the Unraid system."""
        # Querying an extremely minimal set of fields for diagnostics
        query = """
        query ListPhysicalDisksMinimal {
          disks {
            id
            device
            name
          }
        }
        """
        try:
            logger.info(
                "Executing list_physical_disks tool with minimal query and increased timeout"
            )
            # Increased read timeout for this potentially slow query
            long_timeout = httpx.Timeout(10.0, read=90.0, connect=5.0)
            response_data = await make_graphql_request(query, custom_timeout=long_timeout)
            disks = response_data.get("disks", [])
            return list(disks) if isinstance(disks, list) else []
        except Exception as e:
            logger.error(f"Error in list_physical_disks: {e}", exc_info=True)
            raise ToolError(f"Failed to list physical disks: {str(e)}") from e

    @mcp.tool()
    async def get_disk_details(disk_id: str) -> dict[str, Any]:
        """Retrieves detailed SMART information and partition data for a specific physical disk."""
        # Enhanced query with more comprehensive disk information
        query = """
        query GetDiskDetails($id: PrefixedID!) {
          disk(id: $id) {
            id
            device
            type
            name
            vendor
            size
            # bytesPerSector  # Commented out: returns null for some disks despite being non-nullable
            totalCylinders
            totalHeads
            totalSectors
            totalTracks
            tracksPerCylinder
            sectorsPerTrack
            firmwareRevision
            serialNum
            interfaceType
            smartStatus
            temperature
            partitions {
              name
              fsType
              size
            }
            isSpinning
          }
        }
        """
        variables = {"id": disk_id}
        try:
            logger.info(f"Executing get_disk_details for disk: {disk_id}")
            response_data = await make_graphql_request(query, variables)
            raw_disk = response_data.get("disk", {})

            if not raw_disk:
                raise ToolError(f"Disk '{disk_id}' not found")

            # Process disk information for human-readable output
            def format_bytes(bytes_value: int | None) -> str:
                if bytes_value is None:
                    return "N/A"
                value = float(int(bytes_value))
                for unit in ["B", "KB", "MB", "GB", "TB", "PB"]:
                    if value < 1024.0:
                        return f"{value:.2f} {unit}"
                    value /= 1024.0
                return f"{value:.2f} EB"

            summary = {
                "disk_id": raw_disk.get("id"),
                "device": raw_disk.get("device"),
                "name": raw_disk.get("name"),
                "vendor": raw_disk.get("vendor"),
                "serial_number": raw_disk.get("serialNum"),
                "size_formatted": format_bytes(raw_disk.get("size")),
                "temperature": (
                    f"{raw_disk.get('temperature')}°C" if raw_disk.get("temperature") else "N/A"
                ),
                "interface_type": raw_disk.get("interfaceType"),
                "smart_status": raw_disk.get("smartStatus"),
                "is_spinning": raw_disk.get("isSpinning"),
                "firmware": raw_disk.get("firmwareRevision"),
                "partition_count": len(raw_disk.get("partitions", [])),
                "total_partition_size": format_bytes(
                    sum(p.get("size", 0) for p in raw_disk.get("partitions", []) if p.get("size"))
                ),
            }

            return {
                "summary": summary,
                "partitions": raw_disk.get("partitions", []),
                "details": raw_disk,
            }

        except Exception as e:
            logger.error(f"Error in get_disk_details for {disk_id}: {e}", exc_info=True)
            raise ToolError(f"Failed to retrieve disk details for {disk_id}: {str(e)}") from e

    @mcp.tool()
    async def start_parity_check(correct: bool = True) -> dict[str, Any]:
        """Start a parity check."""
        query = """
        mutation StartParityCheck($correct: Boolean!) {
          parityCheck {
            start(correct: $correct)
          }
        }
        """
        variables = {"correct": correct}
        try:
            logger.info(f"Executing start_parity_check, correct={correct}")
            response_data = await make_graphql_request(query, variables)
            result = response_data.get("parityCheck", {}).get("start", {})
            return dict(result) if isinstance(result, dict) else {}
        except Exception as e:
            logger.error(f"Error in start_parity_check: {e}", exc_info=True)
            raise ToolError(f"Failed to start parity check: {str(e)}") from e

    @mcp.tool()
    async def pause_parity_check() -> dict[str, Any]:
        """Pause a parity check."""
        query = """
        mutation PauseParityCheck {
          parityCheck {
            pause
          }
        }
        """
        try:
            logger.info("Executing pause_parity_check")
            response_data = await make_graphql_request(query)
            result = response_data.get("parityCheck", {}).get("pause", {})
            return dict(result) if isinstance(result, dict) else {}
        except Exception as e:
            logger.error(f"Error in pause_parity_check: {e}", exc_info=True)
            raise ToolError(f"Failed to pause parity check: {str(e)}") from e

    @mcp.tool()
    async def resume_parity_check() -> dict[str, Any]:
        """Resume a parity check."""
        query = """
        mutation ResumeParityCheck {
          parityCheck {
            resume
          }
        }
        """
        try:
            logger.info("Executing resume_parity_check")
            response_data = await make_graphql_request(query)
            result = response_data.get("parityCheck", {}).get("resume", {})
            return dict(result) if isinstance(result, dict) else {}
        except Exception as e:
            logger.error(f"Error in resume_parity_check: {e}", exc_info=True)
            raise ToolError(f"Failed to resume parity check: {str(e)}") from e

    @mcp.tool()
    async def cancel_parity_check() -> dict[str, Any]:
        """Cancel a parity check."""
        query = """
        mutation CancelParityCheck {
          parityCheck {
            cancel
          }
        }
        """
        try:
            logger.info("Executing cancel_parity_check")
            response_data = await make_graphql_request(query)
            result = response_data.get("parityCheck", {}).get("cancel", {})
            return dict(result) if isinstance(result, dict) else {}
        except Exception as e:
            logger.error(f"Error in cancel_parity_check: {e}", exc_info=True)
            raise ToolError(f"Failed to cancel parity check: {str(e)}") from e

    logger.info("Storage tools registered successfully")
