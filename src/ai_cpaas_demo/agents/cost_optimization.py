"""Cost Optimization Agent for continuous channel and budget optimization."""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from .base import (
    BaseAIAgent, 
    AgentDecision, 
    OptimizationRecommendation
)
from ..core.models import ChannelType, MessageType

logger = logging.getLogger(__name__)


class CostOptimizationAgent(BaseAIAgent):
    """AI agent for optimizing communication costs and ROI."""

    def __init__(self, region_name: str = "us-east-1"):
        """Initialize the Cost Optimization Agent."""
        super().__init__("CostOptimization", region_name)
        
        # Channel cost structure (per message in USD)
        self.channel_costs = {
            ChannelType.SMS: 0.0075,      # $0.0075 per SMS
            ChannelType.WHATSAPP: 0.005,  # $0.005 per WhatsApp message
            ChannelType.EMAIL: 0.0001,    # $0.0001 per email
            ChannelType.VOICE: 0.15       # $0.15 per voice call (per minute)
        }
        
        # Expected engagement rates by channel (for ROI calculation)
        self.baseline_engagement_rates = {
            ChannelType.SMS: 0.45,        # 45% open rate
            ChannelType.WHATSAPP: 0.70,   # 70% open rate
            ChannelType.EMAIL: 0.25,      # 25% open rate
            ChannelType.VOICE: 0.85       # 85% answer rate
        }
        
        # Conversion rates by channel
        self.baseline_conversion_rates = {
            ChannelType.SMS: 0.08,        # 8% conversion rate
            ChannelType.WHATSAPP: 0.12,   # 12% conversion rate
            ChannelType.EMAIL: 0.05,      # 5% conversion rate
            ChannelType.VOICE: 0.25       # 25% conversion rate
        }
        
        # Optimization strategies
        self.optimization_strategies = {
            "channel_switching": {
                "description": "Switch to more cost-effective channels",
                "potential_savings": 0.30,  # 30% cost reduction
                "implementation_complexity": "low"
            },
            "timing_optimization": {
                "description": "Optimize send times for better engagement",
                "potential_savings": 0.15,  # 15% improvement in ROI
                "implementation_complexity": "medium"
            },
            "frequency_optimization": {
                "description": "Optimize message frequency to reduce waste",
                "potential_savings": 0.25,  # 25% cost reduction
                "implementation_complexity": "medium"
            },
            "audience_segmentation": {
                "description": "Better targeting to reduce wasted sends",
                "potential_savings": 0.40,  # 40% cost reduction
                "implementation_complexity": "high"
            },
            "content_optimization": {
                "description": "Optimize content for better conversion",
                "potential_savings": 0.20,  # 20% ROI improvement
                "implementation_complexity": "medium"
            }
        }

    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process a cost optimization request."""
        logger.info(f"Processing cost optimization request: {request.get('type', 'unknown')}")
        
        request_type = request.get("type", "analyze_costs")
        
        if request_type == "analyze_costs":
            return await self._analyze_current_costs(request)
        elif request_type == "optimize_campaign":
            return await self._optimize_campaign_costs(request)
        elif request_type == "predict_roi":
            return await self._predict_campaign_roi(request)
        elif request_type == "recommend_channels":
            return await self._recommend_optimal_channels(request)
        elif request_type == "budget_allocation":
            return await self._optimize_budget_allocation(request)
        elif request_type == "performance_analysis":
            return await self._analyze_performance_metrics(request)
        else:
            return {
                "success": False,
                "error": f"Unknown request type: {request_type}",
                "supported_types": ["analyze_costs", "optimize_campaign", "predict_roi", "recommend_channels", "budget_allocation", "performance_analysis"]
            }

    async def make_decision(self, context: Dict[str, Any]) -> AgentDecision:
        """Make a cost optimization decision."""
        decision_type = context.get("decision_type", "cost_optimization")
        
        if decision_type == "cost_optimization":
            return await self._decide_optimization_strategy(context)
        elif decision_type == "channel_selection":
            return await self._decide_optimal_channels(context)
        elif decision_type == "budget_reallocation":
            return await self._decide_budget_reallocation(context)
        else:
            return AgentDecision(
                agent_type=self.agent_name,
                decision_type=decision_type,
                reasoning=["Unknown decision type, using default optimization"],
                confidence=0.5,
                recommended_actions=["Review decision context"]
            )

    async def _analyze_current_costs(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze current communication costs and identify optimization opportunities."""
        try:
            time_period_days = request.get("time_period_days", 30)
            campaign_data = request.get("campaign_data", {})
            
            # Get current spending data
            current_costs = await self._calculate_current_costs(campaign_data, time_period_days)
            
            # Analyze optimization opportunities using AI
            optimization_analysis = await self._analyze_optimization_opportunities(current_costs, campaign_data)
            
            # Calculate potential savings
            potential_savings = self._calculate_potential_savings(current_costs, optimization_analysis)
            
            # Record analysis decision
            decision = AgentDecision(
                agent_type=self.agent_name,
                decision_type="cost_analysis",
                context={"period_days": time_period_days, "total_cost": current_costs["total"]},
                reasoning=optimization_analysis.get("reasoning", ["Cost analysis completed"]),
                confidence=optimization_analysis.get("confidence", 0.8),
                recommended_actions=optimization_analysis.get("recommended_actions", [])
            )
            self._record_decision(decision)
            
            return {
                "success": True,
                "current_costs": current_costs,
                "optimization_opportunities": optimization_analysis.get("opportunities", []),
                "potential_savings": potential_savings,
                "recommendations": optimization_analysis.get("recommended_actions", []),
                "decision": decision.dict()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing current costs: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback_analysis": "Cost analysis unavailable"
            }

    async def _optimize_campaign_costs(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize costs for a specific campaign."""
        try:
            campaign_id = request.get("campaign_id")
            campaign_config = request.get("campaign_config", {})
            target_savings = request.get("target_savings_percent", 20)
            
            # Analyze current campaign costs
            current_campaign_cost = self._calculate_campaign_cost(campaign_config)
            
            # Generate optimization recommendations using AI
            optimization_prompt = f"""You are a cost optimization expert analyzing a marketing campaign. Optimize this campaign to achieve {target_savings}% cost savings while maintaining effectiveness:

Current Campaign Configuration:
- Target Audience Size: {campaign_config.get('audience_size', 1000)}
- Channels: {campaign_config.get('channels', [])}
- Message Types: {campaign_config.get('message_types', [])}
- Frequency: {campaign_config.get('frequency_per_week', 2)} messages/week
- Duration: {campaign_config.get('duration_weeks', 4)} weeks
- Current Estimated Cost: ${current_campaign_cost:.2f}

Channel Costs: {dict((ch.value, cost) for ch, cost in self.channel_costs.items())}
Engagement Rates: {dict((ch.value, rate) for ch, rate in self.baseline_engagement_rates.items())}

Provide optimization recommendations:

{{
    "optimized_config": {{
        "channels": ["recommended channels"],
        "frequency_per_week": 1.5,
        "audience_segments": ["segment1", "segment2"],
        "timing_optimization": "optimal send times"
    }},
    "cost_breakdown": {{
        "original_cost": {current_campaign_cost},
        "optimized_cost": 800.0,
        "savings_amount": 200.0,
        "savings_percent": 20.0
    }},
    "optimization_strategies": ["strategy1", "strategy2"],
    "expected_performance": {{
        "engagement_rate": 0.35,
        "conversion_rate": 0.08,
        "roi_improvement": 0.15
    }},
    "implementation_steps": ["step1", "step2"],
    "risk_assessment": "low|medium|high"
}}"""

            optimization_result = await self._analyze_with_bedrock(optimization_prompt)
            
            if not optimization_result.get("parsed", True):
                # Fallback optimization
                optimization_result = self._fallback_campaign_optimization(campaign_config, target_savings)
            
            return {
                "success": True,
                "campaign_id": campaign_id,
                "original_cost": current_campaign_cost,
                "optimization_result": optimization_result,
                "implementation_priority": "high" if optimization_result.get("cost_breakdown", {}).get("savings_percent", 0) > 25 else "medium"
            }
            
        except Exception as e:
            logger.error(f"Error optimizing campaign costs: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback_optimization": "Basic cost reduction strategies available"
            }

    async def _predict_campaign_roi(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Predict ROI for a campaign configuration."""
        try:
            campaign_config = request.get("campaign_config", {})
            revenue_per_conversion = request.get("revenue_per_conversion", 50.0)
            
            # Calculate campaign costs
            total_cost = self._calculate_campaign_cost(campaign_config)
            
            # Predict engagement and conversions
            roi_prediction = self._predict_roi_metrics(campaign_config, revenue_per_conversion, total_cost)
            
            # Generate ROI analysis using AI
            roi_analysis_prompt = f"""You are an ROI prediction expert. Analyze this campaign's expected performance:

Campaign Configuration:
- Audience Size: {campaign_config.get('audience_size', 1000)}
- Channels: {campaign_config.get('channels', [])}
- Total Cost: ${total_cost:.2f}
- Revenue per Conversion: ${revenue_per_conversion:.2f}

Predicted Metrics:
- Expected Conversions: {roi_prediction['expected_conversions']}
- Expected Revenue: ${roi_prediction['expected_revenue']:.2f}
- Predicted ROI: {roi_prediction['roi_percent']:.1f}%

Provide detailed ROI analysis and recommendations:

{{
    "roi_assessment": "excellent|good|fair|poor",
    "confidence_level": 0.8,
    "key_drivers": ["driver1", "driver2"],
    "risk_factors": ["risk1", "risk2"],
    "optimization_suggestions": ["suggestion1", "suggestion2"],
    "benchmark_comparison": "above|at|below industry average",
    "break_even_analysis": {{
        "break_even_conversions": 20,
        "break_even_timeline_days": 14
    }}
}}"""

            roi_analysis = await self._analyze_with_bedrock(roi_analysis_prompt)
            
            if not roi_analysis.get("parsed", True):
                roi_analysis = self._fallback_roi_analysis(roi_prediction)
            
            return {
                "success": True,
                "roi_prediction": roi_prediction,
                "detailed_analysis": roi_analysis,
                "recommendation": "proceed" if roi_prediction["roi_percent"] > 100 else "optimize_first"
            }
            
        except Exception as e:
            logger.error(f"Error predicting campaign ROI: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback_roi": "ROI prediction unavailable"
            }

    async def _recommend_optimal_channels(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Recommend optimal channels based on cost-effectiveness."""
        try:
            audience_profile = request.get("audience_profile", {})
            budget_constraint = request.get("budget_constraint", 1000.0)
            campaign_objectives = request.get("objectives", ["engagement"])
            
            # Calculate cost-effectiveness for each channel
            channel_analysis = self._analyze_channel_cost_effectiveness(audience_profile, campaign_objectives)
            
            # Select optimal channel mix
            optimal_channels = self._select_optimal_channel_mix(channel_analysis, budget_constraint)
            
            return {
                "success": True,
                "channel_analysis": channel_analysis,
                "recommended_channels": optimal_channels,
                "expected_performance": {
                    "total_cost": sum(ch["allocated_budget"] for ch in optimal_channels),
                    "expected_reach": sum(ch["expected_reach"] for ch in optimal_channels),
                    "weighted_engagement_rate": sum(ch["engagement_rate"] * ch["weight"] for ch in optimal_channels)
                }
            }
            
        except Exception as e:
            logger.error(f"Error recommending optimal channels: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback_channels": ["email", "sms"]
            }

    async def _optimize_budget_allocation(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize budget allocation across channels and campaigns."""
        try:
            total_budget = request.get("total_budget", 10000.0)
            campaigns = request.get("campaigns", [])
            constraints = request.get("constraints", {})
            
            # Analyze current allocation
            current_allocation = self._analyze_current_allocation(campaigns, total_budget)
            
            # Optimize allocation using AI
            optimization_prompt = f"""You are a budget optimization expert. Optimize the allocation of ${total_budget} across these campaigns:

Current Campaigns:
{json.dumps(campaigns, indent=2)}

Current Allocation:
{json.dumps(current_allocation, indent=2)}

Constraints:
{json.dumps(constraints, indent=2)}

Optimize for maximum ROI while respecting constraints:

{{
    "optimized_allocation": {{
        "campaign_1": {{
            "budget": 3000.0,
            "channels": {{"email": 1500, "sms": 1500}},
            "expected_roi": 150.0
        }}
    }},
    "total_expected_roi": 180.0,
    "improvement_over_current": 25.0,
    "reallocation_rationale": ["reason1", "reason2"],
    "implementation_priority": "high|medium|low"
}}"""

            optimization_result = await self._analyze_with_bedrock(optimization_prompt)
            
            if not optimization_result.get("parsed", True):
                optimization_result = self._fallback_budget_optimization(campaigns, total_budget)
            
            return {
                "success": True,
                "current_allocation": current_allocation,
                "optimized_allocation": optimization_result,
                "implementation_steps": [
                    "Review optimized allocation with stakeholders",
                    "Implement budget reallocation gradually",
                    "Monitor performance and adjust as needed"
                ]
            }
            
        except Exception as e:
            logger.error(f"Error optimizing budget allocation: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback_allocation": "Equal distribution recommended"
            }

    def _calculate_current_costs(self, campaign_data: Dict[str, Any], time_period_days: int) -> Dict[str, Any]:
        """Calculate current communication costs."""
        # Simulate cost calculation based on campaign data
        total_messages = campaign_data.get("total_messages", 10000)
        channel_distribution = campaign_data.get("channel_distribution", {
            "email": 0.6,
            "sms": 0.3,
            "whatsapp": 0.1
        })
        
        costs_by_channel = {}
        total_cost = 0
        
        for channel_name, percentage in channel_distribution.items():
            try:
                channel = ChannelType(channel_name)
                messages_for_channel = int(total_messages * percentage)
                cost_per_message = self.channel_costs[channel]
                channel_cost = messages_for_channel * cost_per_message
                
                costs_by_channel[channel_name] = {
                    "messages": messages_for_channel,
                    "cost_per_message": cost_per_message,
                    "total_cost": channel_cost
                }
                total_cost += channel_cost
            except ValueError:
                # Skip unknown channels
                continue
        
        return {
            "total": total_cost,
            "by_channel": costs_by_channel,
            "period_days": time_period_days,
            "daily_average": total_cost / time_period_days,
            "cost_per_message": total_cost / total_messages if total_messages > 0 else 0
        }

    async def _analyze_optimization_opportunities(self, current_costs: Dict[str, Any], campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze optimization opportunities using AI."""
        optimization_prompt = f"""You are a cost optimization expert analyzing communication spending. Identify optimization opportunities:

Current Costs:
- Total: ${current_costs['total']:.2f}
- Daily Average: ${current_costs['daily_average']:.2f}
- Cost per Message: ${current_costs['cost_per_message']:.4f}

Channel Breakdown:
{json.dumps(current_costs['by_channel'], indent=2)}

Campaign Data:
{json.dumps(campaign_data, indent=2)}

Identify optimization opportunities:

{{
    "opportunities": [
        {{
            "type": "channel_optimization",
            "description": "Switch high-volume sends to email",
            "potential_savings": 500.0,
            "implementation_effort": "low"
        }}
    ],
    "recommended_actions": ["action1", "action2"],
    "priority_optimizations": ["optimization1", "optimization2"],
    "confidence": 0.8,
    "reasoning": "detailed analysis"
}}"""

        analysis = await self._analyze_with_bedrock(optimization_prompt)
        
        if not analysis.get("parsed", True):
            # Fallback analysis
            analysis = self._fallback_optimization_analysis(current_costs)
        
        return analysis

    def _fallback_optimization_analysis(self, current_costs: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback optimization analysis using rule-based logic."""
        opportunities = []
        recommended_actions = []
        
        # Check for expensive channel usage
        by_channel = current_costs.get("by_channel", {})
        
        if "voice" in by_channel and by_channel["voice"]["total_cost"] > 100:
            opportunities.append({
                "type": "channel_substitution",
                "description": "Replace some voice calls with SMS or email",
                "potential_savings": by_channel["voice"]["total_cost"] * 0.7,
                "implementation_effort": "medium"
            })
            recommended_actions.append("Evaluate voice call necessity")
        
        if "sms" in by_channel and by_channel["sms"]["messages"] > 1000:
            opportunities.append({
                "type": "channel_optimization",
                "description": "Move non-urgent SMS to email",
                "potential_savings": by_channel["sms"]["total_cost"] * 0.4,
                "implementation_effort": "low"
            })
            recommended_actions.append("Segment SMS usage by urgency")
        
        # Check overall cost efficiency
        cost_per_message = current_costs.get("cost_per_message", 0)
        if cost_per_message > 0.01:  # Above $0.01 per message
            opportunities.append({
                "type": "frequency_optimization",
                "description": "Optimize message frequency to reduce waste",
                "potential_savings": current_costs["total"] * 0.2,
                "implementation_effort": "medium"
            })
            recommended_actions.append("Analyze message frequency patterns")
        
        return {
            "opportunities": opportunities,
            "recommended_actions": recommended_actions,
            "priority_optimizations": [opp["type"] for opp in opportunities[:2]],
            "confidence": 0.7,
            "reasoning": "Rule-based analysis of cost patterns"
        }

    def _calculate_potential_savings(self, current_costs: Dict[str, Any], optimization_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate potential savings from optimization opportunities."""
        opportunities = optimization_analysis.get("opportunities", [])
        
        total_potential_savings = sum(opp.get("potential_savings", 0) for opp in opportunities)
        current_total = current_costs.get("total", 0)
        
        savings_percentage = (total_potential_savings / current_total * 100) if current_total > 0 else 0
        
        return {
            "total_potential_savings": total_potential_savings,
            "savings_percentage": savings_percentage,
            "by_opportunity": [
                {
                    "type": opp.get("type", "unknown"),
                    "savings": opp.get("potential_savings", 0),
                    "percentage": (opp.get("potential_savings", 0) / current_total * 100) if current_total > 0 else 0
                }
                for opp in opportunities
            ],
            "implementation_timeline": "2-4 weeks for full optimization"
        }

    def _calculate_campaign_cost(self, campaign_config: Dict[str, Any]) -> float:
        """Calculate the total cost of a campaign configuration."""
        audience_size = campaign_config.get("audience_size", 1000)
        channels = campaign_config.get("channels", ["email"])
        frequency_per_week = campaign_config.get("frequency_per_week", 1)
        duration_weeks = campaign_config.get("duration_weeks", 4)
        
        total_messages = audience_size * frequency_per_week * duration_weeks
        
        # Distribute messages across channels (equal distribution if not specified)
        channel_distribution = campaign_config.get("channel_distribution", {})
        if not channel_distribution:
            # Equal distribution
            distribution_per_channel = 1.0 / len(channels)
            channel_distribution = {ch: distribution_per_channel for ch in channels}
        
        total_cost = 0
        for channel_name, percentage in channel_distribution.items():
            try:
                channel = ChannelType(channel_name)
                messages_for_channel = int(total_messages * percentage)
                cost_per_message = self.channel_costs[channel]
                total_cost += messages_for_channel * cost_per_message
            except (ValueError, KeyError):
                # Skip unknown channels or use default cost
                total_cost += int(total_messages * percentage) * 0.001  # Default $0.001 per message
        
        return total_cost

    def _predict_roi_metrics(self, campaign_config: Dict[str, Any], revenue_per_conversion: float, total_cost: float) -> Dict[str, Any]:
        """Predict ROI metrics for a campaign."""
        audience_size = campaign_config.get("audience_size", 1000)
        channels = campaign_config.get("channels", ["email"])
        
        # Calculate weighted engagement and conversion rates
        channel_weights = {}
        total_weight = 0
        for channel_name in channels:
            try:
                channel = ChannelType(channel_name)
                weight = 1.0 / len(channels)  # Equal weight for simplicity
                channel_weights[channel] = weight
                total_weight += weight
            except ValueError:
                continue
        
        # Normalize weights
        for channel in channel_weights:
            channel_weights[channel] /= total_weight
        
        # Calculate weighted rates
        weighted_engagement_rate = sum(
            self.baseline_engagement_rates[channel] * weight
            for channel, weight in channel_weights.items()
        )
        
        weighted_conversion_rate = sum(
            self.baseline_conversion_rates[channel] * weight
            for channel, weight in channel_weights.items()
        )
        
        # Calculate predictions
        expected_engagements = audience_size * weighted_engagement_rate
        expected_conversions = expected_engagements * weighted_conversion_rate
        expected_revenue = expected_conversions * revenue_per_conversion
        
        roi_amount = expected_revenue - total_cost
        roi_percent = (roi_amount / total_cost * 100) if total_cost > 0 else 0
        
        return {
            "expected_engagements": int(expected_engagements),
            "expected_conversions": int(expected_conversions),
            "expected_revenue": expected_revenue,
            "total_cost": total_cost,
            "roi_amount": roi_amount,
            "roi_percent": roi_percent,
            "engagement_rate": weighted_engagement_rate,
            "conversion_rate": weighted_conversion_rate
        }

    def _fallback_roi_analysis(self, roi_prediction: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback ROI analysis using rule-based logic."""
        roi_percent = roi_prediction.get("roi_percent", 0)
        
        if roi_percent > 200:
            assessment = "excellent"
            benchmark = "above"
        elif roi_percent > 100:
            assessment = "good"
            benchmark = "above"
        elif roi_percent > 50:
            assessment = "fair"
            benchmark = "at"
        else:
            assessment = "poor"
            benchmark = "below"
        
        return {
            "roi_assessment": assessment,
            "confidence_level": 0.7,
            "key_drivers": ["channel_selection", "audience_targeting"],
            "risk_factors": ["market_conditions", "competition"],
            "optimization_suggestions": [
                "Consider higher-converting channels",
                "Improve audience targeting",
                "Test different content approaches"
            ],
            "benchmark_comparison": f"{benchmark} industry average",
            "break_even_analysis": {
                "break_even_conversions": max(1, int(roi_prediction.get("total_cost", 0) / 50)),
                "break_even_timeline_days": 14
            }
        }

    def _analyze_channel_cost_effectiveness(self, audience_profile: Dict[str, Any], objectives: List[str]) -> Dict[str, Any]:
        """Analyze cost-effectiveness of each channel."""
        channel_analysis = {}
        
        for channel, cost_per_message in self.channel_costs.items():
            engagement_rate = self.baseline_engagement_rates[channel]
            conversion_rate = self.baseline_conversion_rates[channel]
            
            # Adjust rates based on audience profile
            if audience_profile.get("age_group") == "young" and channel == ChannelType.WHATSAPP:
                engagement_rate *= 1.2  # Young people prefer WhatsApp
            elif audience_profile.get("age_group") == "senior" and channel == ChannelType.EMAIL:
                engagement_rate *= 1.1  # Seniors prefer email
            
            # Calculate cost per engagement and conversion
            cost_per_engagement = cost_per_message / engagement_rate if engagement_rate > 0 else float('inf')
            cost_per_conversion = cost_per_engagement / conversion_rate if conversion_rate > 0 else float('inf')
            
            # Score based on objectives
            effectiveness_score = 0
            if "engagement" in objectives:
                effectiveness_score += (1 / cost_per_engagement) * 100
            if "conversion" in objectives:
                effectiveness_score += (1 / cost_per_conversion) * 100
            if "reach" in objectives:
                effectiveness_score += engagement_rate * 100
            
            channel_analysis[channel.value] = {
                "cost_per_message": cost_per_message,
                "engagement_rate": engagement_rate,
                "conversion_rate": conversion_rate,
                "cost_per_engagement": cost_per_engagement,
                "cost_per_conversion": cost_per_conversion,
                "effectiveness_score": effectiveness_score
            }
        
        return channel_analysis

    def _select_optimal_channel_mix(self, channel_analysis: Dict[str, Any], budget_constraint: float) -> List[Dict[str, Any]]:
        """Select optimal mix of channels within budget constraint."""
        # Sort channels by effectiveness score
        sorted_channels = sorted(
            channel_analysis.items(),
            key=lambda x: x[1]["effectiveness_score"],
            reverse=True
        )
        
        optimal_channels = []
        remaining_budget = budget_constraint
        
        for channel_name, analysis in sorted_channels[:3]:  # Top 3 channels
            # Allocate budget proportionally to effectiveness
            if len(optimal_channels) == 0:
                allocation_percentage = 0.5  # 50% to best channel
            elif len(optimal_channels) == 1:
                allocation_percentage = 0.3  # 30% to second best
            else:
                allocation_percentage = 0.2  # 20% to third best
            
            allocated_budget = budget_constraint * allocation_percentage
            cost_per_message = analysis["cost_per_message"]
            expected_messages = int(allocated_budget / cost_per_message) if cost_per_message > 0 else 0
            expected_reach = int(expected_messages * analysis["engagement_rate"])
            
            optimal_channels.append({
                "channel": channel_name,
                "allocated_budget": allocated_budget,
                "expected_messages": expected_messages,
                "expected_reach": expected_reach,
                "engagement_rate": analysis["engagement_rate"],
                "weight": allocation_percentage
            })
        
        return optimal_channels

    def _analyze_current_allocation(self, campaigns: List[Dict[str, Any]], total_budget: float) -> Dict[str, Any]:
        """Analyze current budget allocation."""
        current_allocation = {}
        total_allocated = 0
        
        for i, campaign in enumerate(campaigns):
            campaign_id = campaign.get("id", f"campaign_{i}")
            budget = campaign.get("budget", total_budget / len(campaigns))
            
            current_allocation[campaign_id] = {
                "budget": budget,
                "channels": campaign.get("channels", {}),
                "expected_roi": campaign.get("expected_roi", 100.0)
            }
            total_allocated += budget
        
        return {
            "campaigns": current_allocation,
            "total_allocated": total_allocated,
            "unallocated": total_budget - total_allocated,
            "average_expected_roi": sum(camp["expected_roi"] for camp in current_allocation.values()) / len(current_allocation) if current_allocation else 0
        }

    def _fallback_budget_optimization(self, campaigns: List[Dict[str, Any]], total_budget: float) -> Dict[str, Any]:
        """Fallback budget optimization using rule-based logic."""
        # Simple optimization: allocate more budget to higher ROI campaigns
        campaign_rois = []
        for i, campaign in enumerate(campaigns):
            campaign_id = campaign.get("id", f"campaign_{i}")
            expected_roi = campaign.get("expected_roi", 100.0)
            campaign_rois.append((campaign_id, expected_roi))
        
        # Sort by ROI
        campaign_rois.sort(key=lambda x: x[1], reverse=True)
        
        # Allocate budget proportionally to ROI
        total_roi = sum(roi for _, roi in campaign_rois)
        optimized_allocation = {}
        
        for campaign_id, roi in campaign_rois:
            if total_roi > 0:
                allocation_percentage = roi / total_roi
                budget = total_budget * allocation_percentage
            else:
                budget = total_budget / len(campaigns)
            
            optimized_allocation[campaign_id] = {
                "budget": budget,
                "channels": {"email": budget * 0.6, "sms": budget * 0.4},
                "expected_roi": roi
            }
        
        return {
            "optimized_allocation": optimized_allocation,
            "total_expected_roi": sum(camp["expected_roi"] for camp in optimized_allocation.values()) / len(optimized_allocation) if optimized_allocation else 0,
            "improvement_over_current": 15.0,  # Assume 15% improvement
            "reallocation_rationale": ["Allocate more budget to higher ROI campaigns"],
            "implementation_priority": "medium"
        }

    def _fallback_campaign_optimization(self, campaign_config: Dict[str, Any], target_savings: float) -> Dict[str, Any]:
        """Fallback campaign optimization using rule-based logic."""
        current_cost = self._calculate_campaign_cost(campaign_config)
        target_cost = current_cost * (1 - target_savings / 100)
        
        # Simple optimization: switch expensive channels to cheaper ones
        optimized_channels = []
        current_channels = campaign_config.get("channels", ["email"])
        
        for channel in current_channels:
            if channel == "voice":
                optimized_channels.append("sms")  # Replace voice with SMS
            elif channel == "sms" and len(current_channels) > 1:
                optimized_channels.append("email")  # Replace some SMS with email
            else:
                optimized_channels.append(channel)
        
        return {
            "optimized_config": {
                "channels": optimized_channels,
                "frequency_per_week": campaign_config.get("frequency_per_week", 2) * 0.8,  # Reduce frequency by 20%
                "audience_segments": ["high_engagement", "medium_engagement"],
                "timing_optimization": "peak_hours_only"
            },
            "cost_breakdown": {
                "original_cost": current_cost,
                "optimized_cost": target_cost,
                "savings_amount": current_cost - target_cost,
                "savings_percent": target_savings
            },
            "optimization_strategies": ["channel_substitution", "frequency_reduction"],
            "expected_performance": {
                "engagement_rate": 0.35,
                "conversion_rate": 0.08,
                "roi_improvement": 0.10
            },
            "implementation_steps": [
                "Update channel configuration",
                "Adjust message frequency",
                "Implement audience segmentation"
            ],
            "risk_assessment": "low"
        }

    async def _decide_optimization_strategy(self, context: Dict[str, Any]) -> AgentDecision:
        """Decide on the optimal cost optimization strategy."""
        current_costs = context.get("current_costs", {})
        budget_constraints = context.get("budget_constraints", {})
        performance_goals = context.get("performance_goals", {})
        
        # Analyze the situation
        total_cost = current_costs.get("total", 0)
        cost_per_message = current_costs.get("cost_per_message", 0)
        
        # Determine strategy based on cost analysis
        if cost_per_message > 0.01:
            strategy = "channel_optimization"
            reasoning = ["High cost per message indicates need for channel optimization"]
            actions = ["Switch to more cost-effective channels", "Analyze channel performance"]
        elif total_cost > budget_constraints.get("monthly_limit", 5000):
            strategy = "frequency_optimization"
            reasoning = ["Total costs exceed budget constraints"]
            actions = ["Reduce message frequency", "Improve targeting precision"]
        else:
            strategy = "performance_optimization"
            reasoning = ["Costs are reasonable, focus on improving ROI"]
            actions = ["Optimize content for better conversion", "Test different timing strategies"]
        
        return AgentDecision(
            agent_type=self.agent_name,
            decision_type="cost_optimization",
            context=context,
            reasoning=reasoning,
            confidence=0.8,
            recommended_actions=actions,
            metadata={"selected_strategy": strategy}
        )

    async def _decide_optimal_channels(self, context: Dict[str, Any]) -> AgentDecision:
        """Decide on optimal channel selection."""
        budget = context.get("budget", 1000)
        objectives = context.get("objectives", ["engagement"])
        audience_profile = context.get("audience_profile", {})
        
        # Simple channel selection logic
        if budget < 500:
            recommended_channels = ["email"]
            reasoning = ["Low budget requires most cost-effective channel"]
        elif "conversion" in objectives:
            recommended_channels = ["email", "sms"]
            reasoning = ["Conversion focus requires multi-channel approach"]
        else:
            recommended_channels = ["email", "whatsapp"]
            reasoning = ["Balanced approach for engagement and cost-effectiveness"]
        
        return AgentDecision(
            agent_type=self.agent_name,
            decision_type="channel_selection",
            context=context,
            reasoning=reasoning,
            confidence=0.75,
            recommended_actions=[f"Implement {', '.join(recommended_channels)} channel strategy"],
            metadata={"recommended_channels": recommended_channels}
        )

    async def _decide_budget_reallocation(self, context: Dict[str, Any]) -> AgentDecision:
        """Decide on budget reallocation strategy."""
        current_performance = context.get("current_performance", {})
        total_budget = context.get("total_budget", 10000)
        
        # Simple reallocation logic based on performance
        high_performing_campaigns = [
            camp for camp, perf in current_performance.items()
            if perf.get("roi", 0) > 150
        ]
        
        if high_performing_campaigns:
            strategy = "increase_high_performers"
            reasoning = [f"Reallocate budget to {len(high_performing_campaigns)} high-performing campaigns"]
            actions = ["Increase budget for high ROI campaigns", "Reduce budget for underperformers"]
        else:
            strategy = "equal_distribution"
            reasoning = ["No clear performance leaders, maintain balanced allocation"]
            actions = ["Monitor performance closely", "Test optimization strategies"]
        
        return AgentDecision(
            agent_type=self.agent_name,
            decision_type="budget_reallocation",
            context=context,
            reasoning=reasoning,
            confidence=0.7,
            recommended_actions=actions,
            metadata={"reallocation_strategy": strategy}
        )

    async def _analyze_performance_metrics(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze performance metrics and provide optimization insights."""
        try:
            performance_data = request.get("performance_data", {})
            time_period = request.get("time_period_days", 30)
            
            # Calculate key performance indicators
            kpis = self._calculate_performance_kpis(performance_data)
            
            # Identify trends and anomalies
            trends = self._identify_performance_trends(performance_data, time_period)
            
            # Generate optimization recommendations
            recommendations = self._generate_performance_recommendations(kpis, trends)
            
            return {
                "success": True,
                "kpis": kpis,
                "trends": trends,
                "recommendations": recommendations,
                "next_review_date": (datetime.now() + timedelta(days=7)).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing performance metrics: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback_analysis": "Performance analysis unavailable"
            }

    def _calculate_performance_kpis(self, performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate key performance indicators."""
        total_sent = performance_data.get("total_sent", 0)
        total_delivered = performance_data.get("total_delivered", 0)
        total_opened = performance_data.get("total_opened", 0)
        total_clicked = performance_data.get("total_clicked", 0)
        total_converted = performance_data.get("total_converted", 0)
        total_cost = performance_data.get("total_cost", 0)
        total_revenue = performance_data.get("total_revenue", 0)
        
        return {
            "delivery_rate": (total_delivered / total_sent * 100) if total_sent > 0 else 0,
            "open_rate": (total_opened / total_delivered * 100) if total_delivered > 0 else 0,
            "click_rate": (total_clicked / total_opened * 100) if total_opened > 0 else 0,
            "conversion_rate": (total_converted / total_clicked * 100) if total_clicked > 0 else 0,
            "cost_per_conversion": (total_cost / total_converted) if total_converted > 0 else 0,
            "roi": ((total_revenue - total_cost) / total_cost * 100) if total_cost > 0 else 0,
            "revenue_per_message": (total_revenue / total_sent) if total_sent > 0 else 0
        }

    def _identify_performance_trends(self, performance_data: Dict[str, Any], time_period: int) -> Dict[str, Any]:
        """Identify performance trends over the time period."""
        # Simulate trend analysis
        return {
            "engagement_trend": "stable",  # "improving", "declining", "stable"
            "cost_trend": "increasing",    # "increasing", "decreasing", "stable"
            "roi_trend": "improving",      # "improving", "declining", "stable"
            "seasonal_patterns": ["higher_engagement_weekdays", "lower_performance_holidays"],
            "anomalies": []
        }

    def _generate_performance_recommendations(self, kpis: Dict[str, Any], trends: Dict[str, Any]) -> List[str]:
        """Generate performance optimization recommendations."""
        recommendations = []
        
        if kpis["open_rate"] < 20:
            recommendations.append("Improve subject lines and sender reputation to increase open rates")
        
        if kpis["click_rate"] < 5:
            recommendations.append("Optimize email content and call-to-action buttons")
        
        if kpis["conversion_rate"] < 2:
            recommendations.append("Review landing page experience and offer relevance")
        
        if kpis["roi"] < 100:
            recommendations.append("Focus on cost reduction and audience targeting improvements")
        
        if trends["cost_trend"] == "increasing":
            recommendations.append("Implement cost optimization strategies to control spending")
        
        return recommendations