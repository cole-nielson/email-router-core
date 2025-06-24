"""
Webhook handlers for incoming emails with multi-tenant support.
🎯 CORE MVP ENDPOINT: /webhooks/mailgun/inbound
"""

import hashlib
import hmac
import logging
from typing import Annotated, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status

from application.middleware.auth import DualAuthUser, get_dual_auth_user
from core.clients.manager import ClientManager, get_client_manager
from core.dashboard.service import DashboardService, get_dashboard_service
from core.email.classifier import AIClassifier, get_ai_classifier
from core.email.router import RoutingEngine, get_routing_engine
from core.email.service import (
    EmailService,
    get_email_service,
)
from infrastructure.config.manager import get_app_config
from infrastructure.external.mailgun import forward_to_team, send_auto_reply

logger = logging.getLogger(__name__)
router = APIRouter()


def verify_mailgun_signature(timestamp: str, token: str, signature: str, api_key: str) -> bool:
    """
    Verify Mailgun webhook signature using HMAC-SHA256.

    Args:
        timestamp: Mailgun timestamp
        token: Mailgun token
        signature: Mailgun signature
        api_key: Mailgun API key

    Returns:
        True if signature is valid, False otherwise
    """
    if not all([timestamp, token, signature, api_key]):
        logger.warning("Missing required signature parameters")
        return False

    try:
        # Create the signing string as per Mailgun documentation
        signing_string = f"{timestamp}{token}"

        # Create HMAC signature
        expected_signature = hmac.new(
            key=api_key.encode("utf-8"),
            msg=signing_string.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).hexdigest()

        # Compare signatures using constant-time comparison
        return hmac.compare_digest(signature, expected_signature)

    except Exception as e:
        logger.error(f"Error verifying Mailgun signature: {e}")
        return False


@router.post("/mailgun/inbound", response_model=None)
async def mailgun_inbound_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    client_manager: Annotated[ClientManager, Depends(get_client_manager)],
    ai_classifier: Annotated[AIClassifier, Depends(get_ai_classifier)],
    routing_engine: Annotated[RoutingEngine, Depends(get_routing_engine)],
    dashboard_service: Annotated[DashboardService, Depends(get_dashboard_service)],
    email_service: Annotated[EmailService, Depends(get_email_service)],
):
    """
    🎯 CORE MVP ENDPOINT: Receive inbound emails from Mailgun with multi-tenant support

    Flow:
    1. Mailgun → /webhooks/mailgun/inbound
    2. Identify client from recipient domain
    3. Classify email with client-specific Claude prompts
    4. Route to appropriate team member using client rules
    5. Generate personalized auto-reply with client branding
    6. Send auto-reply to customer
    7. Forward with analysis to team member
    """
    try:
        # Extract form data from Mailgun webhook
        form_data = await request.form()

        # Log all received data for debugging
        logger.info(
            f"🔍 Webhook received from {request.client.host if request.client else 'unknown'}"
        )
        logger.info(f"📋 Form fields: {list(form_data.keys())}")

        # Extract Mailgun signature verification fields
        timestamp = form_data.get("timestamp", "")
        token = form_data.get("token", "")
        signature = form_data.get("signature", "")

        # Get Mailgun API key for signature verification
        config = get_app_config()

        # Verify Mailgun signature if we have the webhook signing key
        if config.mailgun_webhook_signing_key:
            if not verify_mailgun_signature(
                timestamp, token, signature, config.mailgun_webhook_signing_key
            ):
                logger.warning(
                    f"❌ Invalid Mailgun signature from {request.client.host if request.client else 'unknown'}"
                )
                logger.warning(
                    f"🔐 Signature details - timestamp: {timestamp}, token: {token[:8]}..., signature: {signature[:8]}..."
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook signature"
                )
            logger.info("✅ Mailgun signature verified successfully")
        else:
            logger.warning(
                "⚠️ Mailgun signature verification skipped - no webhook signing key configured"
            )

        # Extract email data from Mailgun webhook
        email_data = {
            "from": form_data.get("from", "unknown@domain.com"),
            "to": form_data.get("recipient", ""),
            "subject": form_data.get("subject", "No Subject"),
            "body_text": form_data.get("body-plain", ""),
            "body_html": form_data.get("body-html", ""),
            "stripped_text": form_data.get("stripped-text", ""),
            "timestamp": form_data.get("timestamp", ""),
            "message_id": form_data.get("Message-Id", ""),
        }

        logger.info(
            f"📧 Received email from {email_data['from']} to {email_data['to']}: {email_data['subject']}"
        )

        # Identify client from recipient domain
        identification_result = client_manager.identify_client_by_email(email_data["to"])
        client_id = identification_result.client_id if identification_result.is_successful else None

        if client_id:
            logger.info(
                f"🎯 Identified client: {client_id} (confidence: {identification_result.confidence:.2f}, method: {identification_result.method})"
            )
        else:
            logger.warning(f"⚠️ No client identified for recipient: {email_data['to']}")

        # Process email in background (non-blocking)
        background_tasks.add_task(
            process_email_pipeline,
            email_data,
            client_id,
            dynamic_classifier,
            client_manager,
            routing_engine,
            dashboard_service,
            email_service,
        )

        return {"status": "received", "message": "Email processing started", "client_id": client_id}

    except HTTPException:
        # Re-raise HTTP exceptions (like signature verification failures)
        raise
    except Exception as e:
        logger.error(f"❌ Webhook processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Webhook processing failed: {str(e)}",
        )


