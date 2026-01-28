"""Script to generate campaign scenario data for the AI-CPaaS demo."""

import json
from pathlib import Path
from typing import Dict, List

from .campaign_generator import CampaignScenarioGenerator
from ..core.models import CampaignContext


def save_campaigns_to_json(campaigns: Dict[str, List[CampaignContext]], output_path: Path):
    """Save campaign scenarios to JSON file."""
    # Convert campaigns to dict format
    campaigns_data = {}
    for category, campaign_list in campaigns.items():
        campaigns_data[category] = [campaign.model_dump() for campaign in campaign_list]
    
    # Convert datetime objects to ISO format strings
    def convert_datetime(obj):
        if isinstance(obj, dict):
            return {k: convert_datetime(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_datetime(item) for item in obj]
        elif hasattr(obj, 'isoformat'):
            return obj.isoformat()
        else:
            return obj
    
    campaigns_data = convert_datetime(campaigns_data)
    
    # Save to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(campaigns_data, f, indent=2, default=str)
    
    print(f"✅ Saved campaign scenarios to {output_path}")


def generate_campaign_data(output_dir: str = "data/demo"):
    """Generate campaign scenario data."""
    print("🚀 Generating campaign scenarios...")
    
    generator = CampaignScenarioGenerator()
    campaigns = generator.generate_all_scenarios()
    
    # Analyze the generated data
    total_campaigns = sum(len(campaign_list) for campaign_list in campaigns.values())
    
    print(f"\n📊 Campaign Distribution:")
    for category, campaign_list in campaigns.items():
        print(f"   {category.replace('_', ' ').title()}: {len(campaign_list)} campaigns")
    print(f"   Total: {total_campaigns} campaigns")
    
    # Analyze budget impact
    total_budget = 0.0
    total_savings = 0.0
    
    for campaign_list in campaigns.values():
        for campaign in campaign_list:
            if campaign.budget_impact:
                total_budget += campaign.budget_impact.total_cost
                total_savings += campaign.budget_impact.savings_vs_spray_pray
    
    print(f"\n💰 Budget Analysis:")
    print(f"   Total campaign budget: ${total_budget:,.2f}")
    print(f"   Total savings vs spray-and-pray: ${total_savings:,.2f}")
    if total_budget > 0:
        print(f"   Savings percentage: {(total_savings / (total_budget + total_savings)) * 100:.1f}%")
    
    # Analyze channel usage
    channel_counts = {}
    for campaign_list in campaigns.values():
        for campaign in campaign_list:
            for channel in campaign.content.channel_variants.keys():
                channel_counts[channel.value] = channel_counts.get(channel.value, 0) + 1
    
    print(f"\n📱 Channel Usage:")
    for channel, count in sorted(channel_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"   {channel.upper()}: {count} campaigns")
    
    # Save to JSON
    output_path = Path(output_dir) / "campaign_scenarios.json"
    save_campaigns_to_json(campaigns, output_path)
    
    return campaigns


if __name__ == "__main__":
    generate_campaign_data()
