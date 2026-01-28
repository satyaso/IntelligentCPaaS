"""
Intelligent rate limiting and throughput management for AWS End User Messaging.

This module implements token bucket algorithm with DynamoDB backend for
distributed rate limiting across multiple Lambda functions or containers.
"""

import time
import logging
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class Channel(Enum):
    """Communication channels with different rate limits."""
    SMS = "sms"
    WHATSAPP = "whatsapp"
    EMAIL = "email"


@dataclass
class RateLimitConfig:
    """Rate limit configuration for a channel."""
    channel: Channel
    max_requests_per_second: int
    burst_capacity: int  # Maximum burst size
    region: str = "us-east-1"
    
    @classmethod
    def get_default_config(cls, channel: Channel, region: str = "us-east-1") -> 'RateLimitConfig':
        """Get default rate limit configuration for a channel."""
        # Default configurations based on AWS End User Messaging limits
        configs = {
            Channel.SMS: {
                'us-east-1': RateLimitConfig(Channel.SMS, 20, 100, 'us-east-1'),
                'us-west-2': RateLimitConfig(Channel.SMS, 20, 100, 'us-west-2'),
                'eu-west-1': RateLimitConfig(Channel.SMS, 10, 50, 'eu-west-1'),
                'ap-southeast-1': RateLimitConfig(Channel.SMS, 10, 50, 'ap-southeast-1'),
            },
            Channel.WHATSAPP: {
                # WhatsApp Business API standard limits
                'default': RateLimitConfig(Channel.WHATSAPP, 80, 1000, region)
            },
            Channel.EMAIL: {
                # Amazon SES limits (varies by account)
                'default': RateLimitConfig(Channel.EMAIL, 14, 100, region)
            }
        }
        
        # Get region-specific config or default
        channel_configs = configs.get(channel, {})
        return channel_configs.get(region, channel_configs.get('default'))


class RateLimiter:
    """
    Token bucket rate limiter with in-memory storage.
    
    For production, use DynamoDBRateLimiter for distributed rate limiting.
    """
    
    def __init__(self, config: RateLimitConfig):
        """
        Initialize rate limiter.
        
        Args:
            config: Rate limit configuration
        """
        self.config = config
        self.tokens = float(config.burst_capacity)
        self.last_refill = time.time()
        self.max_tokens = float(config.burst_capacity)
        self.refill_rate = float(config.max_requests_per_second)
        
        logger.info(
            f"✅ Rate limiter initialized for {config.channel.value}: "
            f"{config.max_requests_per_second} req/s, burst: {config.burst_capacity}"
        )
    
    def acquire(self, tokens: int = 1) -> Tuple[bool, Optional[float]]:
        """
        Try to acquire tokens for sending messages.
        
        Args:
            tokens: Number of tokens to acquire (usually 1 per message)
            
        Returns:
            Tuple of (success, retry_after_seconds)
            - success: True if tokens acquired, False if rate limited
            - retry_after_seconds: If rate limited, how long to wait before retry
        """
        # Refill tokens based on time elapsed
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(
            self.max_tokens,
            self.tokens + (elapsed * self.refill_rate)
        )
        self.last_refill = now
        
        # Check if we have enough tokens
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True, None
        else:
            # Calculate how long to wait for tokens to refill
            tokens_needed = tokens - self.tokens
            retry_after = tokens_needed / self.refill_rate
            logger.warning(
                f"⚠️  Rate limit reached for {self.config.channel.value}. "
                f"Retry after {retry_after:.2f}s"
            )
            return False, retry_after
    
    def get_available_tokens(self) -> int:
        """Get current number of available tokens."""
        # Refill tokens first
        now = time.time()
        elapsed = now - self.last_refill
        current_tokens = min(
            self.max_tokens,
            self.tokens + (elapsed * self.refill_rate)
        )
        return int(current_tokens)


