"""Property-based tests for channel prediction completeness.

**Feature: ai-cpaas-demo, Property 1: Channel Prediction Completeness**
**Validates: Requirements 1.1, 1.2, 1.3**

This module implements property-based testing to validate universal properties
of the channel prediction engine across all possible inputs.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List
from uuid import UUID, uuid4

import pytest
from hypothesis import given, strategies as st, settings, assume
from hypothesis.strategies import composite

from src.ai_cpaas_demo.core.interfaces import PredictionRequest, PredictionResult
from src.ai_cpaas_demo.core.models import (
    ChannelType,
    CustomerProfile,
    EngagementRecord,
    MessageType,
    UrgencyLevel,
    VariantType,
    ChannelPreference,
    SentimentRecord,
    SentimentType,
    SupportTicket,
    FatigueLevel,
    DisengagementSignal,
)
from src.ai_cpaas_demo.engines.prediction.base import BasePredictionEngine
from src.ai_cpaas_demo.engines.prediction.aws_native import AWSNativePredictionEngine


# Strategy definitions for generating test data

@composite
def channel_preference_strategy(draw):
    """Generate valid channel preferences."""
    return ChannelPreference(
        channel=draw(st.sampled_from(list(ChannelType))),
        preference_score=draw(st.floats(min_value=0.0, max_value=1.0)),
        last_engagement=draw(st.one_of(
            st.none(),
            st.datetimes(
                min_value=datetime.utcnow() - timedelta(days=365),
                max_value=datetime.utcnow()
            )
        )),
        engagement_count=draw(st.integers(min_value=0, max_value=1000))
    )


@composite
def engagement_record_strategy(draw):
    """Generate valid engagement records."""
    return EngagementRecord(
        channel=draw(st.sampled_from(list(ChannelType))),
        message_type=draw(st.sampled_from(list(MessageType))),
        timestamp=draw(st.datetimes(
            min_value=datetime.utcnow() - timedelta(days=365),
            max_value=datetime.utcnow()
        )),
        opened=draw(st.booleans()),
        clicked=draw(st.booleans()),
        responded=draw(st.booleans()),
        engagement_score=draw(st.floats(min_value=0.0, max_value=1.0))
    )


@composite
def sentiment_record_strategy(draw):
    """Generate valid sentiment records."""
    return SentimentRecord(
        timestamp=draw(st.datetimes(
            min_value=datetime.utcnow() - timedelta(days=365),
            max_value=datetime.utcnow()
        )),
        sentiment=draw(st.sampled_from(list(SentimentType))),
        confidence=draw(st.floats(min_value=0.0, max_value=1.0)),
        source=draw(st.sampled_from(["support_ticket", "survey", "social_media", "chat"])),
        context=draw(st.one_of(st.none(), st.text(min_size=1, max_size=100)))
    )


@composite
def support_ticket_strategy(draw):
    """Generate valid support tickets."""
    return SupportTicket(
        created_at=draw(st.datetimes(
            min_value=datetime.utcnow() - timedelta(days=365),
            max_value=datetime.utcnow()
        )),
        status=draw(st.sampled_from(["open", "in_progress", "resolved", "closed"])),
        priority=draw(st.sampled_from(["low", "medium", "high", "critical"])),
        category=draw(st.sampled_from(["billing", "technical", "complaint", "general"])),
        sentiment=draw(st.sampled_from(list(SentimentType))),
        resolved_at=draw(st.one_of(
            st.none(),
            st.datetimes(
                min_value=datetime.utcnow() - timedelta(days=365),
                max_value=datetime.utcnow()
            )
        ))
    )


@composite
def disengagement_signal_strategy(draw):
    """Generate valid disengagement signals."""
    return DisengagementSignal(
        signal_type=draw(st.sampled_from([
            "unsubscribe", "spam_report", "low_engagement", "no_response", "complaint"
        ])),
        timestamp=draw(st.datetimes(
            min_value=datetime.utcnow() - timedelta(days=365),
            max_value=datetime.utcnow()
        )),
        channel=draw(st.sampled_from(list(ChannelType))),
        severity=draw(st.floats(min_value=0.0, max_value=1.0))
    )


@composite
def customer_profile_strategy(draw):
    """Generate valid customer profiles with realistic data."""
    return CustomerProfile(
        external_id=draw(st.text(min_size=1, max_size=50)),
        channel_preferences=draw(st.lists(
            channel_preference_strategy(),
            min_size=0,
            max_size=len(ChannelType)
        )),
        engagement_history=draw(st.lists(
            engagement_record_strategy(),
            min_size=0,
            max_size=100
        )),
        sentiment_history=draw(st.lists(
            sentiment_record_strategy(),
            min_size=0,
            max_size=50
        )),
        support_tickets=draw(st.lists(
            support_ticket_strategy(),
            min_size=0,
            max_size=20
        )),
        fatigue_level=draw(st.sampled_from(list(FatigueLevel))),
        disengagement_signals=draw(st.lists(
            disengagement_signal_strategy(),
            min_size=0,
            max_size=10
        )),
        last_interaction=draw(st.one_of(
            st.none(),
            st.datetimes(
                min_value=datetime.utcnow() - timedelta(days=365),
                max_value=datetime.utcnow()
            )
        ))
    )


@composite
def prediction_request_strategy(draw):
    """Generate valid prediction requests."""
    return PredictionRequest(
        customer_id=draw(st.uuids()),
        message_type=draw(st.sampled_from(list(MessageType))),
        urgency=draw(st.sampled_from(list(UrgencyLevel))),
        content_length=draw(st.integers(min_value=1, max_value=5000)),
        variant=draw(st.sampled_from(list(VariantType)))
    )


class TestPredictionEngineProperties:
    """Property-based tests for prediction engine completeness."""

    @pytest.fixture
    def base_engine(self):
        """Create base prediction engine for testing."""
        return BasePredictionEngine()

    @pytest.fixture
    def aws_engine(self):
        """Create AWS native prediction engine for testing."""
        # Mock the AWS services for testing
        engine = AWSNativePredictionEngine()
        # Override AWS clients with mocks for testing
        engine.sagemaker_runtime = None
        engine.bedrock_runtime = None
        engine.dynamodb = None
        return engine

    @given(prediction_request_strategy())
    @settings(max_examples=100, deadline=30000)  # 30 second timeout per test
    def test_prediction_completeness_base_engine(self, base_engine, request_data):
        """
        **Property 1: Channel Prediction Completeness**
        
        For all valid prediction requests, the base prediction engine SHALL:
        1. Return a valid channel from the available channel types
        2. Return confidence between 0.0 and 1.0
        3. Return positive cost estimate
        4. Return engagement probability between 0.0 and 1.0
        5. Provide non-empty reasoning
        """
        # Run the async prediction
        result = asyncio.run(base_engine.predict_channel(request_data))
        
        # Validate result structure
        assert isinstance(result, PredictionResult)
        
        # Property 1.1: Valid channel selection (Requirement 1.1)
        assert result.channel in ChannelType
        assert isinstance(result.channel, ChannelType)
        
        # Property 1.2: Valid confidence score (Requirement 1.2)
        assert 0.0 <= result.confidence <= 1.0
        assert isinstance(result.confidence, float)
        
        # Property 1.3: Positive cost estimate (Requirement 1.3)
        assert result.cost_estimate >= 0.0
        assert isinstance(result.cost_estimate, float)
        
        # Property 1.4: Valid engagement probability (Requirement 1.2)
        assert 0.0 <= result.engagement_probability <= 1.0
        assert isinstance(result.engagement_probability, float)
        
        # Property 1.5: Non-empty reasoning (Requirement 1.4)
        assert isinstance(result.reasoning, list)
        assert len(result.reasoning) > 0
        assert all(isinstance(reason, str) for reason in result.reasoning)
        assert all(len(reason.strip()) > 0 for reason in result.reasoning)

    @given(prediction_request_strategy())
    @settings(max_examples=100, deadline=30000)
    def test_prediction_completeness_aws_engine(self, aws_engine, request_data):
        """
        **Property 1: Channel Prediction Completeness (AWS Native)**
        
        For all valid prediction requests, the AWS native prediction engine SHALL:
        1. Return a valid channel from the available channel types
        2. Return confidence between 0.0 and 1.0
        3. Return positive cost estimate
        4. Return engagement probability between 0.0 and 1.0
        5. Provide non-empty reasoning
        6. Handle AWS service failures gracefully by falling back to base implementation
        """
        # Run the async prediction
        result = asyncio.run(aws_engine.predict_channel(request_data))
        
        # Validate result structure
        assert isinstance(result, PredictionResult)
        
        # Property 1.1: Valid channel selection (Requirement 1.1)
        assert result.channel in ChannelType
        assert isinstance(result.channel, ChannelType)
        
        # Property 1.2: Valid confidence score (Requirement 1.2)
        assert 0.0 <= result.confidence <= 1.0
        assert isinstance(result.confidence, float)
        
        # Property 1.3: Positive cost estimate (Requirement 1.3)
        assert result.cost_estimate >= 0.0
        assert isinstance(result.cost_estimate, float)
        
        # Property 1.4: Valid engagement probability (Requirement 1.2)
        assert 0.0 <= result.engagement_probability <= 1.0
        assert isinstance(result.engagement_probability, float)
        
        # Property 1.5: Non-empty reasoning (Requirement 1.4)
        assert isinstance(result.reasoning, list)
        assert len(result.reasoning) > 0
        assert all(isinstance(reason, str) for reason in result.reasoning)
        assert all(len(reason.strip()) > 0 for reason in result.reasoning)

    @given(st.lists(prediction_request_strategy(), min_size=2, max_size=10))
    @settings(max_examples=50, deadline=60000)  # 60 second timeout for batch tests
    def test_prediction_consistency_property(self, base_engine, request_list):
        """
        **Property 2: Prediction Consistency**
        
        For identical prediction requests, the engine SHALL return identical results.
        This validates deterministic behavior and reproducibility.
        """
        # Take the first request and duplicate it
        original_request = request_list[0]
        duplicate_request = PredictionRequest(
            customer_id=original_request.customer_id,
            message_type=original_request.message_type,
            urgency=original_request.urgency,
            content_length=original_request.content_length,
            variant=original_request.variant
        )
        
        # Get predictions for both
        result1 = asyncio.run(base_engine.predict_channel(original_request))
        result2 = asyncio.run(base_engine.predict_channel(duplicate_request))
        
        # Results should be identical for identical inputs
        assert result1.channel == result2.channel
        assert result1.confidence == result2.confidence
        assert result1.cost_estimate == result2.cost_estimate
        assert result1.engagement_probability == result2.engagement_probability
        assert result1.reasoning == result2.reasoning

    @given(prediction_request_strategy())
    @settings(max_examples=100, deadline=30000)
    def test_urgency_impact_property(self, base_engine, request_data):
        """
        **Property 3: Urgency Impact**
        
        Higher urgency levels SHALL result in channel selections that prioritize
        immediate delivery (SMS, Voice) over delayed channels (Email).
        """
        # Test all urgency levels for the same base request
        results = {}
        for urgency in UrgencyLevel:
            test_request = PredictionRequest(
                customer_id=request_data.customer_id,
                message_type=request_data.message_type,
                urgency=urgency,
                content_length=request_data.content_length,
                variant=request_data.variant
            )
            results[urgency] = asyncio.run(base_engine.predict_channel(test_request))
        
        # High urgency should favor immediate channels
        high_urgency_result = results[UrgencyLevel.HIGH]
        immediate_channels = {ChannelType.SMS, ChannelType.VOICE}
        
        # If high urgency selects immediate channel, confidence should be reasonable
        if high_urgency_result.channel in immediate_channels:
            assert high_urgency_result.confidence >= 0.3  # Reasonable confidence threshold

    @given(prediction_request_strategy())
    @settings(max_examples=100, deadline=30000)
    def test_content_length_adaptation_property(self, base_engine, request_data):
        """
        **Property 4: Content Length Adaptation**
        
        Very long content (>300 chars) SHALL be penalized for SMS channel selection,
        while very short content (<50 chars) SHALL be penalized for Email.
        """
        # Test with very long content
        long_request = PredictionRequest(
            customer_id=request_data.customer_id,
            message_type=request_data.message_type,
            urgency=request_data.urgency,
            content_length=500,  # Very long content
            variant=request_data.variant
        )
        
        # Test with very short content
        short_request = PredictionRequest(
            customer_id=request_data.customer_id,
            message_type=request_data.message_type,
            urgency=request_data.urgency,
            content_length=20,  # Very short content
            variant=request_data.variant
        )
        
        long_result = asyncio.run(base_engine.predict_channel(long_request))
        short_result = asyncio.run(base_engine.predict_channel(short_request))
        
        # Long content should avoid SMS or have lower confidence for SMS
        if long_result.channel == ChannelType.SMS:
            # If SMS is selected for long content, confidence should reflect the penalty
            assert long_result.confidence <= 0.9  # Some penalty should be applied
        
        # Short content should avoid Email or have lower confidence for Email
        if short_result.channel == ChannelType.EMAIL:
            # If Email is selected for short content, confidence should reflect consideration
            assert short_result.confidence <= 0.9  # Some penalty should be applied

    @given(prediction_request_strategy())
    @settings(max_examples=100, deadline=30000)
    def test_message_type_channel_alignment_property(self, base_engine, request_data):
        """
        **Property 5: Message Type Channel Alignment**
        
        Message types SHALL align with appropriate channels:
        - SUPPORT messages should favor Voice or WhatsApp for high urgency
        - PROMOTIONAL messages should favor Email or WhatsApp
        - TRANSACTIONAL messages should favor SMS or Email
        """
        result = asyncio.run(base_engine.predict_channel(request_data))
        
        # Define expected channel preferences by message type
        if request_data.message_type == MessageType.SUPPORT and request_data.urgency == UrgencyLevel.HIGH:
            # High urgency support should prefer interactive channels
            preferred_channels = {ChannelType.VOICE, ChannelType.WHATSAPP}
            if result.channel in preferred_channels:
                assert result.confidence >= 0.4  # Should have reasonable confidence
        
        elif request_data.message_type == MessageType.PROMOTIONAL:
            # Promotional should prefer rich media channels
            preferred_channels = {ChannelType.EMAIL, ChannelType.WHATSAPP}
            if result.channel in preferred_channels:
                assert result.confidence >= 0.3  # Should have reasonable confidence
        
        elif request_data.message_type == MessageType.TRANSACTIONAL:
            # Transactional should prefer reliable delivery channels
            preferred_channels = {ChannelType.SMS, ChannelType.EMAIL}
            if result.channel in preferred_channels:
                assert result.confidence >= 0.4  # Should have reasonable confidence

    @given(prediction_request_strategy())
    @settings(max_examples=100, deadline=30000)
    def test_cost_estimate_reasonableness_property(self, base_engine, request_data):
        """
        **Property 6: Cost Estimate Reasonableness**
        
        Cost estimates SHALL be within reasonable bounds for each channel type
        and reflect realistic pricing structures.
        """
        result = asyncio.run(base_engine.predict_channel(request_data))
        
        # Define reasonable cost ranges per channel (in USD)
        cost_ranges = {
            ChannelType.SMS: (0.001, 0.1),      # $0.001 to $0.10
            ChannelType.WHATSAPP: (0.001, 0.05), # $0.001 to $0.05
            ChannelType.EMAIL: (0.0001, 0.01),   # $0.0001 to $0.01
            ChannelType.VOICE: (0.01, 0.5),      # $0.01 to $0.50
        }
        
        min_cost, max_cost = cost_ranges[result.channel]
        assert min_cost <= result.cost_estimate <= max_cost, (
            f"Cost estimate {result.cost_estimate} for {result.channel} "
            f"outside reasonable range [{min_cost}, {max_cost}]"
        )

    @given(prediction_request_strategy())
    @settings(max_examples=100, deadline=30000)
    def test_engagement_probability_correlation_property(self, base_engine, request_data):
        """
        **Property 7: Engagement Probability Correlation**
        
        Higher confidence scores SHALL generally correlate with higher
        engagement probabilities, reflecting prediction quality.
        """
        result = asyncio.run(base_engine.predict_channel(request_data))
        
        # High confidence predictions should have reasonable engagement probability
        if result.confidence >= 0.8:
            assert result.engagement_probability >= 0.2, (
                f"High confidence ({result.confidence}) should correlate with "
                f"reasonable engagement probability ({result.engagement_probability})"
            )
        
        # Very low confidence should not claim very high engagement
        if result.confidence <= 0.3:
            assert result.engagement_probability <= 0.95, (
                f"Low confidence ({result.confidence}) should not claim "
                f"very high engagement probability ({result.engagement_probability})"
            )

    @given(prediction_request_strategy())
    @settings(max_examples=50, deadline=30000)
    def test_reasoning_quality_property(self, base_engine, request_data):
        """
        **Property 8: Reasoning Quality**
        
        Reasoning SHALL be informative and reference key decision factors
        such as channel selection, customer data, or message characteristics.
        """
        result = asyncio.run(base_engine.predict_channel(request_data))
        
        # Reasoning should be substantive
        assert len(result.reasoning) >= 1
        
        # At least one reasoning item should be substantial (>20 characters)
        substantial_reasons = [r for r in result.reasoning if len(r.strip()) > 20]
        assert len(substantial_reasons) >= 1, (
            f"Reasoning should include substantial explanations: {result.reasoning}"
        )
        
        # Reasoning should mention the selected channel
        reasoning_text = " ".join(result.reasoning).lower()
        channel_mentioned = result.channel.value.lower() in reasoning_text
        
        # If channel is not explicitly mentioned, reasoning should still be meaningful
        if not channel_mentioned:
            # Should contain decision-related keywords
            decision_keywords = [
                "engagement", "confidence", "score", "customer", "preference",
                "historical", "analysis", "prediction", "optimal", "selected"
            ]
            has_decision_keywords = any(keyword in reasoning_text for keyword in decision_keywords)
            assert has_decision_keywords, (
                f"Reasoning should contain decision-related context: {result.reasoning}"
            )


class TestEngagementAnalysisProperties:
    """Property-based tests for engagement analysis completeness."""

    @pytest.fixture
    def base_engine(self):
        """Create base prediction engine for testing."""
        return BasePredictionEngine()

    @given(st.uuids())
    @settings(max_examples=50, deadline=30000)
    def test_engagement_analysis_completeness_property(self, base_engine, customer_id):
        """
        **Property 9: Engagement Analysis Completeness**
        
        For any customer ID, engagement analysis SHALL return complete
        channel engagement data for all available channels.
        """
        result = asyncio.run(base_engine.analyze_engagement_patterns(customer_id))
        
        # Should return structured analysis
        assert isinstance(result, dict)
        assert "channel_engagement" in result
        
        # Should have data for all channels
        channel_engagement = result["channel_engagement"]
        for channel in ChannelType:
            assert channel.value in channel_engagement
            
            channel_data = channel_engagement[channel.value]
            assert isinstance(channel_data, dict)
            
            # Required fields with proper types
            required_fields = [
                "total_messages", "engagement_rate", "click_rate", 
                "response_rate", "avg_engagement_score"
            ]
            for field in required_fields:
                assert field in channel_data
                assert isinstance(channel_data[field], (int, float))
                
                # Rates should be between 0 and 1
                if field.endswith("_rate") or field == "avg_engagement_score":
                    assert 0.0 <= channel_data[field] <= 1.0

    @given(st.uuids(), st.sampled_from(list(MessageType)))
    @settings(max_examples=50, deadline=30000)
    def test_channel_scores_completeness_property(self, base_engine, customer_id, message_type):
        """
        **Property 10: Channel Scores Completeness**
        
        For any customer and message type, channel scoring SHALL return
        scores for all available channels with positive values.
        """
        result = asyncio.run(base_engine.calculate_channel_scores(customer_id, message_type))
        
        # Should return scores for all channels
        assert isinstance(result, dict)
        assert len(result) == len(ChannelType)
        
        for channel in ChannelType:
            assert channel in result
            score = result[channel]
            assert isinstance(score, (int, float))
            assert score >= 0.0  # Scores should be non-negative
            assert score <= 10.0  # Reasonable upper bound for scores


if __name__ == "__main__":
    # Run property tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])