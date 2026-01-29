"""Unit tests for core data models."""

import pytest
from datetime import datetime
from uuid import uuid4

from ai_cpaas_demo.core.models import (
    ChannelType,
    CustomerProfile,
    EngagementRecord,
    MessageType,
    SentimentType,
    FatigueLevel,
)


class TestCustomerProfile:
    """Test CustomerProfile model."""

    def test_customer_profile_creation(self):
        """Test creating a customer profile with default values."""
        profile = CustomerProfile(external_id="test-customer-123")
        
        assert profile.external_id == "test-customer-123"
        assert profile.fatigue_level == FatigueLevel.LOW
        assert len(profile.channel_preferences) == 0
        assert len(profile.engagement_history) == 0
        assert len(profile.sentiment_history) == 0
        assert len(profile.support_tickets) == 0
        assert len(profile.disengagement_signals) == 0
        assert isinstance(profile.created_at, datetime)
        assert isinstance(profile.updated_at, datetime)

    def test_customer_profile_with_engagement_history(self):
        """Test customer profile with engagement records."""
        engagement = EngagementRecord(
            channel=ChannelType.SMS,
            message_type=MessageType.PROMOTIONAL,
            timestamp=datetime.utcnow(),
            opened=True,
            engagement_score=0.8
        )
        
        profile = CustomerProfile(
            external_id="test-customer-456",
            engagement_history=[engagement]
        )
        
        assert len(profile.engagement_history) == 1
        assert profile.engagement_history[0].channel == ChannelType.SMS
        assert profile.engagement_history[0].opened is True
        assert profile.engagement_history[0].engagement_score == 0.8

    def test_updated_at_auto_update(self):
        """Test that updated_at is automatically set."""
        profile = CustomerProfile(external_id="test-customer-789")
        original_updated_at = profile.updated_at
        
        # Create a new instance (simulating an update)
        updated_profile = CustomerProfile(
            external_id="test-customer-789",
            fatigue_level=FatigueLevel.HIGH
        )
        
        # updated_at should be different (newer)
        assert updated_profile.updated_at >= original_updated_at


class TestEngagementRecord:
    """Test EngagementRecord model."""

    def test_engagement_record_creation(self):
        """Test creating an engagement record."""
        record = EngagementRecord(
            channel=ChannelType.EMAIL,
            message_type=MessageType.TRANSACTIONAL,
            timestamp=datetime.utcnow(),
            engagement_score=0.6
        )
        
        assert record.channel == ChannelType.EMAIL
        assert record.message_type == MessageType.TRANSACTIONAL
        assert record.opened is False  # Default value
        assert record.clicked is False  # Default value
        assert record.responded is False  # Default value
        assert record.engagement_score == 0.6
        assert record.engagement_count == 0  # Default value

    def test_engagement_score_validation(self):
        """Test engagement score validation (0.0 to 1.0)."""
        # Valid score
        record = EngagementRecord(
            channel=ChannelType.WHATSAPP,
            message_type=MessageType.SUPPORT,
            timestamp=datetime.utcnow(),
            engagement_score=0.5
        )
        assert record.engagement_score == 0.5
        
        # Test boundary values
        record_min = EngagementRecord(
            channel=ChannelType.SMS,
            message_type=MessageType.PROMOTIONAL,
            timestamp=datetime.utcnow(),
            engagement_score=0.0
        )
        assert record_min.engagement_score == 0.0
        
        record_max = EngagementRecord(
            channel=ChannelType.EMAIL,
            message_type=MessageType.TRANSACTIONAL,
            timestamp=datetime.utcnow(),
            engagement_score=1.0
        )
        assert record_max.engagement_score == 1.0