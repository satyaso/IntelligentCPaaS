"""Cost savings calculator for AI-CPaaS demo."""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from uuid import UUID

from ai_cpaas_demo.core.models import (
    ChannelType,
    MessageType,
    AIDecisionRecord,
)

logger = logging.getLogger(__name__)


@dataclass
class ChannelCost:
    """Cost structure for a communication channel."""
    channel: ChannelType
    cost_per_message: float
    engagement_rate: float  # Expected engagement rate (0.0 to 1.0)


@dataclass
class CostSavingsReport:
    """Comprehensive cost savings report."""
    # Period metrics
    period_days: int
    optimized_cost: float
    spray_pray_cost: float
    period_savings: float
    savings_percentage: float
    
    # Annual projections
    annual_savings: float
    annual_optimized_cost: float
    annual_spray_pray_cost: float
    
    # ROI metrics
    roi_percentage: float
    payback_period_days: Optional[int]
    
    # Channel breakdown
    cost_by_channel: Dict[str, float]
    savings_by_channel: Dict[str, float]
    
    # Message metrics
    total_messages: int
    optimized_messages: int
    spray_pray_messages: int
    messages_avoided: int
    
    # Engagement metrics
    optimized_engagement_rate: float
    spray_pray_engagement_rate: float
    engagement_improvement: float
    
    # Timestamp
    calculated_at: datetime


