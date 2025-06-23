"""
API v2 Router for self-service configuration management.
🔧 Client configuration endpoints with database backend.
"""

import logging
from typing import Annotated, Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from application.dependencies.auth import require_auth
from core.authentication.context import SecurityContext
from infrastructure.config.database_bridge import DatabaseConfigBridge
from infrastructure.database.connection import get_database_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/config", tags=["Configuration Management"])


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================


class ClientCreateRequest(BaseModel):
    """Request model for creating a new client."""

    id: str
    name: str
    industry: str
    timezone: str = "UTC"
    business_hours: str = "9-17"
    status: str = "active"


class ClientResponse(BaseModel):
    """Response model for client information."""

    id: str
    name: str
    industry: str
    status: str
    timezone: str
    business_hours: str
    created_at: str
    updated_at: str


class RoutingRuleRequest(BaseModel):
    """Request model for routing rule updates."""

    email_address: EmailStr


class RoutingRulesResponse(BaseModel):
    """Response model for routing rules."""

    rules: Dict[str, str]  # category -> email_address


class BrandingRequest(BaseModel):
    """Request model for branding updates."""

    company_name: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    logo_url: Optional[str] = None
    email_signature: Optional[str] = None
    footer_text: Optional[str] = None
    colors: Optional[Dict[str, Any]] = None


class BrandingResponse(BaseModel):
    """Response model for branding configuration."""

    company_name: str
    primary_color: str
    secondary_color: str
    logo_url: Optional[str]
    email_signature: str
    footer_text: Optional[str]
    colors: Optional[Dict[str, Any]]


class ResponseTimeRequest(BaseModel):
    """Request model for response time updates."""

    target_response: str
    business_hours_only: bool = True


class ResponseTimesResponse(BaseModel):
    """Response model for response times."""

    times: Dict[str, Dict[str, Any]]  # category -> {target_response, business_hours_only}


class AIPromptRequest(BaseModel):
    """Request model for AI prompt updates."""

    prompt_content: str


class AIPromptResponse(BaseModel):
    """Response model for AI prompt."""

    prompt_type: str
    prompt_content: str
    version: int
    updated_at: str


# =============================================================================
# CLIENT MANAGEMENT
# =============================================================================


