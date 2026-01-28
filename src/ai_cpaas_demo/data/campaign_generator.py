"""Campaign scenario generator for creating realistic demo campaigns."""

from datetime import datetime, timedelta
from typing import Dict, List
from uuid import uuid4

from ..core.models import (
    BrandProfile,
    BudgetAnalysis,
    CampaignConstraints,
    CampaignContext,
    ChannelType,
    ContentTemplate,
    MessageType,
    PredictedOutcome,
)


class CampaignScenarioGenerator:
    """Generates campaign scenarios for demo purposes."""

    def __init__(self):
        """Initialize the campaign generator."""
        self.brand_profile = self._create_brand_profile()

    def generate_all_scenarios(self) -> Dict[str, List[CampaignContext]]:
        """Generate all campaign scenarios."""
        return {
            "promotional": self.generate_promotional_campaigns(),
            "transactional": self.generate_transactional_campaigns(),
            "support_recovery": self.generate_support_recovery_campaigns(),
        }

    def generate_promotional_campaigns(self) -> List[CampaignContext]:
        """Generate promotional campaign templates."""
        campaigns = []

        # Black Friday Campaign
        campaigns.append(
            CampaignContext(
                name="Black Friday 2026 - Flash Sale",
                type=MessageType.PROMOTIONAL,
                target_audience=["high-value", "medium-value"],
                content=ContentTemplate(
                    name="black_friday_flash_sale",
                    content="🎉 BLACK FRIDAY EXCLUSIVE! Get 50% OFF on all premium products. Limited time only - Shop now before midnight! Use code: BF2026",
                    placeholders=["discount_percentage", "promo_code", "expiry_time"],
                    channel_variants={
                        ChannelType.SMS: "BLACK FRIDAY! 50% OFF with code BF2026. Shop now: [link]",
                        ChannelType.EMAIL: "🎉 BLACK FRIDAY EXCLUSIVE!\n\nDear Valued Customer,\n\nGet ready for our biggest sale of the year! Enjoy 50% OFF on all premium products.\n\n✨ Limited Time Offer\n⏰ Ends at Midnight\n🎁 Use Code: BF2026\n\nShop Now: [link]\n\nHappy Shopping!",
                        ChannelType.WHATSAPP: "🎉 BLACK FRIDAY ALERT!\n\nHey! Our biggest sale is LIVE!\n\n💥 50% OFF Everything\n⏰ Ends Tonight at Midnight\n🎁 Code: BF2026\n\nShop here: [link]",
                        ChannelType.VOICE: "Hello! This is a special Black Friday announcement. Get fifty percent off all premium products today only. Use promo code B F 2 0 2 6 at checkout.",
                    },
                    brand_profile=self.brand_profile,
                ),
                constraints=CampaignConstraints(
                    max_budget=50000.0,
                    start_time=datetime.utcnow(),
                    end_time=datetime.utcnow() + timedelta(hours=24),
                    excluded_channels=[],
                    target_segments=["high-value", "medium-value"],
                    respect_fatigue_limits=True,
                    require_guardrail_approval=True,
                ),
                expected_outcomes=self._generate_expected_outcomes(),
                budget_impact=BudgetAnalysis(
                    total_cost=15000.0,
                    cost_per_channel={
                        ChannelType.SMS: 3750.0,
                        ChannelType.WHATSAPP: 2500.0,
                        ChannelType.EMAIL: 500.0,
                        ChannelType.VOICE: 8250.0,
                    },
                    savings_vs_spray_pray=15000.0,  # 30% savings
                    projected_annual_savings=180000.0,
                    roi_percentage=450.0,
                ),
            )
        )

        # Product Launch Campaign
        campaigns.append(
            CampaignContext(
                name="New Product Launch - Premium Series",
                type=MessageType.PROMOTIONAL,
                target_audience=["high-value"],
                content=ContentTemplate(
                    name="product_launch_premium",
                    content="Introducing our NEW Premium Series! Be among the first to experience innovation. Early bird discount: 30% OFF. Reserve yours today!",
                    placeholders=["product_name", "discount", "launch_date"],
                    channel_variants={
                        ChannelType.EMAIL: "🚀 EXCLUSIVE LAUNCH INVITATION\n\nDear [Name],\n\nAs one of our valued customers, you're invited to be among the first to experience our NEW Premium Series.\n\n✨ What's New:\n• Advanced features\n• Premium design\n• Enhanced performance\n\n🎁 Early Bird Offer: 30% OFF\n📅 Limited Availability\n\nReserve Now: [link]",
                        ChannelType.VOICE: "Hello, this is an exclusive invitation for our valued customers. We're launching our new Premium Series, and you're invited to get early access with thirty percent off. Visit our website to learn more.",
                    },
                    brand_profile=self.brand_profile,
                ),
                constraints=CampaignConstraints(
                    max_budget=30000.0,
                    start_time=datetime.utcnow(),
                    end_time=datetime.utcnow() + timedelta(days=7),
                    excluded_channels=[ChannelType.SMS],  # Premium customers prefer email/voice
                    target_segments=["high-value"],
                    respect_fatigue_limits=True,
                    require_guardrail_approval=True,
                ),
                expected_outcomes=self._generate_expected_outcomes(high_value=True),
                budget_impact=BudgetAnalysis(
                    total_cost=8000.0,
                    cost_per_channel={
                        ChannelType.EMAIL: 200.0,
                        ChannelType.VOICE: 6000.0,
                        ChannelType.WHATSAPP: 1800.0,
                    },
                    savings_vs_spray_pray=12000.0,
                    projected_annual_savings=144000.0,
                    roi_percentage=380.0,
                ),
            )
        )

        # Seasonal Sale Campaign
        campaigns.append(
            CampaignContext(
                name="Summer Sale - All Customers",
                type=MessageType.PROMOTIONAL,
                target_audience=["all"],
                content=ContentTemplate(
                    name="summer_sale",
                    content="☀️ SUMMER SALE IS HERE! Enjoy up to 40% OFF on selected items. Refresh your collection today!",
                    placeholders=["discount_range", "category"],
                    channel_variants={
                        ChannelType.SMS: "SUMMER SALE! Up to 40% OFF. Shop now: [link]",
                        ChannelType.WHATSAPP: "☀️ Summer Sale Alert!\n\nUp to 40% OFF on selected items\n🏖️ Perfect time to refresh your collection\n\nBrowse deals: [link]",
                        ChannelType.EMAIL: "☀️ SUMMER SALE IS HERE!\n\nHello,\n\nBeat the heat with our amazing summer deals!\n\n🌊 Up to 40% OFF\n🏖️ Selected Items\n☀️ Limited Time\n\nShop Now: [link]",
                    },
                    brand_profile=self.brand_profile,
                ),
                constraints=CampaignConstraints(
                    max_budget=40000.0,
                    start_time=datetime.utcnow(),
                    end_time=datetime.utcnow() + timedelta(days=14),
                    excluded_channels=[],
                    target_segments=["all"],
                    respect_fatigue_limits=True,
                    require_guardrail_approval=True,
                ),
                expected_outcomes=self._generate_expected_outcomes(),
                budget_impact=BudgetAnalysis(
                    total_cost=20000.0,
                    cost_per_channel={
                        ChannelType.SMS: 7500.0,
                        ChannelType.WHATSAPP: 5000.0,
                        ChannelType.EMAIL: 1000.0,
                        ChannelType.VOICE: 6500.0,
                    },
                    savings_vs_spray_pray=20000.0,
                    projected_annual_savings=240000.0,
                    roi_percentage=420.0,
                ),
            )
        )

        return campaigns

    def generate_transactional_campaigns(self) -> List[CampaignContext]:
        """Generate transactional message templates."""
        campaigns = []

        # Order Confirmation
        campaigns.append(
            CampaignContext(
                name="Order Confirmation",
                type=MessageType.TRANSACTIONAL,
                target_audience=["all"],
                content=ContentTemplate(
                    name="order_confirmation",
                    content="Order confirmed! Your order #[ORDER_ID] has been received and is being processed. Expected delivery: [DELIVERY_DATE]",
                    placeholders=["order_id", "delivery_date", "order_total"],
                    channel_variants={
                        ChannelType.SMS: "Order #[ORDER_ID] confirmed! Delivery by [DATE]. Track: [link]",
                        ChannelType.EMAIL: "✅ Order Confirmation\n\nThank you for your order!\n\nOrder #: [ORDER_ID]\nTotal: $[AMOUNT]\nExpected Delivery: [DATE]\n\nTrack your order: [link]",
                        ChannelType.WHATSAPP: "✅ Order Confirmed!\n\nOrder #[ORDER_ID]\n💰 Total: $[AMOUNT]\n📦 Delivery: [DATE]\n\nTrack here: [link]",
                    },
                    brand_profile=self.brand_profile,
                ),
                constraints=CampaignConstraints(
                    respect_fatigue_limits=False,  # Transactional messages bypass fatigue
                    require_guardrail_approval=False,
                ),
            )
        )

        # Shipping Update
        campaigns.append(
            CampaignContext(
                name="Shipping Update",
                type=MessageType.TRANSACTIONAL,
                target_audience=["all"],
                content=ContentTemplate(
                    name="shipping_update",
                    content="📦 Your order #[ORDER_ID] has shipped! Track your package: [TRACKING_LINK]",
                    placeholders=["order_id", "tracking_number", "carrier"],
                    channel_variants={
                        ChannelType.SMS: "Shipped! Order #[ORDER_ID]. Track: [link]",
                        ChannelType.EMAIL: "📦 Your Order Has Shipped!\n\nOrder #: [ORDER_ID]\nTracking #: [TRACKING]\nCarrier: [CARRIER]\n\nTrack Package: [link]",
                        ChannelType.WHATSAPP: "📦 Package on the way!\n\nOrder #[ORDER_ID]\n🚚 Tracking: [TRACKING]\n\nTrack here: [link]",
                    },
                    brand_profile=self.brand_profile,
                ),
                constraints=CampaignConstraints(
                    respect_fatigue_limits=False,
                    require_guardrail_approval=False,
                ),
            )
        )

        # Delivery Confirmation
        campaigns.append(
            CampaignContext(
                name="Delivery Confirmation",
                type=MessageType.TRANSACTIONAL,
                target_audience=["all"],
                content=ContentTemplate(
                    name="delivery_confirmation",
                    content="✅ Delivered! Your order #[ORDER_ID] was delivered successfully. Enjoy your purchase!",
                    placeholders=["order_id", "delivery_time"],
                    channel_variants={
                        ChannelType.SMS: "Delivered! Order #[ORDER_ID]. Enjoy!",
                        ChannelType.EMAIL: "✅ Delivery Confirmed\n\nYour order #[ORDER_ID] was delivered at [TIME].\n\nWe hope you love your purchase!\n\nRate your experience: [link]",
                        ChannelType.WHATSAPP: "✅ Delivered!\n\nOrder #[ORDER_ID]\n📍 Delivered at [TIME]\n\nHow was your experience? [link]",
                    },
                    brand_profile=self.brand_profile,
                ),
                constraints=CampaignConstraints(
                    respect_fatigue_limits=False,
                    require_guardrail_approval=False,
                ),
            )
        )

        return campaigns

    def generate_support_recovery_campaigns(self) -> List[CampaignContext]:
        """Generate support recovery scenarios."""
        campaigns = []

        # Angry Customer Recovery
        campaigns.append(
            CampaignContext(
                name="Support Recovery - Angry Customer",
                type=MessageType.SUPPORT,
                target_audience=["angry_customers"],
                content=ContentTemplate(
                    name="angry_customer_recovery",
                    content="We sincerely apologize for your recent experience. Your satisfaction is our priority. We'd like to make this right. Please contact us at [SUPPORT_CONTACT]",
                    placeholders=["customer_name", "ticket_id", "support_contact"],
                    channel_variants={
                        ChannelType.EMAIL: "Dear [NAME],\n\nWe sincerely apologize for your recent experience with us. Your satisfaction is our top priority, and we clearly fell short.\n\nWe'd like to make this right. Our support team is ready to help resolve your issue immediately.\n\nTicket #: [TICKET_ID]\nDirect Line: [PHONE]\nEmail: [EMAIL]\n\nWe value your business and hope to regain your trust.\n\nSincerely,\nCustomer Support Team",
                        ChannelType.VOICE: "Hello, this is our customer support team. We're calling regarding your recent experience. We sincerely apologize and would like to make things right. A support specialist is standing by to help you.",
                    },
                    brand_profile=self.brand_profile,
                ),
                constraints=CampaignConstraints(
                    excluded_channels=[ChannelType.SMS, ChannelType.WHATSAPP],  # Too impersonal
                    respect_fatigue_limits=False,  # Critical recovery
                    require_guardrail_approval=True,  # Must check sentiment first
                ),
            )
        )

        # Complaint Resolution Follow-up
        campaigns.append(
            CampaignContext(
                name="Complaint Resolution Follow-up",
                type=MessageType.SUPPORT,
                target_audience=["resolved_complaints"],
                content=ContentTemplate(
                    name="complaint_followup",
                    content="We wanted to follow up on your recent issue (Ticket #[TICKET_ID]). We hope everything has been resolved to your satisfaction. Your feedback matters to us.",
                    placeholders=["ticket_id", "resolution_date"],
                    channel_variants={
                        ChannelType.EMAIL: "Hello [NAME],\n\nWe wanted to follow up on your recent support ticket (#[TICKET_ID]).\n\nWe hope the issue has been resolved to your satisfaction. Your feedback is important to us.\n\nIf you have any remaining concerns, please don't hesitate to reach out.\n\nThank you for your patience.\n\nBest regards,\nSupport Team",
                        ChannelType.WHATSAPP: "Hi [NAME],\n\nFollowing up on ticket #[TICKET_ID].\n\nWe hope everything is resolved! 😊\n\nAny concerns? Let us know.\n\nThanks for your patience!",
                    },
                    brand_profile=self.brand_profile,
                ),
                constraints=CampaignConstraints(
                    respect_fatigue_limits=True,
                    require_guardrail_approval=True,
                ),
            )
        )

        return campaigns

    def _create_brand_profile(self) -> BrandProfile:
        """Create a brand profile for campaigns."""
        return BrandProfile(
            brand_name="AI-CPaaS Demo Brand",
            voice_tone="professional-friendly",
            key_messages=[
                "Customer satisfaction is our priority",
                "Innovation meets reliability",
                "Your trusted partner",
            ],
            prohibited_words=["cheap", "spam", "scam", "fake"],
            style_guidelines={
                "emoji_usage": "moderate",
                "formality": "professional-casual",
                "personalization": "high",
            },
        )

    def _generate_expected_outcomes(self, high_value: bool = False) -> List[PredictedOutcome]:
        """Generate expected outcomes for campaigns."""
        if high_value:
            return [
                PredictedOutcome(
                    channel=ChannelType.EMAIL,
                    engagement_probability=0.75,
                    cost_estimate=200.0,
                    expected_roi=3.8,
                    confidence=0.85,
                ),
                PredictedOutcome(
                    channel=ChannelType.VOICE,
                    engagement_probability=0.65,
                    cost_estimate=6000.0,
                    expected_roi=3.2,
                    confidence=0.80,
                ),
            ]
        else:
            return [
                PredictedOutcome(
                    channel=ChannelType.SMS,
                    engagement_probability=0.55,
                    cost_estimate=7500.0,
                    expected_roi=4.2,
                    confidence=0.75,
                ),
                PredictedOutcome(
                    channel=ChannelType.WHATSAPP,
                    engagement_probability=0.62,
                    cost_estimate=5000.0,
                    expected_roi=4.5,
                    confidence=0.78,
                ),
                PredictedOutcome(
                    channel=ChannelType.EMAIL,
                    engagement_probability=0.48,
                    cost_estimate=1000.0,
                    expected_roi=5.0,
                    confidence=0.70,
                ),
            ]
