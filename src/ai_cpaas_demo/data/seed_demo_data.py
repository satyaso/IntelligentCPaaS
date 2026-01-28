"""Seed demo data for interactive campaign demonstrations."""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ai_cpaas_demo.data.data_seeder import DataSeeder


def main():
    """Seed demo data and demonstrate query capabilities."""
    print("=" * 80)
    print("AI-CPaaS Demo Data Seeding")
    print("=" * 80)
    print()
    
    # Initialize seeder
    seeder = DataSeeder()
    
    # Seed data into memory
    stats = seeder.seed_in_memory()
    
    print("\n" + "=" * 80)
    print("Data Statistics")
    print("=" * 80)
    
    # Display location breakdown
    print("\n📍 Customer Distribution by Location:")
    for location, count in sorted(
        stats["locations"].items(), key=lambda x: x[1], reverse=True
    ):
        percentage = (count / stats["total_customers"]) * 100
        print(f"   {location:15s}: {count:4d} customers ({percentage:5.1f}%)")
    
    # Display SKU statistics
    print(f"\n🛍️  Product SKU Statistics:")
    print(f"   Total SKUs tracked: {stats['skus_tracked']}")
    print(f"   Avg interests per customer: {stats['avg_interests_per_customer']:.1f}")
    
    # Get top SKUs
    full_stats = seeder.get_statistics()
    print(f"\n   Top 5 SKUs by customer interest:")
    for sku, count in full_stats["top_skus"][:5]:
        print(f"   {sku:20s}: {count:4d} customers")
    
    # Demo query: Bangalore users for SKU-LAPTOP-001
    print("\n" + "=" * 80)
    print("Demo Query: Bangalore Users for SKU-LAPTOP-001")
    print("=" * 80)
    
    bangalore_laptop_users = seeder.query_by_location_and_sku(
        "Bangalore", "SKU-LAPTOP-001"
    )
    
    print(f"\n✅ Found {len(bangalore_laptop_users)} Bangalore users interested in SKU-LAPTOP-001")
    
    if bangalore_laptop_users:
        print("\nSample customers:")
        for i, customer in enumerate(bangalore_laptop_users[:5], 1):
            print(f"\n{i}. Customer {customer['external_id']}")
            print(f"   Location: {customer['location']}")
            print(f"   Product Interests: {', '.join(customer['product_interests'][:3])}")
            print(f"   Purchase History: {len(customer['purchase_history'])} items")
            print(f"   Cart Items: {len(customer['cart_items'])} items")
    
    # Demo query: All Bangalore users
    print("\n" + "=" * 80)
    print("Demo Query: All Bangalore Users")
    print("=" * 80)
    
    bangalore_users = seeder.query_by_location("Bangalore")
    print(f"\n✅ Found {len(bangalore_users)} total Bangalore users")
    
    # Demo query: All users interested in SKU-PHONE-002
    print("\n" + "=" * 80)
    print("Demo Query: All Users Interested in SKU-PHONE-002")
    print("=" * 80)
    
    phone_users = seeder.query_by_sku("SKU-PHONE-002")
    print(f"\n✅ Found {len(phone_users)} users interested in SKU-PHONE-002")
    
    # Location breakdown for phone users
    phone_locations = {}
    for user in phone_users:
        loc = user["location"]
        phone_locations[loc] = phone_locations.get(loc, 0) + 1
    
    print("\n   Location breakdown:")
    for location, count in sorted(
        phone_locations.items(), key=lambda x: x[1], reverse=True
    )[:5]:
        print(f"   {location:15s}: {count:4d} users")
    
    # Export enriched data
    print("\n" + "=" * 80)
    print("Exporting Enriched Data")
    print("=" * 80)
    print()
    
    output_file = seeder.export_enriched_data()
    
    print("\n" + "=" * 80)
    print("Demo Data Ready!")
    print("=" * 80)
    print("\n✅ Data seeding complete. You can now:")
    print("   1. Query customers by location: seeder.query_by_location('Bangalore')")
    print("   2. Query by SKU: seeder.query_by_sku('SKU-LAPTOP-001')")
    print("   3. Query by both: seeder.query_by_location_and_sku('Bangalore', 'SKU-LAPTOP-001')")
    print("   4. Get customer: seeder.get_customer(customer_id)")
    print("   5. Refresh data: seeder.refresh_data()")
    print("\n📊 Enriched data exported to: data/demo/enriched_customers.json")
    print()


if __name__ == "__main__":
    main()
