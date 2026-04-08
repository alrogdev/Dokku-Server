"""Tests for MCP tools."""

import pytest
import asyncio

from kimidokku.mcp_server import get_mcp_server


class TestMCPServer:
    """Test MCP server setup."""

    def test_mcp_server_created(self):
        """Test that MCP server is created."""
        mcp = get_mcp_server()
        assert mcp is not None
        assert mcp.name == "kimidokku-mcp"

    @pytest.mark.asyncio
    async def test_app_tools_registered(self):
        """Test that app tools are registered."""
        mcp = get_mcp_server()
        tools = await mcp.list_tools()
        tool_names = [tool.name for tool in tools]

        assert "list_apps" in tool_names
        assert "get_app_status" in tool_names
        assert "deploy_git" in tool_names
        assert "deploy_image" in tool_names

    @pytest.mark.asyncio
    async def test_logs_tools_registered(self):
        """Test that logs tools are registered."""
        mcp = get_mcp_server()
        tools = await mcp.list_tools()
        tool_names = [tool.name for tool in tools]

        assert "get_logs" in tool_names
        assert "restart_app" in tool_names
        assert "run_command" in tool_names

    @pytest.mark.asyncio
    async def test_config_tools_registered(self):
        """Test that config tools are registered."""
        mcp = get_mcp_server()
        tools = await mcp.list_tools()
        tool_names = [tool.name for tool in tools]

        assert "get_config" in tool_names
        assert "set_config" in tool_names

    @pytest.mark.asyncio
    async def test_domain_tools_registered(self):
        """Test that domain tools are registered."""
        mcp = get_mcp_server()
        tools = await mcp.list_tools()
        tool_names = [tool.name for tool in tools]

        assert "list_domains" in tool_names
        assert "add_custom_domain" in tool_names
        assert "remove_custom_domain" in tool_names

    @pytest.mark.asyncio
    async def test_database_tools_registered(self):
        """Test that database tools are registered."""
        mcp = get_mcp_server()
        tools = await mcp.list_tools()
        tool_names = [tool.name for tool in tools]

        assert "create_database" in tool_names
        assert "list_databases" in tool_names
        assert "unlink_database" in tool_names
