"""MCP Prompts for deployment workflows."""

from kimidokku.mcp_server import mcp


@mcp.prompt()
def deployment_workflow(app_name: str) -> str:
    """Deployment checklist for AI agents."""
    return f"""# Deployment Workflow for '{app_name}'

You are deploying to Dokku app '{app_name}'. Follow this checklist:

## Pre-deployment Checks
1. **Check current status** - Use `get_app_status(app_name="{app_name}")`
2. **If crashed, investigate logs** - Use `get_logs(app_name="{app_name}", lines=100)`
3. **Verify critical ENV vars** - Use `get_config(app_name="{app_name}")`
   - Ensure DATABASE_URL is set (if using database)
   - Ensure all required secrets are configured
4. **Check recent deploy history** - Review last deployment status

## Deployment
5. **Execute deployment**
   - For git: `deploy_git(app_name="{app_name}", branch="main")`
   - For image: `deploy_image(app_name="{app_name}", image_url="...")`

## Post-deployment Verification
6. **Poll status every 10s for up to 2 minutes**
   - Use `get_app_status(app_name="{app_name}")`
7. **Verify health by checking logs**
   - Use `get_logs(app_name="{app_name}", lines=50)`
   - Look for "Server started", "Listening on port", or similar indicators
8. **Confirm app status is 'running'**

## Rollback (if needed)
9. If deployment fails:
   - Check logs for error details
   - Consider restarting: `restart_app(app_name="{app_name}")`
   - Or revert config changes if applicable

Remember: Always verify before declaring success!
"""


@mcp.prompt()
def debug_crashed_app(app_name: str) -> str:
    """Diagnostic steps for crashed applications."""
    return f"""# Debug Crashed App: '{app_name}'

App '{app_name}' is not running. Follow these diagnostic steps:

## Step 1: Get Recent Logs
Use `get_logs(app_name="{app_name}", lines=100)`
- Filter for ERROR or FATAL messages
- Look for stack traces
- Check the last few lines before crash

## Step 2: Check Recent Config Changes
Use `get_config(app_name="{app_name}")`
- Compare with previous working configuration
- Check if any sensitive values were changed
- Verify all required ENV vars are present

## Step 3: Verify Database Connectivity (if applicable)
Use `run_command(app_name="{app_name}", command="python -c 'import os; print(\"DB_URL set:\", \"DATABASE_URL\" in os.environ)'")`
- Check if DATABASE_URL or similar is accessible
- For Rails apps: `rails db:migrate:status`
- For Django apps: `python manage.py showmigrations`

## Step 4: Analyze Common Issues

### If OOM (Out of Memory) detected in logs:
- Suggest: Restart app to free memory
- Use: `restart_app(app_name="{app_name}")`
- Long-term: Consider scaling or memory optimization

### If missing module/dependency error:
- Check: Was requirements.txt/package.json updated?
- Suggest: Rebuild with `deploy_git` to reinstall dependencies
- Check: Verify the correct branch/commit is deployed

### If database connection error:
- Verify: `get_config` shows correct DATABASE_URL
- Check: Database service is running (via dokku)
- Test: Connection from app container

### If port binding error:
- Verify: App listens on $PORT (not hardcoded)
- Check: Multiple processes not conflicting

## Step 5: Attempt Recovery

### Option A: Restart
```
restart_app(app_name="{app_name}")
```

### Option B: Check running processes
```
run_command(app_name="{app_name}", command="ps aux")
```

### Option C: Test one-off command
```
run_command(app_name="{app_name}", command="echo 'Container is accessible'")
```

## Step 6: Document Findings
Once root cause is identified:
1. Note the specific error
2. Document the fix applied
3. Consider preventive measures
"""
