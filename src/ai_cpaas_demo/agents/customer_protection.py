"""Customer Protection Agent for real-time sentiment and fatigue monitoring."""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from .base import (
    BaseAIAgent, 
    AgentDecision, 
    InterventionAction
)
from ..core.models import ChannelType, MessageType

logger = logging.getLogger(__name__)


class CustomerProtectionAgent(BaseAIAgent):
    """AI agent for protecting customers from communication fatigue and inappropriate messaging."""

    def __init__(self, region_name: str = "us-east-1"):
        """Initialize the Customer Protection Agent."""
        super().__init__("CustomerProtection", region_name)
        
        # Protection thresholds
        self.protection_thresholds = {
            "high_frequency_hours": 4,      # More than X messages in Y hours triggers protection
            "high_frequency_count": 3,
            "negative_sentiment_threshold": -0.6,  # Below this triggers protection
            "fatigue_score_threshold": 0.7,       # Above this triggers protection
            "support_ticket_cooldown_hours": 48,  # Hours to wait after support ticket
            "complaint_cooldown_hours": 72        # Hours to wait after complaint
        }
        
        # Intervention strategies
        self.intervention_strategies = {
            "pause_all": {
                "description": "Pause all non-critical communications",
                "duration_hours": 24,
                "severity": "high"
            },
            "pause_promotional": {
                "description": "Pause promotional messages only",
                "duration_hours": 12,
                "severity": "medium"
            },
            "reduce_frequency": {
                "description": "Reduce communication frequency by 50%",
                "duration_hours": 48,
                "severity": "medium"
            },
            "channel_switch": {
                "description": "Switch to less intrusive channel",
                "duration_hours": 6,
                "severity": "low"
            },
            "personalize_content": {
                "description": "Switch to personalized, supportive content",
                "duration_hours": 24,
                "severity": "low"
            }
        }

    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process a customer protection request."""
        logger.info(f"Processing customer protection request: {request.get('type', 'unknown')}")
        
        request_type = request.get("type", "monitor_customer")
        
        if request_type == "monitor_customer":
            return await self._monitor_customer_state(request)
        elif request_type == "assess_risk":
            return await self._assess_communication_risk(request)
        elif request_type == "recommend_intervention":
            return await self._recommend_intervention(request)
        elif request_type == "check_fatigue":
            return await self._check_customer_fatigue(request)
        elif request_type == "analyze_sentiment_trend":
            return await self._analyze_sentiment_trend(request)
        else:
            return {
                "success": False,
                "error": f"Unknown request type: {request_type}",
                "supported_types": ["monitor_customer", "assess_risk", "recommend_intervention", "check_fatigue", "analyze_sentiment_trend"]
            }

    async def make_decision(self, context: Dict[str, Any]) -> AgentDecision:
        """Make a protective decision based on customer context."""
        decision_type = context.get("decision_type", "protection_assessment")
        
        if decision_type == "protection_assessment":
            return await self._decide_protection_level(context)
        elif decision_type == "intervention_strategy":
            return await self._decide_intervention_strategy(context)
        elif decision_type == "communication_approval":
            return await self._decide_communication_approval(context)
        else:
            return AgentDecision(
                agent_type=self.agent_name,
                decision_type=decision_type,
                reasoning=["Unknown decision type, defaulting to no protection"],
                confidence=0.5,
                recommended_actions=["Review decision context"]
            )

    async def _monitor_customer_state(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Monitor real-time customer state for protection triggers."""
        try:
            customer_id = UUID(request["customer_id"])
            monitoring_window_hours = request.get("window_hours", 24)
            
            # Gather customer state data
            customer_state = await self._gather_customer_state(customer_id, monitoring_window_hours)
            
            # Analyze protection needs using AI
            protection_analysis = await self._analyze_protection_needs(customer_state)
            
            # Determine if intervention is needed
            intervention_needed = self._evaluate_intervention_need(protection_analysis)
            
            # Record monitoring decision
            decision = AgentDecision(
                agent_type=self.agent_name,
                decision_type="customer_monitoring",
                context={"customer_id": str(customer_id), "state": customer_state},
                reasoning=protection_analysis.get("reasoning", ["Routine monitoring completed"]),
                confidence=protection_analysis.get("confidence", 0.8),
                recommended_actions=protection_analysis.get("recommended_actions", ["Continue monitoring"])
            )
            self._record_decision(decision)
            
            return {
                "success": True,
                "customer_id": str(customer_id),
                "protection_status": protection_analysis.get("protection_level", "normal"),
                "intervention_needed": intervention_needed,
                "risk_factors": protection_analysis.get("risk_factors", []),
                "recommendations": protection_analysis.get("recommended_actions", []),
                "decision": decision.dict()
            }
            
        except Exception as e:
            logger.error(f"Error monitoring customer state: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback_status": "monitoring_unavailable"
            }

    async def _assess_communication_risk(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Assess the risk of sending a specific communication to a customer."""
        try:
            customer_id = UUID(request["customer_id"])
            proposed_message = request.get("proposed_message", {})
            message_type = request.get("message_type", "promotional")
            
            # Get customer context
            customer_context = await self._get_customer_context(customer_id)
            
            # Analyze risk using AI
            risk_prompt = f"""You are a customer protection AI analyzing communication risk. Assess whether this message should be sent:

Customer Context:
- Recent sentiment: {customer_context.get('sentiment', 'unknown')}
- Communication frequency (24h): {customer_context.get('frequency_24h', 0)}
- Last interaction: {customer_context.get('last_interaction', 'unknown')}
- Support tickets: {customer_context.get('open_tickets', 0)} open
- Fatigue indicators: {customer_context.get('fatigue_signals', [])}

Proposed Message:
- Type: {message_type}
- Content: {proposed_message.get('content', 'N/A')[:200]}
- Channel: {proposed_message.get('channel', 'unknown')}
- Urgency: {proposed_message.get('urgency', 'medium')}

Assess the risk and provide recommendations:

{{
    "risk_level": "low|medium|high",
    "risk_factors": ["factor1", "factor2"],
    "should_send": true/false,
    "alternative_actions": ["action1", "action2"],
    "recommended_delay_hours": 0,
    "confidence": 0.0-1.0,
    "reasoning": "detailed explanation"
}}"""

            risk_analysis = await self._analyze_with_bedrock(risk_prompt)
            
            if not risk_analysis.get("parsed", True):
                # Fallback risk assessment
                risk_analysis = self._fallback_risk_assessment(customer_context, proposed_message, message_type)
            
            return {
                "success": True,
                "customer_id": str(customer_id),
                "risk_assessment": risk_analysis,
                "protection_recommendation": "block" if risk_analysis.get("risk_level") == "high" else "allow"
            }
            
        except Exception as e:
            logger.error(f"Error assessing communication risk: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback_recommendation": "allow_with_caution"
            }

    async def _recommend_intervention(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Recommend protective intervention actions."""
        try:
            customer_id = UUID(request["customer_id"])
            risk_factors = request.get("risk_factors", [])
            severity = request.get("severity", "medium")
            
            # Select appropriate intervention strategy
            intervention_strategy = self._select_intervention_strategy(risk_factors, severity)
            
            # Create intervention action
            intervention = InterventionAction(
                action_type=intervention_strategy["type"],
                target_customer=customer_id,
                reason=f"Protection triggered by: {', '.join(risk_factors)}",
                severity=severity,
                recommended_delay=intervention_strategy["duration_hours"] * 60,
                alternative_actions=intervention_strategy.get("alternatives", [])
            )
            
            return {
                "success": True,
                "intervention": intervention.dict(),
                "strategy": intervention_strategy,
                "implementation_steps": intervention_strategy.get("steps", [])
            }
            
        except Exception as e:
            logger.error(f"Error recommending intervention: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback_intervention": "pause_promotional"
            }

    async def _check_customer_fatigue(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Check customer fatigue levels and recommend actions."""
        try:
            customer_id = UUID(request["customer_id"])
            
            # Calculate fatigue score
            fatigue_data = await self._calculate_fatigue_score(customer_id)
            
            # Determine fatigue level
            fatigue_score = fatigue_data["score"]
            if fatigue_score >= self.protection_thresholds["fatigue_score_threshold"]:
                fatigue_level = "high"
                recommendations = [
                    "Pause all non-essential communications",
                    "Reduce frequency by 75% for next 48 hours",
                    "Switch to supportive content only"
                ]
            elif fatigue_score >= 0.5:
                fatigue_level = "medium"
                recommendations = [
                    "Reduce communication frequency by 50%",
                    "Avoid promotional content for 24 hours",
                    "Focus on value-added content"
                ]
            else:
                fatigue_level = "low"
                recommendations = [
                    "Continue normal communication patterns",
                    "Monitor for changes in engagement"
                ]
            
            return {
                "success": True,
                "customer_id": str(customer_id),
                "fatigue_level": fatigue_level,
                "fatigue_score": fatigue_score,
                "indicators": fatigue_data["indicators"],
                "recommendations": recommendations
            }
            
        except Exception as e:
            logger.error(f"Error checking customer fatigue: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback_level": "unknown"
            }

    async def _analyze_sentiment_trend(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze customer sentiment trends over time."""
        try:
            customer_id = UUID(request["customer_id"])
            days_back = request.get("days_back", 30)
            
            # Get sentiment history
            sentiment_history = await self._get_sentiment_history(customer_id, days_back)
            
            # Analyze trends
            trend_analysis = self._analyze_sentiment_trends(sentiment_history)
            
            return {
                "success": True,
                "customer_id": str(customer_id),
                "trend": trend_analysis["trend"],  # "improving", "declining", "stable"
                "current_sentiment": trend_analysis["current"],
                "average_sentiment": trend_analysis["average"],
                "risk_indicators": trend_analysis["risk_indicators"],
                "recommendations": trend_analysis["recommendations"]
            }
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment trend: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback_trend": "stable"
            }

    async def _gather_customer_state(self, customer_id: UUID, window_hours: int) -> Dict[str, Any]:
        """Gather comprehensive customer state for protection analysis."""
        # In a real implementation, this would query multiple data sources
        # For now, simulate customer state data
        
        customer_hash = hash(str(customer_id))
        
        # Simulate varied customer states
        if customer_hash % 10 == 0:
            # High-risk customer
            state = {
                "sentiment_score": -0.7,
                "communication_frequency_24h": 5,
                "last_interaction_hours": 2,
                "open_support_tickets": 2,
                "recent_complaints": 1,
                "engagement_trend": "declining",
                "fatigue_indicators": ["low_open_rates", "unsubscribe_attempts", "support_escalation"]
            }
        elif customer_hash % 10 < 3:
            # Medium-risk customer
            state = {
                "sentiment_score": -0.3,
                "communication_frequency_24h": 3,
                "last_interaction_hours": 8,
                "open_support_tickets": 1,
                "recent_complaints": 0,
                "engagement_trend": "stable",
                "fatigue_indicators": ["reduced_engagement"]
            }
        else:
            # Low-risk customer
            state = {
                "sentiment_score": 0.4,
                "communication_frequency_24h": 1,
                "last_interaction_hours": 24,
                "open_support_tickets": 0,
                "recent_complaints": 0,
                "engagement_trend": "stable",
                "fatigue_indicators": []
            }
        
        return state

    async def _analyze_protection_needs(self, customer_state: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze customer state to determine protection needs."""
        protection_prompt = f"""You are a customer protection AI. Analyze this customer state and determine protection needs:

Customer State:
- Sentiment Score: {customer_state.get('sentiment_score', 0)} (-1 to 1 scale)
- Communications (24h): {customer_state.get('communication_frequency_24h', 0)}
- Last Interaction: {customer_state.get('last_interaction_hours', 24)} hours ago
- Open Support Tickets: {customer_state.get('open_support_tickets', 0)}
- Recent Complaints: {customer_state.get('recent_complaints', 0)}
- Engagement Trend: {customer_state.get('engagement_trend', 'stable')}
- Fatigue Indicators: {customer_state.get('fatigue_indicators', [])}

Determine protection level and recommendations:

{{
    "protection_level": "low|medium|high",
    "risk_factors": ["factor1", "factor2"],
    "recommended_actions": ["action1", "action2"],
    "intervention_urgency": "low|medium|high",
    "confidence": 0.0-1.0,
    "reasoning": "detailed analysis"
}}"""

        analysis = await self._analyze_with_bedrock(protection_prompt)
        
        if not analysis.get("parsed", True):
            # Fallback analysis
            analysis = self._fallback_protection_analysis(customer_state)
        
        return analysis

    def _fallback_protection_analysis(self, customer_state: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback protection analysis using rule-based logic."""
        sentiment = customer_state.get('sentiment_score', 0)
        frequency = customer_state.get('communication_frequency_24h', 0)
        support_tickets = customer_state.get('open_support_tickets', 0)
        complaints = customer_state.get('recent_complaints', 0)
        
        risk_factors = []
        protection_level = "low"
        
        if sentiment < self.protection_thresholds["negative_sentiment_threshold"]:
            risk_factors.append("negative_sentiment")
            protection_level = "high"
        
        if frequency >= self.protection_thresholds["high_frequency_count"]:
            risk_factors.append("high_communication_frequency")
            protection_level = "medium" if protection_level == "low" else "high"
        
        if support_tickets > 0:
            risk_factors.append("open_support_tickets")
            protection_level = "medium" if protection_level == "low" else "high"
        
        if complaints > 0:
            risk_factors.append("recent_complaints")
            protection_level = "high"
        
        recommended_actions = []
        if protection_level == "high":
            recommended_actions = ["pause_all_communications", "escalate_to_human_review"]
        elif protection_level == "medium":
            recommended_actions = ["pause_promotional_messages", "monitor_closely"]
        else:
            recommended_actions = ["continue_monitoring"]
        
        return {
            "protection_level": protection_level,
            "risk_factors": risk_factors,
            "recommended_actions": recommended_actions,
            "intervention_urgency": protection_level,
            "confidence": 0.7,
            "reasoning": f"Rule-based analysis identified {len(risk_factors)} risk factors"
        }

    def _evaluate_intervention_need(self, protection_analysis: Dict[str, Any]) -> bool:
        """Evaluate if intervention is needed based on protection analysis."""
        protection_level = protection_analysis.get("protection_level", "low")
        return protection_level in ["medium", "high"]

    async def _get_customer_context(self, customer_id: UUID) -> Dict[str, Any]:
        """Get customer context for risk assessment."""
        # Simulate customer context - in real implementation would query databases
        return await self._gather_customer_state(customer_id, 24)

    def _fallback_risk_assessment(self, customer_context: Dict[str, Any], proposed_message: Dict[str, Any], message_type: str) -> Dict[str, Any]:
        """Fallback risk assessment using rule-based logic."""
        risk_level = "low"
        risk_factors = []
        should_send = True
        
        # Check sentiment
        sentiment = customer_context.get('sentiment_score', 0)
        if sentiment < -0.5:
            risk_level = "high"
            risk_factors.append("negative_sentiment")
            should_send = False
        
        # Check frequency
        frequency = customer_context.get('communication_frequency_24h', 0)
        if frequency >= 3:
            risk_level = "medium" if risk_level == "low" else "high"
            risk_factors.append("high_frequency")
            if message_type == "promotional":
                should_send = False
        
        # Check support tickets
        if customer_context.get('open_support_tickets', 0) > 0:
            risk_level = "medium" if risk_level == "low" else "high"
            risk_factors.append("support_issues")
            if message_type == "promotional":
                should_send = False
        
        return {
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "should_send": should_send,
            "alternative_actions": ["delay_24_hours", "switch_to_supportive_content"] if not should_send else [],
            "recommended_delay_hours": 24 if not should_send else 0,
            "confidence": 0.8,
            "reasoning": f"Rule-based assessment found {len(risk_factors)} risk factors"
        }

    def _select_intervention_strategy(self, risk_factors: List[str], severity: str) -> Dict[str, Any]:
        """Select appropriate intervention strategy based on risk factors and severity."""
        if severity == "high" or "negative_sentiment" in risk_factors or "recent_complaints" in risk_factors:
            strategy_key = "pause_all"
        elif "high_frequency" in risk_factors or "support_issues" in risk_factors:
            strategy_key = "pause_promotional"
        elif "fatigue_indicators" in risk_factors:
            strategy_key = "reduce_frequency"
        else:
            strategy_key = "personalize_content"
        
        strategy = self.intervention_strategies[strategy_key].copy()
        strategy["type"] = strategy_key
        strategy["alternatives"] = [
            "Monitor customer response",
            "Escalate to human review if needed",
            "Adjust strategy based on feedback"
        ]
        strategy["steps"] = [
            f"Implement {strategy['description'].lower()}",
            f"Monitor for {strategy['duration_hours']} hours",
            "Reassess customer state",
            "Gradually resume normal communications"
        ]
        
        return strategy

    async def _calculate_fatigue_score(self, customer_id: UUID) -> Dict[str, Any]:
        """Calculate customer fatigue score based on multiple indicators."""
        # Simulate fatigue calculation
        customer_hash = hash(str(customer_id))
        
        # Base fatigue score
        base_score = (customer_hash % 100) / 100.0
        
        # Adjust based on simulated factors
        indicators = []
        if base_score > 0.7:
            indicators.extend(["high_frequency", "low_engagement", "unsubscribe_attempts"])
        elif base_score > 0.4:
            indicators.extend(["reduced_engagement", "delayed_responses"])
        
        return {
            "score": base_score,
            "indicators": indicators,
            "calculation_factors": {
                "communication_frequency": base_score * 0.4,
                "engagement_decline": base_score * 0.3,
                "negative_feedback": base_score * 0.3
            }
        }

    async def _get_sentiment_history(self, customer_id: UUID, days_back: int) -> List[Dict[str, Any]]:
        """Get customer sentiment history."""
        # Simulate sentiment history
        history = []
        customer_hash = hash(str(customer_id))
        
        for i in range(days_back):
            date = datetime.now() - timedelta(days=i)
            # Create varied sentiment pattern
            base_sentiment = ((customer_hash + i) % 200 - 100) / 100.0
            
            history.append({
                "date": date.isoformat(),
                "sentiment_score": base_sentiment,
                "interaction_count": (customer_hash + i) % 3,
                "source": "email" if i % 2 == 0 else "sms"
            })
        
        return history

    def _analyze_sentiment_trends(self, sentiment_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze sentiment trends from historical data."""
        if not sentiment_history:
            return {
                "trend": "stable",
                "current": 0.0,
                "average": 0.0,
                "risk_indicators": [],
                "recommendations": ["Insufficient data for trend analysis"]
            }
        
        scores = [entry["sentiment_score"] for entry in sentiment_history]
        current_sentiment = scores[0] if scores else 0.0
        average_sentiment = sum(scores) / len(scores)
        
        # Simple trend analysis
        recent_avg = sum(scores[:7]) / min(7, len(scores))  # Last 7 days
        older_avg = sum(scores[7:14]) / max(1, min(7, len(scores) - 7))  # Previous 7 days
        
        if recent_avg < older_avg - 0.2:
            trend = "declining"
            risk_indicators = ["sentiment_decline", "potential_churn_risk"]
            recommendations = ["Implement protective measures", "Consider supportive outreach"]
        elif recent_avg > older_avg + 0.2:
            trend = "improving"
            risk_indicators = []
            recommendations = ["Continue current approach", "Consider engagement opportunities"]
        else:
            trend = "stable"
            risk_indicators = []
            recommendations = ["Maintain monitoring", "Continue normal communications"]
        
        return {
            "trend": trend,
            "current": current_sentiment,
            "average": average_sentiment,
            "risk_indicators": risk_indicators,
            "recommendations": recommendations
        }

    async def _decide_protection_level(self, context: Dict[str, Any]) -> AgentDecision:
        """Decide on the appropriate protection level for a customer."""
        customer_state = context.get("customer_state", {})
        
        # Analyze protection needs
        protection_analysis = await self._analyze_protection_needs(customer_state)
        protection_level = protection_analysis.get("protection_level", "low")
        
        return AgentDecision(
            agent_type=self.agent_name,
            decision_type="protection_assessment",
            context=context,
            reasoning=protection_analysis.get("reasoning", ["Protection level assessment completed"]),
            confidence=protection_analysis.get("confidence", 0.8),
            recommended_actions=protection_analysis.get("recommended_actions", []),
            metadata={"protection_level": protection_level}
        )

    async def _decide_intervention_strategy(self, context: Dict[str, Any]) -> AgentDecision:
        """Decide on the intervention strategy."""
        risk_factors = context.get("risk_factors", [])
        severity = context.get("severity", "medium")
        
        strategy = self._select_intervention_strategy(risk_factors, severity)
        
        return AgentDecision(
            agent_type=self.agent_name,
            decision_type="intervention_strategy",
            context=context,
            reasoning=[
                f"Selected {strategy['type']} intervention",
                f"Based on {len(risk_factors)} risk factors",
                f"Severity level: {severity}"
            ],
            confidence=0.85,
            recommended_actions=strategy.get("steps", []),
            metadata={"strategy": strategy["type"], "duration_hours": strategy["duration_hours"]}
        )

    async def _decide_communication_approval(self, context: Dict[str, Any]) -> AgentDecision:
        """Decide whether to approve a communication."""
        risk_assessment = context.get("risk_assessment", {})
        should_send = risk_assessment.get("should_send", True)
        risk_level = risk_assessment.get("risk_level", "low")
        
        if should_send:
            decision = "approve"
            reasoning = ["Risk assessment indicates communication is safe to send"]
            actions = ["Proceed with sending", "Monitor customer response"]
        else:
            decision = "block"
            reasoning = [f"Risk level {risk_level} requires blocking communication"]
            actions = risk_assessment.get("alternative_actions", ["Delay and reassess"])
        
        return AgentDecision(
            agent_type=self.agent_name,
            decision_type="communication_approval",
            context=context,
            reasoning=reasoning,
            confidence=risk_assessment.get("confidence", 0.8),
            recommended_actions=actions,
            metadata={"decision": decision, "risk_level": risk_level}
        )