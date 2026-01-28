"""Customer profile generator for creating realistic demo data."""

import random
from datetime import datetime, timedelta
from typing import List
from uuid import uuid4

from faker import Faker

from ..core.models import (
    ChannelPreference,
    ChannelType,
    CustomerProfile,
    DisengagementSignal,
    EngagementRecord,
    FatigueLevel,
    FrequencySettings,
    MessageType,
    SentimentRecord,
    SentimentType,
    SupportTicket,
)


class CustomerProfileGenerator:
    """Generates realistic customer profiles for demo purposes."""

    def __init__(self, seed: int = 42):
        """Initialize the generator with a seed for reproducibility."""
        self.faker = Faker()
        Faker.seed(seed)
        random.seed(seed)

    def generate_profiles(self, count: int = 1000) -> List[CustomerProfile]:
        """
        Generate a specified number of customer profiles.
        
        Distribution:
        - High-value customers: 10% (100 customers)
        - Medium-value customers: 40% (400 customers)
        - Low-value customers: 50% (500 customers)
        """
        profiles = []
        
        # Generate high-value customers (10%)
        high_value_count = int(count * 0.10)
        for _ in range(high_value_count):
            profiles.append(self._generate_profile(value_tier="high"))
        
        # Generate medium-value customers (40%)
        medium_value_count = int(count * 0.40)
        for _ in range(medium_value_count):
            profiles.append(self._generate_profile(value_tier="medium"))
        
        # Generate low-value customers (remaining ~50%)
        low_value_count = count - high_value_count - medium_value_count
        for _ in range(low_value_count):
            profiles.append(self._generate_profile(value_tier="low"))
        
        return profiles

    def _generate_profile(self, value_tier: str) -> CustomerProfile:
        """Generate a single customer profile based on value tier."""
        customer_id = uuid4()
        external_id = f"CUST-{self.faker.unique.random_number(digits=8)}"
        
        # Generate name for personalization
        first_name = self.faker.first_name()
        last_name = self.faker.last_name()
        
        # Generate channel preferences based on value tier
        channel_preferences = self._generate_channel_preferences(value_tier)
        
        # Generate engagement history (6 months)
        engagement_history = self._generate_engagement_history(
            value_tier, channel_preferences
        )
        
        # Generate sentiment history
        sentiment_history = self._generate_sentiment_history(value_tier)
        
        # Generate support tickets
        support_tickets = self._generate_support_tickets(value_tier)
        
        # Generate disengagement signals
        disengagement_signals = self._generate_disengagement_signals(value_tier)
        
        # Determine fatigue level
        fatigue_level = self._determine_fatigue_level(value_tier)
        
        # Generate frequency settings
        frequency_settings = self._generate_frequency_settings(value_tier)
        
        # Calculate last interaction
        last_interaction = None
        if engagement_history:
            last_interaction = max(record.timestamp for record in engagement_history)
        
        profile = CustomerProfile(
            id=customer_id,
            external_id=external_id,
            channel_preferences=channel_preferences,
            engagement_history=engagement_history,
            sentiment_history=sentiment_history,
            communication_frequency=frequency_settings,
            last_interaction=last_interaction,
            support_tickets=support_tickets,
            fatigue_level=fatigue_level,
            disengagement_signals=disengagement_signals,
        )
        
        # Store names as metadata (since CustomerProfile doesn't have these fields)
        # They will be added during enrichment
        profile._first_name = first_name
        profile._last_name = last_name
        
        return profile

    def _generate_channel_preferences(
        self, value_tier: str
    ) -> List[ChannelPreference]:
        """Generate channel preferences based on customer value tier."""
        preferences = []
        
        if value_tier == "high":
            # High-value customers prefer email and voice
            preferences = [
                ChannelPreference(
                    channel=ChannelType.EMAIL,
                    preference_score=random.uniform(0.7, 0.95),
                    last_engagement=datetime.utcnow() - timedelta(days=random.randint(1, 30)),
                    engagement_count=random.randint(20, 50),
                ),
                ChannelPreference(
                    channel=ChannelType.VOICE,
                    preference_score=random.uniform(0.6, 0.85),
                    last_engagement=datetime.utcnow() - timedelta(days=random.randint(1, 60)),
                    engagement_count=random.randint(10, 30),
                ),
                ChannelPreference(
                    channel=ChannelType.WHATSAPP,
                    preference_score=random.uniform(0.4, 0.7),
                    last_engagement=datetime.utcnow() - timedelta(days=random.randint(30, 90)),
                    engagement_count=random.randint(5, 15),
                ),
                ChannelPreference(
                    channel=ChannelType.SMS,
                    preference_score=random.uniform(0.2, 0.5),
                    last_engagement=datetime.utcnow() - timedelta(days=random.randint(60, 180)),
                    engagement_count=random.randint(0, 10),
                ),
            ]
        elif value_tier == "medium":
            # Medium-value customers prefer WhatsApp and email
            preferences = [
                ChannelPreference(
                    channel=ChannelType.WHATSAPP,
                    preference_score=random.uniform(0.6, 0.9),
                    last_engagement=datetime.utcnow() - timedelta(days=random.randint(1, 45)),
                    engagement_count=random.randint(15, 40),
                ),
                ChannelPreference(
                    channel=ChannelType.EMAIL,
                    preference_score=random.uniform(0.5, 0.8),
                    last_engagement=datetime.utcnow() - timedelta(days=random.randint(1, 60)),
                    engagement_count=random.randint(10, 30),
                ),
                ChannelPreference(
                    channel=ChannelType.SMS,
                    preference_score=random.uniform(0.3, 0.6),
                    last_engagement=datetime.utcnow() - timedelta(days=random.randint(30, 90)),
                    engagement_count=random.randint(5, 20),
                ),
                ChannelPreference(
                    channel=ChannelType.VOICE,
                    preference_score=random.uniform(0.2, 0.5),
                    last_engagement=datetime.utcnow() - timedelta(days=random.randint(60, 180)),
                    engagement_count=random.randint(0, 10),
                ),
            ]
        else:  # low value
            # Low-value customers prefer SMS and WhatsApp
            preferences = [
                ChannelPreference(
                    channel=ChannelType.SMS,
                    preference_score=random.uniform(0.5, 0.85),
                    last_engagement=datetime.utcnow() - timedelta(days=random.randint(1, 60)),
                    engagement_count=random.randint(10, 35),
                ),
                ChannelPreference(
                    channel=ChannelType.WHATSAPP,
                    preference_score=random.uniform(0.4, 0.75),
                    last_engagement=datetime.utcnow() - timedelta(days=random.randint(1, 90)),
                    engagement_count=random.randint(5, 25),
                ),
                ChannelPreference(
                    channel=ChannelType.EMAIL,
                    preference_score=random.uniform(0.2, 0.5),
                    last_engagement=datetime.utcnow() - timedelta(days=random.randint(30, 120)),
                    engagement_count=random.randint(0, 15),
                ),
                ChannelPreference(
                    channel=ChannelType.VOICE,
                    preference_score=random.uniform(0.1, 0.3),
                    last_engagement=datetime.utcnow() - timedelta(days=random.randint(90, 180)),
                    engagement_count=random.randint(0, 5),
                ),
            ]
        
        return preferences

    def _generate_engagement_history(
        self, value_tier: str, channel_preferences: List[ChannelPreference]
    ) -> List[EngagementRecord]:
        """Generate 6 months of engagement history."""
        records = []
        
        # Determine engagement frequency based on value tier
        if value_tier == "high":
            num_records = random.randint(40, 80)
        elif value_tier == "medium":
            num_records = random.randint(20, 50)
        else:
            num_records = random.randint(10, 30)
        
        # Generate records over 6 months
        for _ in range(num_records):
            # Pick a channel based on preferences
            channel = random.choices(
                [pref.channel for pref in channel_preferences],
                weights=[pref.preference_score for pref in channel_preferences],
            )[0]
            
            # Generate timestamp within last 6 months
            days_ago = random.randint(0, 180)
            timestamp = datetime.utcnow() - timedelta(days=days_ago)
            
            # Determine engagement based on channel preference
            channel_pref = next(p for p in channel_preferences if p.channel == channel)
            engagement_score = channel_pref.preference_score
            
            # Determine if opened/clicked/responded based on engagement score
            opened = random.random() < engagement_score
            clicked = opened and random.random() < (engagement_score * 0.7)
            responded = clicked and random.random() < (engagement_score * 0.5)
            
            # Pick message type
            message_type = random.choice(list(MessageType))
            
            records.append(
                EngagementRecord(
                    channel=channel,
                    message_type=message_type,
                    timestamp=timestamp,
                    opened=opened,
                    clicked=clicked,
                    responded=responded,
                    engagement_score=engagement_score,
                )
            )
        
        return sorted(records, key=lambda r: r.timestamp)

    def _generate_sentiment_history(self, value_tier: str) -> List[SentimentRecord]:
        """Generate sentiment history over 6 months."""
        records = []
        
        # Distribution: 5% angry, 15% neutral, 80% satisfied
        # But adjust based on value tier
        if value_tier == "high":
            sentiment_weights = [0.02, 0.10, 0.88]  # Mostly positive
        elif value_tier == "medium":
            sentiment_weights = [0.05, 0.15, 0.80]  # Standard distribution
        else:
            sentiment_weights = [0.08, 0.20, 0.72]  # More negative/neutral
        
        num_records = random.randint(5, 20)
        
        for _ in range(num_records):
            sentiment = random.choices(
                [SentimentType.NEGATIVE, SentimentType.NEUTRAL, SentimentType.POSITIVE],
                weights=sentiment_weights,
            )[0]
            
            days_ago = random.randint(0, 180)
            timestamp = datetime.utcnow() - timedelta(days=days_ago)
            
            # Confidence varies
            confidence = random.uniform(0.6, 0.95)
            
            # Source varies
            source = random.choice([
                "support_ticket",
                "survey",
                "social_media",
                "email_response",
                "chat_interaction",
            ])
            
            records.append(
                SentimentRecord(
                    timestamp=timestamp,
                    sentiment=sentiment,
                    confidence=confidence,
                    source=source,
                    context=self.faker.sentence() if random.random() < 0.5 else None,
                )
            )
        
        return sorted(records, key=lambda r: r.timestamp)

    def _generate_support_tickets(self, value_tier: str) -> List[SupportTicket]:
        """Generate support ticket history."""
        tickets = []
        
        # High-value customers have fewer tickets but higher priority
        if value_tier == "high":
            num_tickets = random.randint(0, 3)
            priority_weights = [0.1, 0.2, 0.4, 0.3]  # low, medium, high, critical
        elif value_tier == "medium":
            num_tickets = random.randint(0, 5)
            priority_weights = [0.2, 0.4, 0.3, 0.1]
        else:
            num_tickets = random.randint(0, 8)
            priority_weights = [0.4, 0.4, 0.15, 0.05]
        
        for _ in range(num_tickets):
            days_ago = random.randint(0, 180)
            created_at = datetime.utcnow() - timedelta(days=days_ago)
            
            priority = random.choices(
                ["low", "medium", "high", "critical"],
                weights=priority_weights,
            )[0]
            
            status = random.choices(
                ["open", "in_progress", "resolved", "closed"],
                weights=[0.1, 0.15, 0.35, 0.4],
            )[0]
            
            category = random.choice([
                "billing",
                "technical",
                "complaint",
                "feature_request",
                "account",
            ])
            
            # Sentiment based on category and status
            if category == "complaint" or status == "open":
                sentiment = SentimentType.NEGATIVE
            elif status == "resolved" or status == "closed":
                sentiment = SentimentType.POSITIVE
            else:
                sentiment = SentimentType.NEUTRAL
            
            resolved_at = None
            if status in ["resolved", "closed"]:
                resolved_at = created_at + timedelta(days=random.randint(1, 14))
            
            tickets.append(
                SupportTicket(
                    created_at=created_at,
                    status=status,
                    priority=priority,
                    category=category,
                    sentiment=sentiment,
                    resolved_at=resolved_at,
                )
            )
        
        return sorted(tickets, key=lambda t: t.created_at)

    def _generate_disengagement_signals(
        self, value_tier: str
    ) -> List[DisengagementSignal]:
        """Generate disengagement signals."""
        signals = []
        
        # Low-value customers have more disengagement signals
        if value_tier == "high":
            num_signals = random.randint(0, 1)
        elif value_tier == "medium":
            num_signals = random.randint(0, 2)
        else:
            num_signals = random.randint(0, 4)
        
        for _ in range(num_signals):
            signal_type = random.choice([
                "low_engagement",
                "unsubscribe",
                "spam_report",
                "bounce",
                "no_response",
            ])
            
            days_ago = random.randint(0, 180)
            timestamp = datetime.utcnow() - timedelta(days=days_ago)
            
            channel = random.choice(list(ChannelType))
            
            # Severity varies by signal type
            if signal_type in ["unsubscribe", "spam_report"]:
                severity = random.uniform(0.7, 1.0)
            elif signal_type == "bounce":
                severity = random.uniform(0.5, 0.8)
            else:
                severity = random.uniform(0.3, 0.6)
            
            signals.append(
                DisengagementSignal(
                    signal_type=signal_type,
                    timestamp=timestamp,
                    channel=channel,
                    severity=severity,
                )
            )
        
        return sorted(signals, key=lambda s: s.timestamp)

    def _determine_fatigue_level(self, value_tier: str) -> FatigueLevel:
        """Determine customer fatigue level."""
        if value_tier == "high":
            # High-value customers rarely fatigued
            return random.choices(
                [FatigueLevel.LOW, FatigueLevel.MEDIUM, FatigueLevel.HIGH],
                weights=[0.85, 0.12, 0.03],
            )[0]
        elif value_tier == "medium":
            return random.choices(
                [FatigueLevel.LOW, FatigueLevel.MEDIUM, FatigueLevel.HIGH],
                weights=[0.70, 0.20, 0.10],
            )[0]
        else:
            return random.choices(
                [FatigueLevel.LOW, FatigueLevel.MEDIUM, FatigueLevel.HIGH],
                weights=[0.55, 0.30, 0.15],
            )[0]

    def _generate_frequency_settings(self, value_tier: str) -> FrequencySettings:
        """Generate communication frequency preferences."""
        if value_tier == "high":
            # High-value customers prefer less frequent communication
            return FrequencySettings(
                daily_limit=random.randint(1, 2),
                weekly_limit=random.randint(5, 8),
                monthly_limit=random.randint(15, 25),
                preferred_time_start=random.randint(9, 11),
                preferred_time_end=random.randint(16, 18),
                timezone=random.choice(["America/New_York", "America/Los_Angeles", "Europe/London"]),
            )
        elif value_tier == "medium":
            return FrequencySettings(
                daily_limit=random.randint(2, 4),
                weekly_limit=random.randint(8, 15),
                monthly_limit=random.randint(25, 40),
                preferred_time_start=random.randint(8, 10),
                preferred_time_end=random.randint(17, 19),
                timezone=random.choice(["America/New_York", "America/Chicago", "America/Los_Angeles"]),
            )
        else:
            return FrequencySettings(
                daily_limit=random.randint(3, 5),
                weekly_limit=random.randint(10, 20),
                monthly_limit=random.randint(30, 50),
                preferred_time_start=random.randint(8, 12),
                preferred_time_end=random.randint(17, 21),
                timezone="UTC",
            )
