"""
Email template generation for customer and team communications.
📧 Creates beautiful HTML and text templates with client-specific branding.
Enhanced with logo support and dynamic color injection.
"""

import logging
from typing import Dict, Any, Tuple, Optional

logger = logging.getLogger(__name__)

def generate_ticket_id() -> str:
    """Generate a simple ticket ID"""
    import random
    import string
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def create_customer_template(draft_response: str, classification: dict, branding: dict = None) -> tuple[str, str]:
    """
    Create customer-facing auto-reply with client-specific branding (text + HTML).
    
    Args:
        draft_response: AI-generated response content
        classification: Email classification result
        branding: Client branding configuration with colors and logo
        
    Returns:
        Tuple of (text_body, html_body)
    """
    
    category = classification.get('category', 'general')
    
    # Determine response time based on category
    response_times = {
        "support": "within 4 hours",
        "billing": "within 24 hours", 
        "sales": "within 2 hours",
        "general": "within 24 hours"
    }
    response_time = response_times.get(category, "within 24 hours")
    ticket_id = generate_ticket_id()
    
    # Get branding or use defaults
    if not branding:
        branding = _get_default_branding()
    
    company_name = branding.get('company_name', 'Support Team')
    logo_url = branding.get('logo_url', '')
    
    # Plain text version with client branding
    text_body = f"""
{draft_response}

Expected Response Time: {response_time}

Best regards,
{company_name}

---
Ticket #: {ticket_id}
This is an automated acknowledgment. A team member will follow up personally.
"""

    # Enhanced HTML version with dynamic branding
    # Hide logo if URL is empty
    logo_style = "display: none;" if not logo_url else ""
    
    html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Thank You for Contacting Us</title>
    <style>
        @media only screen and (max-width: 600px) {{
            .email-container {{ width: 100% !important; }}
            .content-padding {{ padding: 20px !important; }}
            .header-padding {{ padding: 20px !important; }}
        }}
    </style>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; background-color: #f8f9fa;">
    <div class="email-container" style="max-width: 600px; margin: 0 auto; background-color: {branding.get('body_background', '#ffffff')};">
        
        <!-- Header with dynamic branding -->
        <div class="header-padding" style="background: {branding.get('header_gradient', 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)')}; padding: 30px; text-align: center;">
            <div style="margin-bottom: 15px; {logo_style}">
                <img src="{logo_url}" alt="{company_name}" style="max-height: 60px; max-width: 200px;">
            </div>
            <h1 style="color: {branding.get('header_text_color', '#ffffff')}; margin: 0; font-size: 24px; font-weight: 600;">Thank You for Contacting Us</h1>
        </div>
        
        <!-- Main Content -->
        <div class="content-padding" style="padding: 40px 30px;">
            <div style="background-color: {branding.get('accent_background', '#f8f9ff')}; border-left: 4px solid {branding.get('accent_border_color', '#667eea')}; padding: 20px; margin-bottom: 30px; border-radius: 0 6px 6px 0;">
                <p style="margin: 0; color: {branding.get('body_text_color', '#2d3748')}; line-height: 1.6; font-size: 16px;">{draft_response}</p>
            </div>
            
            <div style="background-color: #f0f9ff; border: 1px solid #e0f2fe; border-radius: 8px; padding: 20px; margin-bottom: 30px;">
                <div style="display: flex; align-items: center; margin-bottom: 10px;">
                    <span style="color: {branding.get('link_color', '#0369a1')}; font-size: 18px; margin-right: 8px;">⏱️</span>
                    <strong style="color: {branding.get('link_color', '#0369a1')};">Expected Response Time:</strong>
                </div>
                <p style="margin: 0; color: #075985; font-size: 16px; font-weight: 600;">{response_time}</p>
            </div>
            
            <div style="text-align: center; color: {branding.get('footer_text_color', '#64748b')}; font-size: 14px; line-height: 1.5;">
                <p>Ticket #: <strong>{ticket_id}</strong></p>
                <p>Best regards,<br><strong>{company_name}</strong></p>
            </div>
        </div>
        
        <!-- Footer with client branding -->
        <div style="background-color: {branding.get('footer_background', '#f8f9fa')}; padding: 20px 30px; text-align: center; border-top: 1px solid #e2e8f0;">
            <p style="margin: 0; color: {branding.get('footer_text_color', '#64748b')}; font-size: 12px;">
                🤖 This is an automated acknowledgment. A team member will follow up personally.
            </p>
            <p style="margin: 10px 0 0 0; color: {branding.get('footer_text_color', '#64748b')}; font-size: 11px;">
                {branding.get('footer_text', '')}
            </p>
        </div>
        
    </div>