async def process_email_pipeline(
    email_data: dict,
    client_id: Optional[str],
    dynamic_classifier,
    client_manager,
    routing_engine,
    dashboard_service,
    email_service,
):
    """
    🔄 Background task: Complete multi-tenant email processing pipeline
    """
    try:
        import time

        start_time = time.time()

        logger.info(
            f"🤖 Processing email for client {client_id or 'unknown'}: {email_data['subject']}"
        )

        # Record email received activity
        if client_id:
            await dashboard_service.record_email_processed(
                client_id,
                {
                    "sender": email_data["from"],
                    "recipient": email_data["to"],
                    "subject": email_data["subject"],
                    "status": "received",
                    "stage": "email_received",
                    "success": True,
                },
            )

        # Step 1: AI Classification with client-specific prompts
        classification = await ai_classifier.classify_email(email_data, client_id)

        category = classification.get("category", "general")
        confidence = classification.get("confidence", 0.0)
        method = classification.get("method", "unknown")

        logger.info(f"📋 Classification: {category} ({confidence:.2f}, {method})")

        # Record classification activity
        if client_id:
            await dashboard_service.record_email_processed(
                client_id,
                {
                    "sender": email_data["from"],
                    "recipient": email_data["to"],
                    "subject": email_data["subject"],
                    "category": category,
                    "confidence": confidence,
                    "classification_method": method,
                    "status": "classified",
                    "stage": "classification_complete",
                    "success": True,
                },
            )

        # Step 2: Routing with client-specific rules
        if client_id:
            routing_result = routing_engine.route_email(client_id, classification, email_data)
            forward_to = routing_result["primary_destination"]

            logger.info(f"📍 Routing: {category} → {forward_to}")

            # Record routing activity
            await dashboard_service.record_email_processed(
                client_id,
                {
                    "sender": email_data["from"],
                    "recipient": email_data["to"],
                    "subject": email_data["subject"],
                    "category": category,
                    "routing_destination": forward_to,
                    "status": "routed",
                    "stage": "routing_complete",
                    "success": True,
                },
            )

            # Log special handling if any
            special_handling = routing_result.get("special_handling", [])
            if special_handling:
                logger.info(f"🚨 Special handling: {', '.join(special_handling)}")
        else:
            # Fallback routing when no client identified
            forward_to = "admin@example.com"  # TODO: Make this configurable
            logger.warning("Using fallback routing for unknown client")

        # Step 3: Generate human-like plain text customer response and HTML team analysis
        customer_response, team_analysis = await email_service.generate_plain_text_emails(
            email_data, classification, client_id
        )

        # Step 4: Send plain text customer acknowledgment (human-like)
        await send_auto_reply(email_data, classification, customer_response, client_id)

        # Step 5: Forward HTML team analysis to team
        await forward_to_team(email_data, forward_to, classification, team_analysis, client_id)

        # Record successful completion
        if client_id:
            processing_time_ms = int((time.time() - start_time) * 1000)
            await dashboard_service.record_email_processed(
                client_id,
                {
                    "sender": email_data["from"],
                    "recipient": email_data["to"],
                    "subject": email_data["subject"],
                    "category": category,
                    "routing_destination": forward_to,
                    "processing_time_ms": processing_time_ms,
                    "status": "completed",
                    "stage": "delivery_complete",
                    "success": True,
                },
            )

        # Log successful completion
        if client_id:
            client_config = client_manager.get_client_config(client_id)
            company_name = client_config.branding.company_name
            logger.info(
                f"✅ Email processed for {company_name}: "
                f"acknowledgment sent + analysis forwarded to {forward_to}"
            )
        else:
            logger.info(
                f"✅ Email processed (no client): "
                f"acknowledgment sent + analysis forwarded to {forward_to}"
            )

    except Exception as e:
        logger.error(f"❌ Email pipeline failed: {e}")

        # Record failed processing activity
        if client_id:
            try:
                processing_time_ms = (
                    int((time.time() - start_time) * 1000) if "start_time" in locals() else 0
                )
                await dashboard_service.record_email_processed(
                    client_id,
                    {
                        "sender": email_data.get("from", "unknown"),
                        "recipient": email_data.get("to", "unknown"),
                        "subject": email_data.get("subject", "unknown"),
                        "error_message": str(e),
                        "processing_time_ms": processing_time_ms,
                        "status": "failed",
                        "stage": "processing_error",
                        "success": False,
                    },
                )
            except Exception as dashboard_error:
                logger.error(f"❌ Failed to record dashboard activity: {dashboard_error}")

        # Try to send a basic notification about the failure
        try:
            if client_id:
                client_config = client_manager.get_client_config(client_id)
                admin_email = client_config.contacts.primary_contact
            else:
                admin_email = "admin@example.com"  # TODO: Make this configurable

            await _send_failure_notification(email_data, str(e), admin_email)

        except Exception as notification_error:
            logger.error(f"❌ Failed to send failure notification: {notification_error}")


