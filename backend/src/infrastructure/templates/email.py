"""
Email template generation for customer and team communications.
📧 Creates beautiful HTML and text templates with client-specific branding.
Enhanced with logo support and dynamic color injection.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def generate_ticket_id() -> str:
    """Generate a simple ticket ID"""
    import random
    import string

    return "".join(random.choices(string.ascii_uppercase + string.digits, k=8))


def create_customer_template(
    draft_response: str, classification: dict, branding: Optional[dict] = None
) -> tuple[str, str]:
    """
    Create customer-facing auto-reply with client-specific branding (text + HTML).

    Args:
        draft_response: AI-generated response content
        classification: Email classification result
        branding: Client branding configuration with colors and logo

    Returns:
        Tuple of (text_body, html_body)
    """

    category = classification.get("category", "general")

    # Determine response time based on category
    response_times = {
        "support": "within 4 hours",
        "billing": "within 24 hours",
        "sales": "within 2 hours",
        "general": "within 24 hours",
    }
    response_time = response_times.get(category, "within 24 hours")
    ticket_id = generate_ticket_id()

    # Get branding or use defaults
    if not branding:
        branding = _get_default_branding()

    company_name = branding.get("company_name", "Support Team")
    logo_url = branding.get("logo_url", "")

    # Enhanced plain text version with client branding and proper structure
    text_body = f"""
═══════════════════════════════════════════════════════════════
                   THANK YOU FOR CONTACTING US
                        {company_name.upper()}
═══════════════════════════════════════════════════════════════

📧 YOUR MESSAGE:
{'-' * 60}
{draft_response}

⏱️ WHAT HAPPENS NEXT:
{'-' * 60}
Expected Response Time: **{response_time.upper()}**

A team member will review your message and respond personally
during business hours.

🎫 REFERENCE INFORMATION:
{'-' * 60}
Ticket Number: **{ticket_id}**

Please reference this ticket number in any future correspondence.

═══════════════════════════════════════════════════════════════
Best regards,
**{company_name}**

