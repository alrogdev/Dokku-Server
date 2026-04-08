"""Tests for MCP resources and prompts."""

from kimidokku.mcp_server import get_mcp_server


class TestMCPResources:
    """Test MCP resources."""

    def test_resources_registered(self):
        """Test that resources are registered."""
        mcp = get_mcp_server()
        components = mcp._local_provider._components

        # Resource templates have 'template:' prefix in components
        assert "template:dokku://config/{app_name}{?api_key}@" in components
        assert "template:dokku://logs/{app_name}/recent{?api_key}@" in components
        assert "template:dokku://domains/{app_name}{?api_key}@" in components

    def test_prompts_registered(self):
        """Test that prompts are registered."""
        mcp = get_mcp_server()
        components = mcp._local_provider._components

        # Prompts have 'prompt:' prefix in components
        assert "prompt:deployment_workflow@" in components
        assert "prompt:debug_crashed_app@" in components