class CostSavingsCalculator:
    """Calculator for cost savings vs spray-and-pray approach."""
    
    # Default channel costs (in USD)
    DEFAULT_CHANNEL_COSTS = {
        ChannelType.SMS: ChannelCost(
            channel=ChannelType.SMS,
            cost_per_message=0.0075,  # $0.0075 per SMS
            engagement_rate=0.20,  # 20% baseline engagement
        ),
        ChannelType.WHATSAPP: ChannelCost(
            channel=ChannelType.WHATSAPP,
            cost_per_message=0.005,  # $0.005 per WhatsApp message
            engagement_rate=0.35,  # 35% baseline engagement
        ),
        ChannelType.EMAIL: ChannelCost(
            channel=ChannelType.EMAIL,
            cost_per_message=0.0001,  # $0.0001 per email
            engagement_rate=0.15,  # 15% baseline engagement
        ),
        ChannelType.VOICE: ChannelCost(
            channel=ChannelType.VOICE,
            cost_per_message=0.02,  # $0.02 per voice call
            engagement_rate=0.40,  # 40% baseline engagement
        ),
    }
    
    def __init__(self, channel_costs: Optional[Dict[ChannelType, ChannelCost]] = None):
        """Initialize cost savings calculator.
        
        Args:
            channel_costs: Custom channel cost structure (optional)
        """
        self.channel_costs = channel_costs or self.DEFAULT_CHANNEL_COSTS
        
        # Spray-and-pray assumptions
        self.spray_pray_channels_per_message = 3  # Send to 3 channels
        self.spray_pray_engagement_rate = 0.15  # 15% average engagement
        
        # AI optimization assumptions
        self.ai_channel_selection_accuracy = 0.85  # 85% accuracy
        self.ai_optimized_engagement_rate = 0.35  # 35% average engagement
        
        logger.info("Initialized CostSavingsCalculator")

    def calculate_comprehensive_savings(
        self,
        ai_decisions: List[AIDecisionRecord],
        time_period_days: int = 30,
    ) -> CostSavingsReport:
        """Calculate comprehensive cost savings report.
        
        Args:
            ai_decisions: List of AI decision records
            time_period_days: Time period for analysis
            
        Returns:
            Comprehensive cost savings report
        """
        # Calculate optimized costs
        optimized_cost = 0.0
        optimized_messages = 0
        cost_by_channel: Dict[str, float] = {}
        
        for decision in ai_decisions:
            if decision.decision_type == "channel":
                # Get selected channel from output
                channel_str = decision.output_data.get("channel", "sms")
                try:
                    channel = ChannelType(channel_str)
                    cost = self.channel_costs[channel].cost_per_message
                    optimized_cost += cost
                    optimized_messages += 1
                    
                    # Track by channel
                    if channel.value not in cost_by_channel:
                        cost_by_channel[channel.value] = 0.0
                    cost_by_channel[channel.value] += cost
                    
                except (ValueError, KeyError):
                    logger.warning(f"Unknown channel: {channel_str}")
        
        # Calculate spray-and-pray costs
        spray_pray_cost = self._calculate_spray_pray_cost(optimized_messages)
        spray_pray_messages = optimized_messages * self.spray_pray_channels_per_message
        
        # Calculate savings
        period_savings = spray_pray_cost - optimized_cost
        savings_percentage = (
            (period_savings / spray_pray_cost * 100) if spray_pray_cost > 0 else 0.0
        )
        
        # Project annual costs
        days_per_year = 365
        annual_multiplier = days_per_year / time_period_days
        annual_savings = period_savings * annual_multiplier
        annual_optimized_cost = optimized_cost * annual_multiplier
        annual_spray_pray_cost = spray_pray_cost * annual_multiplier
        
        # Calculate ROI
        roi_percentage = (
            (period_savings / optimized_cost * 100) if optimized_cost > 0 else 0.0
        )
        
        # Calculate payback period (if there's an implementation cost)
        # Assuming implementation cost is 3 months of spray-and-pray cost
        implementation_cost = spray_pray_cost * 3
        if period_savings > 0:
            payback_period_days = int(
                (implementation_cost / period_savings) * time_period_days
            )
        else:
            payback_period_days = None
        
        # Calculate savings by channel
        savings_by_channel = self._calculate_savings_by_channel(
            cost_by_channel, optimized_messages
        )
        
        # Calculate engagement metrics
        optimized_engagement_rate = self.ai_optimized_engagement_rate
        spray_pray_engagement_rate = self.spray_pray_engagement_rate
        engagement_improvement = (
            (optimized_engagement_rate - spray_pray_engagement_rate) * 100
        )
        
        return CostSavingsReport(
            period_days=time_period_days,
            optimized_cost=optimized_cost,
            spray_pray_cost=spray_pray_cost,
            period_savings=period_savings,
            savings_percentage=savings_percentage,
            annual_savings=annual_savings,
            annual_optimized_cost=annual_optimized_cost,
            annual_spray_pray_cost=annual_spray_pray_cost,
            roi_percentage=roi_percentage,
            payback_period_days=payback_period_days,
            cost_by_channel=cost_by_channel,
            savings_by_channel=savings_by_channel,
            total_messages=optimized_messages + spray_pray_messages,
            optimized_messages=optimized_messages,
            spray_pray_messages=spray_pray_messages,
            messages_avoided=spray_pray_messages - optimized_messages,
            optimized_engagement_rate=optimized_engagement_rate,
            spray_pray_engagement_rate=spray_pray_engagement_rate,
            engagement_improvement=engagement_improvement,
            calculated_at=datetime.utcnow(),
        )

    def _calculate_spray_pray_cost(self, message_count: int) -> float:
        """Calculate cost for spray-and-pray approach.
        
        Args:
            message_count: Number of unique messages
            
        Returns:
            Total cost for spray-and-pray
        """
        # Spray-and-pray sends to multiple channels
        # Typically: SMS + Email + WhatsApp
        cost_per_spray = (
            self.channel_costs[ChannelType.SMS].cost_per_message +
            self.channel_costs[ChannelType.EMAIL].cost_per_message +
            self.channel_costs[ChannelType.WHATSAPP].cost_per_message
        )
        
        return message_count * cost_per_spray

    def _calculate_savings_by_channel(
        self,
        optimized_costs: Dict[str, float],
        message_count: int,
    ) -> Dict[str, float]:
        """Calculate savings breakdown by channel.
        
        Args:
            optimized_costs: Actual costs by channel
            message_count: Total message count
            
        Returns:
            Savings by channel
        """
        savings_by_channel = {}
        
        # Calculate what spray-and-pray would have cost per channel
        spray_pray_per_channel = message_count / self.spray_pray_channels_per_message
        
        for channel_type in [ChannelType.SMS, ChannelType.EMAIL, ChannelType.WHATSAPP]:
            channel_str = channel_type.value
            spray_pray_cost = (
                spray_pray_per_channel * 
                self.channel_costs[channel_type].cost_per_message
            )
            optimized_cost = optimized_costs.get(channel_str, 0.0)
            savings = spray_pray_cost - optimized_cost
            savings_by_channel[channel_str] = savings
        
        return savings_by_channel

    def calculate_roi_dashboard_data(
        self, report: CostSavingsReport
    ) -> Dict[str, Any]:
        """Generate ROI dashboard data from savings report.
        
        Args:
            report: Cost savings report
            
        Returns:
            Dictionary with dashboard-ready metrics
        """
        return {
            "headline_metrics": {
                "period_savings": f"${report.period_savings:,.2f}",
                "savings_percentage": f"{report.savings_percentage:.1f}%",
                "annual_savings": f"${report.annual_savings:,.2f}",
                "roi": f"{report.roi_percentage:.1f}%",
            },
            "cost_comparison": {
                "optimized": report.optimized_cost,
                "spray_pray": report.spray_pray_cost,
                "difference": report.period_savings,
            },
            "message_efficiency": {
                "messages_sent": report.optimized_messages,
                "messages_avoided": report.messages_avoided,
                "efficiency_gain": f"{(report.messages_avoided / report.spray_pray_messages * 100):.1f}%",
            },
            "engagement_improvement": {
                "optimized_rate": f"{report.optimized_engagement_rate * 100:.1f}%",
                "spray_pray_rate": f"{report.spray_pray_engagement_rate * 100:.1f}%",
                "improvement": f"{report.engagement_improvement:.1f}%",
            },
            "channel_breakdown": {
                "costs": report.cost_by_channel,
                "savings": report.savings_by_channel,
            },
            "payback": {
                "period_days": report.payback_period_days,
                "period_months": (
                    report.payback_period_days / 30 
                    if report.payback_period_days else None
                ),
            },
        }

    def format_savings_summary(self, report: CostSavingsReport) -> str:
        """Format savings report as human-readable summary.
        
        Args:
            report: Cost savings report
            
        Returns:
            Formatted summary string
        """
        summary = f"""
Cost Savings Analysis ({report.period_days} days)
{'=' * 50}

💰 COST COMPARISON:
   Optimized Cost:     ${report.optimized_cost:,.2f}
   Spray-and-Pray:     ${report.spray_pray_cost:,.2f}
   Savings:            ${report.period_savings:,.2f} ({report.savings_percentage:.1f}%)

📊 ANNUAL PROJECTION:
   Annual Savings:     ${report.annual_savings:,.2f}
   ROI:                {report.roi_percentage:.1f}%
   Payback Period:     {report.payback_period_days or 'N/A'} days

📨 MESSAGE EFFICIENCY:
   Messages Sent:      {report.optimized_messages:,}
   Messages Avoided:   {report.messages_avoided:,}
   Efficiency Gain:    {(report.messages_avoided / report.spray_pray_messages * 100):.1f}%

📈 ENGAGEMENT IMPROVEMENT:
   Optimized Rate:     {report.optimized_engagement_rate * 100:.1f}%
   Spray-Pray Rate:    {report.spray_pray_engagement_rate * 100:.1f}%
   Improvement:        +{report.engagement_improvement:.1f}%

🎯 CHANNEL BREAKDOWN:
"""
        
        for channel, cost in report.cost_by_channel.items():
            savings = report.savings_by_channel.get(channel, 0.0)
            summary += f"   {channel.upper():12} ${cost:,.2f} (saved ${savings:,.2f})\n"
        
        return summary
