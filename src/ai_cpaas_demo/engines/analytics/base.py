"""Base implementation of real-time analytics engine."""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from ai_cpaas_demo.core.interfaces import (
    RealTimeAnalytics,
    AnalyticsRequest,
    AnalyticsResult,
)
from ai_cpaas_demo.core.models import (
    AnalyticsMetric,
    BusinessInsight,
    AIDecisionRecord,
    ChannelType,
    MessageType,
)

logger = logging.getLogger(__name__)


class BaseAnalyticsEngine(RealTimeAnalytics):
    """Base implementation of real-time analytics engine.
    
    Processes communication patterns, extracts insights, and provides
    business intelligence for the AI-CPaaS demo system.
    """

    def __init__(self):
        """Initialize the base analytics engine."""
        # In-memory storage for demo purposes
        self._decision_records: List[AIDecisionRecord] = []
        self._metrics_cache: Dict[str, AnalyticsMetric] = {}
        self._insights_cache: List[BusinessInsight] = []
        
        logger.info("Initialized BaseAnalyticsEngine")

    async def process_communication_event(
        self, event: Dict[str, Any]
    ) -> None:
        """Process a communication event in real-time.
        
        Args:
            event: Communication event data
        """
        try:
            # Extract event details
            event_type = event.get("type", "unknown")
            customer_id = event.get("customer_id")
            channel = event.get("channel")
            timestamp = event.get("timestamp", datetime.utcnow())
            
            logger.info(
                f"Processing communication event: type={event_type}, "
                f"customer={customer_id}, channel={channel}"
            )
            
            # Update metrics based on event type
            if event_type == "message_sent":
                await self._update_message_metrics(event)
            elif event_type == "message_opened":
                await self._update_engagement_metrics(event)
            elif event_type == "ai_decision":
                await self._record_ai_decision(event)
            elif event_type == "fatigue_protection":
                await self._update_protection_metrics(event)
            
            # Generate insights if patterns detected
            await self._generate_insights()
            
        except Exception as e:
            logger.error(f"Error processing communication event: {e}")

    async def get_analytics(
        self, request: AnalyticsRequest
    ) -> AnalyticsResult:
        """Get analytics data for specified time range and metrics.
        
        Args:
            request: Analytics request with filters and time range
            
        Returns:
            AnalyticsResult with metrics, trends, and insights
        """
        try:
            # Filter metrics by time range
            filtered_metrics = await self._filter_metrics_by_time(
                request.time_range
            )
            
            # Calculate trends
            trends = await self._calculate_trends(filtered_metrics)
            
            # Get relevant insights
            insights = await self._get_relevant_insights(request)
            
            # Check for alert conditions
            alerts = await self._check_alert_conditions(filtered_metrics)
            
            return AnalyticsResult(
                metrics=filtered_metrics,
                trends=trends,
                alerts=alerts,
                insights=insights,
            )
            
        except Exception as e:
            logger.error(f"Error getting analytics: {e}")
            return AnalyticsResult(
                metrics=[],
                trends=[],
                alerts=[],
                insights=[],
            )

    async def calculate_cost_savings(
        self,
        optimized_cost: float,
        spray_pray_cost: float,
        time_period_days: int = 30,
    ) -> Dict[str, float]:
        """Calculate cost savings vs spray-and-pray approach.
        
        Args:
            optimized_cost: Cost with AI optimization
            spray_pray_cost: Cost with traditional spray-and-pray
            time_period_days: Time period for calculation
            
        Returns:
            Dictionary with cost savings metrics
        """
        # Calculate savings
        savings = spray_pray_cost - optimized_cost
        savings_percentage = (savings / spray_pray_cost * 100) if spray_pray_cost > 0 else 0
        
        # Project annual savings
        days_per_year = 365
        annual_savings = (savings / time_period_days) * days_per_year
        
        # Calculate ROI
        roi_percentage = (savings / optimized_cost * 100) if optimized_cost > 0 else 0
        
        result = {
            "period_savings": savings,
            "savings_percentage": savings_percentage,
            "annual_savings": annual_savings,
            "roi_percentage": roi_percentage,
            "optimized_cost": optimized_cost,
            "spray_pray_cost": spray_pray_cost,
        }
        
        logger.info(
            f"Cost savings calculated: ${savings:.2f} ({savings_percentage:.1f}%), "
            f"Annual projection: ${annual_savings:.2f}"
        )
        
        return result

    async def _update_message_metrics(self, event: Dict[str, Any]) -> None:
        """Update metrics for message sent events.
        
        Args:
            event: Message sent event data
        """
        channel = event.get("channel", "unknown")
        message_type = event.get("message_type", "unknown")
        cost = event.get("cost", 0.0)
        
        # Update total messages metric
        self._increment_metric("total_messages", 1.0)
        
        # Update channel-specific metrics
        self._increment_metric(f"messages_{channel}", 1.0)
        
        # Update cost metrics
        self._increment_metric("total_cost", cost)
        self._increment_metric(f"cost_{channel}", cost)
        
        # Update message type metrics
        self._increment_metric(f"messages_{message_type}", 1.0)

    async def _update_engagement_metrics(self, event: Dict[str, Any]) -> None:
        """Update metrics for engagement events.
        
        Args:
            event: Engagement event data
        """
        channel = event.get("channel", "unknown")
        
        # Update engagement metrics
        self._increment_metric("total_engagements", 1.0)
        self._increment_metric(f"engagements_{channel}", 1.0)
        
        # Calculate engagement rate
        total_messages = self._get_metric_value("total_messages")
        total_engagements = self._get_metric_value("total_engagements")
        
        if total_messages > 0:
            engagement_rate = (total_engagements / total_messages) * 100
            self._set_metric("engagement_rate", engagement_rate)

    async def _record_ai_decision(self, event: Dict[str, Any]) -> None:
        """Record AI decision for analytics.
        
        Args:
            event: AI decision event data
        """
        try:
            decision_record = AIDecisionRecord(
                customer_id=UUID(event.get("customer_id")),
                decision_type=event.get("decision_type", "unknown"),
                input_data=event.get("input_data", {}),
                output_data=event.get("output_data", {}),
                confidence=event.get("confidence", 0.0),
                reasoning=event.get("reasoning", []),
                variant=event.get("variant", "aws"),
                cost_savings=event.get("cost_savings", 0.0),
                engine_name=event.get("engine_name", "unknown"),
            )
            
            self._decision_records.append(decision_record)
            
            # Update AI decision metrics
            self._increment_metric("ai_decisions", 1.0)
            self._increment_metric(
                f"ai_decisions_{decision_record.engine_name}", 1.0
            )
            
            # Update cost savings from AI
            if decision_record.cost_savings > 0:
                self._increment_metric(
                    "total_ai_savings", decision_record.cost_savings
                )
                
        except Exception as e:
            logger.error(f"Error recording AI decision: {e}")

    async def _update_protection_metrics(self, event: Dict[str, Any]) -> None:
        """Update metrics for protection events.
        
        Args:
            event: Protection event data
        """
        protection_type = event.get("protection_type", "unknown")
        
        # Update protection metrics
        self._increment_metric("total_protections", 1.0)
        self._increment_metric(f"protections_{protection_type}", 1.0)
        
        # Track prevented brand damage
        if event.get("prevented_damage", False):
            self._increment_metric("prevented_brand_damage", 1.0)

    async def _filter_metrics_by_time(
        self, time_range: Dict[str, datetime]
    ) -> List[AnalyticsMetric]:
        """Filter metrics by time range.
        
        Args:
            time_range: Dictionary with 'start' and 'end' datetime
            
        Returns:
            List of filtered metrics
        """
        start_time = time_range.get("start", datetime.utcnow() - timedelta(hours=24))
        end_time = time_range.get("end", datetime.utcnow())
        
        filtered = []
        for metric in self._metrics_cache.values():
            if start_time <= metric.timestamp <= end_time:
                filtered.append(metric)
        
        return filtered

    async def _calculate_trends(
        self, metrics: List[AnalyticsMetric]
    ) -> List[Dict[str, Any]]:
        """Calculate trends from metrics.
        
        Args:
            metrics: List of metrics
            
        Returns:
            List of trend analyses
        """
        trends = []
        
        # Group metrics by name
        metric_groups: Dict[str, List[AnalyticsMetric]] = {}
        for metric in metrics:
            if metric.name not in metric_groups:
                metric_groups[metric.name] = []
            metric_groups[metric.name].append(metric)
        
        # Calculate trend for each metric
        for name, group in metric_groups.items():
            if len(group) >= 2:
                # Sort by timestamp
                sorted_group = sorted(group, key=lambda m: m.timestamp)
                
                # Calculate trend
                first_value = sorted_group[0].value
                last_value = sorted_group[-1].value
                
                if first_value > 0:
                    change_percent = ((last_value - first_value) / first_value) * 100
                else:
                    change_percent = 0.0
                
                # Determine trend direction
                if change_percent > 5:
                    trend = "up"
                elif change_percent < -5:
                    trend = "down"
                else:
                    trend = "stable"
                
                trends.append({
                    "metric_name": name,
                    "trend": trend,
                    "change_percent": change_percent,
                    "current_value": last_value,
                    "previous_value": first_value,
                })
        
        return trends

    async def _get_relevant_insights(
        self, request: AnalyticsRequest
    ) -> List[BusinessInsight]:
        """Get relevant business insights.
        
        Args:
            request: Analytics request
            
        Returns:
            List of relevant insights
        """
        # Return recent insights
        return self._insights_cache[-10:]  # Last 10 insights

    async def _check_alert_conditions(
        self, metrics: List[AnalyticsMetric]
    ) -> List[Dict[str, Any]]:
        """Check for alert conditions in metrics.
        
        Args:
            metrics: List of metrics to check
            
        Returns:
            List of alert conditions
        """
        alerts = []
        
        # Check for high cost
        for metric in metrics:
            if metric.name == "total_cost" and metric.value > 1000:
                alerts.append({
                    "type": "high_cost",
                    "severity": "warning",
                    "message": f"Total cost exceeds threshold: ${metric.value:.2f}",
                    "metric": metric.name,
                    "value": metric.value,
                })
            
            # Check for low engagement rate
            if metric.name == "engagement_rate" and metric.value < 20:
                alerts.append({
                    "type": "low_engagement",
                    "severity": "warning",
                    "message": f"Engagement rate below threshold: {metric.value:.1f}%",
                    "metric": metric.name,
                    "value": metric.value,
                })
        
        return alerts

    async def _generate_insights(self) -> None:
        """Generate business insights from current metrics."""
        try:
            # Calculate cost savings insight
            total_cost = self._get_metric_value("total_cost")
            ai_savings = self._get_metric_value("total_ai_savings")
            
            if ai_savings > 0:
                insight = BusinessInsight(
                    type="cost-savings",
                    description=f"AI optimization saved ${ai_savings:.2f} in communication costs",
                    impact=ai_savings,
                    confidence=0.95,
                    actionable=True,
                    supporting_data={
                        "total_cost": total_cost,
                        "savings": ai_savings,
                    },
                )
                self._insights_cache.append(insight)
            
            # Calculate engagement improvement insight
            engagement_rate = self._get_metric_value("engagement_rate")
            if engagement_rate > 0:
                # Assume baseline of 15% for spray-and-pray
                baseline_rate = 15.0
                improvement = engagement_rate - baseline_rate
                
                if improvement > 0:
                    insight = BusinessInsight(
                        type="engagement-improvement",
                        description=f"Engagement rate improved by {improvement:.1f}% vs spray-and-pray",
                        impact=improvement,
                        confidence=0.90,
                        actionable=True,
                        supporting_data={
                            "current_rate": engagement_rate,
                            "baseline_rate": baseline_rate,
                        },
                    )
                    self._insights_cache.append(insight)
            
            # Calculate risk prevention insight
            prevented_damage = self._get_metric_value("prevented_brand_damage")
            if prevented_damage > 0:
                insight = BusinessInsight(
                    type="risk-prevention",
                    description=f"Prevented {int(prevented_damage)} potential brand damage incidents",
                    impact=prevented_damage,
                    confidence=1.0,
                    actionable=True,
                    supporting_data={
                        "incidents_prevented": int(prevented_damage),
                    },
                )
                self._insights_cache.append(insight)
                
        except Exception as e:
            logger.error(f"Error generating insights: {e}")

    def _increment_metric(self, name: str, value: float) -> None:
        """Increment a metric value.
        
        Args:
            name: Metric name
            value: Value to add
        """
        if name in self._metrics_cache:
            metric = self._metrics_cache[name]
            metric.value += value
            metric.timestamp = datetime.utcnow()
        else:
            self._metrics_cache[name] = AnalyticsMetric(
                name=name,
                value=value,
                trend="stable",
                change_percent=0.0,
            )

    def _set_metric(self, name: str, value: float) -> None:
        """Set a metric to a specific value.
        
        Args:
            name: Metric name
            value: Value to set
        """
        if name in self._metrics_cache:
            metric = self._metrics_cache[name]
            old_value = metric.value
            metric.value = value
            metric.timestamp = datetime.utcnow()
            
            # Calculate change
            if old_value > 0:
                change_percent = ((value - old_value) / old_value) * 100
                metric.change_percent = change_percent
                
                # Update trend
                if change_percent > 5:
                    metric.trend = "up"
                elif change_percent < -5:
                    metric.trend = "down"
                else:
                    metric.trend = "stable"
        else:
            self._metrics_cache[name] = AnalyticsMetric(
                name=name,
                value=value,
                trend="stable",
                change_percent=0.0,
            )

    def _get_metric_value(self, name: str) -> float:
        """Get current value of a metric.
        
        Args:
            name: Metric name
            
        Returns:
            Current metric value or 0.0 if not found
        """
        if name in self._metrics_cache:
            return self._metrics_cache[name].value
        return 0.0

    async def process_analytics(self, request: AnalyticsRequest) -> AnalyticsResult:
        """Process analytics request and return insights.
        
        This is an alias for get_analytics() for interface compatibility.
        
        Args:
            request: Analytics request
            
        Returns:
            AnalyticsResult with metrics and insights
        """
        return await self.get_analytics(request)

    async def extract_sentiment_and_topics(self, content: str) -> Dict[str, Any]:
        """Extract sentiment and topics from communication content.
        
        Args:
            content: Communication content to analyze
            
        Returns:
            Dictionary with sentiment and topics
        """
        # Basic sentiment analysis (placeholder)
        # In production, this would use NLP models
        
        # Simple keyword-based sentiment
        positive_words = ["great", "excellent", "happy", "love", "amazing", "wonderful"]
        negative_words = ["bad", "terrible", "hate", "awful", "poor", "disappointed"]
        
        content_lower = content.lower()
        
        positive_count = sum(1 for word in positive_words if word in content_lower)
        negative_count = sum(1 for word in negative_words if word in content_lower)
        
        if positive_count > negative_count:
            sentiment = "positive"
            confidence = min(0.9, 0.5 + (positive_count * 0.1))
        elif negative_count > positive_count:
            sentiment = "negative"
            confidence = min(0.9, 0.5 + (negative_count * 0.1))
        else:
            sentiment = "neutral"
            confidence = 0.5
        
        # Extract simple topics (placeholder)
        topics = []
        if "promotion" in content_lower or "sale" in content_lower:
            topics.append("promotional")
        if "order" in content_lower or "shipping" in content_lower:
            topics.append("transactional")
        if "support" in content_lower or "help" in content_lower:
            topics.append("support")
        
        return {
            "sentiment": sentiment,
            "confidence": confidence,
            "topics": topics,
            "word_count": len(content.split()),
        }

    async def detect_trends(self, metrics: List[AnalyticsMetric]) -> List[Dict[str, Any]]:
        """Detect trends in communication patterns.
        
        Args:
            metrics: List of metrics to analyze
            
        Returns:
            List of detected trends
        """
        return await self._calculate_trends(metrics)
