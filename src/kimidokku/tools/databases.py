"""Database Services MCP Tools."""

import asyncio
import uuid

from kimidokku.database import db
from kimidokku.mcp_server import mcp
from kimidokku.models import DBType


@mcp.tool()
async def create_database(
    app_name: str,
    api_key_id: str,
    db_type: str,
    version: str = "latest",
) -> dict:
    """
    Create and link database service to app.
    Steps:
      1. dokku {db_type}:create {service_name} {version}
      2. dokku {db_type}:link {service_name} {app_name}
      3. Store connection info, update apps.db_services
    Returns: service_name, env_var, connection_string_masked
    """
    # Verify app ownership
    app = await db.fetch_one(
        "SELECT name FROM apps WHERE name = ? AND api_key_id = ?",
        (app_name, api_key_id),
    )

    if not app:
        raise ValueError(f"App '{app_name}' not found or access denied")

    # Validate db_type
    try:
        db_type_enum = DBType(db_type.lower())
    except ValueError:
        raise ValueError(
            f"Invalid db_type '{db_type}'. Must be one of: postgres, redis, mysql, mongo"
        )

    # Generate service name
    service_name = f"{db_type_enum.value}-{app_name}-{uuid.uuid4().hex[:8]}"

    try:
        # Step 1: Create service
        create_proc = await asyncio.create_subprocess_exec(
            "dokku",
            f"{db_type_enum.value}:create",
            service_name,
            version,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await create_proc.communicate()

        if create_proc.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown error"
            raise RuntimeError(f"Failed to create database service: {error_msg}")

        # Step 2: Link service to app
        link_proc = await asyncio.create_subprocess_exec(
            "dokku",
            f"{db_type_enum.value}:link",
            service_name,
            app_name,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await link_proc.communicate()

        if link_proc.returncode != 0:
            # Try to destroy the service we just created
            await asyncio.create_subprocess_exec(
                "dokku",
                f"{db_type_enum.value}:destroy",
                service_name,
                "--force",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            error_msg = stderr.decode() if stderr else "Unknown error"
            raise RuntimeError(f"Failed to link database service: {error_msg}")

        # Step 3: Store in database
        env_var = _get_default_env_var(db_type_enum)
        await db.execute(
            """
            INSERT INTO db_services (id, app_name, db_type, env_var_name)
            VALUES (?, ?, ?, ?)
            """,
            (service_name, app_name, db_type_enum.value, env_var),
        )

        return {
            "service_name": service_name,
            "db_type": db_type_enum.value,
            "env_var": env_var,
            "connection_string_masked": f"${env_var} (set in app environment)",
            "message": f"{db_type_enum.value} service '{service_name}' created and linked to '{app_name}'",
        }

    except Exception as e:
        raise RuntimeError(f"Failed to create database: {e}")


@mcp.tool()
async def list_databases(app_name: str, api_key_id: str) -> list[dict]:
    """
    List linked databases with types and status.
    Returns: [{service_name, db_type, env_var, created_at}]
    """
    # Verify app ownership
    app = await db.fetch_one(
        "SELECT name FROM apps WHERE name = ? AND api_key_id = ?",
        (app_name, api_key_id),
    )

    if not app:
        raise ValueError(f"App '{app_name}' not found or access denied")

    # Get linked databases
    services = await db.fetch_all(
        """
        SELECT id, db_type, env_var_name, created_at
        FROM db_services
        WHERE app_name = ?
        ORDER BY created_at DESC
        """,
        (app_name,),
    )

    return [
        {
            "service_name": s["id"],
            "db_type": s["db_type"],
            "env_var": s["env_var_name"],
            "created_at": s["created_at"],
        }
        for s in services
    ]


@mcp.tool()
async def unlink_database(
    app_name: str,
    api_key_id: str,
    service_name: str,
    preserve_data: bool = True,
) -> dict:
    """
    Unlink service from app. If preserve_data=false, also deletes service.
    Returns: success, message
    """
    # Verify app ownership
    app = await db.fetch_one(
        "SELECT name FROM apps WHERE name = ? AND api_key_id = ?",
        (app_name, api_key_id),
    )

    if not app:
        raise ValueError(f"App '{app_name}' not found or access denied")

    # Get service info
    service = await db.fetch_one(
        "SELECT db_type FROM db_services WHERE id = ? AND app_name = ?",
        (service_name, app_name),
    )

    if not service:
        raise ValueError(f"Service '{service_name}' not found for app '{app_name}'")

    db_type = service["db_type"]

    try:
        # Unlink service
        unlink_proc = await asyncio.create_subprocess_exec(
            "dokku",
            f"{db_type}:unlink",
            service_name,
            app_name,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await unlink_proc.communicate()

        # Delete from database
        await db.execute(
            "DELETE FROM db_services WHERE id = ?",
            (service_name,),
        )

        if not preserve_data:
            # Destroy the service
            destroy_proc = await asyncio.create_subprocess_exec(
                "dokku",
                f"{db_type}:destroy",
                service_name,
                "--force",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await destroy_proc.communicate()

            return {
                "success": True,
                "message": f"Service '{service_name}' unlinked and destroyed",
            }

        return {
            "success": True,
            "message": f"Service '{service_name}' unlinked (data preserved)",
        }

    except Exception as e:
        raise RuntimeError(f"Failed to unlink database: {e}")


def _get_default_env_var(db_type: DBType) -> str:
    """Get default environment variable name for database type."""
    env_vars = {
        DBType.POSTGRES: "DATABASE_URL",
        DBType.REDIS: "REDIS_URL",
        DBType.MYSQL: "DATABASE_URL",
        DBType.MONGO: "MONGODB_URI",
    }
    return env_vars.get(db_type, "DATABASE_URL")