class DynamoDBRateLimiter:
    """
    Distributed rate limiter using DynamoDB for state storage.
    
    This allows multiple Lambda functions or containers to share
    the same rate limit state.
    """
    
    def __init__(
        self,
        config: RateLimitConfig,
        table_name: str = 'ai-cpaas-rate-limits',
        dry_run: bool = False
    ):
        """
        Initialize DynamoDB-backed rate limiter.
        
        Args:
            config: Rate limit configuration
            table_name: DynamoDB table name for storing rate limit state
            dry_run: If True, simulate without actual DynamoDB calls
        """
        self.config = config
        self.table_name = table_name
        self.dry_run = dry_run
        self.key = f"{config.channel.value}#{config.region}"
        
        if not dry_run:
            import boto3
            self.dynamodb = boto3.resource('dynamodb', region_name=config.region)
            self.table = self.dynamodb.Table(table_name)
            logger.info(f"✅ DynamoDB rate limiter initialized: {table_name}")
        else:
            # Fallback to in-memory for dry run
            self.fallback_limiter = RateLimiter(config)
            logger.info("🔧 Using in-memory rate limiter (dry run mode)")
    
    def acquire(self, tokens: int = 1) -> Tuple[bool, Optional[float]]:
        """
        Try to acquire tokens using DynamoDB atomic operations.
        
        Args:
            tokens: Number of tokens to acquire
            
        Returns:
            Tuple of (success, retry_after_seconds)
        """
        if self.dry_run:
            return self.fallback_limiter.acquire(tokens)
        
        try:
            now = time.time()
            
            # Use DynamoDB conditional update for atomic token acquisition
            response = self.table.update_item(
                Key={'limiter_key': self.key},
                UpdateExpression="""
                    SET 
                        tokens = if_not_exists(tokens, :max_tokens) + 
                                 (:now - if_not_exists(last_refill, :now)) * :refill_rate,
                        tokens = if_not_exists(tokens, :max_tokens) - :tokens_needed,
                        last_refill = :now
                """,
                ConditionExpression='tokens >= :tokens_needed OR attribute_not_exists(tokens)',
                ExpressionAttributeValues={
                    ':tokens_needed': tokens,
                    ':max_tokens': self.config.burst_capacity,
                    ':refill_rate': self.config.max_requests_per_second,
                    ':now': now
                },
                ReturnValues='ALL_NEW'
            )
            
            return True, None
        
        except self.dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
            # Not enough tokens available
            tokens_needed = tokens
            retry_after = tokens_needed / self.config.max_requests_per_second
            logger.warning(
                f"⚠️  Rate limit reached for {self.config.channel.value}. "
                f"Retry after {retry_after:.2f}s"
            )
            return False, retry_after
        
        except Exception as e:
            logger.error(f"❌ DynamoDB rate limiter error: {e}")
            # Fail open - allow the request but log the error
            return True, None


class ThroughputManager:
    """
    High-level throughput manager that coordinates rate limiting across channels.
    
    Features:
    - Per-channel rate limiting
    - Burst capacity management
    - Automatic backoff and retry
    - Throughput monitoring and metrics
    """
    
    def __init__(
        self,
        use_dynamodb: bool = False,
        dynamodb_table: str = 'ai-cpaas-rate-limits',
        dry_run: bool = False
    ):
        """
        Initialize throughput manager.
        
        Args:
            use_dynamodb: If True, use DynamoDB for distributed rate limiting
            dynamodb_table: DynamoDB table name
            dry_run: If True, simulate without actual AWS calls
        """
        self.use_dynamodb = use_dynamodb
        self.dynamodb_table = dynamodb_table
        self.dry_run = dry_run
        self.limiters: Dict[str, RateLimiter] = {}
        
        logger.info(
            f"✅ Throughput manager initialized "
            f"(DynamoDB: {use_dynamodb}, Dry run: {dry_run})"
        )
    
    def get_limiter(self, channel: Channel, region: str = 'us-east-1') -> RateLimiter:
        """Get or create rate limiter for a channel."""
        key = f"{channel.value}#{region}"
        
        if key not in self.limiters:
            config = RateLimitConfig.get_default_config(channel, region)
            
            if self.use_dynamodb:
                limiter = DynamoDBRateLimiter(config, self.dynamodb_table, self.dry_run)
            else:
                limiter = RateLimiter(config)
            
            self.limiters[key] = limiter
        
        return self.limiters[key]
    
    def can_send(
        self,
        channel: Channel,
        count: int = 1,
        region: str = 'us-east-1'
    ) -> Tuple[bool, Optional[float]]:
        """
        Check if messages can be sent without exceeding rate limits.
        
        Args:
            channel: Communication channel
            count: Number of messages to send
            region: AWS region
            
        Returns:
            Tuple of (can_send, retry_after_seconds)
        """
        limiter = self.get_limiter(channel, region)
        return limiter.acquire(count)
    
    def get_throughput_stats(self, channel: Channel, region: str = 'us-east-1') -> Dict:
        """Get current throughput statistics for a channel."""
        limiter = self.get_limiter(channel, region)
        available = limiter.get_available_tokens()
        config = limiter.config
        
        return {
            'channel': channel.value,
            'region': region,
            'available_capacity': available,
            'max_capacity': config.burst_capacity,
            'rate_per_second': config.max_requests_per_second,
            'utilization_percent': ((config.burst_capacity - available) / config.burst_capacity) * 100
        }
    
    def wait_for_capacity(
        self,
        channel: Channel,
        count: int = 1,
        region: str = 'us-east-1',
        max_wait: float = 60.0
    ) -> bool:
        """
        Wait for rate limit capacity to become available.
        
        Args:
            channel: Communication channel
            count: Number of messages to send
            region: AWS region
            max_wait: Maximum time to wait in seconds
            
        Returns:
            True if capacity acquired, False if timeout
        """
        start_time = time.time()
        
        while True:
            can_send, retry_after = self.can_send(channel, count, region)
            
            if can_send:
                return True
            
            # Check if we've exceeded max wait time
            elapsed = time.time() - start_time
            if elapsed >= max_wait:
                logger.warning(
                    f"⚠️  Timeout waiting for capacity: {channel.value} "
                    f"(waited {elapsed:.2f}s)"
                )
                return False
            
            # Wait for the suggested retry time (or max remaining time)
            wait_time = min(retry_after or 1.0, max_wait - elapsed)
            logger.info(f"⏳ Waiting {wait_time:.2f}s for capacity...")
            time.sleep(wait_time)
