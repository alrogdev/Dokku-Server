"""Web Admin UI routes."""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from kimidokku.auth import verify_basic_auth
from kimidokku.config import get_settings
from kimidokku.database import db

router = APIRouter(tags=["ui"])


def get_templates(request: Request):
    """Get templates from app state."""
    return request.app.state.templates


@router.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    templates=Depends(get_templates),
    username: str = Depends(verify_basic_auth),
):
    """Dashboard page."""
    # Get stats
    stats_result = await db.fetch_one("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN status = 'running' THEN 1 ELSE 0 END) as running,
            SUM(CASE WHEN status = 'stopped' THEN 1 ELSE 0 END) as stopped,
            SUM(CASE WHEN status = 'crashed' THEN 1 ELSE 0 END) as crashed,
            SUM(CASE WHEN status = 'deploying' THEN 1 ELSE 0 END) as deploying,
            SUM(CASE WHEN tls_status IN ('expiring', 'error') THEN 1 ELSE 0 END) as tls_expiring
        FROM apps
    """)

    stats = {
        "total_apps": stats_result["total"] or 0,
        "running": stats_result["running"] or 0,
        "stopped": stats_result["stopped"] or 0,
        "crashed": stats_result["crashed"] or 0,
        "deploying": stats_result["deploying"] or 0,
        "tls_expiring": stats_result["tls_expiring"] or 0,
        "bans": 0,  # Will be updated when CrowdSec is implemented
    }

    # Get recent deploys
    recent_deploys = await db.fetch_all("""
        SELECT 
            d.app_name,
            d.triggered_by,
            d.status,
            d.started_at,
            d.git_ref
        FROM deploy_logs d
        ORDER BY d.started_at DESC
        LIMIT 10
    """)

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "stats": stats,
            "recent_deploys": recent_deploys,
            "version": "0.1.0",
        },
    )
