"""AWS Native implementation of anti-fatigue protection with DynamoDB and CloudWatch."""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from ai_cpaas_demo.core.interfaces import FatigueCheckRequest, FatigueProtectionResult
from ai_cpaas_demo.core.models import (
    ChannelType,
    CommunicationFrequency,
    DisengagementSignal,
    FatigueLevel,
)

from .base import BaseFatigueProtection

logger = logging.getLogger(__name__)


class AWSNativeFatigueProtection(BaseFatigueProtection):
    """AWS Native implementation using DynamoDB for frequency tracking.
    
    Features:
    - DynamoDB for persistent frequency tracking with TTL
    - CloudWatch for fatigue metrics and alerting
    - Automatic cleanup of old records via TTL
    - Real-time disengagement signal detection
    """

    def __init__(
        self,
        dynamodb_client: Optional[Any] = None,
        cloudwatch_client: Optional[Any] = None,
        frequency_table_name: Optional[str] = None,
        signals_table_name: Optional[str] = None,
    ):
        """Initialize AWS Native fatigue protection engine.
        
        Args:
            dynamodb_client: Boto3 DynamoDB client (optional, will create if None)
            cloudwatch_client: Boto3 CloudWatch client (optional, will create if None)
            frequency_table_name: DynamoDB table for frequency tracking
            signals_table_name: DynamoDB table for disengagement signals
        """
        super().__init__()
        
        self.use_aws = os.getenv("USE_AWS_SERVICES", "false").lower() == "true"
        
        if self.use_aws:
            try:
                import boto3
                
                self.dynamodb = dynamodb_client or boto3.client("dynamodb")
                self.cloudwatch = cloudwatch_client or boto3.client("cloudwatch")
                
                self.frequency_table = frequency_table_name or os.getenv(
                    "FATIGUE_FREQUENCY_TABLE", "ai-cpaas-frequency-tracking"
                )
                self.signals_table = signals_table_name or os.getenv(
                    "FATIGUE_SIGNALS_TABLE", "ai-cpaas-disengagement-signals"
                )
                
                logger.info(
                    f"Initialized AWSNativeFatigueProtection with DynamoDB tables: "
                    f"{self.frequency_table}, {self.signals_table}"
                )
            except Exception as e:
                logger.warning(
                    f"Failed to initialize AWS services: {e}. Falling back to base implementation."
                )
                self.use_aws = False
        else:
            logger.info("AWS services disabled, using base implementation")

    async def check_fatigue(
        self, request: FatigueCheckRequest
    ) -> FatigueProtectionResult:
        """Check if sending a message would cause customer fatigue.
        
        Uses DynamoDB for persistent tracking and CloudWatch for metrics.
        
        Args:
            request: Fatigue check request
            
        Returns:
            FatigueProtectionResult with decision and recommendations
        """
        if self.use_aws:
            try:
                # Load frequency from DynamoDB
                frequency = await self._load_frequency_from_dynamodb(
                    request.customer_id
                )
                
                # Update in-memory cache
                self._frequency_tracking[request.customer_id] = frequency
                
                # Perform check using base logic
                result = await super().check_fatigue(request)
                
                # Log metrics to CloudWatch
                await self._log_fatigue_metrics(request.customer_id, result)
                
                return result
                
            except Exception as e:
                logger.error(f"AWS fatigue check failed: {e}. Using fallback.")
                return await super().check_fatigue(request)
        else:
            return await super().check_fatigue(request)

    async def track_communication_frequency(
        self, customer_id: UUID, channel: ChannelType
    ) -> None:
        """Track communication frequency with DynamoDB persistence.
        
        Args:
            customer_id: Customer identifier
            channel: Communication channel used
        """
        # Update in-memory tracking
        await super().track_communication_frequency(customer_id, channel)
        
        if self.use_aws:
            try:
                # Persist to DynamoDB
                frequency = self._frequency_tracking[customer_id]
                await self._save_frequency_to_dynamodb(frequency)
                
                logger.info(
                    f"Persisted frequency tracking to DynamoDB for customer {customer_id}"
                )
            except Exception as e:
                logger.error(
                    f"Failed to persist frequency to DynamoDB: {e}. "
                    "Continuing with in-memory tracking."
                )

    async def detect_disengagement_signals(
        self, customer_id: UUID
    ) -> List[DisengagementSignal]:
        """Detect disengagement signals using DynamoDB storage.
        
        Args:
            customer_id: Customer identifier
            
        Returns:
            List of detected disengagement signals
        """
        if self.use_aws:
            try:
                # Load signals from DynamoDB
                signals = await self._load_signals_from_dynamodb(customer_id)
                
                # Update in-memory cache
                self._disengagement_signals[customer_id] = signals
                
                # Also check for new signals based on frequency
                new_signals = await super().detect_disengagement_signals(customer_id)
                
                # Combine and deduplicate
                all_signals = signals + new_signals
                unique_signals = self._deduplicate_signals(all_signals)
                
                return unique_signals
                
            except Exception as e:
                logger.error(f"Failed to load signals from DynamoDB: {e}")
                return await super().detect_disengagement_signals(customer_id)
        else:
            return await super().detect_disengagement_signals(customer_id)

    async def _load_frequency_from_dynamodb(
        self, customer_id: UUID
    ) -> CommunicationFrequency:
        """Load frequency tracking from DynamoDB.
        
        Args:
            customer_id: Customer identifier
            
        Returns:
            CommunicationFrequency record
        """
        try:
            response = self.dynamodb.get_item(
                TableName=self.frequency_table,
                Key={"customer_id": {"S": str(customer_id)}},
            )
            
            if "Item" in response:
                item = response["Item"]
                
                # Parse DynamoDB item
                frequency = CommunicationFrequency(
                    customer_id=customer_id,
                    daily_count=int(item.get("daily_count", {}).get("N", "0")),
                    weekly_count=int(item.get("weekly_count", {}).get("N", "0")),
                    monthly_count=int(item.get("monthly_count", {}).get("N", "0")),
                    last_message_time=self._parse_datetime(
                        item.get("last_message_time", {}).get("S")
                    ),
                    channel_breakdown=self._parse_channel_breakdown(
                        item.get("channel_breakdown", {}).get("M", {})
                    ),
                    fatigue_score=float(item.get("fatigue_score", {}).get("N", "0.0")),
                    last_updated=self._parse_datetime(
                        item.get("last_updated", {}).get("S")
                    ) or datetime.utcnow(),
                )
                
                return frequency
            else:
                # No existing record
                return CommunicationFrequency(customer_id=customer_id)
                
        except Exception as e:
            logger.error(f"Error loading frequency from DynamoDB: {e}")
            return CommunicationFrequency(customer_id=customer_id)

    async def _save_frequency_to_dynamodb(
        self, frequency: CommunicationFrequency
    ) -> None:
        """Save frequency tracking to DynamoDB with TTL.
        
        Args:
            frequency: Frequency record to save
        """
        # Calculate TTL (30 days from now)
        ttl = int((datetime.utcnow() + timedelta(days=30)).timestamp())
        
        item = {
            "customer_id": {"S": str(frequency.customer_id)},
            "daily_count": {"N": str(frequency.daily_count)},
            "weekly_count": {"N": str(frequency.weekly_count)},
            "monthly_count": {"N": str(frequency.monthly_count)},
            "fatigue_score": {"N": str(frequency.fatigue_score)},
            "last_updated": {"S": frequency.last_updated.isoformat()},
            "ttl": {"N": str(ttl)},
        }
        
        if frequency.last_message_time:
            item["last_message_time"] = {"S": frequency.last_message_time.isoformat()}
        
        if frequency.channel_breakdown:
            item["channel_breakdown"] = {
                "M": {
                    channel.value: {"N": str(count)}
                    for channel, count in frequency.channel_breakdown.items()
                }
            }
        
        self.dynamodb.put_item(TableName=self.frequency_table, Item=item)

    async def _load_signals_from_dynamodb(
        self, customer_id: UUID
    ) -> List[DisengagementSignal]:
        """Load disengagement signals from DynamoDB.
        
        Args:
            customer_id: Customer identifier
            
        Returns:
            List of disengagement signals
        """
        try:
            # Query signals for customer (within window)
            cutoff = datetime.utcnow() - timedelta(days=self.disengagement_window_days)
            
            response = self.dynamodb.query(
                TableName=self.signals_table,
                KeyConditionExpression="customer_id = :cid AND #ts >= :cutoff",
                ExpressionAttributeNames={"#ts": "timestamp"},
                ExpressionAttributeValues={
                    ":cid": {"S": str(customer_id)},
                    ":cutoff": {"S": cutoff.isoformat()},
                },
            )
            
            signals = []
            for item in response.get("Items", []):
                signal = DisengagementSignal(
                    signal_type=item["signal_type"]["S"],
                    timestamp=datetime.fromisoformat(item["timestamp"]["S"]),
                    channel=ChannelType(item["channel"]["S"]),
                    severity=float(item["severity"]["N"]),
                )
                signals.append(signal)
            
            return signals
            
        except Exception as e:
            logger.error(f"Error loading signals from DynamoDB: {e}")
            return []

    async def _save_signal_to_dynamodb(
        self, customer_id: UUID, signal: DisengagementSignal
    ) -> None:
        """Save disengagement signal to DynamoDB with TTL.
        
        Args:
            customer_id: Customer identifier
            signal: Signal to save
        """
        # Calculate TTL (30 days from now)
        ttl = int((datetime.utcnow() + timedelta(days=30)).timestamp())
        
        item = {
            "customer_id": {"S": str(customer_id)},
            "timestamp": {"S": signal.timestamp.isoformat()},
            "signal_type": {"S": signal.signal_type},
            "channel": {"S": signal.channel.value},
            "severity": {"N": str(signal.severity)},
            "ttl": {"N": str(ttl)},
        }
        
        self.dynamodb.put_item(TableName=self.signals_table, Item=item)

    async def _log_fatigue_metrics(
        self, customer_id: UUID, result: FatigueProtectionResult
    ) -> None:
        """Log fatigue metrics to CloudWatch.
        
        Args:
            customer_id: Customer identifier
            result: Fatigue protection result
        """
        try:
            metrics = [
                {
                    "MetricName": "FatigueProtectionActivated",
                    "Value": 0.0 if result.allow_message else 1.0,
                    "Unit": "Count",
                    "Timestamp": datetime.utcnow(),
                },
                {
                    "MetricName": "FatigueLevel",
                    "Value": self._fatigue_level_to_numeric(result.fatigue_level),
                    "Unit": "None",
                    "Timestamp": datetime.utcnow(),
                },
            ]
            
            if result.recommended_delay > 0:
                metrics.append({
                    "MetricName": "RecommendedDelay",
                    "Value": float(result.recommended_delay),
                    "Unit": "Minutes",
                    "Timestamp": datetime.utcnow(),
                })
            
            self.cloudwatch.put_metric_data(
                Namespace="AI-CPaaS/FatigueProtection",
                MetricData=metrics,
            )
            
            logger.debug(f"Logged fatigue metrics to CloudWatch for {customer_id}")
            
        except Exception as e:
            logger.error(f"Failed to log metrics to CloudWatch: {e}")

    def _parse_datetime(self, dt_str: Optional[str]) -> Optional[datetime]:
        """Parse datetime string from DynamoDB.
        
        Args:
            dt_str: ISO format datetime string
            
        Returns:
            Parsed datetime or None
        """
        if dt_str:
            try:
                return datetime.fromisoformat(dt_str)
            except Exception:
                return None
        return None

    def _parse_channel_breakdown(
        self, breakdown_map: Dict[str, Any]
    ) -> Dict[ChannelType, int]:
        """Parse channel breakdown from DynamoDB map.
        
        Args:
            breakdown_map: DynamoDB map structure
            
        Returns:
            Channel breakdown dictionary
        """
        result = {}
        for channel_str, count_dict in breakdown_map.items():
            try:
                channel = ChannelType(channel_str)
                count = int(count_dict.get("N", "0"))
                result[channel] = count
            except Exception:
                continue
        return result

    def _deduplicate_signals(
        self, signals: List[DisengagementSignal]
    ) -> List[DisengagementSignal]:
        """Remove duplicate signals keeping most recent.
        
        Args:
            signals: List of signals
            
        Returns:
            Deduplicated list
        """
        seen = {}
        for signal in sorted(signals, key=lambda s: s.timestamp, reverse=True):
            key = (signal.signal_type, signal.channel.value)
            if key not in seen:
                seen[key] = signal
        
        return list(seen.values())

    def _fatigue_level_to_numeric(self, level: str) -> float:
        """Convert fatigue level to numeric value for metrics.
        
        Args:
            level: Fatigue level string
            
        Returns:
            Numeric value (0.0 to 1.0)
        """
        mapping = {
            "low": 0.0,
            "medium": 0.5,
            "high": 1.0,
        }
        return mapping.get(level.lower(), 0.0)

    def record_disengagement_signal(
        self,
        customer_id: UUID,
        signal: DisengagementSignal,
    ) -> None:
        """Record disengagement signal with DynamoDB persistence.
        
        Args:
            customer_id: Customer identifier
            signal: Disengagement signal to record
        """
        # Update in-memory
        super().record_disengagement_signal(customer_id, signal)
        
        if self.use_aws:
            try:
                # Persist to DynamoDB
                import asyncio
                asyncio.create_task(
                    self._save_signal_to_dynamodb(customer_id, signal)
                )
            except Exception as e:
                logger.error(f"Failed to persist signal to DynamoDB: {e}")
