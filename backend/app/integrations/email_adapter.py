# FILE: backend/app/integrations/email_adapter.py
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging
import smtplib
from typing import Optional
from app.core.config import settings

logger = logging.getLogger("replyflow.email")


class EmailAdapter:
    """
    Enterprise Multi-Tenant Email Dispatch Engine.
    Dispatches calendar invites, personalized follow-ups, and transactional emails
    branded strictly for the specific tenant organization.
    """

    @classmethod
    async def send_meeting_invite_email(
        cls,
        recipient_email: str,
        recipient_name: str,
        business_name: str,
        meeting_time: str,
        meeting_link: str,
        project_scope: str,
        sender_email: Optional[str] = None
    ) -> bool:
        subject = f"Discovery Session Confirmed: {business_name} & {recipient_name}"
        from_display = f"{business_name} Operations"
        smtp_user = getattr(settings, "SMTP_USER", "")
        smtp_password = getattr(settings, "SMTP_PASSWORD", "")
        smtp_host = getattr(settings, "SMTP_HOST", "smtp.gmail.com")
        smtp_port = getattr(settings, "SMTP_PORT", 587)

        from_addr = sender_email or smtp_user or "operations@replyflow.ai"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #0b0f19; margin: 0; padding: 20px; color: #f8fafc; }}
            .card {{ max-width: 580px; margin: 0 auto; background-color: #111827; border: 1px solid #1f2937; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }}
            .header {{ background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%); padding: 32px 24px; text-align: center; }}
            .header h1 {{ margin: 0; font-size: 22px; font-weight: 700; color: #ffffff; letter-spacing: -0.5px; }}
            .content {{ padding: 28px 24px; }}
            .badge {{ display: inline-block; padding: 4px 12px; background-color: #064e3b; color: #34d399; font-size: 11px; font-weight: 700; border-radius: 9999px; text-transform: uppercase; margin-bottom: 16px; border: 1px solid #059669; }}
            .meeting-box {{ background-color: #1f2937; border-radius: 12px; padding: 20px; margin: 20px 0; border-left: 4px solid #6366f1; }}
            .btn {{ display: block; text-align: center; background-color: #4f46e5; color: #ffffff; text-decoration: none; padding: 14px 20px; border-radius: 10px; font-weight: 700; font-size: 14px; margin: 24px 0 10px; }}
            .footer {{ border-top: 1px solid #1f2937; padding: 20px; text-align: center; font-size: 11px; color: #6b7280; }}
          </style>
        </head>
        <body>
          <div class="card">
            <div class="header">
              <h1>{business_name}</h1>
            </div>
            <div class="content">
              <span class="badge">Meeting Confirmed</span>
              <p style="font-size: 15px; line-height: 1.5;">Hello <strong>{recipient_name}</strong>,</p>
              <p style="font-size: 14px; color: #94a3b8; line-height: 1.6;">
                Your discovery session with our senior solutions team has been scheduled. We look forward to exploring your requirements for <strong>{project_scope}</strong>.
              </p>
              
              <div class="meeting-box">
                <p style="margin: 0 0 8px; font-size: 13px; color: #94a3b8;">📅 Date & Time:</p>
                <p style="margin: 0 0 16px; font-size: 16px; font-weight: bold; color: #ffffff;">{meeting_time}</p>
                
                <p style="margin: 0 0 8px; font-size: 13px; color: #94a3b8;">📍 Platform:</p>
                <p style="margin: 0; font-size: 14px; font-weight: bold; color: #818cf8;">Google Meet</p>
              </div>

              <a href="{meeting_link}" class="btn" target="_blank">Join Google Meet Discovery Room</a>

              <p style="font-size: 12px; color: #64748b; margin-top: 20px; text-align: center;">
                Need to reschedule? Simply reply to this email or send a message directly on our WhatsApp line.
              </p>
            </div>
            <div class="footer">
              Sent autonomously by {business_name} AI via ReplyFlow. Confidential communication.
            </div>
          </div>
        </body>
        </html>
        """

        # If SMTP credentials are not yet configured in .env, simulate and log cleanly
        if not smtp_user or not smtp_password:
            logger.info(
                f"[Email Simulator] Verified email prepared for {recipient_email} ({business_name}):\n"
                f"Subject: {subject}\n"
                f"Recipient: {recipient_email}\n"
                f"Meeting: {meeting_time} at {meeting_link}"
            )
            return True

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{from_display} <{from_addr}>"
            msg["To"] = recipient_email

            part = MIMEText(html_content, "html")
            msg.attach(part)

            server = smtplib.SMTP(smtp_host, smtp_port, timeout=10.0)
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(from_addr, [recipient_email], msg.as_string())
            server.quit()

            logger.info(f"[Email Live] Successfully dispatched meeting invite to {recipient_email}")
            return True
        except Exception as exc:
            logger.error(f"[Email Dispatch Error] Could not send to {recipient_email}: {exc}")
            return False