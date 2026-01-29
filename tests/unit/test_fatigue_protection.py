"""Unit tests for anti-fatigue protection system."""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from ai_cpaas_demo.core.interfaces import FatigueCheckRequest
from ai_cpaas_demo.core.models import (
    ChannelType,
    CommunicationFrequency,
    DisengagementSignal,
    FatigueLevel,
    MessageContext,
    MessageType,
)
from ai_cpaas_demo.engines.fatigue.base import BaseFatigueProtection


@pytest.fixture
def fatigue_engine():
    """Create a fatigue protection engine for testing."""
    return BaseFatigueProtection()


@pytest.fixture
def sample_customer_id():
    """Generate a sample customer ID."""
    return uuid4()


@pytest.fixture
def sample_message_context():
    """Create a sample message context."""
    return MessageContext(
        content="Test promotional message",
        message_type=MessageType.PROMOTIONAL,
        channel=ChannelType.SMS,
    )


class TestCommunicationFrequencyTracking:
    """Test communication frequency tracking functionality."""

    @pytest.mark.asyncio
    async def test_track_first_communication(self, fatigue_engine, sample_customer_id):
        """Test tracking the first communication for a customer."""
        # Track first message
        await fatigue_engine.track_communication_frequency(
            sample_customer_id, ChannelType.SMS
        )
        
        # Verify frequency was tracked
        frequency = fatigue_engine._frequency_tracking.get(sample_customer_id)
        assert frequency is not None
        assert frequency.daily_count == 1
        assert frequency.weekly_count == 1
        assert frequency.monthly_count == 1
        assert frequency.last_message_time is not None
        assert ChannelType.SMS in frequency.channel_breakdown
        assert frequency.channel_breakdown[ChannelType.SMS] == 1

    @pytest.mark.asyncio
    async def test_track_multiple_communications(self, fatigue_engine, sample_customer_id):
        """Test tracking multiple communications across channels."""
        # Track multiple messages
        await fatigue_engine.track_communication_frequency(
            sample_customer_id, ChannelType.SMS
        )
        await fatigue_engine.track_communication_frequency(
            sample_customer_id, ChannelType.EMAIL
        )
        await fatigue_engine.track_communication_frequency(
            sample_customer_id, ChannelType.SMS
        )
        
        # Verify counts
        frequency = fatigue_engine._frequency_tracking.get(sample_customer_id)
        assert frequency.daily_count == 3
        assert frequency.weekly_count == 3
        assert frequency.monthly_count == 3
        assert frequency.channel_breakdown[ChannelType.SMS] == 2
        assert frequency.channel_breakdown[ChannelType.EMAIL] == 1

    @pytest.mark.asyncio
    async def test_fatigue_score_calculation(self, fatigue_engine, sample_customer_id):
        """Test that fatigue score increases with frequency."""
        # Track messages up to threshold
        for _ in range(3):  # Daily threshold
            await fatigue_engine.track_communication_frequency(
                sample_customer_id, ChannelType.SMS
            )
        
        frequency = fatigue_engine._frequency_tracking.get(sample_customer_id)
        assert frequency.fatigue_score > 0.0
        assert frequency.fatigue_score <= 1.0


class TestFatigueDetection:
    """Test fatigue detection and protection logic."""

    @pytest.mark.asyncio
    async def test_allow_message_under_threshold(
        self, fatigue_engine, sample_customer_id, sample_message_context
    ):
        """Test that messages are allowed when under threshold."""
        # Track one message (under threshold)
        await fatigue_engine.track_communication_frequency(
            sample_customer_id, ChannelType.SMS
        )
        
        # Check fatigue
        request = FatigueCheckRequest(
            customer_id=sample_customer_id,
            proposed_message=sample_message_context,
        )
        result = await fatigue_engine.check_fatigue(request)
        
        assert result.allow_message is True
        assert result.fatigue_level in ["low", "medium"]

    @pytest.mark.asyncio
    async def test_block_message_at_daily_threshold(
        self, fatigue_engine, sample_customer_id, sample_message_context
    ):
        """Test that messages are blocked at daily threshold."""
        # Track messages up to daily threshold
        for _ in range(fatigue_engine.daily_threshold):
            await fatigue_engine.track_communication_frequency(
                sample_customer_id, ChannelType.SMS
            )
        
        # Check fatigue - should block
        request = FatigueCheckRequest(
            customer_id=sample_customer_id,
            proposed_message=sample_message_context,
        )
        result = await fatigue_engine.check_fatigue(request)
        
        assert result.allow_message is False
        assert "Daily limit reached" in " ".join(result.protection_reason)
        assert result.recommended_delay > 0
        assert len(result.alternative_actions) > 0

    @pytest.mark.asyncio
    async def test_fatigue_level_progression(
        self, fatigue_engine, sample_customer_id, sample_message_context
    ):
        """Test that fatigue level increases with frequency."""
        # Start with low fatigue
        request = FatigueCheckRequest(
            customer_id=sample_customer_id,
            proposed_message=sample_message_context,
        )
        result = await fatigue_engine.check_fatigue(request)
        assert result.fatigue_level == "low"
        
        # Track messages to medium threshold (60% of limit)
        for _ in range(2):  # 2 out of 3 daily threshold
            await fatigue_engine.track_communication_frequency(
                sample_customer_id, ChannelType.SMS
            )
        
        result = await fatigue_engine.check_fatigue(request)
        assert result.fatigue_level in ["medium", "high"]


