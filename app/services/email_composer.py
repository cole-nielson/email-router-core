"""
AI-powered email response generation with multi-tenant support.
✍️ Creates personalized response drafts using client-specific AI prompts.
Enhanced with branded email template generation.
"""

import logging
import httpx
from typing import Dict, Any, Optional, Tuple

from ..utils.config import get_config
from ..services.client_manager import ClientManager, get_client_manager
from ..services.template_engine import EnhancedTemplateEngine
from ..utils.email_templates import create_branded_template, _get_default_branding

logger = logging.getLogger(__name__)


async def generate_customer_acknowledgment(email_data: Dict[str, Any], classification: Dict[str, Any],
                                         client_id: Optional[str] = None) -> str:
    """
    ✍️ Generate brief customer acknowledgment using client-specific templates.
    
    Args:
        email_data: Email data from webhook
        classification: Email classification result
        client_id: Optional client ID (will be identified if not provided)
        
    Returns:
        Generated acknowledgment text
    """
    try:
        # Get client manager and enhanced template engine
        client_manager = get_client_manager()
        template_engine = EnhancedTemplateEngine(client_manager)
        
        # Identify client if not provided
        if not client_id:
            client_id = client_manager.identify_client_by_email(
                email_data.get('to') or email_data.get('recipient', '')
            )
        
        if client_id:
            # Use client-specific template
            try:
                prompt = template_engine.compose_acknowledgment_prompt(client_id, email_data, classification)
                acknowledgment = await _call_ai_service(prompt)
                
                logger.info(f"✍️ Generated client-specific acknowledgment for {client_id}")
                return acknowledgment
                
            except Exception as e:
                logger.warning(f"Client-specific acknowledgment failed for {client_id}: {e}")
                # Fall back to client's fallback response
                return template_engine.get_fallback_response(
                    client_id, 'customer_acknowledgments', classification.get('category', 'general')
                )
        else:
            # No client identified, use generic acknowledgment
            logger.warning("No client identified, using generic acknowledgment")
            return await _generate_generic_acknowledgment(email_data, classification)
            
    except Exception as e:
        logger.error(f"❌ Acknowledgment generation failed: {e}")
        return _get_hard_fallback_acknowledgment(classification)


async def generate_team_analysis(email_data: Dict[str, Any], classification: Dict[str, Any],
                                client_id: Optional[str] = None) -> str:
    """
    ✍️ Generate detailed team analysis using client-specific templates.
    
    Args:
        email_data: Email data from webhook
        classification: Email classification result
        client_id: Optional client ID (will be identified if not provided)
        
    Returns:
        Generated team analysis text
    """
    try:
        # Get client manager and enhanced template engine
        client_manager = get_client_manager()
        template_engine = EnhancedTemplateEngine(client_manager)
        
        # Identify client if not provided
        if not client_id:
            client_id = client_manager.identify_client_by_email(
                email_data.get('to') or email_data.get('recipient', '')
            )
        
        if client_id:
            # Use client-specific template
            try:
                prompt = template_engine.compose_team_analysis_prompt(client_id, email_data, classification)
                analysis = await _call_ai_service(prompt)
                
                logger.info(f"✍️ Generated client-specific team analysis for {client_id}")
                return analysis
                
            except Exception as e:
                logger.warning(f"Client-specific team analysis failed for {client_id}: {e}")
                # Fall back to client's fallback response
                return template_engine.get_fallback_response(
                    client_id, 'team_analysis', classification.get('category', 'general')
                )
        else:
            # No client identified, use generic analysis
            logger.warning("No client identified, using generic team analysis")
            return await _generate_generic_team_analysis(email_data, classification)
            
    except Exception as e:
        logger.error(f"❌ Team analysis generation failed: {e}")
        return _get_hard_fallback_team_analysis(classification)


async def generate_branded_email_templates(
    email_data: Dict[str, Any], 
    classification: Dict[str, Any],
    draft_response: str,
    client_id: Optional[str] = None
) -> Tuple[Tuple[str, str], Tuple[str, str]]:
    """
    🎨 Generate branded email templates for both customer and team communications.
    
    Args:
        email_data: Email data from webhook
        classification: Email classification result
        draft_response: AI-generated response content
        client_id: Optional client ID (will be identified if not provided)
        
    Returns:
        Tuple of ((customer_text, customer_html), (team_text, team_html))
    """
    try:
        # Get client manager and enhanced template engine
        client_manager = get_client_manager()
        template_engine = EnhancedTemplateEngine(client_id and client_manager or None)
        
        # Identify client if not provided
        if not client_id:
            client_id = client_manager.identify_client_by_email(
                email_data.get('to') or email_data.get('recipient', '')
            )
        
        # Load client branding
        branding = None
        if client_id and hasattr(template_engine, '_load_client_branding'):
            try:
                branding = template_engine._load_client_branding(client_id)
                logger.info(f"🎨 Loaded branding for client {client_id}")
            except Exception as e:
                logger.warning(f"Failed to load branding for {client_id}: {e}")
                branding = _get_default_branding()
        else:
            branding = _get_default_branding()
        
        # Generate customer template
        customer_context = {
            'draft_response': draft_response,
            'classification': classification,
            'email_data': email_data
        }
        customer_templates = create_branded_template('customer_reply', customer_context, branding)
        
        # Generate team analysis template  
        team_context = {
            'email_data': email_data,
            'classification': classification,
            'draft_response': draft_response
        }
        team_templates = create_branded_template('team_forward', team_context, branding)
        
        logger.info(f"🎨 Generated branded templates for {client_id or 'generic'}")
        return customer_templates, team_templates
        
    except Exception as e:
        logger.error(f"❌ Branded template generation failed: {e}")
        # Fallback to default branding
        branding = _get_default_branding()
        
        customer_context = {
            'draft_response': draft_response,
            'classification': classification
        }
        team_context = {
            'email_data': email_data,
            'classification': classification,
            'draft_response': draft_response
        }
        
        return (
            create_branded_template('customer_reply', customer_context, branding),
            create_branded_template('team_forward', team_context, branding)
        )


