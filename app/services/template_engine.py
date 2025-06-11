"""
Template engine for AI prompt composition with client-specific context.
🎨 Composes prompts by injecting client data into template files.
Enhanced with professional email template support and branding integration.
"""

import logging
import re
from typing import Dict, Any, Optional, List
from string import Template
import yaml
from pathlib import Path

from ..services.client_manager import ClientManager
from ..utils.client_loader import load_ai_prompt, load_fallback_responses, ClientLoadError
from ..models.client_config import ClientConfig

logger = logging.getLogger(__name__)

class ValidationResult:
    """Template validation result."""
    def __init__(self, is_valid: bool = True, errors: List[str] = None, warnings: List[str] = None):
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []

class EnhancedTemplateEngine:
    """
    Enhanced AI prompt template engine with client-specific data injection.
    
    Features:
    - Standardized {{variable}} syntax only
    - Dynamic client branding injection
    - Template validation and caching
    - Fallback value support: {{variable|default:"fallback"}}
    - Nested variable access: {{client.branding.primary_color}}
    """
    
    def __init__(self, client_manager: ClientManager):
        """
        Initialize enhanced template engine.
        
        Args:
            client_manager: ClientManager instance for accessing client data
        """
        self.client_manager = client_manager
        self._template_cache: Dict[str, str] = {}
        self._branding_cache: Dict[str, Dict[str, Any]] = {}
        self.validation_rules = {
            'required_variables': ['client.name'],
            'max_template_size': 50000,  # 50KB max template size
            'allowed_html_tags': ['div', 'p', 'h1', 'h2', 'h3', 'span', 'strong', 'em', 'br', 'img', 'a']
        }
    
    def _load_client_branding(self, client_id: str) -> Dict[str, Any]:
        """
        Load client branding configuration including colors.
        
        Args:
            client_id: Client identifier
            
        Returns:
            Complete branding configuration
        """
        cache_key = f"branding_{client_id}"
        
        # Check cache first
        if cache_key in self._branding_cache:
            return self._branding_cache[cache_key]
        
        try:
            client_config = self.client_manager.get_client_config(client_id)
            
            # Load colors from branding/colors.yaml
            colors_file = Path(f"clients/active/{client_id}/branding/colors.yaml")
            colors = {}
            if colors_file.exists():
                with open(colors_file, 'r') as f:
                    colors = yaml.safe_load(f) or {}
            
            # Enhanced branding context
            branding = {
                'company_name': client_config.branding.company_name,
                'email_signature': client_config.branding.email_signature,
                'primary_color': client_config.branding.primary_color,
                'secondary_color': client_config.branding.secondary_color,
                'logo_url': client_config.branding.logo_url or '',
                'footer_text': getattr(client_config.branding, 'footer_text', ''),
                
                # Enhanced color palette from colors.yaml
                'colors': colors,
                
                # Template-ready color variables
                'header_gradient': colors.get('email', {}).get('header_background', 
                    f"linear-gradient(135deg, {client_config.branding.primary_color}, {client_config.branding.secondary_color})"),
                'header_text_color': colors.get('email', {}).get('header_text', '#ffffff'),
                'body_background': colors.get('email', {}).get('body_background', '#ffffff'),
                'body_text_color': colors.get('email', {}).get('body_text', '#374151'),
                'accent_background': colors.get('email', {}).get('accent_background', '#f8f9ff'),
                'accent_border_color': colors.get('email', {}).get('accent_border', client_config.branding.primary_color),
                'footer_background': colors.get('email', {}).get('footer_background', '#f8f9fa'),
                'footer_text_color': colors.get('email', {}).get('footer_text', '#6b7280'),
                'link_color': colors.get('email', {}).get('link_color', client_config.branding.primary_color),
            }
            
            # Cache the result
            self._branding_cache[cache_key] = branding
            return branding
            
        except Exception as e:
            logger.error(f"Failed to load client branding for {client_id}: {e}")
            # Return minimal branding fallback
            return {
                'company_name': 'Email Router',
                'primary_color': '#667eea',
                'secondary_color': '#764ba2',
                'header_gradient': 'linear-gradient(135deg, #667eea, #764ba2)',
                'header_text_color': '#ffffff',
                'body_background': '#ffffff',
                'body_text_color': '#374151',
                'logo_url': ''
            }
    
    def validate_template(self, template_content: str, client_id: str = None) -> ValidationResult:
        """
        Validate template content for syntax and structure.
        
        Args:
            template_content: Template content to validate
            client_id: Optional client ID for client-specific validation
            
        Returns:
            ValidationResult with validation status and messages
        """
        errors = []
        warnings = []
        
        try:
            # Check template size
            if len(template_content) > self.validation_rules['max_template_size']:
                errors.append(f"Template exceeds maximum size of {self.validation_rules['max_template_size']} bytes")
            
            # Validate variable syntax - only {{}} allowed
            # Find single braces that are NOT part of double braces
            old_syntax_matches = re.findall(r'(?<!\{)\{([^{][^}]*)\}(?!\})', template_content)
            if old_syntax_matches:
                warnings.append(f"Found {len(old_syntax_matches)} old-style {{variable}} patterns. Use {{{{variable}}}} syntax instead.")
            
            # Check for properly formed {{}} variables
            variable_matches = re.findall(r'\{\{([^}]+)\}\}', template_content)
            for var in variable_matches:
                # Check for default value syntax: {{variable|default:"value"}}
                if '|default:' in var:
                    var_name, default_part = var.split('|default:', 1)
                    if not (default_part.startswith('"') and default_part.endswith('"')):
                        errors.append(f"Invalid default syntax for variable {var_name}. Use: {{{{variable|default:\"value\"}}}}")
            
            # Check for required variables if client_id provided
            if client_id:
                for required_var in self.validation_rules['required_variables']:
                    pattern = required_var.replace('.', r'\.')
                    if not re.search(rf'\{{{{{pattern}(\|[^}}]*)?}}}}', template_content):
                        warnings.append(f"Missing recommended variable: {{{{{required_var}}}}}")
            
            # Basic HTML validation for email templates
            if '<html>' in template_content or '<div>' in template_content:
                # Check for balanced tags
                for tag in ['div', 'p', 'h1', 'h2', 'h3', 'span']:
                    open_tags = len(re.findall(rf'<{tag}[^>]*>', template_content))
                    close_tags = len(re.findall(rf'</{tag}>', template_content))
                    if open_tags != close_tags:
                        errors.append(f"Unbalanced {tag} tags: {open_tags} opening, {close_tags} closing")
            
            return ValidationResult(
                is_valid=(len(errors) == 0),
                errors=errors,
                warnings=warnings
            )
            
        except Exception as e:
            logger.error(f"Template validation failed: {e}")
            return ValidationResult(
                is_valid=False,
                errors=[f"Validation error: {str(e)}"]
            )

    def _load_template(self, client_id: str, template_type: str) -> str:
        """
        Load prompt template for a client with validation.
        
        Args:
            client_id: Client identifier
            template_type: Type of template ('classification', 'acknowledgment', 'team-analysis')
            
        Returns:
            Template content as string
            
        Raises:
            ClientLoadError: If template cannot be loaded
        """
        cache_key = f"{client_id}_{template_type}"
        
        # Check cache first
        if cache_key in self._template_cache:
            return self._template_cache[cache_key]
        
        try:
            template_content = load_ai_prompt(client_id, template_type)
            
            # Validate template
            validation = self.validate_template(template_content, client_id)
            if not validation.is_valid:
                logger.warning(f"Template validation failed for {client_id}/{template_type}: {validation.errors}")
                # Still cache and use template, but log warnings
            
            if validation.warnings:
                logger.info(f"Template warnings for {client_id}/{template_type}: {validation.warnings}")
            
            self._template_cache[cache_key] = template_content
            return template_content
            
        except ClientLoadError as e:
            logger.error(f"Failed to load {template_type} template for {client_id}: {e}")
            raise
    
    def _prepare_template_context(self, client_id: str, email_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Prepare enhanced context data for template injection.
        
        Args:
            client_id: Client identifier
            email_data: Optional email data for context
            
        Returns:
            Dictionary of context data for template injection
        """
        try:
            client_config = self.client_manager.get_client_config(client_id)
            routing_rules = self.client_manager.get_routing_rules(client_id)
            branding = self._load_client_branding(client_id)
            
            # Enhanced context with full branding support
            context = {
                'client': {
                    'id': client_config.client.id,
                    'name': client_config.client.name,
                    'industry': client_config.client.industry,
                    'timezone': client_config.client.timezone,
                    'business_hours': client_config.client.business_hours,
                },
                'branding': branding,
                'response_times': {
                    'support': client_config.response_times.support,
                    'billing': client_config.response_times.billing,
                    'sales': client_config.response_times.sales,
                    'general': client_config.response_times.general,
                },
                'routing': routing_rules.routing,
                'domains': {
                    'primary': client_config.domains.primary,
                    'support': client_config.domains.support,
                    'mailgun': client_config.domains.mailgun,
                }
            }
            
            # Add email data if provided
            if email_data:
                context.update({
                    'sender': email_data.get('from', ''),
                    'subject': email_data.get('subject', ''),
                    'body': email_data.get('stripped_text') or email_data.get('body_text', ''),
                    'recipient': email_data.get('to', ''),
                })
            
            return context
            
        except Exception as e:
            logger.error(f"Failed to prepare template context for {client_id}: {e}")
            raise
    
    def _inject_template_variables(self, template: str, context: Dict[str, Any]) -> str:
        """
        Enhanced variable injection with standardized {{}} syntax only.
        
        Supports:
        - Simple variables: {{client.name}}
        - Nested access: {{client.branding.primary_color}}
        - Default values: {{variable|default:"fallback"}}
        
        Args:
            template: Template string with variables
            context: Context data for injection
            
        Returns:
            Template with variables injected
        """
        try:
            def replace_variable(match):
                var_expression = match.group(1).strip()
                
                # Handle default values: variable|default:"value"
                if '|default:' in var_expression:
                    var_path, default_part = var_expression.split('|default:', 1)
                    var_path = var_path.strip()
                    
                    # Extract default value (remove quotes)
                    default_value = default_part.strip()
                    if default_value.startswith('"') and default_value.endswith('"'):
                        default_value = default_value[1:-1]
                    
                    # Get variable value or use default
                    value = self._get_nested_value(context, var_path, default_value)
                else:
                    # No default value
                    value = self._get_nested_value(context, var_expression)
                
                return str(value)
            
            # Replace all {{variable}} patterns
            result = re.sub(r'\{\{([^}]+)\}\}', replace_variable, template)
            
            return result
            
        except Exception as e:
            logger.error(f"Error injecting template variables: {e}")
            return template  # Return original template if injection fails
    
    def _get_nested_value(self, data: Dict[str, Any], path: str, default: str = None) -> str:
        """
        Get nested value from dictionary using dot notation with default support.
        
        Args:
            data: Dictionary to search
            path: Dot-separated path (e.g., 'client.branding.primary_color')
            default: Default value if path not found
            
        Returns:
            Value as string, default if provided, or placeholder if not found
        """
        try:
            keys = path.split('.')
            value = data
            
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    # Path not found
                    if default is not None:
                        return default
                    return f"{{{{MISSING: {path}}}}}"
            
            return str(value)
            
        except Exception:
            if default is not None:
                return default
            return f"{{{{ERROR: {path}}}}}"
    
    def compose_classification_prompt(self, client_id: str, email_data: Dict[str, Any]) -> str:
        """
        Compose classification prompt for a client.
        
        Args:
            client_id: Client identifier
            email_data: Email data from webhook
            
        Returns:
            Composed classification prompt
        """
        try:
            template = self._load_template(client_id, 'classification')
            context = self._prepare_template_context(client_id, email_data)
            
            prompt = self._inject_template_variables(template, context)
            
            logger.debug(f"Composed classification prompt for {client_id} ({len(prompt)} chars)")
            return prompt
            
        except Exception as e:
            logger.error(f"Failed to compose classification prompt for {client_id}: {e}")
            
            # Fallback to basic classification prompt
            return self._get_fallback_classification_prompt(email_data)
    
    def compose_acknowledgment_prompt(self, client_id: str, email_data: Dict[str, Any], 
                                    classification: Dict[str, Any]) -> str:
        """
        Compose acknowledgment prompt for a client.
        
        Args:
            client_id: Client identifier
            email_data: Email data from webhook
            classification: Email classification result
            
        Returns:
            Composed acknowledgment prompt
        """
        try:
            template = self._load_template(client_id, 'acknowledgment')
            context = self._prepare_template_context(client_id, email_data)
            
            # Add classification context
            context.update({
                'category': classification.get('category', 'general'),
                'priority': classification.get('priority', 'medium'),
                'confidence': classification.get('confidence', 0.5),
            })
            
            prompt = self._inject_template_variables(template, context)
            
            logger.debug(f"Composed acknowledgment prompt for {client_id} ({len(prompt)} chars)")
            return prompt
            
        except Exception as e:
            logger.error(f"Failed to compose acknowledgment prompt for {client_id}: {e}")
            
            # Fallback to basic acknowledgment prompt
            return self._get_fallback_acknowledgment_prompt(client_id, classification)
    
    def compose_team_analysis_prompt(self, client_id: str, email_data: Dict[str, Any], 
                                   classification: Dict[str, Any]) -> str:
        """
        Compose team analysis prompt for a client.
        
        Args:
            client_id: Client identifier
            email_data: Email data from webhook
            classification: Email classification result
            
        Returns:
            Composed team analysis prompt
        """
        try:
            template = self._load_template(client_id, 'team-analysis')
            context = self._prepare_template_context(client_id, email_data)
            
            # Add classification and routing context
            routing_destination = self.client_manager.get_routing_destination(
                client_id, classification.get('category', 'general')
            )
            
            context.update({
                'category': classification.get('category', 'general'),
                'priority': classification.get('priority', 'medium'),
                'confidence': classification.get('confidence', 0.5),
                'reasoning': classification.get('reasoning', ''),
                'assigned_to': routing_destination,
            })
            
            prompt = self._inject_template_variables(template, context)
            
            logger.debug(f"Composed team analysis prompt for {client_id} ({len(prompt)} chars)")
            return prompt
            
        except Exception as e:
            logger.error(f"Failed to compose team analysis prompt for {client_id}: {e}")
            
            # Fallback to basic team analysis prompt
            return self._get_fallback_team_analysis_prompt(client_id, classification)
    
    def get_fallback_response(self, client_id: str, response_type: str, category: str = 'general') -> str:
        """
        Get fallback response when AI services fail.
        
        Args:
            client_id: Client identifier
            response_type: Type of response ('customer_acknowledgments', 'team_analysis')
            category: Email category
            
        Returns:
            Fallback response string
        """
        try:
            fallback_data = load_fallback_responses(client_id)
            
            if response_type in fallback_data and category in fallback_data[response_type]:
                template = fallback_data[response_type][category]
                context = self._prepare_template_context(client_id)
                return self._inject_template_variables(template, context)
            
            # Fallback to general if category not found
            if response_type in fallback_data and 'general' in fallback_data[response_type]:
                template = fallback_data[response_type]['general']
                context = self._prepare_template_context(client_id)
                return self._inject_template_variables(template, context)
                
        except Exception as e:
            logger.error(f"Failed to get fallback response for {client_id}: {e}")
        
        # Hard fallback
        return self._get_hard_fallback_response(response_type, category)
    
    def _get_fallback_classification_prompt(self, email_data: Dict[str, Any]) -> str:
        """Get basic fallback classification prompt."""
        return f"""
You are an intelligent email classifier. Analyze this email and classify it:

Categories:
- billing: Payment issues, invoices, account billing
- support: Technical problems, how-to questions, product issues  
- sales: Pricing inquiries, product demos, new business
- general: Everything else

Email:
Subject: {email_data.get('subject', '')}
Body: {email_data.get('stripped_text') or email_data.get('body_text', '')}

Respond in JSON format:
{{
    "category": "one of the categories above",
    "confidence": 0.95,
    "reasoning": "Brief explanation",
    "suggested_actions": ["action1", "action2"]
}}
"""
    
    def _get_fallback_acknowledgment_prompt(self, client_id: str, classification: Dict[str, Any]) -> str:
        """Get basic fallback acknowledgment prompt."""
        category = classification.get('category', 'general')
        return f"""
Generate a brief professional acknowledgment for a {category} inquiry.
Keep it under 150 words, thank the customer, and mention we'll respond within 24 hours.
"""
    
    def _get_fallback_team_analysis_prompt(self, client_id: str, classification: Dict[str, Any]) -> str:
        """Get basic fallback team analysis prompt."""
        category = classification.get('category', 'general')
        return f"""
Email classified as {category.upper()} inquiry (fallback classification).
Please review the original message and respond accordingly.
"""
    
    def _get_hard_fallback_response(self, response_type: str, category: str) -> str:
        """Get hard-coded fallback response when all else fails."""
        if response_type == 'customer_acknowledgments':
            return f"Thank you for contacting us. We've received your {category} inquiry and will respond within 24 hours."
        elif response_type == 'team_analysis':
            return f"Email classified as {category.upper()} inquiry. Please review and respond accordingly."
        else:
            return "Email received and being processed."
    
    def clear_cache(self):
        """Clear template and branding caches."""
        self._template_cache.clear()
        self._branding_cache.clear()
        logger.info("Template and branding caches cleared")

# Backward compatibility - maintain the original TemplateEngine class
class TemplateEngine(EnhancedTemplateEngine):
    """Backward compatible template engine."""
    pass 