"""
Delivery tracking and analytics for AWS End User Messaging.

This module tracks message delivery status, handles callbacks from AWS,
and provides analytics for throughput optimization.
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict

logger = logging.getLogger(__name__)


class DeliveryStatus(Enum):
    """Message delivery status."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    BOUNCED = "bounced"
    COMPLAINED = "complained"
    UNSUBSCRIBED = "unsubscribed"


@dataclass
class DeliveryRecord:
    """Record of a message delivery attempt."""
    message_id: str
    customer_id: str
    channel: str
    destination: str
    status: DeliveryStatus
    sent_at: datetime
    delivered_at: Optional[datetime] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    attempts: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChannelStats:
    """Statistics for a communication channel."""
    channel: str
    total_sent: int = 0
    total_delivered: int = 0
    total_failed: int = 0
    total_bounced: int = 0
    total_complained: int = 0
    delivery_rate: float = 0.0
    average_delivery_time: float = 0.0  # seconds
    
    def calculate_rates(self):
        """Calculate delivery and failure rates."""
        if self.total_sent > 0:
            self.delivery_rate = (self.total_delivered / self.total_sent) * 100


class DeliveryTracker:
    """
    Track message delivery status and provide analytics.
    
    Features:
    - Delivery status tracking per message
    - Channel-level analytics
    - Customer-level delivery history
    - Automatic channel fallback on failures
    - Bounce and complaint handling
    """
    
    def __init__(self, use_dynamodb: bool = False, table_name: str = 'ai-cpaas-delivery', dry_run: bool = False):
        """
        Initialize delivery tracker.
        
        Args:
            use_dynamodb: If True, use DynamoDB for persistent storage
            table_name: DynamoDB table name
            dry_run: If True, simulate without actual AWS calls
        """
        self.use_dynamodb = use_dynamodb
        self.table_name = table_name
        self.dry_run = dry_run
        
        # In-memory storage (for demo or as cache)
        self.deliveries: Dict[str, DeliveryRecord] = {}
        self.customer_history: Dict[str, List[str]] = defaultdict(list)
        self.channel_stats: Dict[str, ChannelStats] = {}
        
        if use_dynamodb and not dry_run:
            import boto3
            self.dynamodb = boto3.resource('dynamodb')
            self.table = self.dynamodb.Table(table_name)
            logger.info(f"✅ Delivery tracker initialized with DynamoDB: {table_name}")
        else:
            self.dynamodb = None
            logger.info("✅ Delivery tracker initialized (in-memory mode)")
    
    def record_sent(
        self,
        message_id: str,
        customer_id: str,
        channel: str,
        destination: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> DeliveryRecord:
        """
        Record that a message was sent.
        
        Args:
            message_id: Unique message identifier
            customer_id: Customer identifier
            channel: Communication channel (SMS, WhatsApp, Email)
            destination: Destination address (phone number or email)
            metadata: Additional metadata
            
        Returns:
            DeliveryRecord for the sent message
        """
        record = DeliveryRecord(
            message_id=message_id,
            customer_id=customer_id,
            channel=channel,
            destination=destination,
            status=DeliveryStatus.SENT,
            sent_at=datetime.utcnow(),
            metadata=metadata or {}
        )
        
        # Store in memory
        self.deliveries[message_id] = record
        self.customer_history[customer_id].append(message_id)
        
        # Update channel stats
        self._update_channel_stats(channel, 'sent')
        
        # Store in DynamoDB if enabled
        if self.use_dynamodb and not self.dry_run:
            self._store_in_dynamodb(record)
        
        logger.info(f"📤 Recorded sent message: {message_id} ({channel} to {destination})")
        return record
    
    def update_status(
        self,
        message_id: str,
        status: DeliveryStatus,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> Optional[DeliveryRecord]:
        """
        Update delivery status for a message.
        
        Args:
            message_id: Message identifier
            status: New delivery status
            error_code: Error code if failed
            error_message: Error message if failed
            
        Returns:
            Updated DeliveryRecord or None if not found
        """
        record = self.deliveries.get(message_id)
        if not record:
            logger.warning(f"⚠️  Message not found: {message_id}")
            return None
        
        # Update status
        old_status = record.status
        record.status = status
        
        if status == DeliveryStatus.DELIVERED:
            record.delivered_at = datetime.utcnow()
            self._update_channel_stats(record.channel, 'delivered')
        elif status == DeliveryStatus.FAILED:
            record.error_code = error_code
            record.error_message = error_message
            self._update_channel_stats(record.channel, 'failed')
        elif status == DeliveryStatus.BOUNCED:
            record.error_code = error_code
            record.error_message = error_message
            self._update_channel_stats(record.channel, 'bounced')
        elif status == DeliveryStatus.COMPLAINED:
            self._update_channel_stats(record.channel, 'complained')
        
        # Update in DynamoDB if enabled
        if self.use_dynamodb and not self.dry_run:
            self._update_in_dynamodb(record)
        
        logger.info(f"📊 Updated status: {message_id} ({old_status.value} → {status.value})")
        return record
    
    def get_delivery_record(self, message_id: str) -> Optional[DeliveryRecord]:
        """Get delivery record for a message."""
        return self.deliveries.get(message_id)
    
    def get_customer_history(
        self,
        customer_id: str,
        limit: int = 10
    ) -> List[DeliveryRecord]:
        """
        Get delivery history for a customer.
        
        Args:
            customer_id: Customer identifier
            limit: Maximum number of records to return
            
        Returns:
            List of delivery records, most recent first
        """
        message_ids = self.customer_history.get(customer_id, [])
        records = [self.deliveries[mid] for mid in message_ids if mid in self.deliveries]
        
        # Sort by sent_at descending
        records.sort(key=lambda r: r.sent_at, reverse=True)
        
        return records[:limit]
    
    def get_channel_stats(self, channel: str) -> ChannelStats:
        """Get statistics for a channel."""
        if channel not in self.channel_stats:
            self.channel_stats[channel] = ChannelStats(channel=channel)
        
        stats = self.channel_stats[channel]
        stats.calculate_rates()
        return stats
    
    def get_all_stats(self) -> Dict[str, ChannelStats]:
        """Get statistics for all channels."""
        for stats in self.channel_stats.values():
            stats.calculate_rates()
        return self.channel_stats
    
    def should_fallback(self, customer_id: str, channel: str) -> bool:
        """
        Determine if we should fallback to another channel for a customer.
        
        Args:
            customer_id: Customer identifier
            channel: Current channel
            
        Returns:
            True if should fallback to another channel
        """
        # Get recent delivery history for this customer and channel
        history = self.get_customer_history(customer_id, limit=5)
        channel_history = [r for r in history if r.channel == channel]
        
        if len(channel_history) < 2:
            return False
        
        # Check if last 2 attempts failed
        recent_failures = sum(
            1 for r in channel_history[:2]
            if r.status in [DeliveryStatus.FAILED, DeliveryStatus.BOUNCED]
        )
        
        if recent_failures >= 2:
            logger.warning(
                f"⚠️  Channel fallback recommended for {customer_id}: "
                f"{channel} has {recent_failures} recent failures"
            )
            return True
        
        return False
    
    def get_best_channel(self, customer_id: str, available_channels: List[str]) -> str:
        """
        Get the best channel for a customer based on delivery history.
        
        Args:
            customer_id: Customer identifier
            available_channels: List of available channels
            
        Returns:
            Best channel name
        """
        history = self.get_customer_history(customer_id, limit=20)
        
        # Calculate success rate per channel
        channel_success: Dict[str, tuple] = {}
        for channel in available_channels:
            channel_records = [r for r in history if r.channel == channel]
            if not channel_records:
                # No history, use global stats
                stats = self.get_channel_stats(channel)
                channel_success[channel] = (stats.delivery_rate, 0)
            else:
                delivered = sum(1 for r in channel_records if r.status == DeliveryStatus.DELIVERED)
                total = len(channel_records)
                success_rate = (delivered / total) * 100 if total > 0 else 0
                channel_success[channel] = (success_rate, total)
        
        # Select channel with highest success rate (prefer channels with more history)
        best_channel = max(
            available_channels,
            key=lambda c: (channel_success[c][0], channel_success[c][1])
        )
        
        logger.info(
            f"📊 Best channel for {customer_id}: {best_channel} "
            f"({channel_success[best_channel][0]:.1f}% success)"
        )
        
        return best_channel
    
    def _update_channel_stats(self, channel: str, event: str):
        """Update channel statistics for an event."""
        if channel not in self.channel_stats:
            self.channel_stats[channel] = ChannelStats(channel=channel)
        
        stats = self.channel_stats[channel]
        
        if event == 'sent':
            stats.total_sent += 1
        elif event == 'delivered':
            stats.total_delivered += 1
        elif event == 'failed':
            stats.total_failed += 1
        elif event == 'bounced':
            stats.total_bounced += 1
        elif event == 'complained':
            stats.total_complained += 1
    
    def _store_in_dynamodb(self, record: DeliveryRecord):
        """Store delivery record in DynamoDB."""
        try:
            self.table.put_item(
                Item={
                    'message_id': record.message_id,
                    'customer_id': record.customer_id,
                    'channel': record.channel,
                    'destination': record.destination,
                    'status': record.status.value,
                    'sent_at': record.sent_at.isoformat(),
                    'delivered_at': record.delivered_at.isoformat() if record.delivered_at else None,
                    'error_code': record.error_code,
                    'error_message': record.error_message,
                    'attempts': record.attempts,
                    'metadata': record.metadata
                }
            )
        except Exception as e:
            logger.error(f"❌ Failed to store in DynamoDB: {e}")
    
    def _update_in_dynamodb(self, record: DeliveryRecord):
        """Update delivery record in DynamoDB."""
        try:
            self.table.update_item(
                Key={'message_id': record.message_id},
                UpdateExpression="""
                    SET #status = :status,
                        delivered_at = :delivered_at,
                        error_code = :error_code,
                        error_message = :error_message,
                        attempts = :attempts
                """,
                ExpressionAttributeNames={
                    '#status': 'status'
                },
                ExpressionAttributeValues={
                    ':status': record.status.value,
                    ':delivered_at': record.delivered_at.isoformat() if record.delivered_at else None,
                    ':error_code': record.error_code,
                    ':error_message': record.error_message,
                    ':attempts': record.attempts
                }
            )
        except Exception as e:
            logger.error(f"❌ Failed to update in DynamoDB: {e}")