@router.get("/clients/{client_id}", response_model=ClientResponse)
async def get_client_config(
    client_id: Annotated[str, Path(description="Client ID")],
    db_session: Annotated[Session, Depends(get_database_session)],
    security_context: Annotated[SecurityContext, Depends(require_auth)],
):
    """Get complete client configuration."""
    # Check permission
    if not security_context.has_permission("client:read", client_id):
        raise HTTPException(
            status_code=403, detail=f"Permission denied: client:read for {client_id}"
        )

    config_bridge = DatabaseConfigBridge(db_session)
    client = config_bridge.get_client(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    return ClientResponse(
        id=client.id,
        name=client.name,
        industry=client.industry,
        status=client.status,
        timezone=client.timezone,
        business_hours=client.business_hours,
        created_at=client.created_at.isoformat(),
        updated_at=client.updated_at.isoformat(),
    )


@router.post("/clients", response_model=ClientResponse, status_code=201)
async def create_client(
    request: ClientCreateRequest,
    db_session: Annotated[Session, Depends(get_database_session)],
    security_context: Annotated[SecurityContext, Depends(require_auth)],
):
    """Create a new client configuration."""
    # Check permission
    if not security_context.has_permission("clients:write"):
        raise HTTPException(status_code=403, detail="Permission denied: clients:write")

    config_bridge = DatabaseConfigBridge(db_session)

    # Check if client already exists
    existing = config_bridge.get_client(request.id)
    if existing:
        raise HTTPException(status_code=409, detail="Client already exists")

    client_data = request.model_dump()
    client = config_bridge.create_client(client_data, security_context.username)
    db_session.commit()

    return ClientResponse(
        id=client.id,
        name=client.name,
        industry=client.industry,
        status=client.status,
        timezone=client.timezone,
        business_hours=client.business_hours,
        created_at=client.created_at.isoformat(),
        updated_at=client.updated_at.isoformat(),
    )


@router.put("/clients/{client_id}", response_model=ClientResponse)
async def update_client_config(
    client_id: Annotated[str, Path(description="Client ID")],
    updates: Dict[str, Any],
    db_session: Annotated[Session, Depends(get_database_session)],
    security_context: Annotated[SecurityContext, Depends(require_auth)],
):
    """Update client configuration."""
    # Check permission
    if not security_context.has_permission("client:write", client_id):
        raise HTTPException(
            status_code=403, detail=f"Permission denied: client:write for {client_id}"
        )

    config_bridge = DatabaseConfigBridge(db_session)
    client = config_bridge.update_client(client_id, updates, security_context.username)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    db_session.commit()

    return ClientResponse(
        id=client.id,
        name=client.name,
        industry=client.industry,
        status=client.status,
        timezone=client.timezone,
        business_hours=client.business_hours,
        created_at=client.created_at.isoformat(),
        updated_at=client.updated_at.isoformat(),
    )


# =============================================================================
# ROUTING RULES
# =============================================================================


@router.get("/clients/{client_id}/routing", response_model=RoutingRulesResponse)
async def get_routing_rules(
    client_id: Annotated[str, Path(description="Client ID")],
    db_session: Annotated[Session, Depends(get_database_session)],
    security_context: Annotated[SecurityContext, Depends(require_auth)],
):
    """Get routing rules for a client."""
    # Check permission
    if not security_context.has_permission("routing:read", client_id):
        raise HTTPException(
            status_code=403, detail=f"Permission denied: routing:read for {client_id}"
        )

    config_bridge = DatabaseConfigBridge(db_session)
    rules = config_bridge.get_routing_rules(client_id)
    rules_dict = {rule.category: rule.email_address for rule in rules}

    return RoutingRulesResponse(rules=rules_dict)


@router.put("/clients/{client_id}/routing/{category}", response_model=Dict[str, str])
async def update_routing_rule(
    client_id: Annotated[str, Path(description="Client ID")],
    category: Annotated[str, Path(description="Email category")],
    request: RoutingRuleRequest,
    db_session: Annotated[Session, Depends(get_database_session)],
    security_context: Annotated[SecurityContext, Depends(require_auth)],
):
    """Update routing rule for a specific category."""
    # Check permission
    if not security_context.has_permission("routing:write", client_id):
        raise HTTPException(
            status_code=403, detail=f"Permission denied: routing:write for {client_id}"
        )

    config_bridge = DatabaseConfigBridge(db_session)
    rule = config_bridge.update_routing_rule(
        client_id, category, request.email_address, security_context.username
    )
    db_session.commit()

    return {"category": category, "email_address": rule.email_address}


@router.delete("/clients/{client_id}/routing/{category}")
async def delete_routing_rule(
    client_id: Annotated[str, Path(description="Client ID")],
    category: Annotated[str, Path(description="Email category")],
    db_session: Annotated[Session, Depends(get_database_session)],
    security_context: Annotated[SecurityContext, Depends(require_auth)],
):
    """Delete routing rule for a specific category."""
    # Check permission
    if not security_context.has_permission("routing:delete", client_id):
        raise HTTPException(
            status_code=403, detail=f"Permission denied: routing:delete for {client_id}"
        )

    config_bridge = DatabaseConfigBridge(db_session)
    success = config_bridge.delete_routing_rule(client_id, category, security_context.username)
    if not success:
        raise HTTPException(status_code=404, detail="Routing rule not found")

    db_session.commit()
    return {"message": f"Routing rule for {category} deleted"}


# =============================================================================
# BRANDING
# =============================================================================


@router.get("/clients/{client_id}/branding", response_model=BrandingResponse)
async def get_branding_config(
    client_id: Annotated[str, Path(description="Client ID")],
    db_session: Annotated[Session, Depends(get_database_session)],
    security_context: Annotated[SecurityContext, Depends(require_auth)],
):
    """Get branding configuration for a client."""
    # Check permission
    if not security_context.has_permission("branding:read", client_id):
        raise HTTPException(
            status_code=403, detail=f"Permission denied: branding:read for {client_id}"
        )

    config_bridge = DatabaseConfigBridge(db_session)
    branding = config_bridge.get_branding(client_id)
    if not branding:
        raise HTTPException(status_code=404, detail="Branding configuration not found")

    return BrandingResponse(
        company_name=branding.company_name,
        primary_color=branding.primary_color,
        secondary_color=branding.secondary_color,
        logo_url=branding.logo_url,
        email_signature=branding.email_signature,
        footer_text=branding.footer_text,
        colors=branding.colors,
    )


@router.put("/clients/{client_id}/branding", response_model=BrandingResponse)
async def update_branding_config(
    client_id: Annotated[str, Path(description="Client ID")],
    request: BrandingRequest,
    db_session: Annotated[Session, Depends(get_database_session)],
    security_context: Annotated[SecurityContext, Depends(require_auth)],
):
    """Update branding configuration for a client."""
    # Check permission
    if not security_context.has_permission("branding:write", client_id):
        raise HTTPException(
            status_code=403, detail=f"Permission denied: branding:write for {client_id}"
        )

    # Filter out None values
    branding_data = {k: v for k, v in request.model_dump().items() if v is not None}

    config_bridge = DatabaseConfigBridge(db_session)
    branding = config_bridge.update_branding(client_id, branding_data, security_context.username)
    db_session.commit()

    return BrandingResponse(
        company_name=branding.company_name,
        primary_color=branding.primary_color,
        secondary_color=branding.secondary_color,
        logo_url=branding.logo_url,
        email_signature=branding.email_signature,
        footer_text=branding.footer_text,
        colors=branding.colors,
    )


# =============================================================================
# RESPONSE TIMES
# =============================================================================


@router.get("/clients/{client_id}/response-times", response_model=ResponseTimesResponse)
async def get_response_times(
    client_id: Annotated[str, Path(description="Client ID")],
    db_session: Annotated[Session, Depends(get_database_session)],
    security_context: Annotated[SecurityContext, Depends(require_auth)],
):
    """Get response time configuration for a client."""
    # Check permission
    if not security_context.has_permission("response_times:read", client_id):
        raise HTTPException(
            status_code=403, detail=f"Permission denied: response_times:read for {client_id}"
        )

    config_bridge = DatabaseConfigBridge(db_session)
    response_times = config_bridge.get_response_times(client_id)
    times_dict = {
        rt.category: {
            "target_response": rt.target_response,
            "business_hours_only": rt.business_hours_only,
        }
        for rt in response_times
    }

    return ResponseTimesResponse(times=times_dict)


@router.put("/clients/{client_id}/response-times/{category}", response_model=Dict[str, Any])
async def update_response_time(
    client_id: Annotated[str, Path(description="Client ID")],
    category: Annotated[str, Path(description="Email category")],
    request: ResponseTimeRequest,
    db_session: Annotated[Session, Depends(get_database_session)],
    security_context: Annotated[SecurityContext, Depends(require_auth)],
):
    """Update response time for a specific category."""
    # Check permission
    if not security_context.has_permission("response_times:write", client_id):
        raise HTTPException(
            status_code=403, detail=f"Permission denied: response_times:write for {client_id}"
        )

    config_bridge = DatabaseConfigBridge(db_session)
    response_time = config_bridge.update_response_time(
        client_id,
        category,
        request.target_response,
        request.business_hours_only,
        security_context.username,
    )
    db_session.commit()

    return {
        "category": category,
        "target_response": response_time.target_response,
        "business_hours_only": response_time.business_hours_only,
    }


# =============================================================================
# AI PROMPTS
# =============================================================================


@router.get("/clients/{client_id}/ai-prompts/{prompt_type}", response_model=AIPromptResponse)
async def get_ai_prompt(
    client_id: Annotated[str, Path(description="Client ID")],
    prompt_type: Annotated[str, Path(description="Prompt type")],
    db_session: Annotated[Session, Depends(get_database_session)],
    security_context: Annotated[SecurityContext, Depends(require_auth)],
):
    """Get AI prompt for a specific type."""
    # Check permission
    if not security_context.has_permission("ai_prompts:read", client_id):
        raise HTTPException(
            status_code=403, detail=f"Permission denied: ai_prompts:read for {client_id}"
        )

    config_bridge = DatabaseConfigBridge(db_session)
    prompt = config_bridge.get_ai_prompt(client_id, prompt_type)
    if not prompt:
        raise HTTPException(status_code=404, detail="AI prompt not found")

    return AIPromptResponse(
        prompt_type=prompt.prompt_type,
        prompt_content=prompt.prompt_content,
        version=prompt.version,
        updated_at=prompt.updated_at.isoformat(),
    )


@router.put("/clients/{client_id}/ai-prompts/{prompt_type}", response_model=AIPromptResponse)
async def update_ai_prompt(
    client_id: Annotated[str, Path(description="Client ID")],
    prompt_type: Annotated[str, Path(description="Prompt type")],
    request: AIPromptRequest,
    db_session: Annotated[Session, Depends(get_database_session)],
    security_context: Annotated[SecurityContext, Depends(require_auth)],
):
    """Update AI prompt for a specific type."""
    # Check permission
    if not security_context.has_permission("ai_prompts:write", client_id):
        raise HTTPException(
            status_code=403, detail=f"Permission denied: ai_prompts:write for {client_id}"
        )

    config_bridge = DatabaseConfigBridge(db_session)
    prompt = config_bridge.update_ai_prompt(
        client_id, prompt_type, request.prompt_content, security_context.username
    )
    db_session.commit()

    return AIPromptResponse(
        prompt_type=prompt.prompt_type,
        prompt_content=prompt.prompt_content,
        version=prompt.version,
        updated_at=prompt.updated_at.isoformat(),
    )


# =============================================================================
# CONFIGURATION SYNC
# =============================================================================


@router.post("/clients/{client_id}/sync-from-yaml")
async def sync_from_yaml(
    client_id: Annotated[str, Path(description="Client ID")],
    db_session: Annotated[Session, Depends(get_database_session)],
    security_context: Annotated[SecurityContext, Depends(require_auth)],
):
    """Sync client configuration from YAML files to database."""
    # Check permission
    if not security_context.has_permission("client:admin", client_id):
        raise HTTPException(
            status_code=403, detail=f"Permission denied: client:admin for {client_id}"
        )

    config_bridge = DatabaseConfigBridge(db_session)
    success = config_bridge.sync_from_yaml(client_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to sync from YAML")

    return {"message": f"Successfully synced {client_id} from YAML to database"}


@router.get("/clients/{client_id}/audit-trail")
async def get_audit_trail(
    client_id: Annotated[str, Path(description="Client ID")],
    db_session: Annotated[Session, Depends(get_database_session)],
    security_context: Annotated[SecurityContext, Depends(require_auth)],
    limit: Annotated[int, Query(description="Number of records to return")] = 50,
):
    """Get audit trail for client configuration changes."""
    # Check permission
    if not security_context.has_permission("client:read", client_id):
        raise HTTPException(
            status_code=403, detail=f"Permission denied: client:read for {client_id}"
        )

    config_bridge = DatabaseConfigBridge(db_session)
    changes = config_bridge.get_audit_trail(client_id, limit)

    return {
        "changes": [
            {
                "id": change.id,
                "change_type": change.change_type,
                "table_name": change.table_name,
                "record_id": change.record_id,
                "old_values": change.old_values,
                "new_values": change.new_values,
                "changed_by": change.changed_by,
                "created_at": change.created_at.isoformat(),
            }
            for change in changes
        ]
    }
