"""Base prediction engine implementation."""

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from uuid import UUID

import numpy as np
import pandas as pd

from ...core.interfaces import PredictionEngine, PredictionRequest, PredictionResult
from ...core.models import (
    ChannelType,
    CustomerProfile,
    EngagementRecord,
    MessageType,
    UrgencyLevel,
)

logger = logging.getLogger(__name__)


class BasePredictionEngine(PredictionEngine):
    """Base implementation of the prediction engine with core algorithms."""

    def __init__(self):
        """Initialize the prediction engine."""
        self.channel_weights = {
            ChannelType.SMS: 1.0,
            ChannelType.WHATSAPP: 1.2,
            ChannelType.EMAIL: 0.8,
            ChannelType.VOICE: 0.6,
        }
        self.urgency_multipliers = {
            UrgencyLevel.LOW: 1.0,
            UrgencyLevel.MEDIUM: 1.3,
            UrgencyLevel.HIGH: 1.8,
        }
        self.message_type_preferences = {
            MessageType.PROMOTIONAL: {
                ChannelType.EMAIL: 1.2,
                ChannelType.WHATSAPP: 1.1,
                ChannelType.SMS: 0.9,
                ChannelType.VOICE: 0.3,
            },
            MessageType.TRANSACTIONAL: {
                ChannelType.SMS: 1.3,
                ChannelType.EMAIL: 1.2,
                ChannelType.WHATSAPP: 1.0,
                ChannelType.VOICE: 0.4,
            },
            MessageType.SUPPORT: {
                ChannelType.VOICE: 1.5,
                ChannelType.WHATSAPP: 1.2,
                ChannelType.EMAIL: 1.0,
                ChannelType.SMS: 0.8,
            },
        }

    async def predict_channel(self, request: PredictionRequest) -> PredictionResult:
        """Predict the optimal channel for a customer and message."""
        logger.info(f"Predicting channel for customer {request.customer_id}")
        
        # Get customer profile (this would normally come from database)
        customer_profile = await self._get_customer_profile(request.customer_id)
        
        # Analyze engagement patterns
        engagement_analysis = await self.analyze_engagement_patterns(request.customer_id)
        
        # Calculate channel scores
        channel_scores = await self.calculate_channel_scores(
            request.customer_id, request.message_type
        )
        
        # Apply urgency and content length adjustments
        adjusted_scores = self._apply_adjustments(
            channel_scores, request.urgency, request.content_length
        )
        
        # Select best channel
        best_channel = max(adjusted_scores.keys(), key=lambda k: adjusted_scores[k])
        confidence = adjusted_scores[best_channel]
        
        # Generate reasoning
        reasoning = self._generate_reasoning(
            customer_profile, engagement_analysis, adjusted_scores, best_channel
        )
        
        # Calculate cost estimate
        cost_estimate = self._calculate_cost_estimate(best_channel, request.content_length)
        
        # Calculate engagement probability
        engagement_probability = self._calculate_engagement_probability(
            customer_profile, best_channel, request.message_type
        )
        
        return PredictionResult(
            channel=best_channel,
            confidence=min(confidence, 1.0),  # Cap at 1.0
            cost_estimate=cost_estimate,
            engagement_probability=engagement_probability,
            reasoning=reasoning,
        )

    async def analyze_engagement_patterns(self, customer_id: UUID) -> Dict[str, any]:
        """Analyze customer engagement patterns across channels."""
        logger.debug(f"Analyzing engagement patterns for customer {customer_id}")
        
        customer_profile = await self._get_customer_profile(customer_id)
        
        # Calculate engagement rates by channel
        channel_engagement = {}
        for channel in ChannelType:
            channel_records = [
                record for record in customer_profile.engagement_history
                if record.channel == channel
            ]
            
            if channel_records:
                total_messages = len(channel_records)
                opened_messages = sum(1 for record in channel_records if record.opened)
                clicked_messages = sum(1 for record in channel_records if record.clicked)
                responded_messages = sum(1 for record in channel_records if record.responded)
                
                engagement_rate = opened_messages / total_messages if total_messages > 0 else 0
                click_rate = clicked_messages / total_messages if total_messages > 0 else 0
                response_rate = responded_messages / total_messages if total_messages > 0 else 0
                
                # Calculate average engagement score
                avg_engagement_score = np.mean([record.engagement_score for record in channel_records])
                
                channel_engagement[channel.value] = {
                    "total_messages": total_messages,
                    "engagement_rate": engagement_rate,
                    "click_rate": click_rate,
                    "response_rate": response_rate,
                    "avg_engagement_score": avg_engagement_score,
                    "last_engagement": max(record.timestamp for record in channel_records) if channel_records else None,
                }
            else:
                channel_engagement[channel.value] = {
                    "total_messages": 0,
                    "engagement_rate": 0.0,
                    "click_rate": 0.0,
                    "response_rate": 0.0,
                    "avg_engagement_score": 0.0,
                    "last_engagement": None,
                }
        
        # Calculate time-based patterns
        recent_cutoff = datetime.utcnow() - timedelta(days=30)
        recent_records = [
            record for record in customer_profile.engagement_history
            if record.timestamp >= recent_cutoff
        ]
        
        # Calculate preferred time patterns (simplified)
        hour_engagement = {}
        for record in recent_records:
            hour = record.timestamp.hour
            if hour not in hour_engagement:
                hour_engagement[hour] = []
            hour_engagement[hour].append(record.engagement_score)
        
        preferred_hours = []
        for hour, scores in hour_engagement.items():
            if np.mean(scores) > 0.6:  # Threshold for good engagement
                preferred_hours.append(hour)
        
        return {
            "channel_engagement": channel_engagement,
            "preferred_hours": preferred_hours,
            "total_recent_messages": len(recent_records),
            "overall_engagement_trend": self._calculate_engagement_trend(customer_profile.engagement_history),
        }

    async def calculate_channel_scores(
        self, customer_id: UUID, message_type: MessageType
    ) -> Dict[ChannelType, float]:
        """Calculate probability scores for each available channel."""
        logger.debug(f"Calculating channel scores for customer {customer_id}")
        
        customer_profile = await self._get_customer_profile(customer_id)
        engagement_analysis = await self.analyze_engagement_patterns(customer_id)
        
        scores = {}
        
        for channel in ChannelType:
            # Base score from channel weights
            base_score = self.channel_weights[channel]
            
            # Message type preference
            message_type_score = self.message_type_preferences[message_type][channel]
            
            # Historical engagement score
            channel_engagement = engagement_analysis["channel_engagement"][channel.value]
            engagement_score = (
                channel_engagement["engagement_rate"] * 0.4 +
                channel_engagement["click_rate"] * 0.3 +
                channel_engagement["response_rate"] * 0.3
            )
            
            # Customer preference score
            preference_score = 0.5  # Default
            for pref in customer_profile.channel_preferences:
                if pref.channel == channel:
                    preference_score = pref.preference_score
                    break
            
            # Recency bonus (more recent engagement gets higher score)
            recency_score = 1.0
            if channel_engagement["last_engagement"]:
                days_since_last = (datetime.utcnow() - channel_engagement["last_engagement"]).days
                recency_score = max(0.5, 1.0 - (days_since_last / 90))  # Decay over 90 days
            
            # Combine all scores
            final_score = (
                base_score * 0.2 +
                message_type_score * 0.3 +
                engagement_score * 0.25 +
                preference_score * 0.15 +
                recency_score * 0.1
            )
            
            scores[channel] = final_score
        
        return scores

    def _apply_adjustments(
        self, 
        channel_scores: Dict[ChannelType, float], 
        urgency: UrgencyLevel, 
        content_length: int
    ) -> Dict[ChannelType, float]:
        """Apply urgency and content length adjustments to channel scores."""
        adjusted_scores = channel_scores.copy()
        urgency_multiplier = self.urgency_multipliers[urgency]
        
        for channel in adjusted_scores:
            # Apply urgency multiplier
            adjusted_scores[channel] *= urgency_multiplier
            
            # Apply content length adjustments
            if channel == ChannelType.SMS and content_length > 160:
                # Penalize SMS for long content
                adjusted_scores[channel] *= 0.7
            elif channel == ChannelType.EMAIL and content_length < 50:
                # Penalize email for very short content
                adjusted_scores[channel] *= 0.8
            elif channel == ChannelType.WHATSAPP and content_length > 500:
                # Slight penalty for very long WhatsApp messages
                adjusted_scores[channel] *= 0.9
        
        return adjusted_scores

    def _generate_reasoning(
        self,
        customer_profile: CustomerProfile,
        engagement_analysis: Dict[str, any],
        channel_scores: Dict[ChannelType, float],
        selected_channel: ChannelType,
    ) -> List[str]:
        """Generate human-readable reasoning for the channel selection."""
        reasoning = []
        
        # Channel selection reasoning
        reasoning.append(f"Selected {selected_channel.value} with confidence score {channel_scores[selected_channel]:.2f}")
        
        # Engagement pattern reasoning
        channel_engagement = engagement_analysis["channel_engagement"][selected_channel.value]
        if channel_engagement["total_messages"] > 0:
            reasoning.append(
                f"Customer has {channel_engagement['engagement_rate']:.1%} engagement rate on {selected_channel.value}"
            )
        else:
            reasoning.append(f"No historical data for {selected_channel.value}, using predictive modeling")
        
        # Preference reasoning
        for pref in customer_profile.channel_preferences:
            if pref.channel == selected_channel:
                reasoning.append(f"Customer preference score for {selected_channel.value}: {pref.preference_score:.2f}")
                break
        
        # Comparative reasoning
        sorted_channels = sorted(channel_scores.items(), key=lambda x: x[1], reverse=True)
        if len(sorted_channels) > 1:
            second_best = sorted_channels[1]
            score_diff = channel_scores[selected_channel] - second_best[1]
            reasoning.append(
                f"Outperformed {second_best[0].value} by {score_diff:.2f} points"
            )
        
        return reasoning

    def _calculate_cost_estimate(self, channel: ChannelType, content_length: int) -> float:
        """Calculate estimated cost for sending message through the channel."""
        # Base costs per message (these would come from configuration)
        base_costs = {
            ChannelType.SMS: 0.0075,
            ChannelType.WHATSAPP: 0.005,
            ChannelType.EMAIL: 0.0001,
            ChannelType.VOICE: 0.013,  # per minute, assuming 1 minute average
        }
        
        base_cost = base_costs[channel]
        
        # Adjust for content length
        if channel == ChannelType.SMS and content_length > 160:
            # Multiple SMS messages
            segments = (content_length + 159) // 160
            base_cost *= segments
        
        return base_cost

    def _calculate_engagement_probability(
        self, customer_profile: CustomerProfile, channel: ChannelType, message_type: MessageType
    ) -> float:
        """Calculate probability of customer engagement."""
        # Base engagement probabilities by channel
        base_probabilities = {
            ChannelType.SMS: 0.85,
            ChannelType.WHATSAPP: 0.75,
            ChannelType.EMAIL: 0.25,
            ChannelType.VOICE: 0.15,
        }
        
        base_prob = base_probabilities[channel]
        
        # Adjust based on customer's historical engagement
        channel_records = [
            record for record in customer_profile.engagement_history
            if record.channel == channel
        ]
        
        if channel_records:
            historical_engagement = np.mean([record.engagement_score for record in channel_records])
            # Blend historical data with base probability
            adjusted_prob = (base_prob * 0.3) + (historical_engagement * 0.7)
        else:
            adjusted_prob = base_prob * 0.8  # Slight penalty for no historical data
        
        # Adjust for message type
        message_type_adjustments = {
            MessageType.TRANSACTIONAL: 1.2,  # Higher engagement for transactional
            MessageType.PROMOTIONAL: 0.8,    # Lower engagement for promotional
            MessageType.SUPPORT: 1.1,        # Slightly higher for support
        }
        
        adjusted_prob *= message_type_adjustments[message_type]
        
        return min(adjusted_prob, 1.0)  # Cap at 1.0

    def _calculate_engagement_trend(self, engagement_history: List[EngagementRecord]) -> str:
        """Calculate overall engagement trend for the customer."""
        if len(engagement_history) < 5:
            return "insufficient_data"
        
        # Sort by timestamp
        sorted_history = sorted(engagement_history, key=lambda x: x.timestamp)
        
        # Calculate trend over last 10 messages
        recent_messages = sorted_history[-10:]
        if len(recent_messages) < 5:
            return "insufficient_recent_data"
        
        # Simple trend calculation
        first_half = recent_messages[:len(recent_messages)//2]
        second_half = recent_messages[len(recent_messages)//2:]
        
        first_half_avg = np.mean([record.engagement_score for record in first_half])
        second_half_avg = np.mean([record.engagement_score for record in second_half])
        
        if second_half_avg > first_half_avg + 0.1:
            return "improving"
        elif second_half_avg < first_half_avg - 0.1:
            return "declining"
        else:
            return "stable"

    async def _get_customer_profile(self, customer_id: UUID) -> CustomerProfile:
        """Get customer profile from storage (mock implementation for now)."""
        # This would normally fetch from database
        # For now, return a mock profile for testing
        return CustomerProfile(
            external_id=f"customer-{customer_id}",
            channel_preferences=[],
            engagement_history=[],
            sentiment_history=[],
            support_tickets=[],
        )