"""Pydantic models for data validation and serialization."""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


class AppStatus(str, Enum):
    """Application status enum."""

    RUNNING = "running"
    STOPPED = "stopped"
    CRASHED = "crashed"
    DEPLOYING = "deploying"
    ERROR = "error"


class TLSStatus(str, Enum):
    """TLS certificate status enum."""

    ACTIVE = "active"
    EXPIRING = "expiring"
    ERROR = "error"
    NONE = "none"


class DeployStatus(str, Enum):
    """Deployment status enum."""

    SUCCESS = "success"
    FAILED = "failed"
    IN_PROGRESS = "in_progress"


class TriggeredBy(str, Enum):
    """Who triggered the deployment."""

    MCP = "mcp"
    WEBHOOK = "webhook"
    UI = "ui"


class DBType(str, Enum):
    """Database service types."""

    POSTGRES = "postgres"
    REDIS = "redis"
    MYSQL = "mysql"
    MONGO = "mongo"


# ============== API Key Models ==============


class APIKeyBase(BaseModel):
    """Base API Key model."""

    name: Optional[str] = None
    max_apps: int = Field(default=10, ge=1, le=100)


class APIKeyCreate(APIKeyBase):
    """API Key creation model."""

    pass


class APIKeyResponse(APIKeyBase):
    """API Key response model."""

    id: str
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


class APIKeyWithSecret(APIKeyResponse):
    """API Key response with the actual key (shown only once)."""

    key: str


# ============== App Models ==============


class AppBase(BaseModel):
    """Base App model."""

    name: str = Field(..., pattern=r"^[a-z0-9-]+$")
    git_url: Optional[str] = None
    branch: str = "main"

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate app name format."""
        if not v:
            raise ValueError("App name cannot be empty")
        if len(v) > 63:
            raise ValueError("App name must be 63 characters or less")
        return v


class AppCreate(AppBase):
    """App creation model."""

    api_key_id: str


class AppResponse(AppBase):
    """App response model."""

    auto_domain: str
    status: AppStatus
    created_at: datetime
    last_deploy_at: Optional[datetime] = None
    tls_status: TLSStatus
    tls_expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AppStatusResponse(BaseModel):
    """Detailed app status response."""

    name: str
    status: AppStatus
    auto_domain: str
    custom_domains: list[str] = []
    containers: list[dict[str, Any]] = []
    git_ref: Optional[str] = None
    tls_expires_in_days: Optional[int] = None


class AppListResponse(BaseModel):
    """App list item response."""

    name: str
    auto_domain: str
    custom_domains: list[str] = []
    status: AppStatus
    last_deploy_at: Optional[datetime] = None
    tls_status: TLSStatus


# ============== Domain Models ==============


class CustomDomainBase(BaseModel):
    """Base custom domain model."""

    domain: str


class CustomDomainCreate(CustomDomainBase):
    """Custom domain creation model."""

    pass


class CustomDomainResponse(CustomDomainBase):
    """Custom domain response model."""

    id: int
    tls_active: bool
    expires_in_days: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DomainsResponse(BaseModel):
    """All domains for an app."""

    auto_domain: str
    custom_domains: list[CustomDomainResponse] = []


# ============== Database Service Models ==============


class DBServiceBase(BaseModel):
    """Base database service model."""

    db_type: DBType
    env_var_name: str = "DATABASE_URL"


class DBServiceCreate(DBServiceBase):
    """Database service creation model."""

    pass


class DBServiceResponse(DBServiceBase):
    """Database service response model."""

    id: str
    created_at: datetime
    connection_string_masked: str

    class Config:
        from_attributes = True


# ============== Config Models ==============


class ConfigVariable(BaseModel):
    """Single config variable."""

    key: str
    value: str
    is_secret: bool = False


class ConfigResponse(BaseModel):
    """App configuration response."""

    variables: dict[str, str]
    secrets_masked: list[str] = []


class ConfigSetRequest(BaseModel):
    """Request to set config variables."""

    variables: dict[str, str]
    restart: bool = True


# ============== Deploy Log Models ==============


class DeployLogResponse(BaseModel):
    """Deploy log entry response."""

    id: int
    triggered_by: TriggeredBy
    git_ref: Optional[str] = None
    status: DeployStatus
    started_at: datetime
    finished_at: Optional[datetime] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


# ============== Webhook Models ==============


class GitHubWebhookPayload(BaseModel):
    """GitHub webhook payload."""

    ref: str
    after: str
    repository: dict[str, Any]


# ============== CrowdSec Models ==============


class CrowdSecBan(BaseModel):
    """CrowdSec ban entry."""

    ip: str
    country: Optional[str] = None
    scenario: Optional[str] = None
    banned_at: datetime
    expires_at: datetime

    class Config:
        from_attributes = True
