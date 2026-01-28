"""
AWS SES (Simple Email Service) integration for email messaging.

Separate from AWS End User Messaging - uses SES API for email delivery.
"""

import logging
import boto3
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class AWSSESClient:
    """
    AWS SES client for sending emails.
    
    Features:
    - HTML and plain text email support
    - Template-based emails
    - Delivery tracking integration
    - Rate limiting support
    """
    
    def __init__(
        self,
        region: str = 'us-east-1',
        sender_email: str = 'noreply@example.com',
        dry_run: bool = False
    ):
        """
        Initialize AWS SES client.
        
        Args:
            region: AWS region
            sender_email: Verified sender email address
            dry_run: If True, simulate without actual sends
        """
        self.region = region
        self.sender_email = sender_email
        self.dry_run = dry_run
        
        if not dry_run:
            self.client = boto3.client('ses', region_name=region)
            logger.info(f"✅ AWS SES client initialized: {region}")
        else:
            self.client = None
            logger.info("🔧 AWS SES client in dry-run mode")
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        body_text: str,
        body_html: Optional[str] = None,
        customer_id: Optional[str] = None
    ) -> Dict:
        """
        Send an email via AWS SES.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body_text: Plain text email body
            body_html: Optional HTML email body
            customer_id: Optional customer ID for tracking
            
        Returns:
            Dict with message_id and status
        """
        if self.dry_run:
            message_id = f"dry-run-email-{datetime.utcnow().timestamp()}"
            logger.info(
                f"🔧 DRY RUN: Would send email to {to_email}\n"
                f"   Subject: {subject}\n"
                f"   Body: {body_text[:100]}..."
            )
            return {
                'message_id': message_id,
                'status': 'dry_run',
                'customer_id': customer_id
            }
        
        try:
            # Prepare email body
            body = {'Text': {'Data': body_text, 'Charset': 'UTF-8'}}
            if body_html:
                body['Html'] = {'Data': body_html, 'Charset': 'UTF-8'}
            
            # Send email
            response = self.client.send_email(
                Source=self.sender_email,
                Destination={'ToAddresses': [to_email]},
                Message={
                    'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                    'Body': body
                }
            )
            
            message_id = response['MessageId']
            logger.info(f"✅ Email sent to {to_email}: {message_id}")
            
            return {
                'message_id': message_id,
                'status': 'sent',
                'customer_id': customer_id,
                'channel': 'email'
            }
        
        except Exception as e:
            logger.error(f"❌ Failed to send email to {to_email}: {e}")
            return {
                'message_id': None,
                'status': 'failed',
                'error': str(e),
                'customer_id': customer_id,
                'channel': 'email'
            }
    
    def send_templated_email(
        self,
        to_email: str,
        template_name: str,
        template_data: Dict,
        customer_id: Optional[str] = None
    ) -> Dict:
        """
        Send an email using an SES template.
        
        Args:
            to_email: Recipient email address
            template_name: SES template name
            template_data: Template variables
            customer_id: Optional customer ID for tracking
            
        Returns:
            Dict with message_id and status
        """
        if self.dry_run:
            message_id = f"dry-run-template-{datetime.utcnow().timestamp()}"
            logger.info(
                f"🔧 DRY RUN: Would send templated email to {to_email}\n"
                f"   Template: {template_name}\n"
                f"   Data: {template_data}"
            )
            return {
                'message_id': message_id,
                'status': 'dry_run',
                'customer_id': customer_id
            }
        
        try:
            response = self.client.send_templated_email(
                Source=self.sender_email,
                Destination={'ToAddresses': [to_email]},
                Template=template_name,
                TemplateData=str(template_data)
            )
            
            message_id = response['MessageId']
            logger.info(f"✅ Templated email sent to {to_email}: {message_id}")
            
            return {
                'message_id': message_id,
                'status': 'sent',
                'customer_id': customer_id,
                'channel': 'email',
                'template': template_name
            }
        
        except Exception as e:
            logger.error(f"❌ Failed to send templated email to {to_email}: {e}")
            return {
                'message_id': None,
                'status': 'failed',
                'error': str(e),
                'customer_id': customer_id,
                'channel': 'email'
            }
    
    def verify_email_address(self, email: str) -> bool:
        """
        Verify an email address for sending (required in SES sandbox).
        
        Args:
            email: Email address to verify
            
        Returns:
            True if verification initiated successfully
        """
        if self.dry_run:
            logger.info(f"🔧 DRY RUN: Would verify email {email}")
            return True
        
        try:
            self.client.verify_email_identity(EmailAddress=email)
            logger.info(f"✅ Verification email sent to {email}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to verify email {email}: {e}")
            return False
    
    def get_send_quota(self) -> Dict:
        """
        Get current SES sending quota and statistics.
        
        Returns:
            Dict with quota information
        """
        if self.dry_run:
            return {
                'max_24_hour_send': 200,
                'max_send_rate': 1.0,
                'sent_last_24_hours': 0
            }
        
        try:
            response = self.client.get_send_quota()
            return {
                'max_24_hour_send': response['Max24HourSend'],
                'max_send_rate': response['MaxSendRate'],
                'sent_last_24_hours': response['SentLast24Hours']
            }
        except Exception as e:
            logger.error(f"❌ Failed to get send quota: {e}")
            return {}
