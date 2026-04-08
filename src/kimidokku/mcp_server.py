"""MCP Server setup with FastMCP."""

from fastmcp import FastMCP

# Create MCP server instance
mcp = FastMCP(
    name="kimidokku-mcp",
    instructions="""
    KimiDokku MCP Server - Manage Dokku applications via AI agents.
    
    Available capabilities:
    - App Lifecycle: list_apps, get_app_status, deploy_git, deploy_image
    - Logs & Debug: get_logs, restart_app, run_command
    - Configuration: get_config, set_config
    - Domains: add_custom_domain, remove_custom_domain, list_domains
    - Database Services: create_database, list_databases, unlink_database
    """,
)


# Import tools to register them
from kimidokku.tools import apps


def get_mcp_server() -> FastMCP:
    """Get MCP server instance."""
    return mcp
