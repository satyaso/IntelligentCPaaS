"""Core interfaces and abstract base classes for the AI-CPaaS demo system."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from .models import (
    AnalyticsMetric,
    BusinessInsight,
    ChannelType,
    CustomerProfile,
    MessageType,
    UrgencyLevel,
    VariantType,
)


class PredictionRequest(BaseModel):
    """Request for channel prediction."""
    customer_id: UUID
    message_type: MessageType
    urgency: UrgencyLevel
    content_length: int
    variant: VariantType = VariantType.AWS


class PredictionResult(BaseModel):
    """Result of channel prediction."""
    channel: ChannelType
    confidence: float = Field(..., ge=0.0, le=1.0)
    cost_estimate: float = Field(..., ge=0.0)
    engagement_probability: float = Field(..., ge=0.0, le=1.0)
    reasoning: List[str] = Field(default_factory=list)


class AdaptationRequest(BaseModel):
    """Request for content adaptation."""
    original_content: str
    target_channel: ChannelType
    brand_guidelines: Optional[Dict[str, Any]] = None
    max_length: Optional[int] = None
    variant: VariantType = VariantType.AWS


class ContentChange(BaseModel):
    """Record of content modification."""
    change_type: str  # "shortened", "expanded", "reformatted", etc.
    original_text: str
    modified_text: str
    reason: str


class AdaptationResult(BaseModel):
    """Result of content adaptation."""
    adapted_content: str
    preserved_elements: List[str] = Field(default_factory=list)
    modifications: List[ContentChange] = Field(default_factory=list)
    quality_score: float = Field(..., ge=0.0, le=1.0)


class GuardrailRequest(BaseModel):
    """Request for safety guardrail check."""
    customer_id: UUID
    proposed_message: str
    message_type: MessageType
    recent_interactions: List[Dict[str, Any]] = Field(default_factory=list)
    variant: VariantType = VariantType.AWS


class GuardrailResult(BaseModel):
    """Result of safety guardrail check."""
    approved: bool
    risk_level: str  # "low", "medium", "high"
    blocked_reasons: List[str] = Field(default_factory=list)
    alternative_actions: List[str] = Field(default_factory=list)
    confidence: float = Field(..., ge=0.0, le=1.0)


class FatigueCheckRequest(BaseModel):
    """Request for fatigue protection check."""
    customer_id: UUID
    proposed_message: Dict[str, Any]
    current_frequency: Dict[str, int]
    recent_engagement: Dict[str, Any]
    variant: VariantType = VariantType.AWS


class FatigueProtectionResult(BaseModel):
    """Result of fatigue protection check."""
    allow_message: bool
    fatigue_level: str  # "low", "medium", "high"
    recommended_delay: int  # minutes
    protection_reason: List[str] = Field(default_factory=list)
    alternative_actions: List[str] = Field(default_factory=list)


class AnalyticsRequest(BaseModel):
    """Request for analytics processing."""
    time_range: Dict[str, Any]
    metrics: List[str] = Field(default_factory=list)
    filters: Dict[str, Any] = Field(default_factory=dict)
    aggregation: str = "hourly"  # "hourly", "daily", "weekly"


class AnalyticsResult(BaseModel):
    """Result of analytics processing."""
    metrics: List[AnalyticsMetric] = Field(default_factory=list)
    trends: List[Dict[str, Any]] = Field(default_factory=list)
    alerts: List[Dict[str, Any]] = Field(default_factory=list)
    insights: List[BusinessInsight] = Field(default_factory=list)
    export_url: Optional[str] = None


# Abstract base classes for AI engines

class PredictionEngine(ABC):
    """Abstract base class for prediction engines."""

    @abstractmethod
    async def predict_channel(self, request: PredictionRequest) -> PredictionResult:
        """Predict the optimal channel for a customer and message."""
        pass

    @abstractmethod
    async def analyze_engagement_patterns(self, customer_id: UUID) -> Dict[str, Any]:
        """Analyze customer engagement patterns across channels."""
        pass

    @abstractmethod
    async def calculate_channel_scores(
        self, customer_id: UUID, message_type: MessageType
    ) -> Dict[ChannelType, float]:
        """Calculate probability scores for each available channel."""
        pass


class ContentAdaptationEngine(ABC):
    """Abstract base class for content adaptation engines."""

    @abstractmethod
    async def adapt_content(self, request: AdaptationRequest) -> AdaptationResult:
        """Adapt content for the target channel."""
        pass

    @abstractmethod
    async def shrink_for_sms(self, content: str, max_length: int = 160) -> str:
        """Intelligently shrink content for SMS while preserving key elements."""
        pass

    @abstractmethod
    async def expand_for_rich_media(
        self, content: str, channel: ChannelType
    ) -> str:
        """Expand content with rich media for email/WhatsApp."""
        pass


class SafetyGuardrail(ABC):
    """Abstract base class for safety guardrail systems."""

    @abstractmethod
    async def check_safety(self, request: GuardrailRequest) -> GuardrailResult:
        """Check if a message is safe to send to a customer."""
        pass

    @abstractmethod
    async def analyze_customer_sentiment(self, customer_id: UUID) -> Dict[str, Any]:
        """Analyze recent customer sentiment and interactions."""
        pass

    @abstractmethod
    async def check_support_issues(self, customer_id: UUID) -> bool:
        """Check if customer has unresolved support issues."""
        pass


class AntiFatigueProtection(ABC):
    """Abstract base class for anti-fatigue protection systems."""

    @abstractmethod
    async def check_fatigue(self, request: FatigueCheckRequest) -> FatigueProtectionResult:
        """Check if sending a message would cause customer fatigue."""
        pass

    @abstractmethod
    async def track_communication_frequency(
        self, customer_id: UUID, channel: ChannelType
    ) -> None:
        """Track communication frequency for a customer."""
        pass

    @abstractmethod
    async def detect_disengagement_signals(self, customer_id: UUID) -> List[str]:
        """Detect signals indicating customer disengagement."""
        pass


class RealTimeAnalytics(ABC):
    """Abstract base class for real-time analytics engines."""

    @abstractmethod
    async def process_communication_event(self, event: Dict[str, Any]) -> None:
        """Process a communication event in real-time."""
        pass

    @abstractmethod
    async def get_analytics(self, request: AnalyticsRequest) -> AnalyticsResult:
        """Get analytics data for specified time range and metrics."""
        pass

    @abstractmethod
    async def calculate_cost_savings(
        self,
        optimized_cost: float,
        spray_pray_cost: float,
        time_period_days: int = 30,
    ) -> Dict[str, float]:
        """Calculate cost savings vs spray-and-pray approach."""
        pass

    @abstractmethod
    async def process_analytics(self, request: AnalyticsRequest) -> AnalyticsResult:
        """Process analytics request and return insights."""
        pass

    @abstractmethod
    async def extract_sentiment_and_topics(self, content: str) -> Dict[str, Any]:
        """Extract sentiment and topics from communication content."""
        pass

    @abstractmethod
    async def detect_trends(self, metrics: List[AnalyticsMetric]) -> List[Dict[str, Any]]:
        """Detect trends in communication patterns."""
        pass


class CPaaSProvider(ABC):
    """Abstract base class for CPaaS service providers."""

    @abstractmethod
    async def send_sms(self, phone_number: str, message: str, **kwargs) -> Dict[str, Any]:
        """Send SMS message."""
        pass

    @abstractmethod
    async def send_whatsapp(
        self, phone_number: str, message: str, **kwargs
    ) -> Dict[str, Any]:
        """Send WhatsApp message."""
        pass

    @abstractmethod
    async def send_email(
        self, email_address: str, subject: str, content: str, **kwargs
    ) -> Dict[str, Any]:
        """Send email message."""
        pass

    @abstractmethod
    async def make_voice_call(
        self, phone_number: str, message: str, **kwargs
    ) -> Dict[str, Any]:
        """Make voice call."""
        pass


