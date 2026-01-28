"""Base safety guardrail engine implementation."""

import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List
from uuid import UUID

from ...core.interfaces import SafetyGuardrail, GuardrailRequest, GuardrailResult
from ...core.models import MessageType

logger = logging.getLogger(__name__)


class BaseSafetyGuardrail(SafetyGuardrail):
    """Base implementation of the safety guardrail system."""

    def __init__(self):
        """Initialize the safety guardrail engine."""
        # Risk keywords that indicate negative sentiment
        self.negative_keywords = [
            'angry', 'frustrated', 'upset', 'disappointed', 'terrible', 'awful',
            'horrible', 'worst', 'hate', 'disgusted', 'furious', 'outraged',
            'complaint', 'complain', 'problem', 'issue', 'broken', 'failed',
            'error', 'bug', 'wrong', 'bad', 'poor', 'unacceptable'
        ]
        
        # Support-related keywords
        self.support_keywords = [
            'support', 'help', 'assistance', 'ticket', 'case', 'resolve',
            'fix', 'repair', 'refund', 'return', 'cancel', 'billing',
            'charge', 'payment', 'account', 'login', 'access'
        ]
        
        # Promotional message indicators
        self.promotional_keywords = [
            'sale', 'discount', 'offer', 'deal', 'promotion', 'special',
            'limited time', 'buy now', 'order now', 'save', 'percent off',
            'free shipping', 'coupon', 'promo code', 'exclusive'
        ]
        
        # Time thresholds for different risk levels
        self.risk_thresholds = {
            'high_risk_hours': 24,      # Block promotional for 24 hours after negative interaction
            'medium_risk_hours': 72,    # Caution for 72 hours after support interaction
            'support_resolution_hours': 168  # Wait 1 week after support ticket creation
        }

    async def check_safety(self, request: GuardrailRequest) -> GuardrailResult:
        """Check if a message is safe to send to a customer."""
        logger.info(f"Checking safety for customer {request.customer_id}")
        
        # Analyze customer sentiment from recent interactions
        sentiment_analysis = await self.analyze_customer_sentiment(request.customer_id)
        
        # Check for unresolved support issues
        has_support_issues = await self.check_support_issues(request.customer_id)
        
        # Analyze the proposed message
        message_analysis = self._analyze_message_content(request.proposed_message, request.message_type)
        
        # Determine risk level and approval
        risk_assessment = self._assess_risk(
            sentiment_analysis, 
            has_support_issues, 
            message_analysis,
            request.recent_interactions
        )
        
        return GuardrailResult(
            approved=risk_assessment['approved'],
            risk_level=risk_assessment['risk_level'],
            blocked_reasons=risk_assessment['blocked_reasons'],
            alternative_actions=risk_assessment['alternative_actions'],
            confidence=risk_assessment['confidence']
        )

    async def analyze_customer_sentiment(self, customer_id: UUID) -> Dict[str, Any]:
        """Analyze recent customer sentiment and interactions."""
        logger.debug(f"Analyzing sentiment for customer {customer_id}")
        
        # In base implementation, we'll simulate sentiment analysis
        # This would typically query a database of recent interactions
        
        # Simulate recent interactions analysis
        recent_interactions = self._get_simulated_interactions(customer_id)
        
        sentiment_scores = []
        negative_indicators = 0
        support_interactions = 0
        
        for interaction in recent_interactions:
            # Analyze sentiment of each interaction
            sentiment = self._analyze_text_sentiment(interaction.get('content', ''))
            sentiment_scores.append(sentiment['score'])
            
            if sentiment['sentiment'] == 'negative':
                negative_indicators += 1
            
            if interaction.get('type') == 'support':
                support_interactions += 1
        
        # Calculate overall sentiment
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.0
        
        return {
            'overall_sentiment': 'negative' if avg_sentiment < -0.3 else 'neutral' if avg_sentiment < 0.3 else 'positive',
            'sentiment_score': avg_sentiment,
            'negative_interactions': negative_indicators,
            'support_interactions': support_interactions,
            'recent_interaction_count': len(recent_interactions),
            'last_interaction_time': recent_interactions[0].get('timestamp') if recent_interactions else None
        }

    async def check_support_issues(self, customer_id: UUID) -> bool:
        """Check if customer has unresolved support issues."""
        logger.debug(f"Checking support issues for customer {customer_id}")
        
        # In base implementation, simulate support ticket check
        # This would typically query a support system database
        
        # Simulate some customers having support issues
        customer_str = str(customer_id)
        
        # Use customer ID hash to determine if they have support issues
        # This creates consistent but varied results for demo purposes
        has_issues = hash(customer_str) % 10 < 2  # ~20% of customers have support issues
        
        if has_issues:
            logger.info(f"Customer {customer_id} has unresolved support issues")
        
        return has_issues

    def _get_simulated_interactions(self, customer_id: UUID) -> List[Dict[str, Any]]:
        """Get simulated recent interactions for a customer."""
        # Simulate 3-5 recent interactions
        customer_hash = hash(str(customer_id))
        interaction_count = 3 + (customer_hash % 3)
        
        interactions = []
        base_time = datetime.now()
        
        for i in range(interaction_count):
            # Create varied interaction types and sentiments
            interaction_type = ['email', 'chat', 'support', 'purchase'][customer_hash % 4]
            
            # Generate content based on customer hash for consistency
            if (customer_hash + i) % 5 == 0:
                # Negative interaction
                content = "I'm very frustrated with this service. The product doesn't work as advertised."
                sentiment = 'negative'
            elif (customer_hash + i) % 5 == 1:
                # Support interaction
                content = "I need help with my account. Can someone assist me with billing?"
                sentiment = 'neutral'
                interaction_type = 'support'
            else:
                # Neutral/positive interaction
                content = "Thank you for the quick delivery. The product looks good."
                sentiment = 'positive'
            
            interactions.append({
                'type': interaction_type,
                'content': content,
                'sentiment': sentiment,
                'timestamp': base_time - timedelta(hours=i * 12),
                'channel': 'email'
            })
        
        return interactions

    def _analyze_text_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of text content using keyword-based approach."""
        text_lower = text.lower()
        
        # Count negative and positive indicators
        negative_count = sum(1 for keyword in self.negative_keywords if keyword in text_lower)
        
        # Simple positive keywords for balance
        positive_keywords = ['good', 'great', 'excellent', 'love', 'happy', 'satisfied', 'thank']
        positive_count = sum(1 for keyword in positive_keywords if keyword in text_lower)
        
        # Calculate sentiment score (-1 to 1)
        if negative_count > positive_count:
            sentiment = 'negative'
            score = -0.5 - (negative_count * 0.2)
        elif positive_count > negative_count:
            sentiment = 'positive'
            score = 0.5 + (positive_count * 0.2)
        else:
            sentiment = 'neutral'
            score = 0.0
        
        # Clamp score to [-1, 1]
        score = max(-1.0, min(1.0, score))
        
        return {
            'sentiment': sentiment,
            'score': score,
            'negative_indicators': negative_count,
            'positive_indicators': positive_count
        }

    def _analyze_message_content(self, message: str, message_type: MessageType) -> Dict[str, Any]:
        """Analyze the proposed message content."""
        message_lower = message.lower()
        
        # Check if message is promotional
        is_promotional = (
            message_type == MessageType.PROMOTIONAL or
            any(keyword in message_lower for keyword in self.promotional_keywords)
        )
        
        # Check message tone
        negative_tone = any(keyword in message_lower for keyword in self.negative_keywords)
        
        # Check urgency indicators
        urgency_keywords = ['urgent', 'immediate', 'asap', 'now', 'today', 'expires']
        is_urgent = any(keyword in message_lower for keyword in urgency_keywords)
        
        return {
            'is_promotional': is_promotional,
            'has_negative_tone': negative_tone,
            'is_urgent': is_urgent,
            'message_type': message_type,
            'length': len(message)
        }

    def _assess_risk(
        self, 
        sentiment_analysis: Dict[str, Any], 
        has_support_issues: bool,
        message_analysis: Dict[str, Any],
        recent_interactions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Assess the overall risk of sending the message."""
        
        blocked_reasons = []
        alternative_actions = []
        risk_level = 'low'
        approved = True
        confidence = 0.8
        
        # Check for high-risk scenarios
        if sentiment_analysis['overall_sentiment'] == 'negative' and message_analysis['is_promotional']:
            blocked_reasons.append("Customer has recent negative sentiment - promotional messages blocked")
            alternative_actions.append("Wait 24-48 hours before sending promotional content")
            alternative_actions.append("Send supportive or helpful content instead")
            risk_level = 'high'
            approved = False
            confidence = 0.9
        
        if has_support_issues and message_analysis['is_promotional']:
            blocked_reasons.append("Customer has unresolved support issues - promotional messages blocked")
            alternative_actions.append("Resolve support issues before sending promotional content")
            alternative_actions.append("Send support follow-up message instead")
            risk_level = 'high'
            approved = False
            confidence = 0.95
        
        # Check for medium-risk scenarios
        if sentiment_analysis['negative_interactions'] > 1 and not blocked_reasons:
            blocked_reasons.append("Multiple recent negative interactions detected")
            alternative_actions.append("Consider personalized outreach or customer service contact")
            risk_level = 'medium'
            confidence = 0.7
            
            # Still approve but with caution
            if message_analysis['is_promotional']:
                approved = False
                alternative_actions.append("Send non-promotional content or wait for sentiment improvement")
        
        # Check recent interaction timing
        if recent_interactions:
            last_interaction = recent_interactions[0]
            if last_interaction.get('timestamp'):
                hours_since = (datetime.now() - last_interaction['timestamp']).total_seconds() / 3600
                
                if hours_since < 2 and sentiment_analysis['overall_sentiment'] == 'negative':
                    blocked_reasons.append("Very recent negative interaction - cooling off period recommended")
                    alternative_actions.append("Wait at least 24 hours before contacting customer")
                    risk_level = 'high'
                    approved = False
                    confidence = 0.85
        
        # If no issues found, provide positive alternatives
        if approved and not blocked_reasons:
            alternative_actions.append("Message approved - proceed with sending")
            if message_analysis['is_promotional']:
                alternative_actions.append("Consider personalizing the offer based on customer preferences")
        
        return {
            'approved': approved,
            'risk_level': risk_level,
            'blocked_reasons': blocked_reasons,
            'alternative_actions': alternative_actions,
            'confidence': confidence
        }