</body>
</html>
"""
    
    return text_body, html_body

def create_team_template(email_data: dict, classification: dict, draft_response: str, branding: dict = None) -> tuple[str, str]:
    """
    Create team-facing forwarded email with client-specific branding (text + HTML).
    
    Args:
        email_data: Original email data from webhook
        classification: AI classification result  
        draft_response: AI-generated response draft
        branding: Client branding configuration
        
    Returns:
        Tuple of (text_body, html_body)
    """
    
    category = classification.get('category', 'general')
    confidence = classification.get('confidence', 0.0)
    reasoning = classification.get('reasoning', 'No reasoning provided')
    
    # Get branding or use defaults
    if not branding:
        branding = _get_default_branding()
    
    company_name = branding.get('company_name', 'Support Team')
    
    # Plain text version with client branding
    text_body = f"""
🤖 AI EMAIL ROUTER - {company_name.upper()}

📋 CLASSIFICATION: {category} (confidence: {confidence:.2f})
💭 REASONING: {reasoning}

📧 ORIGINAL MESSAGE:
From: {email_data['from']}
To: {email_data.get('to', 'N/A')}
Subject: {email_data['subject']}

{email_data['stripped_text'] or email_data['body_text']}

---

✍️ SUGGESTED RESPONSE DRAFT:

{draft_response}

---
Reply to this email to respond to the original sender.
The customer has already received an automated acknowledgment.
"""

    # Enhanced HTML with client branding
    analysis_html = draft_response.replace('\n', '<br>')
    email_body_html = (email_data['stripped_text'] or email_data['body_text']).replace('\n', '<br>')
    
    # Dynamic confidence color based on percentage
    confidence_color = "#16a34a" if confidence >= 0.8 else "#f59e0b" if confidence >= 0.6 else "#ef4444"
    confidence_text = "HIGH" if confidence >= 0.8 else "MEDIUM" if confidence >= 0.6 else "LOW"
    
    # Hide logo if URL is empty
    logo_url = branding.get('logo_url', '')
    logo_style = "display: none;" if not logo_url else ""
    
    html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Email Analysis - {company_name}</title>
    <style>
        @media only screen and (max-width: 800px) {{
            .email-container {{ width: 100% !important; margin: 10px !important; }}
            .content-padding {{ padding: 15px !important; }}
            .header-padding {{ padding: 20px !important; }}
        }}
    </style>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; background-color: #f8f9fa;">
    <div class="email-container" style="max-width: 800px; margin: 0 auto; background-color: {branding.get('body_background', '#ffffff')};">
        
        <!-- Header with client branding -->
        <div class="header-padding" style="background: {branding.get('header_gradient', 'linear-gradient(135deg, #1e293b 0%, #334155 100%)')}; padding: 25px; color: {branding.get('header_text_color', 'white')};">
            <div style="text-align: center; margin-bottom: 15px; {logo_style}">
                <img src="{logo_url}" alt="{company_name}" style="max-height: 40px; max-width: 150px;">
            </div>
            <h1 style="margin: 0; font-size: 22px; font-weight: 600;">🤖 AI Email Analysis</h1>
            <p style="margin: 8px 0 0 0; opacity: 0.9; font-size: 14px;">{company_name} - Automated Classification</p>
        </div>
        
        <!-- Classification Card with dynamic colors -->
        <div style="margin: 20px; background: linear-gradient(135deg, #ecfdf5 0%, #f0fdf4 100%); border: 1px solid #bbf7d0; border-radius: 12px; padding: 20px;">
            <div style="margin-bottom: 15px;">
                <span style="font-size: 24px; margin-right: 10px;">📋</span>
                <span style="color: #166534; text-transform: uppercase; letter-spacing: 1px; font-weight: 600; font-size: 18px;">{category}</span>
                <span style="margin-left: 15px; background: {confidence_color}; color: white; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600;">{confidence:.0%} {confidence_text}</span>
            </div>
            <p style="margin: 0; color: #166534; font-weight: 500;">{reasoning}</p>
        </div>
        
        <!-- Original Email Card -->
        <div style="margin: 20px; border: 1px solid #e5e7eb; border-radius: 12px; overflow: hidden;">
            <div style="background: {branding.get('accent_background', '#f9fafb')}; padding: 15px; border-bottom: 1px solid #e5e7eb;">
                <h3 style="margin: 0; color: {branding.get('body_text_color', '#374151')}; font-size: 16px;">📧 Original Message</h3>
            </div>
            <div class="content-padding" style="padding: 20px;">
                <div style="margin-bottom: 15px;">
                    <strong style="color: {branding.get('body_text_color', '#374151')};">From:</strong> <span style="color: {branding.get('footer_text_color', '#6b7280')};">{email_data['from']}</span><br>
                    <strong style="color: {branding.get('body_text_color', '#374151')};">Subject:</strong> <span style="color: {branding.get('footer_text_color', '#6b7280')};">{email_data['subject']}</span>
                </div>
                <div style="background: {branding.get('accent_background', '#f8fafc')}; border-left: 4px solid {branding.get('accent_border_color', '#3b82f6')}; padding: 15px; border-radius: 0 6px 6px 0;">
                    <p style="margin: 0; color: {branding.get('body_text_color', '#1e293b')}; line-height: 1.6;">{email_body_html}</p>
                </div>
            </div>
        </div>
        
        <!-- AI Analysis Card -->
        <div style="margin: 20px; border: 1px solid #e5e7eb; border-radius: 12px; overflow: hidden;">
            <div style="background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%); padding: 15px; border-bottom: 1px solid #93c5fd;">
                <h3 style="margin: 0; color: {branding.get('link_color', '#1e40af')}; font-size: 16px;">🔍 AI Analysis & Recommendations</h3>
            </div>
            <div class="content-padding" style="padding: 20px;">
                <div style="color: {branding.get('body_text_color', '#1e293b')}; line-height: 1.7;">{analysis_html}</div>
            </div>
        </div>
        
        <!-- Action Buttons -->
        <div style="margin: 20px; text-align: center; padding: 20px;">
            <p style="color: {branding.get('footer_text_color', '#6b7280')}; margin-bottom: 15px; font-size: 14px;">
                ✅ Customer has already received an automated acknowledgment
            </p>
            <div style="background: #f0f9ff; border: 1px solid {branding.get('accent_border_color', '#c7d2fe')}; border-radius: 8px; padding: 15px; margin-top: 20px;">
                <p style="margin: 0; color: {branding.get('link_color', '#3730a3')}; font-weight: 600;">
                    📧 Reply to this email to respond directly to the customer
                </p>
            </div>
        </div>
        
        <!-- Footer -->
        <div style="background-color: {branding.get('footer_background', '#f8f9fa')}; padding: 20px; text-align: center; border-top: 1px solid #e2e8f0;">
            <p style="margin: 0; color: {branding.get('footer_text_color', '#64748b')}; font-size: 12px;">
                {company_name} - AI-Powered Email Processing
            </p>
        </div>
        
    </div>
</body>
</html>
"""
    
    return text_body, html_body

