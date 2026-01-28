"""Base implementation of anti-fatigue protection system."""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List
from uuid import UUID

from ai_cpaas_demo.core.interfaces import (
    AntiFatigueProtection,
    FatigueCheckRequest,
    FatigueProtectionResult,
)
from ai_cpaas_demo.core.models import (
    ChannelType,
    CommunicationFrequency,
    DisengagementSignal,
    FatigueLevel,
)

logger = logging.getLogger(__name__)


class BaseFatigueProtection(AntiFatigueProtection):
    """Base implementation of anti-fatigue protection system.
    
    Tracks communication frequency across channels and prevents customer fatigue
    by detecting overload patterns and disengagement signals.
    """

    def __init__(self):
        """Initialize the base fatigue protection engine."""
        # In-memory storage for demo purposes
        self._frequency_tracking: Dict[UUID, CommunicationFrequency] = {}
        self._disengagement_signals: Dict[UUID, List[DisengagementSignal]] = {}
        
        # Fatigue thresholds
        self.daily_threshold = 3
        self.weekly_threshold = 10
        self.monthly_threshold = 30
        
        # Disengagement detection thresholds
        self.low_engagement_threshold = 0.3  # Below 30% engagement
        self.disengagement_window_days = 7
        
        logger.info("Initialized BaseFatigueProtection engine")

    async def check_fatigue(
        self, request: FatigueCheckRequest
    ) -> FatigueProtectionResult:
        """Check if sending a message would cause customer fatigue.
        
        Args:
            request: Fatigue check request with customer and message details
            
        Returns:
            FatigueProtectionResult with decision and recommendations
        """
        customer_id = request.customer_id
        
        # Get or create frequency tracking
        frequency = self._frequency_tracking.get(
            customer_id,
            CommunicationFrequency(customer_id=customer_id)
        )
        
        # Calculate fatigue level
        fatigue_level = self._calculate_fatigue_level(frequency)
        
        # Check disengagement signals
        disengagement_signals = await self.detect_disengagement_signals(customer_id)
        
        # Determine if message should be allowed
        allow_message = True
        protection_reasons = []
        alternative_actions = []
        recommended_delay = 0
        
        # Check frequency limits
        if frequency.daily_count >= self.daily_threshold:
            allow_message = False
            protection_reasons.append(
                f"Daily limit reached ({frequency.daily_count}/{self.daily_threshold})"
            )
            recommended_delay = self._calculate_delay_until_next_day()
            alternative_actions.append("Wait until tomorrow to send message")
        
        if frequency.weekly_count >= self.weekly_threshold:
            allow_message = False
            protection_reasons.append(
                f"Weekly limit reached ({frequency.weekly_count}/{self.weekly_threshold})"
            )
            if recommended_delay == 0:
                recommended_delay = self._calculate_delay_until_next_week()
            alternative_actions.append("Reduce communication frequency this week")
        
        # Check for high fatigue
        if fatigue_level == FatigueLevel.HIGH:
            allow_message = False
            protection_reasons.append("Customer showing high fatigue signals")
            recommended_delay = max(recommended_delay, 1440)  # At least 24 hours
            alternative_actions.append("Pause non-critical communications for 48 hours")
        
        # Check disengagement signals
        if disengagement_signals:
            if any(s.severity > 0.7 for s in disengagement_signals):
                allow_message = False
                protection_reasons.append(
                    f"Strong disengagement signals detected: {', '.join(s.signal_type for s in disengagement_signals)}"
                )
                recommended_delay = max(recommended_delay, 2880)  # At least 48 hours
                alternative_actions.append("Review customer preferences and reduce frequency")
        
        # Medium fatigue - allow but warn
        if fatigue_level == FatigueLevel.MEDIUM and allow_message:
            protection_reasons.append("Customer approaching fatigue threshold")
            alternative_actions.append("Consider spacing out future messages")
            recommended_delay = 240  # 4 hours minimum
        
        return FatigueProtectionResult(
            allow_message=allow_message,
            fatigue_level=fatigue_level.value,
            recommended_delay=recommended_delay,
            protection_reason=protection_reasons,
            alternative_actions=alternative_actions,
        )

    async def track_communication_frequency(
        self, customer_id: UUID, channel: ChannelType
    ) -> None:
        """Track communication frequency for a customer.
        
        Args:
            customer_id: Customer identifier
            channel: Communication channel used
        """
        now = datetime.utcnow()
        
        # Get or create frequency record
        if customer_id not in self._frequency_tracking:
            self._frequency_tracking[customer_id] = CommunicationFrequency(
                customer_id=customer_id
            )
        
        frequency = self._frequency_tracking[customer_id]
        
        # Reset counters if needed
        if frequency.last_message_time:
            time_since_last = now - frequency.last_message_time
            
            # Reset daily counter
            if time_since_last.days >= 1:
                frequency.daily_count = 0
            
            # Reset weekly counter
            if time_since_last.days >= 7:
                frequency.weekly_count = 0
            
            # Reset monthly counter
            if time_since_last.days >= 30:
                frequency.monthly_count = 0
        
        # Increment counters
        frequency.daily_count += 1
        frequency.weekly_count += 1
        frequency.monthly_count += 1
        frequency.last_message_time = now
        frequency.last_updated = now
        
        # Update channel breakdown
        if channel not in frequency.channel_breakdown:
            frequency.channel_breakdown[channel] = 0
        frequency.channel_breakdown[channel] += 1
        
        # Calculate fatigue score
        frequency.fatigue_score = self._calculate_fatigue_score(frequency)
        
        logger.info(
            f"Tracked communication for customer {customer_id}: "
            f"daily={frequency.daily_count}, weekly={frequency.weekly_count}, "
            f"fatigue_score={frequency.fatigue_score:.2f}"
        )

    async def detect_disengagement_signals(
        self, customer_id: UUID
    ) -> List[DisengagementSignal]:
        """Detect signals indicating customer disengagement.
        
        Args:
            customer_id: Customer identifier
            
        Returns:
            List of detected disengagement signals
        """
        signals = []
        
        # Get stored signals
        if customer_id in self._disengagement_signals:
            # Filter recent signals (within window)
            cutoff = datetime.utcnow() - timedelta(days=self.disengagement_window_days)
            signals = [
                s for s in self._disengagement_signals[customer_id]
                if s.timestamp >= cutoff
            ]
        
        # Check frequency tracking for low engagement
        if customer_id in self._frequency_tracking:
            frequency = self._frequency_tracking[customer_id]
            
            # High message count with low engagement indicates fatigue
            if frequency.weekly_count > 5 and frequency.fatigue_score > 0.7:
                signals.append(
                    DisengagementSignal(
                        signal_type="low_engagement",
                        timestamp=datetime.utcnow(),
                        channel=ChannelType.SMS,  # Generic
                        severity=frequency.fatigue_score,
                    )
                )
        
        return signals

    def _calculate_fatigue_level(
        self, frequency: CommunicationFrequency
    ) -> FatigueLevel:
        """Calculate customer fatigue level based on frequency.
        
        Args:
            frequency: Communication frequency record
            
        Returns:
            Calculated fatigue level
        """
        # Calculate percentage of limits reached
        daily_pct = frequency.daily_count / self.daily_threshold
        weekly_pct = frequency.weekly_count / self.weekly_threshold
        monthly_pct = frequency.monthly_count / self.monthly_threshold
        
        # Use highest percentage
        max_pct = max(daily_pct, weekly_pct, monthly_pct)
        
        if max_pct >= 0.9:
            return FatigueLevel.HIGH
        elif max_pct >= 0.6:
            return FatigueLevel.MEDIUM
        else:
            return FatigueLevel.LOW

    def _calculate_fatigue_score(
        self, frequency: CommunicationFrequency
    ) -> float:
        """Calculate numeric fatigue score (0.0 to 1.0).
        
        Args:
            frequency: Communication frequency record
            
        Returns:
            Fatigue score between 0.0 and 1.0
        """
        # Weighted average of frequency percentages
        daily_weight = 0.5
        weekly_weight = 0.3
        monthly_weight = 0.2
        
        daily_score = min(1.0, frequency.daily_count / self.daily_threshold)
        weekly_score = min(1.0, frequency.weekly_count / self.weekly_threshold)
        monthly_score = min(1.0, frequency.monthly_count / self.monthly_threshold)
        
        return (
            daily_score * daily_weight +
            weekly_score * weekly_weight +
            monthly_score * monthly_weight
        )

    def _calculate_delay_until_next_day(self) -> int:
        """Calculate minutes until next day.
        
        Returns:
            Minutes until midnight
        """
        now = datetime.utcnow()
        tomorrow = (now + timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        delta = tomorrow - now
        return int(delta.total_seconds() / 60)

    def _calculate_delay_until_next_week(self) -> int:
        """Calculate minutes until next week.
        
        Returns:
            Minutes until next Monday
        """
        now = datetime.utcnow()
        days_until_monday = (7 - now.weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        next_monday = (now + timedelta(days=days_until_monday)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        delta = next_monday - now
        return int(delta.total_seconds() / 60)

    def record_disengagement_signal(
        self,
        customer_id: UUID,
        signal: DisengagementSignal,
    ) -> None:
        """Record a disengagement signal for a customer.
        
        Args:
            customer_id: Customer identifier
            signal: Disengagement signal to record
        """
        if customer_id not in self._disengagement_signals:
            self._disengagement_signals[customer_id] = []
        
        self._disengagement_signals[customer_id].append(signal)
        
        logger.warning(
            f"Recorded disengagement signal for customer {customer_id}: "
            f"{signal.signal_type} (severity={signal.severity:.2f})"
        )
