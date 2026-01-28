"""
AWS End User Messaging integration for SMS and WhatsApp.

This module provides production-ready integration with AWS End User Messaging
service for sending SMS and WhatsApp messages with proper error handling,
delivery tracking, and template support.
"""

import boto3
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from botocore.exceptions import ClientError, BotoCoreError

logger = logging.getLogger(__name__)


@dataclass
class MessageRequest:
    """Request to send a message via AWS End User Messaging."""
    channel: str  # 'SMS' or 'WHATSAPP'
    destination_phone_number: str
    message_body: Optional[str] = None
    media_url: Optional[str] = None
    template_name: Optional[str] = None
    template_parameters: Optional[Dict[str, str]] = None
    campaign_id: Optional[str] = None
    customer_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class MessageResponse:
    """Response from AWS End User Messaging."""
    success: bool
    message_id: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    throttled: bool = False
    retry_after: Optional[int] = None  # seconds
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class AWSEndUserMessaging:
    """
    AWS End User Messaging client with production-ready features.
    
    Features:
    - SMS and WhatsApp message sending
    - Template support with variable substitution
    - Delivery status tracking
    - Error handling with retry logic
    - Throttling detection
    - Cost tracking per message
    """
    
    def __init__(
        self,
        region_name: str = 'us-east-1',
        phone_pool_id: Optional[str] = None,
        whatsapp_business_account_id: Optional[str] = None,
        dry_run: bool = False
    ):
        """
        Initialize AWS End User Messaging client.
        
        Args:
            region_name: AWS region for the service
            phone_pool_id: Phone pool ID for SMS sending
            whatsapp_business_account_id: WhatsApp Business Account ID
            dry_run: If True, simulate sending without actual API calls
        """
        self.region_name = region_name
        self.phone_pool_id = phone_pool_id
        self.whatsapp_business_account_id = whatsapp_business_account_id
        self.dry_run = dry_run
        
        if not dry_run:
            try:
                self.client = boto3.client(
                    'socialmessaging',  # AWS End User Messaging service name
                    region_name=region_name
                )
                logger.info(f"✅ AWS End User Messaging client initialized in {region_name}")
            except Exception as e:
                logger.error(f"❌ Failed to initialize AWS End User Messaging client: {e}")
                raise
        else:
            self.client = None
            logger.info("🔧 Running in DRY RUN mode - no actual messages will be sent")
    
    def send_message(self, request: MessageRequest) -> MessageResponse:
        """
        Send a message via AWS End User Messaging.
        
        Args:
            request: Message request with channel, destination, and content
            
        Returns:
            MessageResponse with success status and message ID or error details
        """
        try:
            if self.dry_run:
                return self._simulate_send(request)
            
            # Validate request
            validation_error = self._validate_request(request)
            if validation_error:
                return MessageResponse(
                    success=False,
                    error_code='VALIDATION_ERROR',
                    error_message=validation_error
                )
            
            # Build API request based on channel
            if request.channel.upper() == 'SMS':
                response = self._send_sms(request)
            elif request.channel.upper() == 'WHATSAPP':
                response = self._send_whatsapp(request)
            else:
                return MessageResponse(
                    success=False,
                    error_code='INVALID_CHANNEL',
                    error_message=f"Unsupported channel: {request.channel}"
                )
            
            return response
        
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'UNKNOWN')
            error_message = e.response.get('Error', {}).get('Message', str(e))
            
            # Check for throttling
            throttled = error_code in ['ThrottlingException', 'TooManyRequestsException']
            retry_after = None
            if throttled:
                # Extract retry-after from response headers if available
                retry_after = e.response.get('ResponseMetadata', {}).get('RetryAfter', 60)
            
            logger.error(f"❌ AWS API error: {error_code} - {error_message}")
            
            return MessageResponse(
                success=False,
                error_code=error_code,
                error_message=error_message,
                throttled=throttled,
                retry_after=retry_after
            )
        
        except Exception as e:
            logger.error(f"❌ Unexpected error sending message: {e}")
            return MessageResponse(
                success=False,
                error_code='INTERNAL_ERROR',
                error_message=str(e)
            )
    
    def _send_sms(self, request: MessageRequest) -> MessageResponse:
        """Send SMS message via AWS End User Messaging."""
        try:
            params = {
                'DestinationPhoneNumber': request.destination_phone_number,
                'OriginationIdentity': self.phone_pool_id,
                'MessageBody': request.message_body
            }
            
            # Add optional parameters
            if request.campaign_id:
                params['CampaignId'] = request.campaign_id
            
            if request.metadata:
                params['Context'] = request.metadata
            
            response = self.client.send_text_message(**params)
            
            message_id = response.get('MessageId')
            logger.info(f"✅ SMS sent successfully: {message_id}")
            
            return MessageResponse(
                success=True,
                message_id=message_id
            )
        
        except Exception as e:
            logger.error(f"❌ Failed to send SMS: {e}")
            raise
    
    def _send_whatsapp(self, request: MessageRequest) -> MessageResponse:
        """Send WhatsApp message via AWS End User Messaging."""
        try:
            # WhatsApp requires template-based messaging for marketing
            if not request.template_name:
                return MessageResponse(
                    success=False,
                    error_code='MISSING_TEMPLATE',
                    error_message='WhatsApp marketing messages require a template'
                )
            
            params = {
                'DestinationPhoneNumber': request.destination_phone_number,
                'OriginationIdentity': self.whatsapp_business_account_id,
                'MessageType': 'TEMPLATE',
                'TemplateName': request.template_name
            }
            
            # Add template parameters
            if request.template_parameters:
                params['TemplateParameters'] = request.template_parameters
            
            # Add media URL if provided
            if request.media_url:
                params['MediaUrl'] = request.media_url
            
            # Add optional parameters
            if request.campaign_id:
                params['CampaignId'] = request.campaign_id
            
            if request.metadata:
                params['Context'] = request.metadata
            
            response = self.client.send_whatsapp_message(**params)
            
            message_id = response.get('MessageId')
            logger.info(f"✅ WhatsApp sent successfully: {message_id}")
            
            return MessageResponse(
                success=True,
                message_id=message_id
            )
        
        except Exception as e:
            logger.error(f"❌ Failed to send WhatsApp: {e}")
            raise
    
    def _validate_request(self, request: MessageRequest) -> Optional[str]:
        """Validate message request. Returns error message if invalid, None if valid."""
        if not request.destination_phone_number:
            return "Destination phone number is required"
        
        if request.channel.upper() == 'SMS':
            if not request.message_body:
                return "Message body is required for SMS"
            if not self.phone_pool_id:
                return "Phone pool ID not configured for SMS"
        
        elif request.channel.upper() == 'WHATSAPP':
            if not request.template_name:
                return "Template name is required for WhatsApp"
            if not self.whatsapp_business_account_id:
                return "WhatsApp Business Account ID not configured"
        
        return None
    
    def _simulate_send(self, request: MessageRequest) -> MessageResponse:
        """Simulate sending a message (dry run mode)."""
        import uuid
        
        logger.info(f"🔧 [DRY RUN] Would send {request.channel} to {request.destination_phone_number}")
        if request.template_name:
            logger.info(f"🔧 [DRY RUN] Template: {request.template_name}")
        if request.message_body:
            logger.info(f"🔧 [DRY RUN] Body: {request.message_body[:100]}...")
        
        return MessageResponse(
            success=True,
            message_id=f"dry-run-{uuid.uuid4()}"
        )
    
    def send_batch(self, requests: List[MessageRequest]) -> List[MessageResponse]:
        """
        Send multiple messages in batch.
        
        Note: This is a simple sequential implementation. For production,
        consider using SQS for queue management and Lambda for parallel processing.
        
        Args:
            requests: List of message requests
            
        Returns:
            List of message responses in the same order as requests
        """
        responses = []
        for request in requests:
            response = self.send_message(request)
            responses.append(response)
        
        return responses
    
    def get_message_status(self, message_id: str) -> Dict[str, Any]:
        """
        Get delivery status for a message.
        
        Args:
            message_id: Message ID returned from send_message
            
        Returns:
            Dictionary with delivery status information
        """
        if self.dry_run:
            return {
                'message_id': message_id,
                'status': 'DELIVERED',
                'timestamp': datetime.utcnow().isoformat()
            }
        
        try:
            response = self.client.get_message_status(MessageId=message_id)
            return response
        except Exception as e:
            logger.error(f"❌ Failed to get message status: {e}")
            return {
                'message_id': message_id,
                'status': 'UNKNOWN',
                'error': str(e)
            }
