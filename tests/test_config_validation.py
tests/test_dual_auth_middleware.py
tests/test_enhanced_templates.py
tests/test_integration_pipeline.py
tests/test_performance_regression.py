from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from backend.src.application.middleware.auth import APIKeyUser, DualAuthMiddleware, DualAuthUser
from backend.src.core.authentication.jwt import AuthenticatedUser
from backend.src.core.clients.manager import ClientManager, get_client_manager
from backend.src.core.email.classifier import AIClassifier, get_ai_classifier
from backend.src.core.email.composer import EmailService, get_email_service
from backend.src.core.email.router import RoutingEngine
from backend.src.infrastructure.config.schema import ClientConfig
from backend.src.infrastructure.templates.email import (
    _get_default_branding,
    create_branded_template,
)
from backend.src.main import app