async def _send_failure_notification(email_data: dict, error_message: str, admin_email: str):
    """
    Send notification about email processing failure.

    Args:
        email_data: Original email data
        error_message: Error that occurred
        admin_email: Admin email to notify
    """
    try:
        failure_classification = {
            "category": "general",
            "confidence": 0.0,
            "reasoning": "Email processing failed",
            "method": "failure_notification",
        }

        failure_message = f"""
Email processing failed with error: {error_message}

Original email:
From: {email_data.get('from', '')}
Subject: {email_data.get('subject', '')}
Body: {email_data.get('stripped_text') or email_data.get('body_text', '')[:200]}...

Please review this email manually.
"""

        await forward_to_team(email_data, admin_email, failure_classification, failure_message)

        logger.info(f"📧 Failure notification sent to {admin_email}")

    except Exception as e:
        logger.error(f"Failed to send failure notification: {e}")


@router.get("/status", response_model=None)
async def webhook_status(
    client_manager: Annotated[ClientManager, Depends(get_client_manager)],
    current_user: Annotated[Optional[DualAuthUser], Depends(get_dual_auth_user)] = None,
):
    """
    Get webhook processing status and client information.

    Returns:
        Status information including available clients
    """
    try:
        available_clients = client_manager.get_available_clients()

        # Get client details
        client_details = []
        for client_id in available_clients:
            try:
                client_config = client_manager.get_client_config(client_id)
                client_details.append(
                    {
                        "id": client_id,
                        "name": client_config.client.name,
                        "industry": client_config.client.industry,
                        "status": client_config.client.status,
                        "domains": {
                            "primary": client_config.domains.primary,
                            "support": client_config.domains.support,
                        },
                        "settings": {
                            "auto_reply_enabled": client_config.settings.auto_reply_enabled,
                            "ai_classification_enabled": client_config.settings.ai_classification_enabled,
                        },
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to load details for client {client_id}: {e}")
                client_details.append({"id": client_id, "error": str(e)})

        response = {
            "status": "active",
            "webhook_endpoint": "/webhooks/mailgun/inbound",
            "total_clients": len(available_clients),
            "clients": client_details,
        }

        # Include auth info if authenticated
        if current_user:
            response["authenticated_as"] = {
                "username": current_user.username,
                "auth_type": current_user.auth_type,
                "client_id": current_user.client_id,
                "role": current_user.role,
            }

        return response

    except Exception as e:
        logger.error(f"Failed to get webhook status: {e}")
        return {"status": "error", "message": str(e)}


@router.post("/test", response_model=None)
async def test_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    client_manager: Annotated[ClientManager, Depends(get_client_manager)],
    ai_classifier: Annotated[AIClassifier, Depends(get_ai_classifier)],
    routing_engine: Annotated[RoutingEngine, Depends(get_routing_engine)],
    dashboard_service: Annotated[DashboardService, Depends(get_dashboard_service)],
    email_service: Annotated[EmailService, Depends(get_email_service)],
):
    """
    Test endpoint for webhook functionality.

    Accepts JSON payload with test email data.
    """
    try:
        # Get JSON data instead of form data for testing
        test_data = await request.json()

        # Convert to expected format
        email_data = {
            "from": test_data.get("from", "test@example.com"),
            "to": test_data.get("to", "support@colenielson.dev"),
            "subject": test_data.get("subject", "Test Email"),
            "body_text": test_data.get("body", "This is a test email."),
            "body_html": "",
            "stripped_text": test_data.get("body", "This is a test email."),
            "timestamp": "",
            "message_id": "test-message-id",
        }

        logger.info(f"🧪 Test email from {email_data['from']}: {email_data['subject']}")

        # Identify client
        identification_result = client_manager.identify_client_by_email(email_data["to"])
        client_id = identification_result.client_id if identification_result.is_successful else None

        # Process in background
        background_tasks.add_task(
            process_email_pipeline,
            email_data,
            client_id,
            dynamic_classifier,
            client_manager,
            routing_engine,
            dashboard_service,
            email_service,
        )

        return {
            "status": "test_received",
            "message": "Test email processing started",
            "client_id": client_id,
            "email_data": email_data,
        }

    except Exception as e:
        logger.error(f"❌ Test webhook failed: {e}")
        return {"status": "error", "message": str(e)}


@router.get("/mailgun/env-check", response_model=None)
async def check_environment_variables():
    """
    🔧 ENV CHECK: Verify which environment variables are actually loaded in production
    """
    try:
        config = get_app_config()

        env_status = {
            "anthropic_api_key": "SET" if config.anthropic_api_key else "MISSING",
            "mailgun_api_key": "SET" if config.mailgun_api_key else "MISSING",
            "mailgun_domain": config.mailgun_domain or "MISSING",
            "mailgun_webhook_signing_key": (
                "SET" if config.mailgun_webhook_signing_key else "MISSING"
            ),
            "ai_service_available": config.ai_service_available,
            "email_service_available": config.email_service_available,
            "environment": config.environment,
        }

        return {
            "status": "env_check_complete",
            "environment_variables": env_status,
            "timestamp": "2024-06-14T20:00:00Z",
        }

    except Exception as e:
        logger.error(f"🔧 ENV CHECK failed: {e}")
        return {"status": "env_check_error", "message": str(e)}


@router.post("/mailgun/debug", response_model=None)
async def mailgun_debug_webhook(request: Request):
    """
    🚧 DEBUG ENDPOINT: Capture and log all Mailgun webhook data for troubleshooting.

    This endpoint logs all incoming data without processing to help identify
    what Mailgun is actually sending vs what we expect.
    """
    try:
        # Get client info
        client_host = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")

        logger.info(f"🐛 DEBUG: Webhook received from {client_host}")
        logger.info(f"🐛 DEBUG: User-Agent: {user_agent}")

        # Log all headers
        logger.info(f"🐛 DEBUG: Headers: {dict(request.headers)}")

        # Try to get form data
        try:
            form_data = await request.form()
            logger.info(f"🐛 DEBUG: Form data keys: {list(form_data.keys())}")
            logger.info(f"🐛 DEBUG: Form data: {dict(form_data)}")
        except Exception as form_error:
            logger.warning(f"🐛 DEBUG: Failed to parse form data: {form_error}")

        # Try to get raw body
        try:
            body = await request.body()
            logger.info(f"🐛 DEBUG: Raw body length: {len(body)} bytes")
            logger.info(
                f"🐛 DEBUG: Raw body (first 500 chars): {body[:500].decode('utf-8', errors='ignore')}"
            )
        except Exception as body_error:
            logger.warning(f"🐛 DEBUG: Failed to get raw body: {body_error}")

        return {
            "status": "debug_received",
            "message": "Debug data logged - check server logs",
            "client_host": client_host,
            "user_agent": user_agent,
            "timestamp": "2024-06-14T20:00:00Z",  # Static for debugging
        }

    except Exception as e:
        logger.error(f"🐛 DEBUG: Debug endpoint failed: {e}")
        return {"status": "debug_error", "message": str(e)}
