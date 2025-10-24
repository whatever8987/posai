"""
Notification Service
Delivers insights through multiple channels: email, webhooks, in-app
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import httpx
import json
from enum import Enum

from ..models import Insight, InsightSeverity


class NotificationChannel(str, Enum):
    """Notification delivery channels"""
    EMAIL = "email"
    WEBHOOK = "webhook"
    IN_APP = "in_app"
    SMS = "sms"  # Future


class NotificationService:
    """
    Service for delivering insight notifications
    
    Supports multiple delivery channels and formats messages appropriately
    """
    
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
    
    async def send_insight_notification(
        self,
        insight: Insight,
        channels: List[NotificationChannel],
        recipient_config: Dict[str, Any]
    ) -> Dict[str, bool]:
        """
        Send notification about an insight through specified channels
        
        Args:
            insight: Insight object to notify about
            channels: List of channels to use
            recipient_config: Configuration for each channel (emails, webhooks, etc.)
        
        Returns:
            Dictionary of channel -> success status
        """
        results = {}
        
        for channel in channels:
            try:
                if channel == NotificationChannel.EMAIL:
                    success = await self._send_email_notification(insight, recipient_config)
                    results[channel.value] = success
                elif channel == NotificationChannel.WEBHOOK:
                    success = await self._send_webhook_notification(insight, recipient_config)
                    results[channel.value] = success
                elif channel == NotificationChannel.IN_APP:
                    # In-app notifications are handled by the database (Insight table)
                    results[channel.value] = True
                else:
                    results[channel.value] = False
            except Exception as e:
                print(f"Error sending {channel} notification: {e}")
                results[channel.value] = False
        
        return results
    
    async def _send_email_notification(
        self,
        insight: Insight,
        config: Dict[str, Any]
    ) -> bool:
        """
        Send email notification about insight
        
        In production, integrate with SendGrid, AWS SES, or similar
        For now, this is a placeholder that logs the email content
        """
        email_addresses = config.get("emails", [])
        
        if not email_addresses:
            return False
        
        # Format email content
        subject = self._format_email_subject(insight)
        body = self._format_email_body(insight)
        
        # TODO: Integrate with actual email service
        # For now, log the email
        print(f"📧 EMAIL NOTIFICATION")
        print(f"To: {', '.join(email_addresses)}")
        print(f"Subject: {subject}")
        print(f"Body:\n{body}")
        print(f"=" * 60)
        
        # In production:
        # async with httpx.AsyncClient() as client:
        #     response = await client.post(
        #         "https://api.sendgrid.com/v3/mail/send",
        #         headers={"Authorization": f"Bearer {SENDGRID_API_KEY}"},
        #         json={
        #             "personalizations": [{"to": [{"email": email} for email in email_addresses]}],
        #             "from": {"email": "insights@nailsalon-ai.com"},
        #             "subject": subject,
        #             "content": [{"type": "text/html", "value": body}]
        #         }
        #     )
        #     return response.status_code == 202
        
        return True  # Simulated success
    
    async def _send_webhook_notification(
        self,
        insight: Insight,
        config: Dict[str, Any]
    ) -> bool:
        """
        Send webhook notification about insight
        
        POSTs insight data to configured webhook URL
        """
        webhook_url = config.get("webhook_url")
        
        if not webhook_url:
            return False
        
        # Prepare payload
        payload = {
            "event": "insight.created",
            "timestamp": datetime.utcnow().isoformat(),
            "tenant_id": str(self.tenant_id),
            "insight": insight.to_dict()
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=10.0
                )
                
                # Consider 2xx responses as success
                return 200 <= response.status_code < 300
                
        except Exception as e:
            print(f"Webhook delivery failed: {e}")
            return False
    
    async def send_daily_digest(
        self,
        insights: List[Insight],
        channels: List[NotificationChannel],
        recipient_config: Dict[str, Any]
    ) -> Dict[str, bool]:
        """
        Send daily digest of insights
        
        Groups and summarizes insights for easier consumption
        """
        if not insights:
            return {channel.value: True for channel in channels}  # No insights = success
        
        results = {}
        
        for channel in channels:
            try:
                if channel == NotificationChannel.EMAIL:
                    success = await self._send_digest_email(insights, recipient_config)
                    results[channel.value] = success
                else:
                    results[channel.value] = False  # Other channels not implemented for digest
            except Exception as e:
                print(f"Error sending digest via {channel}: {e}")
                results[channel.value] = False
        
        return results
    
    async def _send_digest_email(
        self,
        insights: List[Insight],
        config: Dict[str, Any]
    ) -> bool:
        """Send daily digest email"""
        email_addresses = config.get("emails", [])
        
        if not email_addresses:
            return False
        
        # Group insights by severity
        critical = [i for i in insights if i.severity == InsightSeverity.CRITICAL]
        high = [i for i in insights if i.severity == InsightSeverity.HIGH]
        medium = [i for i in insights if i.severity == InsightSeverity.MEDIUM]
        low = [i for i in insights if i.severity == InsightSeverity.LOW]
        info = [i for i in insights if i.severity == InsightSeverity.INFO]
        
        # Format digest
        subject = f"Daily Business Insights - {len(insights)} New Insights"
        body = self._format_digest_body(critical, high, medium, low, info)
        
        # TODO: Send via email service
        print(f"📧 DAILY DIGEST EMAIL")
        print(f"To: {', '.join(email_addresses)}")
        print(f"Subject: {subject}")
        print(f"Body:\n{body}")
        print(f"=" * 60)
        
        return True  # Simulated success
    
    # Formatting helpers
    
    def _format_email_subject(self, insight: Insight) -> str:
        """Format email subject line"""
        severity_emoji = {
            InsightSeverity.CRITICAL: "🚨",
            InsightSeverity.HIGH: "⚠️",
            InsightSeverity.MEDIUM: "📊",
            InsightSeverity.LOW: "💡",
            InsightSeverity.INFO: "ℹ️"
        }
        
        emoji = severity_emoji.get(insight.severity, "📊")
        return f"{emoji} {insight.title}"
    
    def _format_email_body(self, insight: Insight) -> str:
        """Format email body HTML"""
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px;">
                <h2 style="color: #333; margin-top: 0;">{insight.title}</h2>
                
                <div style="background-color: white; padding: 15px; border-radius: 4px; margin: 15px 0;">
                    <p style="color: #666; line-height: 1.6;">{insight.description}</p>
                </div>
                
                {f'''
                <div style="background-color: #e7f3ff; padding: 15px; border-radius: 4px; border-left: 4px solid #0066cc;">
                    <h3 style="color: #0066cc; margin-top: 0; font-size: 16px;">Recommendation</h3>
                    <p style="color: #333; line-height: 1.6; margin-bottom: 0;">{insight.recommendation}</p>
                </div>
                ''' if insight.recommendation else ''}
                
                <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #dee2e6;">
                    <p style="color: #999; font-size: 12px; margin: 0;">
                        Generated: {insight.generated_at.strftime("%B %d, %Y at %I:%M %p") if insight.generated_at else "N/A"}
                    </p>
                </div>
            </div>
            
            <div style="text-align: center; margin-top: 20px;">
                <a href="{self._get_dashboard_url()}" 
                   style="background-color: #0066cc; color: white; padding: 12px 24px; 
                          text-decoration: none; border-radius: 4px; display: inline-block;">
                    View in Dashboard
                </a>
            </div>
        </body>
        </html>
        """
        return html
    
    def _format_digest_body(
        self,
        critical: List[Insight],
        high: List[Insight],
        medium: List[Insight],
        low: List[Insight],
        info: List[Insight]
    ) -> str:
        """Format daily digest email body"""
        sections = []
        
        if critical:
            sections.append(self._format_digest_section("🚨 Critical", critical, "#dc3545"))
        if high:
            sections.append(self._format_digest_section("⚠️ High Priority", high, "#fd7e14"))
        if medium:
            sections.append(self._format_digest_section("📊 Medium Priority", medium, "#ffc107"))
        if low:
            sections.append(self._format_digest_section("💡 Low Priority", low, "#28a745"))
        if info:
            sections.append(self._format_digest_section("ℹ️ Informational", info, "#17a2b8"))
        
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 700px; margin: 0 auto;">
            <div style="background-color: #f8f9fa; padding: 30px; border-radius: 8px;">
                <h1 style="color: #333; margin-top: 0;">Daily Business Insights</h1>
                <p style="color: #666;">
                    Here's your daily summary of insights for {datetime.utcnow().strftime("%B %d, %Y")}
                </p>
                
                {chr(10).join(sections)}
                
                <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #dee2e6;">
                    <a href="{self._get_dashboard_url()}" 
                       style="background-color: #0066cc; color: white; padding: 12px 24px; 
                              text-decoration: none; border-radius: 4px; display: inline-block;">
                        View All Insights in Dashboard
                    </a>
                </div>
            </div>
        </body>
        </html>
        """
        return html
    
    def _format_digest_section(
        self,
        title: str,
        insights: List[Insight],
        color: str
    ) -> str:
        """Format a section of the digest"""
        items = ""
        for insight in insights[:5]:  # Max 5 per section
            items += f"""
            <div style="background-color: white; padding: 12px; margin: 8px 0; border-radius: 4px; 
                        border-left: 3px solid {color};">
                <strong style="color: #333;">{insight.title}</strong>
                <p style="color: #666; font-size: 14px; margin: 4px 0 0 0;">
                    {insight.description[:150]}{"..." if len(insight.description) > 150 else ""}
                </p>
            </div>
            """
        
        if len(insights) > 5:
            items += f"""
            <p style="color: #999; font-size: 12px; margin-top: 8px;">
                + {len(insights) - 5} more {title.lower()} insights
            </p>
            """
        
        return f"""
        <div style="margin: 25px 0;">
            <h2 style="color: {color}; font-size: 18px; margin-bottom: 10px;">{title} ({len(insights)})</h2>
            {items}
        </div>
        """
    
    def _get_dashboard_url(self) -> str:
        """Get URL to dashboard (configure based on environment)"""
        # TODO: Make this configurable
        return f"https://app.nailsalon-ai.com/insights?tenant={self.tenant_id}"


# Scheduled job function (to be called by Celery/background worker)
async def generate_and_notify_insights(tenant_id: str, notify_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate insights and send notifications
    
    This function should be called periodically (e.g., hourly or daily)
    by a background job scheduler
    
    Args:
        tenant_id: Tenant to generate insights for
        notify_config: Notification configuration
    
    Returns:
        Results dictionary
    """
    from .insight_engine import InsightEngine
    from ..core.database import get_async_session
    
    # Generate insights
    engine = InsightEngine(tenant_id)
    new_insights = await engine.generate_all_insights()
    
    if not new_insights:
        return {
            "success": True,
            "insights_generated": 0,
            "notifications_sent": 0
        }
    
    # Save to database
    async with get_async_session() as session:
        for insight in new_insights:
            session.add(insight)
        await session.commit()
    
    # Send notifications for high-priority insights
    notification_service = NotificationService(tenant_id)
    notifications_sent = 0
    
    for insight in new_insights:
        # Only notify for medium+ severity
        if insight.severity in [InsightSeverity.CRITICAL, InsightSeverity.HIGH, InsightSeverity.MEDIUM]:
            channels = notify_config.get("channels", [NotificationChannel.EMAIL])
            await notification_service.send_insight_notification(
                insight,
                channels,
                notify_config
            )
            notifications_sent += 1
    
    return {
        "success": True,
        "insights_generated": len(new_insights),
        "notifications_sent": notifications_sent
    }

