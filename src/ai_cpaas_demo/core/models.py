"""Core data models for the AI-CPaaS demo system."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator


class ChannelType(str, Enum):
    """Available communication channels."""
    SMS = "sms"
    WHATSAPP = "whatsapp"
    EMAIL = "email"
    VOICE = "voice"


class MessageType(str, Enum):
    """Types of messages that can be sent."""
    PROMOTIONAL = "promotional"
    TRANSACTIONAL = "transactional"
    SUPPORT = "support"


class UrgencyLevel(str, Enum):
    """Message urgency levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class FatigueLevel(str, Enum):
    """Customer fatigue levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RiskLevel(str, Enum):
    """Risk assessment levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SentimentType(str, Enum):
    """Customer sentiment types."""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class VariantType(str, Enum):
    """Implementation variants."""
    AWS = "aws"
    OPENSOURCE = "opensource"


class ChannelPreference(BaseModel):
    """Customer preference for a specific channel."""
    channel: ChannelType
    preference_score: float = Field(..., ge=0.0, le=1.0)
    last_engagement: Optional[datetime] = None
    engagement_count: int = Field(default=0, ge=0)


class EngagementRecord(BaseModel):
    """Record of customer engagement with a message."""
    id: UUID = Field(default_factory=uuid4)
    channel: ChannelType
    message_type: MessageType
    timestamp: datetime
    opened: bool = False
    clicked: bool = False
    responded: bool = False
    engagement_score: float = Field(..., ge=0.0, le=1.0)


class SentimentRecord(BaseModel):
    """Record of customer sentiment analysis."""
    id: UUID = Field(default_factory=uuid4)
    timestamp: datetime
    sentiment: SentimentType
    confidence: float = Field(..., ge=0.0, le=1.0)
    source: str  # e.g., "support_ticket", "survey", "social_media"
    context: Optional[str] = None


class SupportTicket(BaseModel):
    """Customer support ticket information."""
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime
    status: str  # "open", "in_progress", "resolved", "closed"
    priority: str  # "low", "medium", "high", "critical"
    category: str  # "billing", "technical", "complaint", etc.
    sentiment: SentimentType
    resolved_at: Optional[datetime] = None


class DisengagementSignal(BaseModel):
    """Signal indicating customer disengagement."""
    signal_type: str  # "unsubscribe", "spam_report", "low_engagement", etc.
    timestamp: datetime
    channel: ChannelType
    severity: float = Field(..., ge=0.0, le=1.0)


class FrequencySettings(BaseModel):
    """Customer communication frequency preferences."""
    daily_limit: int = Field(default=3, ge=0)
    weekly_limit: int = Field(default=10, ge=0)
    monthly_limit: int = Field(default=30, ge=0)
    preferred_time_start: int = Field(default=9, ge=0, le=23)  # Hour of day
    preferred_time_end: int = Field(default=17, ge=0, le=23)  # Hour of day
    timezone: str = Field(default="UTC")


class CustomerProfile(BaseModel):
    """Complete customer profile with preferences and history."""
    id: UUID = Field(default_factory=uuid4)
    external_id: str  # Customer ID from external system
    channel_preferences: List[ChannelPreference] = Field(default_factory=list)
    engagement_history: List[EngagementRecord] = Field(default_factory=list)
    sentiment_history: List[SentimentRecord] = Field(default_factory=list)
    communication_frequency: FrequencySettings = Field(default_factory=FrequencySettings)
    last_interaction: Optional[datetime] = None
    support_tickets: List[SupportTicket] = Field(default_factory=list)
    fatigue_level: FatigueLevel = FatigueLevel.LOW
    disengagement_signals: List[DisengagementSignal] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @validator('updated_at', pre=True, always=True)
    def set_updated_at(cls, v):
        return datetime.utcnow()


class BrandProfile(BaseModel):
    """Brand guidelines and voice settings."""
    brand_name: str
    voice_tone: str  # "professional", "friendly", "casual", etc.
    key_messages: List[str] = Field(default_factory=list)
    prohibited_words: List[str] = Field(default_factory=list)
    style_guidelines: Dict[str, Any] = Field(default_factory=dict)


