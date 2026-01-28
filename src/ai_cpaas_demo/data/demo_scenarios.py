"""Demo presentation scenario generator for AI-CPaaS demonstrations."""

from datetime import datetime, timedelta
from typing import Dict, List
from uuid import uuid4

from ..core.models import (
    ChannelType,
    CustomerProfile,
    DemoMetrics,
    DemoScenario,
    FatigueLevel,
    MessageType,
    PredictedOutcome,
    SentimentType,
)


class DemoScenarioGenerator:
    """Generates demo presentation scenarios showing before/after AI comparisons."""

    def __init__(self, customer_profiles: List[CustomerProfile]):
        """Initialize with customer profiles."""
        self.customer_profiles = customer_profiles
        
        # Segment customers
        self.high_value_customers = self._filter_high_value()
        self.angry_customers = self._filter_angry()
        self.fatigued_customers = self._filter_fatigued()

    def generate_all_scenarios(self) -> Dict[str, DemoScenario]:
        """Generate all demo scenarios."""
        return {
            "spray_and_pray_problem": self.generate_spray_and_pray_scenario(),
            "ai_orchestrated_solution": self.generate_ai_orchestrated_scenario(),
            "cost_savings_demo": self.generate_cost_savings_scenario(),
            "fatigue_protection_demo": self.generate_fatigue_protection_scenario(),
            "tone_deaf_prevention": self.generate_tone_deaf_prevention_scenario(),
        }

    def generate_spray_and_pray_scenario(self) -> DemoScenario:
        """Generate 'before AI' spray-and-pray problem scenario."""
        # Select diverse customer sample
        sample_customers = (
            self.high_value_customers[:3] +
            self.angry_customers[:2] +
            self.fatigued_customers[:2]
        )
        
        story_flow = [
            "📢 BEFORE AI: Traditional Spray-and-Pray Approach",
            "",
            "Problem: Marketing team sends Black Friday promotion to ALL 1000 customers",
            "• Same message sent via ALL channels (SMS, Email, WhatsApp, Voice)",
            "• No personalization or timing optimization",
            "• No consideration of customer sentiment or fatigue",
            "",
            "❌ What Goes Wrong:",
            "",
            "1. HIGH-VALUE CUSTOMERS (3 shown):",
            "   • Receive 4 identical messages across all channels",
            "   • Feel spammed and annoyed by repetition",
            "   • Voice calls interrupt important meetings",
            "   • Result: Brand perception damaged, potential churn",
            "",
            "2. ANGRY CUSTOMERS (2 shown):",
            "   • Already upset about unresolved support issues",
            "   • Receive promotional messages while angry",
            "   • Perceive company as tone-deaf and uncaring",
            "   • Result: Escalated complaints, social media backlash",
            "",
            "3. FATIGUED CUSTOMERS (2 shown):",
            "   • Already received 10+ messages this week",
            "   • Showing disengagement signals (low open rates)",
            "   • Promotional spam pushes them to unsubscribe",
            "   • Result: Lost customers, reduced lifetime value",
            "",
            "💰 COST IMPACT:",
            "• Total spend: $50,000 (1000 customers × 4 channels × $12.50 avg)",
            "• SMS: 1000 × $0.05 = $50",
            "• WhatsApp: 1000 × $0.02 = $20",
            "• Email: 1000 × $0.001 = $1",
            "• Voice: 1000 × $0.15 = $150",
            "• Total per customer: $0.221",
            "• Campaign total: $221 × 1000 = $221,000 (with overhead)",
            "",
            "📊 RESULTS:",
            "• Engagement rate: 12% (low due to poor targeting)",
            "• Unsubscribe rate: 8% (high due to spam perception)",
            "• Complaints: 45 (angry customers escalate)",
            "• Brand damage: Immeasurable",
            "• ROI: Negative (cost > revenue from poor engagement)",
        ]
        
        return DemoScenario(
            name="Spray-and-Pray Problem",
            description="Traditional mass marketing approach without AI orchestration",
            customer_profiles=sample_customers,
            expected_outcomes=[],  # No optimization
            story_flow=story_flow,
            scenario_type="before_ai_problem",
        )

    def generate_ai_orchestrated_scenario(self) -> DemoScenario:
        """Generate 'after AI' orchestrated solution scenario."""
        sample_customers = (
            self.high_value_customers[:3] +
            self.angry_customers[:2] +
            self.fatigued_customers[:2]
        )
        
        story_flow = [
            "🤖 AFTER AI: Intelligent Orchestration",
            "",
            "Solution: AI analyzes each customer and orchestrates personalized approach",
            "",
            "✅ How AI Helps:",
            "",
            "1. HIGH-VALUE CUSTOMERS (3 shown):",
            "   AI Decision:",
            "   • Prediction Engine: 85% prefer email, 65% engage with voice",
            "   • Timing: Send during preferred hours (9-11 AM)",
            "   • Channel: Email first, voice follow-up only if no response",
            "   • Content: Personalized with VIP early access offer",
            "   ",
            "   Result:",
            "   • Only 1-2 channels used per customer (not 4)",
            "   • 75% engagement rate (vs 12% spray-and-pray)",
            "   • Positive brand perception maintained",
            "   • Cost: $8 per customer (vs $50)",
            "",
            "2. ANGRY CUSTOMERS (2 shown):",
            "   AI Decision:",
            "   • Guardrail Engine: BLOCKS promotional messages",
            "   • Sentiment Analysis: Detects negative sentiment (-0.8)",
            "   • Customer Protection Agent: Suggests support follow-up instead",
            "   • Alternative: Route to support recovery campaign",
            "   ",
            "   Result:",
            "   • No promotional spam sent",
            "   • Support team notified for proactive outreach",
            "   • Customer feels heard and valued",
            "   • Cost: $0 (message blocked, crisis averted)",
            "",
            "3. FATIGUED CUSTOMERS (2 shown):",
            "   AI Decision:",
            "   • Fatigue Engine: Detects high message frequency (10+ this week)",
            "   • Protection Agent: Pauses non-critical communications",
            "   • Timing: Delays message by 5 days for recovery",
            "   • Channel: Uses least intrusive (email only)",
            "   ",
            "   Result:",
            "   • Customer given breathing room",
            "   • Unsubscribe prevented",
            "   • Future engagement preserved",
            "   • Cost: $0.001 (email only, delayed)",
            "",
            "💰 COST IMPACT:",
            "• High-value: 229 customers × $8 = $1,832",
            "• Medium-value: 658 customers × $3 = $1,974",
            "• Low-value: 113 customers × $1 = $113",
            "• Angry: 0 customers × $0 = $0 (blocked)",
            "• Fatigued: 0 customers × $0 = $0 (delayed)",
            "• Total: $3,919",
            "",
            "📊 RESULTS:",
            "• Engagement rate: 62% (5x improvement)",
            "• Unsubscribe rate: 0.5% (16x reduction)",
            "• Complaints: 2 (95% reduction)",
            "• Brand protection: Priceless",
            "• ROI: 450% (high engagement, low cost)",
            "",
            "💡 KEY INSIGHTS:",
            "• Cost savings: $217,081 (98% reduction)",
            "• Engagement improvement: 5x",
            "• Customer protection: 45 complaints prevented",
            "• Brand risk reduction: 95%",
        ]
        
        expected_outcomes = [
            PredictedOutcome(
                channel=ChannelType.EMAIL,
                engagement_probability=0.75,
                cost_estimate=1832.0,
                expected_roi=4.5,
                confidence=0.85,
            ),
            PredictedOutcome(
                channel=ChannelType.WHATSAPP,
                engagement_probability=0.62,
                cost_estimate=1974.0,
                expected_roi=4.2,
                confidence=0.78,
            ),
        ]
        
        return DemoScenario(
            name="AI Orchestrated Solution",
            description="Intelligent AI-powered campaign orchestration with customer protection",
            customer_profiles=sample_customers,
            expected_outcomes=expected_outcomes,
            story_flow=story_flow,
            scenario_type="after_ai_solution",
        )

    def generate_cost_savings_scenario(self) -> DemoScenario:
        """Generate cost savings and ROI demonstration."""
        story_flow = [
            "💰 COST SAVINGS ANALYSIS",
            "",
            "Comparing Traditional vs AI-Orchestrated Approach",
            "",
            "📊 SPRAY-AND-PRAY COSTS:",
            "• 1000 customers × 4 channels = 4000 messages",
            "• SMS: 1000 × $0.05 = $50",
            "• WhatsApp: 1000 × $0.02 = $20",
            "• Email: 1000 × $0.001 = $1",
            "• Voice: 1000 × $0.15 = $150",
            "• Overhead (platform, labor): $220,000",
            "• TOTAL: $221,000 per campaign",
            "",
            "🤖 AI-ORCHESTRATED COSTS:",
            "• Intelligent channel selection (avg 1.5 channels per customer)",
            "• High-value (229): Email + Voice = $1,832",
            "• Medium-value (658): WhatsApp + Email = $1,974",
            "• Low-value (113): SMS only = $113",
            "• Blocked/Delayed (0): $0",
            "• AI processing: $1,000",
            "• TOTAL: $3,919 per campaign",
            "",
            "💵 SAVINGS PER CAMPAIGN:",
            "• Direct savings: $217,081 (98.2% reduction)",
            "• Improved engagement: 5x higher conversion",
            "• Reduced churn: 16x fewer unsubscribes",
            "• Brand protection: Immeasurable",
            "",
            "📈 ANNUAL PROJECTIONS:",
            "• Campaigns per year: 52 (weekly)",
            "• Annual spray-and-pray cost: $11,492,000",
            "• Annual AI-orchestrated cost: $203,788",
            "• ANNUAL SAVINGS: $11,288,212",
            "",
            "🎯 ROI BREAKDOWN:",
            "• Cost reduction: 98.2%",
            "• Engagement improvement: 417%",
            "• Revenue per campaign: $17,600 (AI) vs $2,650 (spray-and-pray)",
            "• ROI: 450% (AI) vs -12% (spray-and-pray)",
            "• Payback period: Immediate (first campaign)",
            "",
            "✨ ADDITIONAL BENEFITS:",
            "• Customer satisfaction: +85%",
            "• Brand perception: +92%",
            "• Support ticket reduction: -78%",
            "• Customer lifetime value: +34%",
        ]
        
        return DemoScenario(
            name="Cost Savings Demonstration",
            description="Detailed cost analysis showing ROI of AI orchestration",
            customer_profiles=[],
            expected_outcomes=[],
            story_flow=story_flow,
            scenario_type="cost_savings",
        )

    def generate_fatigue_protection_scenario(self) -> DemoScenario:
        """Generate fatigue protection demonstration."""
        fatigued_sample = self.fatigued_customers[:5]
        
        story_flow = [
            "😴 FATIGUE PROTECTION IN ACTION",
            "",
            "Scenario: Customer has received 12 messages in the past 7 days",
            "",
            "📊 CUSTOMER STATE:",
            "• Messages this week: 12 (limit: 10)",
            "• Open rate trend: 85% → 45% → 12% (declining)",
            "• Last engagement: 5 days ago",
            "• Disengagement signals: 3 detected",
            "  - Low engagement (< 20% open rate)",
            "  - No clicks in last 10 messages",
            "  - Increasing time between opens",
            "",
            "❌ WITHOUT AI PROTECTION:",
            "• Marketing sends 13th message (Black Friday promo)",
            "• Customer feels overwhelmed and spammed",
            "• Clicks 'unsubscribe' button",
            "• Lost customer: -$2,400 lifetime value",
            "• Negative review posted online",
            "",
            "✅ WITH AI PROTECTION:",
            "",
            "1. FATIGUE DETECTION:",
            "   • Anti-Fatigue Engine analyzes communication history",
            "   • Detects: 12 messages > 10 weekly limit",
            "   • Calculates fatigue score: 0.85 (high)",
            "   • Identifies disengagement pattern",
            "",
            "2. PROTECTION AGENT DECISION:",
            "   • Blocks non-critical promotional message",
            "   • Logs decision: 'Customer protection - fatigue'",
            "   • Suggests: Wait 5 days for recovery",
            "   • Alternative: Send personalized re-engagement later",
            "",
            "3. RECOVERY PERIOD:",
            "   • No messages sent for 5 days",
            "   • Customer fatigue score drops: 0.85 → 0.35",
            "   • Engagement signals improve",
            "   • Customer feels respected, not spammed",
            "",
            "4. RE-ENGAGEMENT:",
            "   • After recovery, send personalized offer",
            "   • Content: 'We noticed you've been busy...'",
            "   • Channel: Email (least intrusive)",
            "   • Result: 68% open rate, 34% click rate",
            "",
            "💡 OUTCOME:",
            "• Customer retained: +$2,400 lifetime value",
            "• Positive brand perception maintained",
            "• Future engagement preserved",
            "• Cost: $0.001 (delayed email)",
            "",
            "📈 SCALE IMPACT:",
            "• Fatigued customers protected: 128 (12.8%)",
            "• Unsubscribes prevented: 102 (80% would have churned)",
            "• Lifetime value preserved: $244,800",
            "• Brand reputation: Protected",
        ]
        
        return DemoScenario(
            name="Fatigue Protection Demo",
            description="How AI prevents customer fatigue and churn",
            customer_profiles=fatigued_sample,
            expected_outcomes=[],
            story_flow=story_flow,
            scenario_type="fatigue_protection",
        )

    def generate_tone_deaf_prevention_scenario(self) -> DemoScenario:
        """Generate tone-deaf messaging prevention demonstration."""
        angry_sample = self.angry_customers[:3]
        
        story_flow = [
            "🚫 TONE-DEAF MESSAGING PREVENTION",
            "",
            "Scenario: Customer submitted angry complaint 2 hours ago",
            "",
            "📊 CUSTOMER STATE:",
            "• Support ticket: #12345 (Priority: HIGH)",
            "• Issue: 'Product arrived damaged, terrible service!'",
            "• Sentiment: NEGATIVE (-0.92 confidence: 95%)",
            "• Status: OPEN (unresolved)",
            "• Customer value: HIGH ($5,200 lifetime)",
            "",
            "❌ WITHOUT AI GUARDRAILS:",
            "",
            "Marketing Campaign Triggers:",
            "• Black Friday promotion scheduled",
            "• Customer in 'high-value' segment",
            "• Automated system sends:",
            "  '🎉 AMAZING DEALS! Shop our Black Friday sale!'",
            "",
            "Customer Reaction:",
            "• Receives promotional message while angry",
            "• Feels completely ignored and disrespected",
            "• Posts angry review: '1 star - They spam me with ads",
            "  while my issue is unresolved. Terrible company!'",
            "• Escalates to social media",
            "• Demands refund and cancels account",
            "",
            "Business Impact:",
            "• Lost customer: -$5,200 lifetime value",
            "• Negative review: -15 potential customers",
            "• Social media damage: -$12,000 brand value",
            "• Support escalation: +4 hours labor",
            "• TOTAL COST: $17,200+",
            "",
            "✅ WITH AI GUARDRAILS:",
            "",
            "1. SENTIMENT ANALYSIS:",
            "   • Comprehend analyzes support ticket",
            "   • Detects: NEGATIVE sentiment (-0.92)",
            "   • Keywords: 'terrible', 'damaged', 'angry'",
            "   • Risk level: HIGH",
            "",
            "2. GUARDRAIL DECISION:",
            "   • Safety Guardrail Engine: BLOCKS promotional message",
            "   • Reasoning: 'Customer has active negative sentiment'",
            "   • Risk assessment: 'High probability of escalation'",
            "   • Logs decision for audit trail",
            "",
            "3. CUSTOMER PROTECTION AGENT:",
            "   • Detects blocked message",
            "   • Analyzes customer history and value",
            "   • Recommends: Priority support escalation",
            "   • Suggests: Proactive recovery outreach",
            "",
            "4. ALTERNATIVE ACTION:",
            "   • Support team notified immediately",
            "   • Manager assigned to case",
            "   • Proactive call: 'We saw your issue, let's fix it'",
            "   • Expedited resolution + goodwill gesture",
            "",
            "5. RECOVERY OUTCOME:",
            "   • Issue resolved within 4 hours",
            "   • Customer receives personal apology",
            "   • Goodwill: Free replacement + discount",
            "   • Customer posts: '5 stars - They made it right!'",
            "",
            "💡 OUTCOME:",
            "• Customer retained: +$5,200 lifetime value",
            "• Positive review: +8 new customers",
            "• Brand reputation: Protected",
            "• Support efficiency: +2 hours saved",
            "• TOTAL VALUE: $22,400+",
            "",
            "📈 SCALE IMPACT:",
            "• Angry customers protected: 28 (2.8%)",
            "• Escalations prevented: 23 (82%)",
            "• Lifetime value preserved: $145,600",
            "• Negative reviews prevented: 23",
            "• Brand reputation: Safeguarded",
            "",
            "🎯 KEY INSIGHT:",
            "AI Guardrails don't just save money—they protect your brand",
            "and turn potential disasters into loyalty opportunities.",
        ]
        
        return DemoScenario(
            name="Tone-Deaf Prevention Demo",
            description="How AI prevents sending promotional messages to angry customers",
            customer_profiles=angry_sample,
            expected_outcomes=[],
            story_flow=story_flow,
            scenario_type="tone_deaf_prevention",
        )

    def _filter_high_value(self) -> List[CustomerProfile]:
        """Filter high-value customers (prefer email/voice)."""
        return [
            p for p in self.customer_profiles
            if any(
                pref.channel == ChannelType.EMAIL and pref.preference_score > 0.7
                for pref in p.channel_preferences
            )
        ]

    def _filter_angry(self) -> List[CustomerProfile]:
        """Filter customers with negative sentiment."""
        return [
            p for p in self.customer_profiles
            if any(
                ticket.sentiment == SentimentType.NEGATIVE
                for ticket in p.support_tickets
            )
        ]

    def _filter_fatigued(self) -> List[CustomerProfile]:
        """Filter fatigued customers."""
        return [
            p for p in self.customer_profiles
            if p.fatigue_level in [FatigueLevel.MEDIUM, FatigueLevel.HIGH]
        ]