class TestDisengagementSignals:
    """Test disengagement signal detection."""

    @pytest.mark.asyncio
    async def test_detect_no_signals_initially(self, fatigue_engine, sample_customer_id):
        """Test that no signals are detected initially."""
        signals = await fatigue_engine.detect_disengagement_signals(sample_customer_id)
        assert len(signals) == 0

    @pytest.mark.asyncio
    async def test_record_disengagement_signal(self, fatigue_engine, sample_customer_id):
        """Test recording a disengagement signal."""
        signal = DisengagementSignal(
            signal_type="unsubscribe",
            timestamp=datetime.utcnow(),
            channel=ChannelType.EMAIL,
            severity=0.9,
        )
        
        fatigue_engine.record_disengagement_signal(sample_customer_id, signal)
        
        signals = await fatigue_engine.detect_disengagement_signals(sample_customer_id)
        assert len(signals) == 1
        assert signals[0].signal_type == "unsubscribe"
        assert signals[0].severity == 0.9

    @pytest.mark.asyncio
    async def test_block_message_with_high_disengagement(
        self, fatigue_engine, sample_customer_id, sample_message_context
    ):
        """Test that messages are blocked with high disengagement signals."""
        # Record high severity disengagement signal
        signal = DisengagementSignal(
            signal_type="spam_report",
            timestamp=datetime.utcnow(),
            channel=ChannelType.SMS,
            severity=0.8,
        )
        fatigue_engine.record_disengagement_signal(sample_customer_id, signal)
        
        # Check fatigue - should block
        request = FatigueCheckRequest(
            customer_id=sample_customer_id,
            proposed_message=sample_message_context,
        )
        result = await fatigue_engine.check_fatigue(request)
        
        assert result.allow_message is False
        assert "disengagement" in " ".join(result.protection_reason).lower()
        assert result.recommended_delay >= 2880  # At least 48 hours


class TestFatigueProtectionLogging:
    """Test fatigue protection logging and prevention."""

    @pytest.mark.asyncio
    async def test_protection_reason_provided(
        self, fatigue_engine, sample_customer_id, sample_message_context
    ):
        """Test that protection reasons are provided when blocking."""
        # Exceed daily threshold
        for _ in range(fatigue_engine.daily_threshold):
            await fatigue_engine.track_communication_frequency(
                sample_customer_id, ChannelType.SMS
            )
        
        request = FatigueCheckRequest(
            customer_id=sample_customer_id,
            proposed_message=sample_message_context,
        )
        result = await fatigue_engine.check_fatigue(request)
        
        assert result.allow_message is False
        assert len(result.protection_reason) > 0
        assert all(isinstance(reason, str) for reason in result.protection_reason)

    @pytest.mark.asyncio
    async def test_alternative_actions_suggested(
        self, fatigue_engine, sample_customer_id, sample_message_context
    ):
        """Test that alternative actions are suggested when blocking."""
        # Exceed daily threshold
        for _ in range(fatigue_engine.daily_threshold):
            await fatigue_engine.track_communication_frequency(
                sample_customer_id, ChannelType.SMS
            )
        
        request = FatigueCheckRequest(
            customer_id=sample_customer_id,
            proposed_message=sample_message_context,
        )
        result = await fatigue_engine.check_fatigue(request)
        
        assert result.allow_message is False
        assert len(result.alternative_actions) > 0
        assert all(isinstance(action, str) for action in result.alternative_actions)

    @pytest.mark.asyncio
    async def test_recommended_delay_calculated(
        self, fatigue_engine, sample_customer_id, sample_message_context
    ):
        """Test that recommended delay is calculated when blocking."""
        # Exceed daily threshold
        for _ in range(fatigue_engine.daily_threshold):
            await fatigue_engine.track_communication_frequency(
                sample_customer_id, ChannelType.SMS
            )
        
        request = FatigueCheckRequest(
            customer_id=sample_customer_id,
            proposed_message=sample_message_context,
        )
        result = await fatigue_engine.check_fatigue(request)
        
        assert result.allow_message is False
        assert result.recommended_delay > 0
        assert isinstance(result.recommended_delay, int)


class TestCrossChannelTracking:
    """Test cross-channel communication tracking."""

    @pytest.mark.asyncio
    async def test_track_across_multiple_channels(
        self, fatigue_engine, sample_customer_id
    ):
        """Test that frequency is tracked across all channels."""
        # Send messages across different channels
        await fatigue_engine.track_communication_frequency(
            sample_customer_id, ChannelType.SMS
        )
        await fatigue_engine.track_communication_frequency(
            sample_customer_id, ChannelType.EMAIL
        )
        await fatigue_engine.track_communication_frequency(
            sample_customer_id, ChannelType.WHATSAPP
        )
        
        frequency = fatigue_engine._frequency_tracking.get(sample_customer_id)
        assert frequency.daily_count == 3
        assert len(frequency.channel_breakdown) == 3
        assert ChannelType.SMS in frequency.channel_breakdown
        assert ChannelType.EMAIL in frequency.channel_breakdown
        assert ChannelType.WHATSAPP in frequency.channel_breakdown

    @pytest.mark.asyncio
    async def test_fatigue_applies_across_channels(
        self, fatigue_engine, sample_customer_id, sample_message_context
    ):
        """Test that fatigue protection applies regardless of channel."""
        # Exceed threshold using different channels
        await fatigue_engine.track_communication_frequency(
            sample_customer_id, ChannelType.SMS
        )
        await fatigue_engine.track_communication_frequency(
            sample_customer_id, ChannelType.EMAIL
        )
        await fatigue_engine.track_communication_frequency(
            sample_customer_id, ChannelType.WHATSAPP
        )
        
        # Try to send via a different channel - should still be blocked
        request = FatigueCheckRequest(
            customer_id=sample_customer_id,
            proposed_message=sample_message_context,
        )
        result = await fatigue_engine.check_fatigue(request)
        
        assert result.allow_message is False
        assert "Daily limit reached" in " ".join(result.protection_reason)
