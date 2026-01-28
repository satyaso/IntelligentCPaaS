"""Base classes for AI agents."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from datetime import datetime

from pydantic import BaseModel, Field


class AgentDecision(BaseModel):
    """Represents a decision made by an AI agent."""
    decision_id: UUID = Field(default_factory=uuid4)
    agent_type: str
    decision_type: str
    timestamp: datetime = Field(default_factory=datetime.now)
    context: Dict[str, Any] = Field(default_factory=dict)
    reasoning: List[str] = Field(default_factory=list)
    confidence: float = Field(..., ge=0.0, le=1.0)
    recommended_actions: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CampaignPlan(BaseModel):
    """Represents a multi-step campaign plan."""
    campaign_id: UUID = Field(default_factory=uuid4)
    name: str
    description: str
    target_segments: List[Dict[str, Any]] = Field(default_factory=list)
    steps: List[Dict[str, Any]] = Field(default_factory=list)
    timing_strategy: Dict[str, Any] = Field(default_factory=dict)
    budget_allocation: Dict[str, float] = Field(default_factory=dict)
    success_metrics: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    estimated_duration: int  # minutes
    estimated_cost: float


class CustomerSegment(BaseModel):
    """Represents a customer segment for targeting."""
    segment_id: UUID = Field(default_factory=uuid4)
    name: str
    criteria: Dict[str, Any]
    size: int
    characteristics: Dict[str, Any] = Field(default_factory=dict)
    preferred_channels: List[str] = Field(default_factory=list)
    engagement_patterns: Dict[str, Any] = Field(default_factory=dict)


class InterventionAction(BaseModel):
    """Represents a protective intervention action."""
    action_id: UUID = Field(default_factory=uuid4)
    action_type: str  # "pause", "redirect", "modify", "delay"
    target_customer: UUID
    reason: str
    severity: str  # "low", "medium", "high"
    recommended_delay: int  # minutes
    alternative_actions: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)


class OptimizationRecommendation(BaseModel):
    """Represents a cost optimization recommendation."""
    recommendation_id: UUID = Field(default_factory=uuid4)
    optimization_type: str  # "channel", "timing", "budget", "content"
    current_cost: float
    optimized_cost: float
    potential_savings: float
    confidence: float = Field(..., ge=0.0, le=1.0)
    implementation_steps: List[str] = Field(default_factory=list)
    risk_assessment: str  # "low", "medium", "high"
    created_at: datetime = Field(default_factory=datetime.now)


class BaseAIAgent(ABC):
    """Abstract base class for AI agents."""

    def __init__(self, agent_name: str, region_name: str = "us-east-1"):
        """Initialize the base AI agent."""
        self.agent_name = agent_name
        self.region_name = region_name
        self.decisions_history: List[AgentDecision] = []

    @abstractmethod
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process a request and return a response."""
        pass

    @abstractmethod
    async def make_decision(self, context: Dict[str, Any]) -> AgentDecision:
        """Make a decision based on the given context."""
        pass

    def _record_decision(self, decision: AgentDecision) -> None:
        """Record a decision in the agent's history."""
        self.decisions_history.append(decision)
        
        # Keep only the last 100 decisions to prevent memory issues
        if len(self.decisions_history) > 100:
            self.decisions_history = self.decisions_history[-100:]

    def get_recent_decisions(self, limit: int = 10) -> List[AgentDecision]:
        """Get recent decisions made by this agent."""
        return self.decisions_history[-limit:] if self.decisions_history else []

    async def _analyze_with_bedrock(self, prompt: str, model_id: str = "anthropic.claude-3-haiku-20240307-v1:0") -> Dict[str, Any]:
        """Analyze using Bedrock Claude (with fallback)."""
        try:
            import boto3
            import json
            from botocore.exceptions import ClientError, NoCredentialsError
            
            bedrock_client = boto3.client('bedrock-runtime', region_name=self.region_name)
            
            response = bedrock_client.invoke_model(
                modelId=model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 1000,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                })
            )
            
            response_body = json.loads(response['body'].read())
            content = response_body['content'][0]['text']
            
            # Try to parse as JSON
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return {"analysis": content, "parsed": False}
                
        except (ClientError, NoCredentialsError, ImportError) as e:
            # Fallback to rule-based analysis
            return await self._fallback_analysis(prompt)

    async def _fallback_analysis(self, prompt: str) -> Dict[str, Any]:
        """Fallback analysis when Bedrock is not available."""
        # Simple rule-based analysis
        return {
            "analysis": "Fallback analysis - Bedrock not available",
            "confidence": 0.5,
            "reasoning": ["Using rule-based fallback due to AWS service unavailability"],
            "parsed": False
        }