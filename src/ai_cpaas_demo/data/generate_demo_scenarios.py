"""Script to generate demo presentation scenarios."""

import json
from pathlib import Path
from typing import Dict

from .customer_generator import CustomerProfileGenerator
from .demo_scenarios import DemoScenarioGenerator
from ..core.models import DemoScenario


def save_scenarios_to_json(scenarios: Dict[str, DemoScenario], output_path: Path):
    """Save demo scenarios to JSON file."""
    # Convert scenarios to dict format
    scenarios_data = {}
    for key, scenario in scenarios.items():
        scenarios_data[key] = scenario.model_dump()
    
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
    
    scenarios_data = convert_datetime(scenarios_data)
    
    # Save to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(scenarios_data, f, indent=2, default=str)
    
    print(f"✅ Saved demo scenarios to {output_path}")


def generate_demo_scenarios(output_dir: str = "data/demo"):
    """Generate demo presentation scenarios."""
    print("🚀 Generating demo presentation scenarios...")
    
    # First, generate customer profiles for scenario context
    print("   Loading customer profiles...")
    customer_generator = CustomerProfileGenerator(seed=42)
    customer_profiles = customer_generator.generate_profiles(count=1000)
    
    # Generate scenarios
    print("   Creating before/after AI scenarios...")
    scenario_generator = DemoScenarioGenerator(customer_profiles)
    scenarios = scenario_generator.generate_all_scenarios()
    
    # Analyze the generated scenarios
    print(f"\n📊 Generated Scenarios:")
    for key, scenario in scenarios.items():
        print(f"   {scenario.name}")
        print(f"      Type: {scenario.scenario_type}")
        print(f"      Story steps: {len(scenario.story_flow)}")
        print(f"      Customer samples: {len(scenario.customer_profiles)}")
        print()
    
    # Calculate metrics
    total_story_steps = sum(len(s.story_flow) for s in scenarios.values())
    total_customers_shown = sum(len(s.customer_profiles) for s in scenarios.values())
    
    print(f"📈 Summary:")
    print(f"   Total scenarios: {len(scenarios)}")
    print(f"   Total story steps: {total_story_steps}")
    print(f"   Customer examples: {total_customers_shown}")
    
    # Save to JSON
    output_path = Path(output_dir) / "demo_scenarios.json"
    save_scenarios_to_json(scenarios, output_path)
    
    return scenarios


if __name__ == "__main__":
    generate_demo_scenarios()
