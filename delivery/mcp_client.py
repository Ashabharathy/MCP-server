"""
mcp_client.py — MCP client for communicating with MCP servers.

Handles communication with MCP servers for Google Docs and Gmail.
"""

import json
import logging
import subprocess
import sys
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class MCPClient:
    """Client for communicating with MCP servers."""

    def __init__(self, server_command: list[str], env: Optional[Dict[str, str]] = None):
        """
        Initialize MCP client.

        Args:
            server_command: Command to start the MCP server.
            env: Environment variables for the server process.
        """
        self.server_command = server_command
        self.env = env or {}
        self.process: Optional[subprocess.Popen] = None
        self.request_id = 0

    def start(self) -> None:
        """Start the MCP server process."""
        logger.info("Starting MCP server: %s", " ".join(self.server_command))
        self.process = subprocess.Popen(
            self.server_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env={**dict(os.environ), **self.env} if self.env else None,
        )
        logger.info("MCP server started with PID: %d", self.process.pid)

    def stop(self) -> None:
        """Stop the MCP server process."""
        if self.process:
            logger.info("Stopping MCP server (PID: %d)", self.process.pid)
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
            self.process = None

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a tool on the MCP server.

        Args:
            tool_name: Name of the tool to call.
            arguments: Arguments for the tool.

        Returns:
            Response from the tool.
        """
        if not self.process:
            raise RuntimeError("MCP server not started")

        self.request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments,
            },
        }

        logger.debug("Calling tool: %s with arguments: %s", tool_name, arguments)

        # Send request
        request_json = json.dumps(request) + "\n"
        self.process.stdin.write(request_json)
        self.process.stdin.flush()

        # Read response
        response_line = self.process.stdout.readline()
        if not response_line:
            raise RuntimeError("No response from MCP server")

        response = json.loads(response_line)

        if "error" in response:
            logger.error("MCP server error: %s", response["error"])
            raise RuntimeError(f"MCP server error: {response['error']}")

        logger.debug("Tool response: %s", response.get("result"))
        return response.get("result", {})

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
