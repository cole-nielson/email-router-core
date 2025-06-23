"""
Unified email service for AI-powered response generation and template processing.
✍️ Combines email composition, template engine, and branding in a single service.
🎨 Handles client-specific AI prompts, template processing, and email generation.
"""

import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import httpx

from infrastructure.config.manager import get_app_config, get_config_manager
from infrastructure.templates.email import _get_default_branding, create_branded_template

from ..clients.manager import ClientManager

logger = logging.getLogger(__name__)


class ValidationResult:
    """Template validation result."""

    def __init__(self, is_valid: bool = True, errors: List[str] = None, warnings: List[str] = None):
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []


class EmailService:
    """
    Unified email service combining template engine and email composition.

    Features:
    - AI-powered email generation with client-specific prompts
    - Template processing with variable injection and validation
    - Client branding integration and caching
    - Fallback handling for robustness
    - Professional email template generation
    """

    def __init__(self, client_manager: ClientManager):
        """
        Initialize the email service.

        Args:
            client_manager: ClientManager instance for accessing client data
        """
        self.client_manager = client_manager
        self._template_cache: Dict[str, str] = {}
        self._branding_cache: Dict[str, Dict[str, Any]] = {}
        self.validation_rules = {
            "required_variables": ["client.name"],
            "max_template_size": 50000,  # 50KB limit
            "allowed_html_tags": ["p", "div", "span", "br", "strong", "em", "a", "img"],
        }

    # =============================================================================
    # PUBLIC EMAIL GENERATION API
    # =============================================================================

    async def generate_customer_acknowledgment(
        self,
        email_data: Dict[str, Any],
        classification: Dict[str, Any],
        client_id: Optional[str] = None,
    ) -> str:
        """
        Generate brief customer acknowledgment using client-specific templates.

        Args:
            email_data: Email data from webhook
            classification: Email classification result
            client_id: Optional client ID (will be identified if not provided)

        Returns:
            Generated acknowledgment text
        """
        try:
            # Identify client if not provided
            if not client_id:
                result = self.client_manager.identify_client_by_email(
                    email_data.get("to") or email_data.get("recipient", "")
                )
                client_id = result.client_id if result.is_successful else None

            if client_id:
                # Use client-specific template
                try:
                    prompt = self.compose_acknowledgment_prompt(
                        client_id, email_data, classification
                    )
                    acknowledgment = await self._call_ai_service(prompt)

                    logger.info(f"✍️ Generated client-specific acknowledgment for {client_id}")
                    return acknowledgment

                except Exception as e:
                    logger.warning(f"Client-specific acknowledgment failed for {client_id}: {e}")
                    # Try fallback response
                    return self.get_fallback_response(
                        client_id,
                        "customer_acknowledgments",
                        classification.get("category", "general"),
                    )
            else:
                return await self._generate_generic_acknowledgment(email_data, classification)

        except Exception as e:
            logger.error(f"Acknowledgment generation failed: {e}")
            return self._get_hard_fallback_acknowledgment(classification)

    async def generate_team_analysis(
        self,
        email_data: Dict[str, Any],
        classification: Dict[str, Any],
        client_id: Optional[str] = None,
    ) -> str:
        """
        Generate detailed team analysis using client-specific templates.

        Args:
            email_data: Email data from webhook
            classification: Email classification result
            client_id: Optional client ID (will be identified if not provided)

        Returns:
            Generated team analysis text
        """
        try:
            # Identify client if not provided
            if not client_id:
                result = self.client_manager.identify_client_by_email(
                    email_data.get("to") or email_data.get("recipient", "")
                )
                client_id = result.client_id if result.is_successful else None

            if client_id:
                # Use client-specific template
                try:
                    prompt = self.compose_team_analysis_prompt(
                        client_id, email_data, classification
                    )
                    analysis = await self._call_ai_service(prompt)

                    logger.info(f"✍️ Generated client-specific team analysis for {client_id}")
                    return analysis

                except Exception as e:
                    logger.warning(f"Client-specific team analysis failed for {client_id}: {e}")
                    # Try fallback response
                    return self.get_fallback_response(
                        client_id, "team_analysis", classification.get("category", "general")
                    )
            else:
                return await self._generate_generic_team_analysis(email_data, classification)

        except Exception as e:
            logger.error(f"Team analysis generation failed: {e}")
            return self._get_hard_fallback_team_analysis(classification)

    async def generate_plain_text_emails(
        self,
        email_data: Dict[str, Any],
        classification: Dict[str, Any],
        client_id: Optional[str] = None,
    ) -> Tuple[str, str]:
        """
        Generate human-like plain text customer response and HTML team analysis.

        Args:
            email_data: Email data from webhook
            classification: Email classification result
            client_id: Optional client ID

        Returns:
            Tuple of (plain_text_customer_response, html_team_analysis)
        """
        try:
            # Generate human-like plain text customer response
            customer_content = await self.generate_customer_acknowledgment(
                email_data, classification, client_id
            )

            # Generate team analysis (keep as structured content for internal use)
            team_content = await self.generate_team_analysis(email_data, classification, client_id)

            # For team analysis, apply HTML branding for internal readability
            if client_id:
                branding = self._load_client_branding(client_id)
            else:
                branding = _get_default_branding()

            team_template = create_branded_template(
                content=team_content,
                branding=branding,
                context={
                    "email_type": "team_analysis",
                    "classification": classification,
                    "original_sender": email_data.get("from", ""),
                    "original_subject": email_data.get("subject", "No Subject"),
                    "routing_info": {
                        "category": classification.get("category", "general"),
                        "confidence": classification.get("confidence", 0.0),
                        "priority": classification.get("priority", "medium"),
                    },
                },
            )

            # Customer gets plain text, team gets HTML
            return customer_content, team_template

        except Exception as e:
            logger.error(f"Plain text email generation failed: {e}")
            # Return basic fallback responses
            customer_fallback = self._get_hard_fallback_acknowledgment(classification)
            team_fallback = self._get_hard_fallback_team_analysis(classification)
            return customer_fallback, team_fallback

    # =============================================================================
    # TEMPLATE ENGINE FUNCTIONALITY
    # =============================================================================

    def compose_classification_prompt(self, client_id: str, email_data: Dict[str, Any]) -> str:
        """
        Compose classification prompt for a client.

        Args:
            client_id: Client identifier
            email_data: Email data to classify

        Returns:
            Composed classification prompt
        """
        try:
            logger.debug(f"Loading classification template for {client_id}")
            template = self._load_template(client_id, "classification")

            logger.debug(f"Preparing template context for {client_id}")
            context = self._prepare_template_context(client_id, email_data)

            logger.debug(f"Injecting template variables for {client_id}")
            prompt = self._inject_template_variables(template, context)

            # Check for any remaining MISSING values in the final prompt
            missing_vars = re.findall(r"MISSING: ([^}]+)", prompt)
            if missing_vars:
                logger.warning(
                    f"Template contains missing variables for {client_id}: {missing_vars}"
                )
                logger.debug(f"Full template context keys: {list(context.keys())}")

            logger.info(f"✅ Composed classification prompt for {client_id} ({len(prompt)} chars)")
            logger.debug(f"Classification prompt preview: {prompt[:200]}...")
            return prompt

        except Exception as e:
            logger.error(f"❌ Failed to compose classification prompt for {client_id}: {e}")
            logger.debug(f"Exception details: {str(e)}", exc_info=True)

            # Fallback to basic classification prompt
            logger.warning(f"Using fallback classification prompt for {client_id}")
            return self._get_fallback_classification_prompt(email_data)

    def compose_acknowledgment_prompt(
        self, client_id: str, email_data: Dict[str, Any], classification: Dict[str, Any]
    ) -> str:
        """
        Compose acknowledgment prompt for a client.

        Args:
            client_id: Client identifier
            email_data: Original email data
            classification: Email classification result

        Returns:
            Composed acknowledgment prompt
        """
        try:
            template = self._load_template(client_id, "acknowledgment")
            context = self._prepare_template_context(client_id, email_data)

            # Add classification context
            category = classification.get("category", "general")
            context.update(
                {
                    "category": category,
                    "priority": classification.get("priority", "medium"),
                    "confidence": classification.get("confidence", 0.5),
                    "reasoning": classification.get("reasoning", ""),
                    "response_time_target": self._get_response_time_target(client_id, category),
                }
            )

            prompt = self._inject_template_variables(template, context)

            logger.debug(f"Composed acknowledgment prompt for {client_id}")
            return prompt

        except Exception as e:
            logger.error(f"Failed to compose acknowledgment prompt for {client_id}: {e}")
            return self._get_fallback_acknowledgment_prompt(client_id, classification)

    def compose_team_analysis_prompt(
        self, client_id: str, email_data: Dict[str, Any], classification: Dict[str, Any]
    ) -> str:
        """
        Compose team analysis prompt for a client.

        Args:
            client_id: Client identifier
            email_data: Original email data
            classification: Email classification result

        Returns:
            Composed team analysis prompt
        """
        try:
            template = self._load_template(client_id, "team-analysis")
            context = self._prepare_template_context(client_id, email_data)

            # Add classification and routing context
            category = classification.get("category", "general")
            routing_destination = self.client_manager.get_routing_destination(client_id, category)

            context.update(
                {
                    "category": category,
                    "priority": classification.get("priority", "medium"),
                    "confidence": classification.get("confidence", 0.5),
                    "reasoning": classification.get("reasoning", ""),
                    "routing_destination": routing_destination,
                    "suggested_actions": classification.get("suggested_actions", []),
                    "response_time_target": self._get_response_time_target(client_id, category),
                }
            )

            prompt = self._inject_template_variables(template, context)

            logger.debug(f"Composed team analysis prompt for {client_id}")
            return prompt

        except Exception as e:
            logger.error(f"Failed to compose team analysis prompt for {client_id}: {e}")
            return self._get_fallback_team_analysis_prompt(client_id, classification)

    def validate_template(self, template_content: str, client_id: str = None) -> ValidationResult:
        """
        Validate template content for correctness and security.

        Args:
            template_content: Template content to validate
            client_id: Optional client ID for context

        Returns:
            ValidationResult with validation status and any errors/warnings
        """
        errors = []
        warnings = []

        # Check template size
        if len(template_content) > self.validation_rules["max_template_size"]:
            errors.append(
                f"Template size exceeds maximum of {self.validation_rules['max_template_size']} bytes"
            )

        # Check for required variables
        for required_var in self.validation_rules["required_variables"]:
            pattern = r"{{\s*" + re.escape(required_var) + r"\s*}}"
            if not re.search(pattern, template_content):
                warnings.append(f"Required variable '{required_var}' not found in template")

        # Check for balanced HTML tags
        html_tags = re.findall(r"<(/?)([a-zA-Z][a-zA-Z0-9]*)", template_content)
        tag_stack = []

        for is_closing, tag_name in html_tags:
            if is_closing:
                if tag_stack and tag_stack[-1] == tag_name:
                    tag_stack.pop()
                else:
                    errors.append(f"Unmatched closing tag: </{tag_name}>")
            else:
                # Self-closing tags don't need to be tracked
                if tag_name not in ["br", "img", "hr", "input", "meta", "link"]:
                    tag_stack.append(tag_name)

        if tag_stack:
            errors.append(f"Unclosed HTML tags: {', '.join(tag_stack)}")

        # Check variable syntax
        variable_pattern = r"{{[^}]*}}"
        variables = re.findall(variable_pattern, template_content)

        for var in variables:
            # Check for valid variable syntax
            inner = var[2:-2].strip()
            if "|" in inner:
                var_name, default = inner.split("|", 1)
                if not default.strip().startswith("default:"):
                    errors.append(f"Invalid default syntax in variable: {var}")
                else:
                    # Check if default value is properly quoted
                    default_value = default.strip()[8:]  # Remove 'default:'
                    if default_value and not (
                        default_value.startswith('"') and default_value.endswith('"')
                    ):
                        errors.append(f"Invalid default syntax in variable: {var}")
            elif not re.match(r"^[a-zA-Z][a-zA-Z0-9_.]*$", inner):
                warnings.append(f"Invalid variable name syntax: {var}")

        is_valid = len(errors) == 0
        return ValidationResult(is_valid, errors, warnings)

    def get_fallback_response(
        self, client_id: str, response_type: str, category: str = "general"
    ) -> str:
        """
        Get fallback response for a client and category.

        Args:
            client_id: Client identifier
            response_type: Type of response ('customer_acknowledgments', 'team_analysis')
            category: Email category

        Returns:
            Fallback response text
        """
        try:
            fallback_responses = get_config_manager().load_fallback_responses(client_id)

            if response_type in fallback_responses:
                responses = fallback_responses[response_type]
                if category in responses:
                    return responses[category]
                elif "general" in responses:
                    return responses["general"]

            # Hard fallback
            return self._get_hard_fallback_response(response_type, category)

        except Exception:
            return self._get_hard_fallback_response(response_type, category)

    def clear_cache(self):
        """Clear all caches."""
        self._template_cache.clear()
        self._branding_cache.clear()
        logger.info("Template and branding caches cleared")

    # =============================================================================
    # PRIVATE HELPER METHODS
    # =============================================================================

    def _load_client_branding(self, client_id: str) -> Dict[str, Any]:
        """Load and cache client branding configuration."""
        if client_id in self._branding_cache:
            return self._branding_cache[client_id]

        try:
            client_config = self.client_manager.get_client_config(client_id)

            # Base branding from client config
            branding = {
                "company_name": client_config.branding.company_name,
                "primary_color": client_config.branding.primary_color,
                "secondary_color": client_config.branding.secondary_color,
                "logo_url": client_config.branding.logo_url or "",
                "email_signature": client_config.branding.email_signature,
                "footer_text": client_config.branding.footer_text or "",
            }

            # Load additional colors from consolidated branding.colors section
            try:
                if hasattr(client_config.branding, "colors"):
                    colors_data = client_config.branding.colors

                    # If colors are available as a dict (from YAML), process them
                    if isinstance(colors_data, dict):
                        # Map email-specific colors to expected branding keys
                        if "email" in colors_data:
                            email_colors = colors_data["email"]
                            if "header_background" in email_colors:
                                branding["header_gradient"] = email_colors["header_background"]
                            branding.update(email_colors)

                        # Add other color categories if needed
                        for category, colors in colors_data.items():
                            if isinstance(colors, dict):
                                branding.update({f"{category}_{k}": v for k, v in colors.items()})

            except Exception as e:
                logger.debug(f"Could not load consolidated colors for {client_id}: {e}")

            # Cache the result
            self._branding_cache[client_id] = branding
            return branding

        except Exception as e:
            logger.error(f"Failed to load branding for {client_id}: {e}")
            return _get_default_branding()

    def _load_template(self, client_id: str, template_type: str) -> str:
        """
        Load template from client configuration.

        Args:
            client_id: Client identifier
            template_type: Type of template ('classification', 'acknowledgment', 'team-analysis')

        Returns:
            Template content
        """
        cache_key = f"{client_id}:{template_type}"

        if cache_key in self._template_cache:
            return self._template_cache[cache_key]

        try:
            template = get_config_manager().load_ai_prompt(client_id, template_type)

            # Validate template
            validation = self.validate_template(template, client_id)
            if not validation.is_valid:
                logger.warning(
                    f"Template validation failed for {client_id}:{template_type}: {validation.errors}"
                )

            if validation.warnings:
                logger.debug(
                    f"Template warnings for {client_id}:{template_type}: {validation.warnings}"
                )

            self._template_cache[cache_key] = template
            return template

        except Exception as e:
            logger.error(f"Failed to load template {template_type} for {client_id}: {e}")
            raise

    def _prepare_template_context(
        self, client_id: str, email_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Prepare context for template variable injection.

        Args:
            client_id: Client identifier
            email_data: Optional email data

        Returns:
            Context dictionary for template injection
        """
        try:
            client_config = self.client_manager.get_client_config(client_id)
            if not client_config:
                logger.error(f"Could not load client config for {client_id} to prepare context")
                return {"client": {"name": "Unknown Client"}, "email": {}}

            context = {
                "client": {
                    "name": client_config.name,
                    "id": client_config.client_id,
                    "industry": client_config.industry,
                    "timezone": client_config.timezone,
                    "business_hours": "N/A",  # This needs to be adapted from new config
                    "branding": {
                        "company_name": client_config.branding.company_name,
                        "primary_color": client_config.branding.primary_color,
                        "secondary_color": client_config.branding.secondary_color,
                        "logo_url": client_config.branding.logo_url,
                        "email_signature": client_config.branding.email_signature,
                        "footer_text": client_config.branding.footer_text,
                    },
                },
                "today": str(datetime.now().date()) if "datetime" in globals() else "today",
                "timestamp": str(datetime.now()) if "datetime" in globals() else "now",
            }

            if email_data:
                context.update(
                    {
                        "email": {
                            "from": email_data.get("from", ""),
                            "to": email_data.get("to", email_data.get("recipient", "")),
                            "subject": email_data.get("subject", ""),
                            "body": email_data.get(
                                "stripped_text", email_data.get("body_text", "")
                            ),
                            "timestamp": email_data.get("timestamp", ""),
                        }
                    }
                )

            return context

        except Exception as e:
            logger.error(f"Failed to prepare template context for {client_id}: {e}")
            return {"client": {"name": "Unknown Client"}, "email": {}}

    def _inject_template_variables(self, template: str, context: Dict[str, Any]) -> str:
        """
        Inject variables into template using {{variable}} syntax.

        Args:
            template: Template string with {{variable}} placeholders
            context: Context dictionary with variable values

        Returns:
            Template with variables injected
        """
        missing_variables = []

        def replace_variable(match):
            var_expression = match.group(1).strip()

            # Handle default values: {{variable|default:"fallback"}}
            if "|default:" in var_expression:
                var_name, default_expr = var_expression.split("|default:", 1)
                var_name = var_name.strip()
                default_value = default_expr.strip().strip("\"'")
            else:
                var_name = var_expression
                default_value = f"[{var_name}]"  # Less disruptive placeholder

            # Get nested value
            value = self._get_nested_value(context, var_name, default_value)

            # Track missing variables for logging
            if value == default_value and "|default:" not in var_expression:
                missing_variables.append(var_name)
                logger.warning(f"Missing template variable: {var_name}")

            return str(value)

        # Replace all {{variable}} patterns
        result = re.sub(r"{{\s*([^}]+)\s*}}", replace_variable, template)

        # Log missing variables
        if missing_variables:
            logger.warning(
                f"Template processing completed with {len(missing_variables)} missing variables: {missing_variables}"
            )

        # Check for any remaining MISSING: patterns that would break AI
        if "MISSING:" in result:
            logger.error(
                "Template still contains MISSING: patterns after processing - this will break AI prompts"
            )

        return result

    def _get_nested_value(self, data: Dict[str, Any], path: str, default: str = None) -> str:
        """
        Get nested value from dictionary using dot notation.

        Args:
            data: Dictionary to search
            path: Dot-separated path (e.g., 'client.branding.primary_color')
            default: Default value if path not found

        Returns:
            Found value or default
        """
        try:
            keys = path.split(".")
            current = data

            for key in keys:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    return default or f"MISSING: {path}"

            return current

        except Exception:
            return default or f"ERROR: {path}"

    async def _call_ai_service(self, prompt: str) -> str:
        """
        Call Anthropic Claude API with composed prompt.

        Args:
            prompt: Composed AI prompt

        Returns:
            AI response text
        """
        config = get_app_config()

        # Log prompt quality issues before sending to AI
        if "MISSING:" in prompt:
            logger.error(
                "🚨 CRITICAL: Sending malformed prompt to AI with MISSING: variables - this will fail!"
            )
            logger.error(f"Prompt preview: {prompt[:200]}...")
        elif "[" in prompt and "]" in prompt:
            logger.warning("⚠️ Prompt contains placeholder brackets - may affect AI quality")

        logger.debug(f"📤 Sending prompt to Claude API ({len(prompt)} characters)")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": config.services.anthropic_api_key,
                    "anthropic-version": "2023-06-01",
                },
                json={
                    "model": config.services.anthropic_model,
                    "max_tokens": 1000,
                    "temperature": 0.3,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=30.0,
            )

            response.raise_for_status()
            result = response.json()

            ai_response = result["content"][0]["text"]
            logger.debug(f"📥 Received AI response ({len(ai_response)} characters)")

            # Log if AI response looks like it's explaining template issues
            if "template" in ai_response.lower() or "placeholder" in ai_response.lower():
                logger.warning(
                    "⚠️ AI response mentions templates/placeholders - prompt may have been malformed"
                )

            return ai_response

    async def _generate_generic_acknowledgment(
        self, email_data: Dict[str, Any], classification: Dict[str, Any]
    ) -> str:
        """Generate generic acknowledgment when no client is identified."""
        category = classification.get("category", "general")

        prompt = f"""Generate a brief, professional email acknowledgment for a {category} inquiry.

        Original email subject: {email_data.get('subject', 'No subject')}
        From: {email_data.get('from', 'Unknown sender')}

        Requirements:
        - Keep it under 100 words
        - Be warm and professional
        - Acknowledge the specific type of inquiry
        - Set expectation for response time
        - Thank them for contacting
        """

        try:
            return await self._call_ai_service(prompt)
        except Exception as e:
            logger.error(f"Generic acknowledgment generation failed: {e}")
            return self._get_hard_fallback_acknowledgment(classification)

    async def _generate_generic_team_analysis(
        self, email_data: Dict[str, Any], classification: Dict[str, Any]
    ) -> str:
        """Generate generic team analysis when no client is identified."""
        category = classification.get("category", "general")
        confidence = classification.get("confidence", 0.5)

        prompt = f"""Analyze this email for team routing and response.

        Classification: {category} (confidence: {confidence:.2f})
        From: {email_data.get('from', 'Unknown')}
        Subject: {email_data.get('subject', 'No subject')}
        Content: {email_data.get('stripped_text', email_data.get('body_text', ''))[:500]}...

        Provide:
        1. Summary of the issue/request
        2. Suggested response approach
        3. Priority level
        4. Any special considerations
        """

        try:
            return await self._call_ai_service(prompt)
        except Exception as e:
            logger.error(f"Generic team analysis generation failed: {e}")
            return self._get_hard_fallback_team_analysis(classification)

    def _get_hard_fallback_acknowledgment(self, classification: Dict[str, Any]) -> str:
        """Get hard-coded fallback acknowledgment - used only when AI is completely unavailable."""
        category = classification.get("category", "general")

        # Human-like fallback responses with automation disclaimer
        fallbacks = {
            "support": """Hi!

I got your tech support message and I can see you're having some trouble. I've flagged this for our technical team and they'll dig into it for you.

You should hear back within 4 business hours - they're pretty quick with these things.

Thanks for reaching out!

---
This is an automated acknowledgment, but a real person will review your message and respond personally.""",
            "billing": """Hey there!

Thanks for getting in touch about the billing question. I can see this is important to you, so I've sent it straight to our accounting folks who handle all the payment stuff.

They'll take a look and get back to you within 24 hours with an answer.

Appreciate your patience!

---
This is an automated acknowledgment, but a real person will review your message and respond personally.""",
            "sales": """Hi!

Great to hear from you! I can see you're interested in learning more about what we offer.

I've let our sales team know you reached out and they'll be in touch within 2 business hours to chat about your needs and see how we can help.

Looking forward to connecting!

---
This is an automated acknowledgment, but a real person will review your message and respond personally.""",
            "general": """Hi there!

Thanks for your message! I've received it and made sure it gets to the right people for a proper response.

You should hear back within 24 hours.

Thanks for taking the time to reach out!

---
This is an automated acknowledgment, but a real person will review your message and respond personally.""",
        }

        return fallbacks.get(category, fallbacks["general"])

    def _get_hard_fallback_team_analysis(self, classification: Dict[str, Any]) -> str:
        """Get hard-coded fallback team analysis."""
        category = classification.get("category", "general")
        return f"Email classified as {category.upper()} inquiry (fallback classification). Please review the original message and respond accordingly."

    def _get_fallback_classification_prompt(self, email_data: Dict[str, Any]) -> str:
        """Get basic fallback classification prompt."""
        return f"""
You are an intelligent email classifier. Analyze this email and classify it:

Categories:
- support: Technical problems, how-to questions, product issues
- billing: Payment issues, invoices, account billing questions
- sales: Pricing inquiries, product demos, new business opportunities
- general: Everything else that doesn't fit the above categories

Email to classify:
From: {email_data.get('from', 'Unknown')}
Subject: {email_data.get('subject', 'No subject')}
Content: {email_data.get('stripped_text', email_data.get('body_text', ''))[:1000]}

Respond with JSON: {{"category": "support|billing|sales|general", "confidence": 0.95, "reasoning": "explanation"}}
"""

    def _get_fallback_acknowledgment_prompt(
        self, client_id: str, classification: Dict[str, Any]
    ) -> str:
        """Get fallback acknowledgment prompt."""
        category = classification.get("category", "general")
        return f"Generate a professional acknowledgment for a {category} inquiry from {client_id}. Keep it brief and set appropriate expectations."

    def _get_fallback_team_analysis_prompt(
        self, client_id: str, classification: Dict[str, Any]
    ) -> str:
        """Get fallback team analysis prompt."""
        category = classification.get("category", "general")
        return f"""
Email classified as {category.upper()} inquiry (fallback classification).
Client: {client_id}

Please review the original message and respond according to standard {category} procedures.
Check for any special handling requirements or escalation needs.
"""

    def _get_hard_fallback_response(self, response_type: str, category: str) -> str:
        """Get hard-coded fallback response."""
        if response_type == "customer_acknowledgments":
            return f"Thank you for contacting us regarding your {category} inquiry. We will respond as soon as possible."
        else:
            return f"Email classified as {category.upper()} inquiry. Please review and respond accordingly."

    def _get_response_time_target(self, client_id: str, category: str) -> str:
        """Get response time target for a category."""
        try:
            client_config = self.client_manager.get_client_config(client_id)

            # Check if response_times exists in config
            if hasattr(client_config, "response_times") and client_config.response_times:
                response_times = client_config.response_times

                # Get the specific category target
                if hasattr(response_times, category):
                    category_config = getattr(response_times, category)
                    if hasattr(category_config, "target"):
                        return category_config.target

            # Fallback targets based on category
            fallback_targets = {
                "support": "within 4 hours",
                "billing": "within 24 hours",
                "sales": "within 2 hours",
                "urgent": "within 1 hour",
                "general": "within 24 hours",
            }

            return fallback_targets.get(category, "within 24 hours")

        except Exception as e:
            logger.debug(f"Could not get response time target for {client_id}:{category}: {e}")
            return "within 24 hours"


# =============================================================================
# DEPENDENCY INJECTION FUNCTION
# =============================================================================


def get_email_service() -> EmailService:
    """Dependency injection function for EmailService."""
    if not hasattr(get_email_service, "_instance"):
        from ..clients.manager import get_client_manager

        client_manager = get_client_manager()
        get_email_service._instance = EmailService(client_manager)
    return get_email_service._instance


# =============================================================================
# PUBLIC API FUNCTIONS
# =============================================================================


async def generate_plain_text_emails(
    email_data: Dict[str, Any], classification: Dict[str, Any], client_id: Optional[str] = None
) -> Tuple[str, str]:
    """Generate human-like plain text customer response and HTML team analysis."""
    email_service = get_email_service()
    return await email_service.generate_plain_text_emails(email_data, classification, client_id)