async def render_template_with_branding(
    template_content: str, 
    context: Dict[str, Any], 
    client_id: Optional[str] = None
) -> str:
    """
    🎨 Render template content with client branding variables.
    
    Args:
        template_content: Template content with variables
        context: Template context
        client_id: Optional client ID for branding
        
    Returns:
        Rendered template content
    """
    try:
        if client_id:
            client_manager = get_client_manager()
            template_engine = EnhancedTemplateEngine(client_manager)
            
            # Load branding and merge with context
            branding = template_engine._load_client_branding(client_id)
            context['branding'] = branding
            
            # Render template with enhanced injection
            return template_engine._inject_template_variables(template_content, context)
        else:
            # Use default branding
            context['branding'] = _get_default_branding()
            template_engine = EnhancedTemplateEngine(None)
            return template_engine._inject_template_variables(template_content, context)
            
    except Exception as e:
        logger.error(f"Template rendering failed: {e}")
        return template_content


async def _call_ai_service(prompt: str) -> str:
    """
    Call Anthropic Claude API with prompt.
    
    Args:
        prompt: AI prompt to send
        
    Returns:
        AI response text
        
    Raises:
        Exception: If AI service call fails
    """
    config = get_config()
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "Content-Type": "application/json",
                "x-api-key": config.anthropic_api_key,
                "anthropic-version": "2023-06-01"
            },
            json={
                "model": config.anthropic_model,
                "max_tokens": 400,  # Reasonable size for responses
                "temperature": 0.3,  # Lower temperature for consistency
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=30.0
        )
        
        response.raise_for_status()
        result = response.json()
        
        return result["content"][0]["text"].strip()


async def _generate_generic_acknowledgment(email_data: Dict[str, Any], classification: Dict[str, Any]) -> str:
    """Generate generic acknowledgment when no client is identified."""
    category = classification.get('category', 'general')
    
    prompt = f"""
Generate a brief professional acknowledgment for a {category} inquiry.

Email subject: {email_data.get('subject', '')}

Generate a SHORT acknowledgment that:
1. Thanks them for contacting us
2. Confirms we received their {category} inquiry
3. Mentions we'll respond within 24 hours
4. Stays under 150 words
5. Maintains a professional tone

Acknowledgment:
"""
    
    try:
        return await _call_ai_service(prompt)
    except Exception as e:
        logger.error(f"Generic acknowledgment generation failed: {e}")
        return _get_hard_fallback_acknowledgment(classification)


async def _generate_generic_team_analysis(email_data: Dict[str, Any], classification: Dict[str, Any]) -> str:
    """Generate generic team analysis when no client is identified."""
    category = classification.get('category', 'general')
    confidence = classification.get('confidence', 0.5)
    
    prompt = f"""
Analyze this email for the team member who will handle it.

Email details:
From: {email_data.get('from', '')}
Subject: {email_data.get('subject', '')}
Message: {email_data.get('stripped_text') or email_data.get('body_text', '')}

Classification: {category} (confidence: {confidence:.2f})

Provide analysis including:
1. Key issues identified
2. Customer sentiment
3. Suggested response approach
4. Recommended next steps

Team Analysis:
"""
    
    try:
        return await _call_ai_service(prompt)
    except Exception as e:
        logger.error(f"Generic team analysis generation failed: {e}")
        return _get_hard_fallback_team_analysis(classification)


def _get_hard_fallback_acknowledgment(classification: Dict[str, Any]) -> str:
    """Get hard-coded fallback acknowledgment when all else fails."""
    category = classification.get('category', 'general')
    
    fallbacks = {
        "support": "Thank you for contacting our support team. We've received your technical inquiry and our team will respond within 4 hours during business hours.",
        "billing": "Thank you for your billing inquiry. Our accounting team has been notified and will review your request within 24 hours.",
        "sales": "Thank you for your interest in our services. Our sales team will contact you within 2 hours during business hours to discuss your needs.",
        "general": "Thank you for contacting us. We've received your message and will respond within 24 hours."
    }
    
    return fallbacks.get(category, fallbacks["general"])


def _get_hard_fallback_team_analysis(classification: Dict[str, Any]) -> str:
    """Get hard-coded fallback team analysis when all else fails."""
    category = classification.get('category', 'general')
    return f"Email classified as {category.upper()} inquiry (fallback classification). Please review the original message and respond accordingly."


# Legacy function for backward compatibility
async def generate_response_draft(email_data: Dict[str, Any], classification: Dict[str, Any]) -> str:
    """
    Legacy function - use generate_team_analysis instead.
    
    Args:
        email_data: Original email data from Mailgun webhook
        classification: AI classification result
        
    Returns:
        Generated response draft
    """
    logger.warning("generate_response_draft is deprecated, use generate_team_analysis")
    return await generate_team_analysis(email_data, classification) 