def create_branded_template(template_type: str, context: dict, branding: dict = None) -> tuple[str, str]:
    """
    Create branded email template with client-specific styling.
    
    Args:
        template_type: Type of template ('customer_reply', 'team_forward', 'notification')
        context: Template context with email data and variables
        branding: Client branding configuration
        
    Returns:
        Tuple of (text_body, html_body)
    """
    
    if not branding:
        branding = _get_default_branding()
    
    if template_type == 'customer_reply':
        return create_customer_template(
            context.get('draft_response', ''),
            context.get('classification', {}),
            branding
        )
    elif template_type == 'team_forward':
        return create_team_template(
            context.get('email_data', {}),
            context.get('classification', {}),
            context.get('draft_response', ''),
            branding
        )
    else:
        # Fallback for unknown template types
        logger.warning(f"Unknown template type: {template_type}")
        return create_customer_template(
            context.get('draft_response', 'Thank you for contacting us.'),
            context.get('classification', {}),
            branding
        )

def _get_default_branding() -> dict:
    """
    Get default branding configuration when client branding is not available.
    
    Returns:
        Default branding dictionary
    """
    return {
        'company_name': 'Email Router',
        'primary_color': '#667eea',
        'secondary_color': '#764ba2',
        'header_gradient': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        'header_text_color': '#ffffff',
        'body_background': '#ffffff',
        'body_text_color': '#374151',
        'accent_background': '#f8f9ff',
        'accent_border_color': '#667eea',
        'footer_background': '#f8f9fa',
        'footer_text_color': '#6b7280',
        'link_color': '#667eea',
        'logo_url': '',
        'footer_text': ''
    } 