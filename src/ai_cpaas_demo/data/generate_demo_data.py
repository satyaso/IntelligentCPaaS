"""Script to generate demo data for the AI-CPaaS demo."""

import json
from pathlib import Path
from typing import List

from .customer_generator import CustomerProfileGenerator
from ..core.models import CustomerProfile


def save_profiles_to_json(profiles: List[CustomerProfile], output_path: Path):
    """Save customer profiles to JSON file."""
    # Convert profiles to dict format
    profiles_data = [profile.model_dump() for profile in profiles]
    
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
    
    profiles_data = convert_datetime(profiles_data)
    
    # Save to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(profiles_data, f, indent=2, default=str)
    
    print(f"✅ Saved {len(profiles)} customer profiles to {output_path}")


def generate_customer_data(count: int = 1000, output_dir: str = "data/demo"):
    """Generate customer profile data."""
    print(f"🚀 Generating {count} customer profiles...")
    
    generator = CustomerProfileGenerator(seed=42)
    profiles = generator.generate_profiles(count=count)
    
    # Analyze the generated data
    high_value = sum(1 for p in profiles if any(
        pref.channel.value == "email" and pref.preference_score > 0.7
        for pref in p.channel_preferences
    ))
    
    medium_value = sum(1 for p in profiles if any(
        pref.channel.value == "whatsapp" and pref.preference_score > 0.6
        for pref in p.channel_preferences
    ))
    
    low_value = count - high_value - medium_value
    
    print(f"\n📊 Profile Distribution:")
    print(f"   High-value customers: {high_value} ({high_value/count*100:.1f}%)")
    print(f"   Medium-value customers: {medium_value} ({medium_value/count*100:.1f}%)")
    print(f"   Low-value customers: {low_value} ({low_value/count*100:.1f}%)")
    
    # Analyze fatigue levels
    fatigue_counts = {
        "low": sum(1 for p in profiles if p.fatigue_level.value == "low"),
        "medium": sum(1 for p in profiles if p.fatigue_level.value == "medium"),
        "high": sum(1 for p in profiles if p.fatigue_level.value == "high"),
    }
    
    print(f"\n😴 Fatigue Level Distribution:")
    for level, count_val in fatigue_counts.items():
        print(f"   {level.capitalize()}: {count_val} ({count_val/count*100:.1f}%)")
    
    # Analyze support tickets
    total_tickets = sum(len(p.support_tickets) for p in profiles)
    angry_tickets = sum(
        1 for p in profiles
        for ticket in p.support_tickets
        if ticket.sentiment.value == "negative"
    )
    
    print(f"\n🎫 Support Ticket Statistics:")
    print(f"   Total tickets: {total_tickets}")
    print(f"   Angry/Negative tickets: {angry_tickets} ({angry_tickets/total_tickets*100:.1f}%)")
    
    # Save to JSON
    output_path = Path(output_dir) / "customer_profiles.json"
    save_profiles_to_json(profiles, output_path)
    
    return profiles


if __name__ == "__main__":
    generate_customer_data(count=1000)