class ContentTemplate(BaseModel):
    """Template for message content."""
    id: UUID = Field(default_factory=uuid4)
    name: str
    content: str
    placeholders: List[str] = Field(default_factory=list)
    channel_variants: Dict[ChannelType, str] = Field(default_factory=dict)
    brand_profile: Optional[BrandProfile] = None


class CampaignConstraints(BaseModel):
    """Constraints for campaign execution."""
    max_budget: Optional[float] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    excluded_channels: List[ChannelType] = Field(default_factory=list)
    target_segments: List[str] = Field(default_factory=list)
    respect_fatigue_limits: bool = True
    require_guardrail_approval: bool = True


class PredictedOutcome(BaseModel):
    """Predicted outcome for a campaign or message."""
    channel: ChannelType
    engagement_probability: float = Field(..., ge=0.0, le=1.0)
    cost_estimate: float = Field(..., ge=0.0)
    expected_roi: float
    confidence: float = Field(..., ge=0.0, le=1.0)


class BudgetAnalysis(BaseModel):
    """Budget impact analysis."""
    total_cost: float = Field(..., ge=0.0)
    cost_per_channel: Dict[ChannelType, float] = Field(default_factory=dict)
    savings_vs_spray_pray: float = Field(default=0.0)
    projected_annual_savings: float = Field(default=0.0)
    roi_percentage: float = Field(default=0.0)


class CampaignContext(BaseModel):
    """Context for a marketing campaign."""
    id: UUID = Field(default_factory=uuid4)
    name: str
    type: MessageType
    target_audience: List[str] = Field(default_factory=list)
    content: ContentTemplate
    constraints: CampaignConstraints = Field(default_factory=CampaignConstraints)
    expected_outcomes: List[PredictedOutcome] = Field(default_factory=list)
    budget_impact: Optional[BudgetAnalysis] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CommunicationFrequency(BaseModel):
    """Tracking of customer communication frequency."""
    customer_id: UUID
    daily_count: int = Field(default=0, ge=0)
    weekly_count: int = Field(default=0, ge=0)
    monthly_count: int = Field(default=0, ge=0)
    last_message_time: Optional[datetime] = None
    channel_breakdown: Dict[ChannelType, int] = Field(default_factory=dict)
    fatigue_score: float = Field(default=0.0, ge=0.0, le=1.0)
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class AIDecisionRecord(BaseModel):
    """Record of AI engine decisions."""
    id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    customer_id: UUID
    decision_type: str  # "channel", "content", "timing", "block", "fatigue-protection"
    input_data: Dict[str, Any] = Field(default_factory=dict)
    output_data: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: List[str] = Field(default_factory=list)
    variant: VariantType
    cost_savings: float = Field(default=0.0, ge=0.0)
    engine_name: str  # "prediction", "adaptation", "guardrail", etc.


class AnalyticsMetric(BaseModel):
    """Real-time analytics metric."""
    name: str
    value: float
    trend: str  # "up", "down", "stable"
    change_percent: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BusinessInsight(BaseModel):
    """Business intelligence insight."""
    type: str  # "cost-savings", "engagement-improvement", "risk-prevention"
    description: str
    impact: float
    confidence: float = Field(..., ge=0.0, le=1.0)
    actionable: bool = True
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    supporting_data: Dict[str, Any] = Field(default_factory=dict)


class DemoScenario(BaseModel):
    """Demo presentation scenario."""
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: str
    customer_profiles: List[CustomerProfile] = Field(default_factory=list)
    expected_outcomes: List[PredictedOutcome] = Field(default_factory=list)
    story_flow: List[str] = Field(default_factory=list)  # Presentation steps
    scenario_type: str  # "high-value-promotion", "support-recovery", etc.


class DemoMetrics(BaseModel):
    """Metrics for demo presentation."""
    cost_savings: float = Field(default=0.0, ge=0.0)
    engagement_improvement: float = Field(default=0.0, ge=0.0)
    protected_customers: int = Field(default=0, ge=0)
    channel_optimization: float = Field(default=0.0, ge=0.0)
    brand_risk_reduction: float = Field(default=0.0, ge=0.0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)