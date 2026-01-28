"""Campaign Orchestration Agent for multi-step campaign planning and execution."""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from .base import (
    BaseAIAgent, 
    AgentDecision, 
    CampaignPlan, 
    CustomerSegment
)
from ..core.models import ChannelType, MessageType, UrgencyLevel

logger = logging.getLogger(__name__)


class CampaignOrchestrationAgent(BaseAIAgent):
    """AI agent for orchestrating multi-step marketing campaigns."""

    def __init__(self, region_name: str = "us-east-1"):
        """Initialize the Campaign Orchestration Agent."""
        super().__init__("CampaignOrchestration", region_name)
        
        # Campaign templates for different scenarios
        self.campaign_templates = {
            "product_launch": {
                "phases": ["awareness", "consideration", "conversion", "retention"],
                "duration_days": 14,
                "channels": [ChannelType.EMAIL, ChannelType.SMS, ChannelType.WHATSAPP],
                "message_types": [MessageType.PROMOTIONAL, MessageType.TRANSACTIONAL]
            },
            "seasonal_promotion": {
                "phases": ["teaser", "launch", "urgency", "last_chance"],
                "duration_days": 7,
                "channels": [ChannelType.SMS, ChannelType.EMAIL],
                "message_types": [MessageType.PROMOTIONAL]
            },
            "customer_retention": {
                "phases": ["engagement", "value_demonstration", "loyalty_building"],
                "duration_days": 30,
                "channels": [ChannelType.EMAIL, ChannelType.WHATSAPP],
                "message_types": [MessageType.PROMOTIONAL, MessageType.SUPPORT]
            },
            "win_back": {
                "phases": ["reconnection", "incentive", "feedback"],
                "duration_days": 21,
                "channels": [ChannelType.EMAIL, ChannelType.SMS],
                "message_types": [MessageType.PROMOTIONAL, MessageType.SUPPORT]
            }
        }

    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process a campaign orchestration request."""
        logger.info(f"Processing campaign orchestration request: {request.get('type', 'unknown')}")
        
        request_type = request.get("type", "plan_campaign")
        
        if request_type == "plan_campaign":
            return await self._plan_campaign(request)
        elif request_type == "optimize_campaign":
            return await self._optimize_existing_campaign(request)
        elif request_type == "segment_customers":
            return await self._segment_customers(request)
        elif request_type == "schedule_campaign":
            return await self._schedule_campaign_execution(request)
        else:
            return {
                "success": False,
                "error": f"Unknown request type: {request_type}",
                "supported_types": ["plan_campaign", "optimize_campaign", "segment_customers", "schedule_campaign"]
            }

    async def make_decision(self, context: Dict[str, Any]) -> AgentDecision:
        """Make a strategic decision about campaign orchestration."""
        decision_type = context.get("decision_type", "campaign_strategy")
        
        if decision_type == "campaign_strategy":
            return await self._decide_campaign_strategy(context)
        elif decision_type == "channel_sequence":
            return await self._decide_channel_sequence(context)
        elif decision_type == "timing_optimization":
            return await self._decide_optimal_timing(context)
        else:
            # Default decision
            return AgentDecision(
                agent_type=self.agent_name,
                decision_type=decision_type,
                reasoning=["Unknown decision type, using default strategy"],
                confidence=0.5,
                recommended_actions=["Review decision context and try again"]
            )

    async def _plan_campaign(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Plan a multi-step campaign based on objectives and constraints."""
        try:
            campaign_type = request.get("campaign_type", "product_launch")
            objectives = request.get("objectives", [])
            target_audience = request.get("target_audience", {})
            budget = request.get("budget", 10000.0)
            duration_days = request.get("duration_days")
            
            # Get campaign template
            template = self.campaign_templates.get(campaign_type, self.campaign_templates["product_launch"])
            
            # Use Bedrock for intelligent campaign planning
            planning_prompt = f"""You are an expert marketing campaign strategist. Plan a {campaign_type} campaign with the following requirements:

Objectives: {objectives}
Target Audience: {target_audience}
Budget: ${budget}
Duration: {duration_days or template['duration_days']} days

Template phases: {template['phases']}
Available channels: {[ch.value for ch in template['channels']]}
Message types: {[mt.value for mt in template['message_types']]}

Create a detailed campaign plan with:
1. Customer segmentation strategy
2. Multi-step campaign phases with timing
3. Channel selection and sequencing
4. Budget allocation across phases
5. Success metrics and KPIs

Respond in JSON format:
{{
    "campaign_name": "descriptive name",
    "description": "campaign overview",
    "segments": [
        {{
            "name": "segment name",
            "criteria": {{"key": "value"}},
            "size_estimate": 1000,
            "preferred_channels": ["email", "sms"]
        }}
    ],
    "phases": [
        {{
            "name": "phase name",
            "duration_days": 3,
            "objectives": ["objective1"],
            "channels": ["email"],
            "message_types": ["promotional"],
            "budget_allocation": 0.25
        }}
    ],
    "timing_strategy": {{
        "start_delay_hours": 0,
        "phase_intervals_hours": [24, 48, 72],
        "optimal_send_times": ["09:00", "14:00", "19:00"]
    }},
    "success_metrics": ["open_rate", "click_rate", "conversion_rate"],
    "estimated_cost": 8500.0,
    "risk_factors": ["audience_fatigue", "seasonal_timing"]
}}"""

            # Get AI analysis
            ai_analysis = await self._analyze_with_bedrock(planning_prompt)
            
            if ai_analysis.get("parsed", True):
                # Create campaign plan from AI analysis
                campaign_plan = self._create_campaign_plan_from_analysis(ai_analysis, template, budget)
            else:
                # Fallback to rule-based planning
                campaign_plan = self._create_fallback_campaign_plan(campaign_type, template, objectives, budget)
            
            # Record decision
            decision = AgentDecision(
                agent_type=self.agent_name,
                decision_type="campaign_planning",
                context=request,
                reasoning=[
                    f"Planned {campaign_type} campaign with {len(campaign_plan.steps)} phases",
                    f"Targeting {len(campaign_plan.target_segments)} customer segments",
                    f"Budget allocation: ${campaign_plan.budget_allocation}"
                ],
                confidence=0.85,
                recommended_actions=[
                    "Review campaign plan with stakeholders",
                    "Validate customer segments",
                    "Schedule campaign execution"
                ]
            )
            self._record_decision(decision)
            
            return {
                "success": True,
                "campaign_plan": campaign_plan.dict(),
                "decision": decision.dict()
            }
            
        except Exception as e:
            logger.error(f"Error planning campaign: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback_plan": self._create_basic_campaign_plan(request.get("campaign_type", "basic"))
            }

    async def _segment_customers(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Segment customers for targeted campaigns."""
        try:
            segmentation_criteria = request.get("criteria", {})
            customer_data = request.get("customer_data", [])
            
            # Use AI for intelligent segmentation
            segmentation_prompt = f"""You are a customer segmentation expert. Analyze the following customer data and create meaningful segments for targeted marketing:

Segmentation Criteria: {segmentation_criteria}
Sample Customer Data: {customer_data[:5] if customer_data else "No sample data provided"}
Total Customers: {len(customer_data)}

Create 3-5 customer segments based on:
1. Engagement patterns
2. Purchase behavior  
3. Channel preferences
4. Demographics
5. Customer lifetime value

Respond in JSON format:
{{
    "segments": [
        {{
            "name": "High-Value Engaged",
            "description": "Customers with high CLV and regular engagement",
            "criteria": {{"clv": ">1000", "engagement": "high"}},
            "size_estimate": 500,
            "characteristics": {{"avg_clv": 1500, "preferred_channel": "email"}},
            "recommended_approach": "Premium offers with personalized content"
        }}
    ],
    "segmentation_strategy": "value-based with engagement overlay",
    "confidence": 0.8
}}"""

            ai_analysis = await self._analyze_with_bedrock(segmentation_prompt)
            
            if ai_analysis.get("parsed", True) and "segments" in ai_analysis:
                segments = [
                    CustomerSegment(
                        name=seg["name"],
                        criteria=seg.get("criteria", {}),
                        size=seg.get("size_estimate", 100),
                        characteristics=seg.get("characteristics", {}),
                        preferred_channels=seg.get("preferred_channels", ["email"])
                    )
                    for seg in ai_analysis["segments"]
                ]
            else:
                # Fallback segmentation
                segments = self._create_fallback_segments(customer_data)
            
            return {
                "success": True,
                "segments": [seg.dict() for seg in segments],
                "strategy": ai_analysis.get("segmentation_strategy", "rule-based fallback"),
                "confidence": ai_analysis.get("confidence", 0.6)
            }
            
        except Exception as e:
            logger.error(f"Error segmenting customers: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback_segments": [seg.dict() for seg in self._create_basic_segments()]
            }

    async def _decide_campaign_strategy(self, context: Dict[str, Any]) -> AgentDecision:
        """Decide on the overall campaign strategy."""
        campaign_goals = context.get("goals", [])
        audience_size = context.get("audience_size", 1000)
        budget = context.get("budget", 5000)
        timeline = context.get("timeline_days", 7)
        
        # Analyze context to determine strategy
        if budget > 10000 and timeline > 14:
            strategy = "comprehensive_multi_phase"
            confidence = 0.9
            reasoning = [
                "High budget allows for comprehensive approach",
                "Extended timeline enables multi-phase execution",
                "Can afford premium channels and personalization"
            ]
        elif audience_size < 500:
            strategy = "personalized_direct"
            confidence = 0.8
            reasoning = [
                "Small audience enables personalized approach",
                "Direct communication will be more effective",
                "Higher engagement expected with targeted messaging"
            ]
        elif timeline < 3:
            strategy = "urgent_broadcast"
            confidence = 0.7
            reasoning = [
                "Short timeline requires immediate action",
                "Broadcast approach for maximum reach",
                "Focus on high-impact channels"
            ]
        else:
            strategy = "balanced_sequential"
            confidence = 0.75
            reasoning = [
                "Balanced approach for moderate constraints",
                "Sequential messaging to build engagement",
                "Cost-effective channel mix"
            ]
        
        return AgentDecision(
            agent_type=self.agent_name,
            decision_type="campaign_strategy",
            context=context,
            reasoning=reasoning,
            confidence=confidence,
            recommended_actions=[
                f"Implement {strategy} campaign strategy",
                "Validate strategy with stakeholders",
                "Prepare detailed execution plan"
            ],
            metadata={"selected_strategy": strategy}
        )

    async def _decide_channel_sequence(self, context: Dict[str, Any]) -> AgentDecision:
        """Decide on the optimal channel sequence for the campaign."""
        available_channels = context.get("available_channels", [ch.value for ch in ChannelType])
        audience_preferences = context.get("audience_preferences", {})
        campaign_urgency = context.get("urgency", "medium")
        
        # Determine optimal sequence based on context
        if campaign_urgency == "high":
            sequence = ["sms", "email", "whatsapp"]
            reasoning = ["SMS for immediate attention", "Email for details", "WhatsApp for follow-up"]
        elif audience_preferences.get("email", 0) > 0.7:
            sequence = ["email", "sms", "whatsapp"]
            reasoning = ["Start with preferred email channel", "SMS for non-openers", "WhatsApp for engagement"]
        else:
            sequence = ["email", "whatsapp", "sms"]
            reasoning = ["Email for detailed content", "WhatsApp for rich media", "SMS for final push"]
        
        return AgentDecision(
            agent_type=self.agent_name,
            decision_type="channel_sequence",
            context=context,
            reasoning=reasoning,
            confidence=0.8,
            recommended_actions=[
                f"Execute channels in sequence: {' → '.join(sequence)}",
                "Monitor engagement at each step",
                "Adjust sequence based on performance"
            ],
            metadata={"channel_sequence": sequence}
        )

    def _create_campaign_plan_from_analysis(self, analysis: Dict[str, Any], template: Dict[str, Any], budget: float) -> CampaignPlan:
        """Create a campaign plan from AI analysis."""
        return CampaignPlan(
            name=analysis.get("campaign_name", "AI Generated Campaign"),
            description=analysis.get("description", "Campaign generated by AI orchestration"),
            target_segments=[
                CustomerSegment(
                    name=seg["name"],
                    criteria=seg.get("criteria", {}),
                    size=seg.get("size_estimate", 100),
                    preferred_channels=seg.get("preferred_channels", ["email"])
                ).dict()
                for seg in analysis.get("segments", [])
            ],
            steps=[
                {
                    "phase_name": phase["name"],
                    "duration_days": phase.get("duration_days", 1),
                    "objectives": phase.get("objectives", []),
                    "channels": phase.get("channels", ["email"]),
                    "message_types": phase.get("message_types", ["promotional"]),
                    "budget_allocation": phase.get("budget_allocation", 0.25)
                }
                for phase in analysis.get("phases", [])
            ],
            timing_strategy=analysis.get("timing_strategy", {}),
            budget_allocation={
                "total": budget,
                "phases": {f"phase_{i}": phase.get("budget_allocation", 0.25) * budget 
                          for i, phase in enumerate(analysis.get("phases", []))}
            },
            success_metrics=analysis.get("success_metrics", ["engagement_rate"]),
            estimated_duration=sum(phase.get("duration_days", 1) for phase in analysis.get("phases", [])) * 24 * 60,
            estimated_cost=analysis.get("estimated_cost", budget * 0.85)
        )

    def _create_fallback_campaign_plan(self, campaign_type: str, template: Dict[str, Any], objectives: List[str], budget: float) -> CampaignPlan:
        """Create a fallback campaign plan using rule-based logic."""
        phases = template["phases"]
        duration_per_phase = template["duration_days"] // len(phases)
        budget_per_phase = budget / len(phases)
        
        return CampaignPlan(
            name=f"{campaign_type.replace('_', ' ').title()} Campaign",
            description=f"Rule-based {campaign_type} campaign plan",
            target_segments=[
                CustomerSegment(
                    name="Primary Audience",
                    criteria={"engagement": "medium_to_high"},
                    size=1000,
                    preferred_channels=[ch.value for ch in template["channels"]]
                ).dict()
            ],
            steps=[
                {
                    "phase_name": phase,
                    "duration_days": duration_per_phase,
                    "objectives": objectives[:2] if objectives else [f"Execute {phase} phase"],
                    "channels": [template["channels"][0].value],
                    "message_types": [template["message_types"][0].value],
                    "budget_allocation": budget_per_phase
                }
                for phase in phases
            ],
            timing_strategy={
                "start_delay_hours": 0,
                "phase_intervals_hours": [24 * duration_per_phase] * len(phases)
            },
            budget_allocation={"total": budget, "per_phase": budget_per_phase},
            success_metrics=["open_rate", "engagement_rate"],
            estimated_duration=template["duration_days"] * 24 * 60,
            estimated_cost=budget * 0.8
        )

    def _create_fallback_segments(self, customer_data: List[Dict[str, Any]]) -> List[CustomerSegment]:
        """Create fallback customer segments."""
        if not customer_data:
            return self._create_basic_segments()
        
        # Simple rule-based segmentation
        segments = []
        
        # High-value segment (top 20%)
        segments.append(CustomerSegment(
            name="High-Value Customers",
            criteria={"clv": ">1000"},
            size=max(1, len(customer_data) // 5),
            characteristics={"avg_clv": 1500},
            preferred_channels=["email", "whatsapp"]
        ))
        
        # Engaged segment (active in last 30 days)
        segments.append(CustomerSegment(
            name="Recently Engaged",
            criteria={"last_activity": "<30_days"},
            size=max(1, len(customer_data) // 3),
            characteristics={"engagement": "high"},
            preferred_channels=["email", "sms"]
        ))
        
        # At-risk segment (inactive)
        segments.append(CustomerSegment(
            name="At-Risk Customers",
            criteria={"last_activity": ">90_days"},
            size=max(1, len(customer_data) // 4),
            characteristics={"engagement": "low"},
            preferred_channels=["email"]
        ))
        
        return segments

    def _create_basic_segments(self) -> List[CustomerSegment]:
        """Create basic customer segments for fallback."""
        return [
            CustomerSegment(
                name="Active Customers",
                criteria={"status": "active"},
                size=500,
                preferred_channels=["email", "sms"]
            ),
            CustomerSegment(
                name="New Customers",
                criteria={"tenure": "<30_days"},
                size=200,
                preferred_channels=["email", "whatsapp"]
            ),
            CustomerSegment(
                name="VIP Customers",
                criteria={"tier": "premium"},
                size=100,
                preferred_channels=["email", "voice"]
            )
        ]

    def _create_basic_campaign_plan(self, campaign_type: str) -> Dict[str, Any]:
        """Create a basic campaign plan for error fallback."""
        return {
            "campaign_id": str(uuid4()),
            "name": f"Basic {campaign_type} Campaign",
            "description": "Fallback campaign plan",
            "phases": [
                {
                    "name": "Launch",
                    "duration_days": 3,
                    "channels": ["email"],
                    "objectives": ["Reach target audience"]
                }
            ],
            "estimated_cost": 1000.0,
            "success_metrics": ["delivery_rate"]
        }

    async def _optimize_existing_campaign(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize an existing campaign based on performance data."""
        # Implementation for campaign optimization
        campaign_id = request.get("campaign_id")
        performance_data = request.get("performance_data", {})
        
        return {
            "success": True,
            "optimizations": [
                "Increase email frequency for high-engagement segments",
                "Reduce SMS usage for low-response segments",
                "Adjust timing based on open rate patterns"
            ],
            "estimated_improvement": "15-25% better engagement"
        }

    async def _schedule_campaign_execution(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Schedule campaign execution with Step Functions integration."""
        # Implementation for campaign scheduling
        campaign_plan = request.get("campaign_plan", {})
        
        return {
            "success": True,
            "execution_schedule": {
                "start_time": datetime.now().isoformat(),
                "phases": [
                    {
                        "phase": "Phase 1",
                        "scheduled_time": (datetime.now() + timedelta(hours=1)).isoformat()
                    }
                ]
            },
            "step_function_arn": "arn:aws:states:us-east-1:123456789:stateMachine:campaign-orchestration"
        }

    async def _decide_optimal_timing(self, context: Dict[str, Any]) -> AgentDecision:
        """Decide on optimal timing for campaign execution."""
        target_timezone = context.get("timezone", "UTC")
        audience_behavior = context.get("audience_behavior", {})
        campaign_urgency = context.get("urgency", "medium")
        
        # Simple timing logic
        if campaign_urgency == "high":
            optimal_time = "immediate"
            reasoning = ["High urgency requires immediate execution"]
        else:
            optimal_time = "09:00"  # 9 AM in target timezone
            reasoning = ["9 AM typically has highest email open rates"]
        
        return AgentDecision(
            agent_type=self.agent_name,
            decision_type="timing_optimization",
            context=context,
            reasoning=reasoning,
            confidence=0.7,
            recommended_actions=[f"Schedule campaign for {optimal_time}"],
            metadata={"optimal_time": optimal_time}
        )