"""Dokku integration utilities."""

import asyncio
from kimidokku.database import db


async def get_dokku_apps() -> list[str]:
    """Get list of apps from Dokku."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "dokku",
            "apps:list",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=10.0)

        if proc.returncode != 0:
            return []

        # Parse output: skip header line and empty lines
        lines = stdout.decode().strip().split("\n")
        apps = []
        for line in lines[1:]:  # Skip "=====> My Apps" header
            line = line.strip()
            if line and not line.startswith("="):
                apps.append(line)

        return apps
    except Exception:
        return []


async def get_app_status_from_dokku(app_name: str) -> str:
    """Get app status from Dokku ps:report."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "dokku",
            "ps:report",
            app_name,
            "--format",
            "json",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=10.0)

        if proc.returncode != 0:
            return "stopped"

        import json

        report = json.loads(stdout.decode())

        # Check if any process is running
        if report and len(report) > 0:
            # Check process status
            for key, value in report[0].items():
                if "status" in key.lower():
                    if "running" in str(value).lower():
                        return "running"

        return "stopped"
    except Exception:
        return "stopped"


async def get_app_domains_from_dokku(app_name: str) -> list[str]:
    """Get custom domains for app from Dokku."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "dokku",
            "domains:report",
            app_name,
            "--format",
            "json",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=10.0)

        if proc.returncode != 0:
            return []

        import json

        report = json.loads(stdout.decode())

        domains = []
        if report and len(report) > 0:
            # Get domains from report
            domains_data = report[0].get("Domains", {})
            if domains_data:
                app_domains = domains_data.get("AppDomains", [])
                global_domains = domains_data.get("GlobalDomains", [])
                domains = app_domains + global_domains

        return domains
    except Exception:
        return []


async def sync_apps_from_dokku() -> dict:
    """
    Synchronize apps from Dokku to KimiDokku database.

    Returns:
        Dict with stats: {'added': int, 'updated': int, 'total': int}
    """
    from kimidokku.config import get_settings

    # Get apps from Dokku
    dokku_apps = await get_dokku_apps()

    if not dokku_apps:
        return {"added": 0, "updated": 0, "total": 0}

    # Get existing apps from database
    existing_apps_result = await db.fetch_all("SELECT name, status FROM apps")
    existing_apps = {row["name"]: row for row in existing_apps_result}

    settings = get_settings()
    added = 0
    updated = 0

    for app_name in dokku_apps:
        # Skip the 'kimidokku' app itself
        if app_name == "kimidokku":
            continue

        # Get app status from Dokku
        status = await get_app_status_from_dokku(app_name)

        # Get domains
        domains = await get_app_domains_from_dokku(app_name)

        # Determine auto domain (first domain that matches pattern)
        auto_domain = f"{app_name}.{settings.kimidokku_domain}"
        custom_domains = []

        for domain in domains:
            if domain == auto_domain or domain.endswith(f".{settings.kimidokku_domain}"):
                auto_domain = domain
            else:
                custom_domains.append(domain)

        if app_name in existing_apps:
            # Update existing app status if changed
            existing_status = existing_apps[app_name]["status"]
            if existing_status != status:
                await db.execute("UPDATE apps SET status = ? WHERE name = ?", (status, app_name))
                updated += 1

            # Update custom domains
            # First remove existing custom domains
            await db.execute("DELETE FROM custom_domains WHERE app_name = ?", (app_name,))
            # Add new custom domains
            for domain in custom_domains:
                try:
                    await db.execute(
                        """INSERT INTO custom_domains (app_name, domain) 
                           VALUES (?, ?)""",
                        (app_name, domain),
                    )
                except Exception:
                    pass  # Domain might already exist
        else:
            # Insert new app with no api_key_id (external app)
            await db.execute(
                """INSERT INTO apps 
                   (name, api_key_id, auto_domain, status, git_url, branch)
                   VALUES (?, NULL, ?, ?, NULL, 'main')""",
                (app_name, auto_domain, status),
            )

            # Add custom domains
            for domain in custom_domains:
                try:
                    await db.execute(
                        """INSERT INTO custom_domains (app_name, domain) 
                           VALUES (?, ?)""",
                        (app_name, domain),
                    )
                except Exception:
                    pass

            added += 1

    # Remove apps from database that no longer exist in Dokku
    # But only if they have no api_key_id (external apps)
    for existing_name in existing_apps:
        if existing_name not in dokku_apps:
            # Check if it's an external app (no api_key_id)
            app_record = await db.fetch_one(
                "SELECT api_key_id FROM apps WHERE name = ?", (existing_name,)
            )
            if app_record and app_record["api_key_id"] is None:
                await db.execute("DELETE FROM apps WHERE name = ?", (existing_name,))

    return {"added": added, "updated": updated, "total": len(dokku_apps)}
