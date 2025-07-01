"""
Core Email Module
Provides email classification, routing, composition, and sending services.
"""

from .classifier import AIClassifier, get_ai_classifier
from .router import RoutingEngine, get_routing_engine
from .service import EmailService, generate_plain_text_emails, get_email_service

__all__ = [
    # Classifier
    "AIClassifier",
    "get_ai_classifier",
    # Composer
    "EmailService",
    "get_email_service",
    "generate_plain_text_emails",
    # Router
    "RoutingEngine",
    "get_routing_engine",
]