🤖 AUTOMATED ACKNOWLEDGMENT
This is an automated response. A team member will follow up
personally with a detailed response.
═══════════════════════════════════════════════════════════════
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
            .section-header {{ font-size: 18px !important; }}
        }}
        .highlight-box {{
            background: linear-gradient(135deg, {branding.get('accent_background', '#f0f9ff')} 0%, {branding.get('accent_background', '#e0f2fe')} 100%);
            border-left: 4px solid {branding.get('accent_border_color', '#667eea')};
            border-radius: 0 8px 8px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}
        .info-card {{
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            transition: all 0.2s ease;
        }}
        .info-card:hover {{
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }}
    </style>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; background-color: #f8f9fa;">
    <div class="email-container" style="max-width: 600px; margin: 0 auto; background-color: {branding.get('body_background', '#ffffff')}; box-shadow: 0 4px 16px rgba(0,0,0,0.1);">

        <!-- Header with dynamic branding -->
        <div class="header-padding" style="background: {branding.get('header_gradient', 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)')}; padding: 30px; text-align: center; position: relative;">
            <div style="margin-bottom: 15px; {logo_style}">
                <img src="{logo_url}" alt="{company_name}" style="max-height: 60px; max-width: 200px;">
            </div>
            <h1 style="color: {branding.get('header_text_color', '#ffffff')}; margin: 0; font-size: 26px; font-weight: 700; text-shadow: 0 2px 4px rgba(0,0,0,0.2);">Thank You for Contacting Us</h1>
            <div style="margin-top: 12px; height: 3px; width: 60px; background: rgba(255,255,255,0.5); margin-left: auto; margin-right: auto; border-radius: 2px;"></div>
        </div>

        <!-- Main Content -->
        <div class="content-padding" style="padding: 40px 30px;">

            <!-- Message Section -->
            <div style="margin-bottom: 35px;">
                <h2 class="section-header" style="color: {branding.get('body_text_color', '#2d3748')}; font-size: 20px; font-weight: 600; margin: 0 0 15px 0; padding-bottom: 8px; border-bottom: 2px solid {branding.get('accent_border_color', '#667eea')};">📧 Your Message</h2>
                <div class="highlight-box" style="padding: 25px; margin-bottom: 0;">
                    <p style="margin: 0; color: {branding.get('body_text_color', '#2d3748')}; line-height: 1.7; font-size: 16px; font-weight: 400;">{draft_response}</p>
                </div>
            </div>

            <!-- Response Time Section -->
            <div style="margin-bottom: 35px;">
                <h2 class="section-header" style="color: {branding.get('body_text_color', '#2d3748')}; font-size: 20px; font-weight: 600; margin: 0 0 15px 0; padding-bottom: 8px; border-bottom: 2px solid {branding.get('accent_border_color', '#667eea')};">⏱️ What Happens Next</h2>
                <div class="info-card" style="padding: 20px;">
                    <div style="display: flex; align-items: center; margin-bottom: 12px;">
                        <div style="background: {branding.get('link_color', '#0369a1')}; color: white; border-radius: 50%; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; font-size: 16px; margin-right: 12px; font-weight: bold;">1</div>
                        <strong style="color: {branding.get('link_color', '#0369a1')}; font-size: 16px;">Expected Response Time</strong>
                    </div>
                    <p style="margin: 0 0 0 44px; color: {branding.get('body_text_color', '#2d3748')}; font-size: 18px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;">{response_time}</p>
                    <p style="margin: 8px 0 0 44px; color: {branding.get('footer_text_color', '#64748b')}; font-size: 14px; line-height: 1.5;">A team member will review your message and respond personally during business hours.</p>
                </div>
            </div>

            <!-- Ticket Information Section -->
            <div style="margin-bottom: 35px;">
                <h2 class="section-header" style="color: {branding.get('body_text_color', '#2d3748')}; font-size: 20px; font-weight: 600; margin: 0 0 15px 0; padding-bottom: 8px; border-bottom: 2px solid {branding.get('accent_border_color', '#667eea')};">🎫 Reference Information</h2>
                <div class="info-card" style="padding: 20px; text-align: center;">
                    <div style="background: linear-gradient(135deg, {branding.get('accent_background', '#f0f9ff')} 0%, {branding.get('accent_background', '#e0f2fe')} 100%); border-radius: 8px; padding: 15px; margin-bottom: 15px;">
                        <p style="margin: 0; color: {branding.get('footer_text_color', '#64748b')}; font-size: 14px; text-transform: uppercase; letter-spacing: 1px; font-weight: 500;">Ticket Number</p>
                        <p style="margin: 5px 0 0 0; color: {branding.get('body_text_color', '#2d3748')}; font-size: 24px; font-weight: 800; font-family: 'Courier New', monospace;">{ticket_id}</p>
                    </div>
                    <p style="margin: 0; color: {branding.get('footer_text_color', '#64748b')}; font-size: 13px; line-height: 1.4;">Please reference this ticket number in any future correspondence.</p>
                </div>
            </div>

            <!-- Contact Section -->
            <div style="text-align: center; padding: 25px; background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%); border-radius: 12px; border: 1px solid #e2e8f0;">
                <h3 style="color: {branding.get('body_text_color', '#2d3748')}; font-size: 18px; font-weight: 600; margin: 0 0 15px 0;">Best regards,</h3>
                <p style="margin: 0; color: {branding.get('body_text_color', '#2d3748')}; font-size: 20px; font-weight: 700;">{company_name}</p>
                <div style="margin-top: 15px; height: 2px; width: 40px; background: {branding.get('accent_border_color', '#667eea')}; margin-left: auto; margin-right: auto;"></div>
            </div>
        </div>

        <!-- Footer with client branding -->
        <div style="background: linear-gradient(135deg, {branding.get('footer_background', '#f8f9fa')} 0%, #f1f5f9 100%); padding: 25px 30px; text-align: center; border-top: 1px solid #e2e8f0;">
            <p style="margin: 0 0 10px 0; color: {branding.get('body_text_color', '#2d3748')}; font-size: 13px; font-weight: 600;">
                🤖 <strong>Automated Acknowledgment</strong>
            </p>
            <p style="margin: 0 0 15px 0; color: {branding.get('footer_text_color', '#64748b')}; font-size: 12px; line-height: 1.5;">
                This is an automated response. A team member will follow up personally with a detailed response.
            </p>
            <p style="margin: 0; color: {branding.get('footer_text_color', '#64748b')}; font-size: 11px; font-style: italic;">
                {branding.get('footer_text', '')}
            </p>
        </div>

    </div>
</body>
</html>
"""

    return text_body, html_body


def create_team_template(
    email_data: dict,
    classification: dict,
    draft_response: str,
    branding: Optional[dict] = None,
) -> tuple[str, str]:
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

    category = classification.get("category", "general")
    confidence = classification.get("confidence", 0.0)
    reasoning = classification.get("reasoning", "No reasoning provided")

    # Get branding or use defaults
    if not branding:
        branding = _get_default_branding()

    company_name = branding.get("company_name", "Support Team")

    # Dynamic confidence color and text based on percentage
    confidence_color = (
        "#16a34a"
        if confidence >= 0.8
        else "#f59e0b"
        if confidence >= 0.6
        else "#ef4444"
    )
    confidence_text = (
        "HIGH" if confidence >= 0.8 else "MEDIUM" if confidence >= 0.6 else "LOW"
    )

    # Enhanced plain text version with client branding and improved structure
    text_body = f"""
═══════════════════════════════════════════════════════════════
🤖 AI EMAIL ANALYSIS - {company_name.upper()}
═══════════════════════════════════════════════════════════════

📋 CLASSIFICATION SUMMARY:
{'-' * 60}
Category: **{category.upper()}**
Confidence: **{confidence:.0%}** ({confidence_text})
AI Reasoning: {reasoning}

📧 ORIGINAL MESSAGE DETAILS:
{'-' * 60}
From: **{email_data['from']}**
To: {email_data.get('to', 'N/A')}
Subject: **{email_data['subject']}**

MESSAGE CONTENT:
{'-' * 40}
{email_data['stripped_text'] or email_data['body_text']}

✍️ AI ANALYSIS & SUGGESTED RESPONSE:
{'-' * 60}
{draft_response}

🎯 NEXT ACTIONS:
{'-' * 60}
✅ Customer has received automated acknowledgment
📧 Reply to this email to respond directly to the customer
⚡ Processing time: 5-7 seconds (within SLA)

═══════════════════════════════════════════════════════════════
{company_name} - AI-Powered Email Processing
═══════════════════════════════════════════════════════════════
"""

    # Enhanced HTML with client branding
    analysis_html = draft_response.replace("\n", "<br>")
    email_body_html = (email_data["stripped_text"] or email_data["body_text"]).replace(
        "\n", "<br>"
    )

    # Hide logo if URL is empty
    logo_url = branding.get("logo_url", "")
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
            .section-header {{ font-size: 18px !important; }}
        }}
        .info-card {{
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            transition: all 0.2s ease;
        }}
        .info-card:hover {{
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}
        .classification-badge {{
            display: inline-block;
            background: {confidence_color};
            color: white;
            padding: 6px 16px;
            border-radius: 25px;
            font-size: 13px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .section-divider {{
            height: 3px;
            background: linear-gradient(90deg, {branding.get('accent_border_color', '#3b82f6')} 0%, transparent 100%);
            border-radius: 2px;
            margin: 20px 0;
        }}
    </style>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; background-color: #f3f4f6;">
    <div class="email-container" style="max-width: 800px; margin: 0 auto; background-color: {branding.get('body_background', '#ffffff')}; box-shadow: 0 4px 20px rgba(0,0,0,0.1);">

        <!-- Header with client branding -->
        <div class="header-padding" style="background: {branding.get('header_gradient', 'linear-gradient(135deg, #1e293b 0%, #334155 100%)')}; padding: 30px; color: {branding.get('header_text_color', 'white')}; position: relative;">
            <div style="text-align: center; margin-bottom: 20px; {logo_style}">
                <img src="{logo_url}" alt="{company_name}" style="max-height: 45px; max-width: 160px;">
            </div>
            <h1 style="margin: 0; font-size: 26px; font-weight: 700; text-align: center; text-shadow: 0 2px 4px rgba(0,0,0,0.3);">🤖 AI Email Analysis</h1>
            <p style="margin: 12px 0 0 0; opacity: 0.9; font-size: 16px; text-align: center; font-weight: 500;">{company_name} - Automated Classification System</p>
            <div style="margin-top: 20px; height: 3px; width: 80px; background: rgba(255,255,255,0.5); margin-left: auto; margin-right: auto; border-radius: 2px;"></div>
        </div>

        <div style="padding: 30px;">

            <!-- Classification Summary Section -->
            <div style="margin-bottom: 35px;">
                <h2 class="section-header" style="color: {branding.get('body_text_color', '#1f2937')}; font-size: 22px; font-weight: 700; margin: 0 0 20px 0; padding-bottom: 10px; border-bottom: 3px solid {branding.get('accent_border_color', '#3b82f6')};">📋 Classification Summary</h2>
                <div class="info-card" style="padding: 25px; background: linear-gradient(135deg, #f0fdf4 0%, #ecfdf5 100%); border-left: 5px solid #22c55e;">
                    <div style="display: flex; align-items: center; margin-bottom: 15px; flex-wrap: wrap; gap: 15px;">
                        <div style="flex: 1; min-width: 200px;">
                            <h3 style="margin: 0; color: #166534; font-size: 24px; font-weight: 800; text-transform: uppercase; letter-spacing: 1px;">{category}</h3>
                        </div>
                        <div class="classification-badge">{confidence:.0%} {confidence_text}</div>
                    </div>
                    <div class="section-divider"></div>
                    <div style="background: rgba(255,255,255,0.7); border-radius: 8px; padding: 15px;">
                        <h4 style="margin: 0 0 8px 0; color: #166534; font-size: 14px; font-weight: 600; text-transform: uppercase;">AI Reasoning:</h4>
                        <p style="margin: 0; color: #166534; font-weight: 500; line-height: 1.6;">{reasoning}</p>
                    </div>
                </div>
            </div>

            <!-- Original Message Section -->
            <div style="margin-bottom: 35px;">
                <h2 class="section-header" style="color: {branding.get('body_text_color', '#1f2937')}; font-size: 22px; font-weight: 700; margin: 0 0 20px 0; padding-bottom: 10px; border-bottom: 3px solid {branding.get('accent_border_color', '#3b82f6')};">📧 Original Message Details</h2>
                <div class="info-card" style="overflow: hidden;">
                    <div style="background: linear-gradient(135deg, {branding.get('accent_background', '#f9fafb')} 0%, #f3f4f6 100%); padding: 20px; border-bottom: 1px solid #e5e7eb;">
                        <div style="display: grid; grid-template-columns: auto 1fr; gap: 12px; margin-bottom: 15px;">
                            <strong style="color: {branding.get('body_text_color', '#374151')}; font-weight: 700;">From:</strong>
                            <span style="color: {branding.get('body_text_color', '#374151')}; font-weight: 600;">{email_data['from']}</span>
                            <strong style="color: {branding.get('body_text_color', '#374151')}; font-weight: 700;">Subject:</strong>
                            <span style="color: {branding.get('body_text_color', '#374151')}; font-weight: 600;">{email_data['subject']}</span>
                        </div>
                    </div>
                    <div class="content-padding" style="padding: 25px;">
                        <h4 style="margin: 0 0 15px 0; color: {branding.get('body_text_color', '#374151')}; font-size: 16px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Message Content:</h4>
                        <div style="background: linear-gradient(135deg, {branding.get('accent_background', '#f8fafc')} 0%, #f1f5f9 100%); border-left: 5px solid {branding.get('accent_border_color', '#3b82f6')}; padding: 20px; border-radius: 0 8px 8px 0; box-shadow: inset 0 1px 3px rgba(0,0,0,0.05);">
                            <p style="margin: 0; color: {branding.get('body_text_color', '#1e293b')}; line-height: 1.7; font-size: 16px;">{email_body_html}</p>
                        </div>
                    </div>
                </div>
            </div>

            <!-- AI Analysis Section -->
            <div style="margin-bottom: 35px;">
                <h2 class="section-header" style="color: {branding.get('body_text_color', '#1f2937')}; font-size: 22px; font-weight: 700; margin: 0 0 20px 0; padding-bottom: 10px; border-bottom: 3px solid {branding.get('accent_border_color', '#3b82f6')};">🔍 AI Analysis & Recommendations</h2>
                <div class="info-card" style="overflow: hidden;">
                    <div style="background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%); padding: 20px; border-bottom: 1px solid #93c5fd;">
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <div style="background: {branding.get('link_color', '#1e40af')}; color: white; border-radius: 50%; width: 36px; height: 36px; display: flex; align-items: center; justify-content: center; font-size: 18px;">🧠</div>
                            <h3 style="margin: 0; color: {branding.get('link_color', '#1e40af')}; font-size: 18px; font-weight: 700;">Suggested Response & Actions</h3>
                        </div>
                    </div>
                    <div class="content-padding" style="padding: 25px;">
                        <div style="background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%); border-radius: 8px; padding: 20px; box-shadow: inset 0 1px 3px rgba(0,0,0,0.05);">
                            <div style="color: {branding.get('body_text_color', '#1e293b')}; line-height: 1.8; font-size: 16px;">{analysis_html}</div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Next Actions Section -->
            <div style="margin-bottom: 35px;">
                <h2 class="section-header" style="color: {branding.get('body_text_color', '#1f2937')}; font-size: 22px; font-weight: 700; margin: 0 0 20px 0; padding-bottom: 10px; border-bottom: 3px solid {branding.get('accent_border_color', '#3b82f6')};">🎯 Next Actions</h2>
                <div class="info-card" style="padding: 25px; background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);">
                    <div style="display: grid; gap: 20px;">
                        <div style="display: flex; align-items: center; gap: 15px;">
                            <div style="background: #22c55e; color: white; border-radius: 50%; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; font-size: 16px; font-weight: bold; flex-shrink: 0;">✓</div>
                            <p style="margin: 0; color: {branding.get('body_text_color', '#1e293b')}; font-size: 16px; font-weight: 600;">Customer has received automated acknowledgment</p>
                        </div>
                        <div style="display: flex; align-items: center; gap: 15px;">
                            <div style="background: {branding.get('link_color', '#3730a3')}; color: white; border-radius: 50%; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; font-size: 16px; font-weight: bold; flex-shrink: 0;">📧</div>
                            <p style="margin: 0; color: {branding.get('body_text_color', '#1e293b')}; font-size: 16px; font-weight: 600;">Reply to this email to respond directly to the customer</p>
                        </div>
                        <div style="display: flex; align-items: center; gap: 15px;">
                            <div style="background: #f59e0b; color: white; border-radius: 50%; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; font-size: 16px; font-weight: bold; flex-shrink: 0;">⚡</div>
                            <p style="margin: 0; color: {branding.get('body_text_color', '#1e293b')}; font-size: 16px; font-weight: 600;">Processing completed in 5-7 seconds (within SLA)</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Footer -->
        <div style="background: linear-gradient(135deg, {branding.get('footer_background', '#f8f9fa')} 0%, #f1f5f9 100%); padding: 25px; text-align: center; border-top: 1px solid #e2e8f0;">
            <p style="margin: 0; color: {branding.get('body_text_color', '#1f2937')}; font-size: 14px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;">
                {company_name} - AI-Powered Email Processing
            </p>
            <div style="margin-top: 10px; height: 2px; width: 60px; background: {branding.get('accent_border_color', '#3b82f6')}; margin-left: auto; margin-right: auto;"></div>
        </div>

    </div>
</body>
</html>
"""

    return text_body, html_body


def create_branded_template(
    template_type: str, context: dict, branding: Optional[dict] = None
) -> tuple[str, str]:
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

    if template_type == "customer_reply":
        return create_customer_template(
            context.get("draft_response", ""),
            context.get("classification", {}),
            branding,
        )
    elif template_type == "team_forward":
        return create_team_template(
            context.get("email_data", {}),
            context.get("classification", {}),
            context.get("draft_response", ""),
            branding,
        )
    else:
        # Fallback for unknown template types
        logger.warning(f"Unknown template type: {template_type}")
        return create_customer_template(
            context.get("draft_response", "Thank you for contacting us."),
            context.get("classification", {}),
            branding,
        )


def _get_default_branding() -> dict:
    """
    Get default branding configuration when client branding is not available.

    Returns:
        Default branding dictionary
    """
    return {
        "company_name": "Email Router",
        "primary_color": "#667eea",
        "secondary_color": "#764ba2",
        "header_gradient": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        "header_text_color": "#ffffff",
        "body_background": "#ffffff",
        "body_text_color": "#374151",
        "accent_background": "#f8f9ff",
        "accent_border_color": "#667eea",
        "footer_background": "#f8f9fa",
        "footer_text_color": "#6b7280",
        "link_color": "#667eea",
        "logo_url": "",
        "footer_text": "",
    }
