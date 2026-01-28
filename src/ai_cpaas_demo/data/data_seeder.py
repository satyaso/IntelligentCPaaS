"""Data seeding and management for demo database."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID

from ..core.models import CustomerProfile
from .location_sku_enrichment import LocationSKUEnrichment


class DataSeeder:
    """Manages seeding and refreshing demo data for DynamoDB or in-memory storage."""
    
    def __init__(
        self,
        data_dir: str = "data/demo",
        batch_size: int = 25,  # DynamoDB batch write limit
    ):
        """
        Initialize data seeder.
        
        Args:
            data_dir: Directory containing generated data files
            batch_size: Number of items per batch operation (DynamoDB limit is 25)
        """
        self.data_dir = Path(data_dir)
        self.batch_size = batch_size
        self.enrichment = LocationSKUEnrichment()
        
        # In-memory storage (for demo without DynamoDB)
        self.customers: Dict[str, Dict] = {}
        self.customers_by_location: Dict[str, List[str]] = {}
        self.customers_by_sku: Dict[str, List[str]] = {}
    
    def load_customer_profiles(self) -> List[CustomerProfile]:
        """Load customer profiles from JSON file."""
        profiles_file = self.data_dir / "customer_profiles.json"
        
        if not profiles_file.exists():
            raise FileNotFoundError(
                f"Customer profiles not found at {profiles_file}. "
                "Run generate_demo_data.py first."
            )
        
        with open(profiles_file, "r") as f:
            data = json.load(f)
        
        # Convert JSON to CustomerProfile objects
        profiles = []
        for item in data:
            # Parse datetime strings
            if item.get("last_interaction"):
                item["last_interaction"] = datetime.fromisoformat(
                    item["last_interaction"].replace("Z", "+00:00")
                )
            if item.get("created_at"):
                item["created_at"] = datetime.fromisoformat(
                    item["created_at"].replace("Z", "+00:00")
                )
            if item.get("updated_at"):
                item["updated_at"] = datetime.fromisoformat(
                    item["updated_at"].replace("Z", "+00:00")
                )
            
            # Parse nested datetime fields
            for record in item.get("engagement_history", []):
                if record.get("timestamp"):
                    record["timestamp"] = datetime.fromisoformat(
                        record["timestamp"].replace("Z", "+00:00")
                    )
            
            for record in item.get("sentiment_history", []):
                if record.get("timestamp"):
                    record["timestamp"] = datetime.fromisoformat(
                        record["timestamp"].replace("Z", "+00:00")
                    )
            
            for ticket in item.get("support_tickets", []):
                if ticket.get("created_at"):
                    ticket["created_at"] = datetime.fromisoformat(
                        ticket["created_at"].replace("Z", "+00:00")
                    )
                if ticket.get("resolved_at"):
                    ticket["resolved_at"] = datetime.fromisoformat(
                        ticket["resolved_at"].replace("Z", "+00:00")
                    )
            
            for signal in item.get("disengagement_signals", []):
                if signal.get("timestamp"):
                    signal["timestamp"] = datetime.fromisoformat(
                        signal["timestamp"].replace("Z", "+00:00")
                    )
            
            for pref in item.get("channel_preferences", []):
                if pref.get("last_engagement"):
                    pref["last_engagement"] = datetime.fromisoformat(
                        pref["last_engagement"].replace("Z", "+00:00")
                    )
            
            profiles.append(CustomerProfile(**item))
        
        return profiles
    
    def seed_in_memory(self) -> Dict[str, Any]:
        """
        Seed data into in-memory storage for demo without DynamoDB.
        
        Returns statistics about seeded data.
        """
        # Try to load from enriched file first (has first_name/last_name)
        enriched_file = Path(__file__).parent.parent.parent.parent / "data" / "demo" / "enriched_customers.json"
        
        if enriched_file.exists():
            print("Loading enriched customer profiles from file...")
            try:
                with open(enriched_file, 'r') as f:
                    enriched_profiles = json.load(f)
                print(f"✅ Loaded {len(enriched_profiles)} enriched profiles from file")
            except Exception as e:
                print(f"⚠️  Failed to load enriched file: {e}")
                print("Falling back to generating fresh profiles...")
                enriched_profiles = self._generate_fresh_profiles()
        else:
            print("Loading customer profiles...")
            enriched_profiles = self._generate_fresh_profiles()
        
        # Store in memory
        self.customers = {p["customer_id"]: p for p in enriched_profiles}
        
        # Build indexes
        print("Building location and SKU indexes...")
        self.customers_by_location = {}
        self.customers_by_sku = {}
        
        for profile in enriched_profiles:
            # Location index
            location = profile["location"]
            if location not in self.customers_by_location:
                self.customers_by_location[location] = []
            self.customers_by_location[location].append(profile["customer_id"])
            
            # SKU index
            all_skus = set(
                profile["product_interests"]
                + profile["purchase_history"]
                + profile["browsing_history"]
                + profile["cart_items"]
            )
            for sku in all_skus:
                if sku not in self.customers_by_sku:
                    self.customers_by_sku[sku] = []
                self.customers_by_sku[sku].append(profile["customer_id"])
        
        # Calculate statistics
        stats = {
            "total_customers": len(self.customers),
            "locations": {
                loc: len(ids) for loc, ids in self.customers_by_location.items()
            },
            "bangalore_users": len(self.customers_by_location.get("Bangalore", [])),
            "skus_tracked": len(self.customers_by_sku),
            "avg_interests_per_customer": sum(
                len(p["product_interests"]) for p in enriched_profiles
            ) / len(enriched_profiles),
        }
        
        print(f"\n✅ Seeded {stats['total_customers']} customers into memory")
        print(f"   - Bangalore users: {stats['bangalore_users']}")
        print(f"   - Locations: {len(stats['locations'])}")
        print(f"   - SKUs tracked: {stats['skus_tracked']}")
        
        return stats
    
    def _generate_fresh_profiles(self) -> List[Dict]:
        """Generate fresh profiles when enriched file not available."""
        profiles = self.load_customer_profiles()
        print(f"Enriching {len(profiles)} profiles with location and SKU data...")
        return self.enrichment.enrich_profiles(profiles)
    
    def query_by_location(self, location: str) -> List[Dict]:
        """Query customers by location."""
        customer_ids = self.customers_by_location.get(location, [])
        return [self.customers[cid] for cid in customer_ids]
    
    def query_by_sku(self, sku: str) -> List[Dict]:
        """Query customers interested in a specific SKU."""
        customer_ids = self.customers_by_sku.get(sku, [])
        return [self.customers[cid] for cid in customer_ids]
    
    def query_by_location_and_sku(self, location: str, sku: str) -> List[Dict]:
        """Query customers by location and SKU interest (for demo)."""
        location_ids = set(self.customers_by_location.get(location, []))
        sku_ids = set(self.customers_by_sku.get(sku, []))
        matching_ids = location_ids.intersection(sku_ids)
        return [self.customers[cid] for cid in matching_ids]
    
    def get_customer(self, customer_id: str) -> Optional[Dict]:
        """Get a single customer by ID."""
        return self.customers.get(customer_id)
    
    def export_enriched_data(self, output_file: str = "data/demo/enriched_customers.json"):
        """Export enriched customer data to JSON file."""
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to list for JSON serialization
        customers_list = list(self.customers.values())
        
        with open(output_path, "w") as f:
            json.dump(customers_list, f, indent=2, default=str)
        
        print(f"✅ Exported {len(customers_list)} enriched customers to {output_path}")
        return output_path
    
    def refresh_data(self) -> Dict[str, Any]:
        """Refresh all data (reload from files and re-seed)."""
        print("Refreshing demo data...")
        self.customers.clear()
        self.customers_by_location.clear()
        self.customers_by_sku.clear()
        return self.seed_in_memory()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get current data statistics."""
        return {
            "total_customers": len(self.customers),
            "locations": {
                loc: len(ids) for loc, ids in self.customers_by_location.items()
            },
            "bangalore_users": len(self.customers_by_location.get("Bangalore", [])),
            "skus_tracked": len(self.customers_by_sku),
            "top_skus": sorted(
                [(sku, len(ids)) for sku, ids in self.customers_by_sku.items()],
                key=lambda x: x[1],
                reverse=True,
            )[:10],
        }


class DynamoDBSeeder(DataSeeder):
    """
    DynamoDB-specific seeder (requires boto3 and AWS credentials).
    
    This will be used when Task 3 (AWS infrastructure) is completed.
    """
    
    def __init__(
        self,
        table_name: str = "ai-cpaas-customers",
        data_dir: str = "data/demo",
        batch_size: int = 25,
    ):
        """
        Initialize DynamoDB seeder.
        
        Args:
            table_name: DynamoDB table name
            data_dir: Directory containing generated data files
            batch_size: Number of items per batch write (max 25 for DynamoDB)
        """
        super().__init__(data_dir, batch_size)
        self.table_name = table_name
        self.dynamodb = None
        self.table = None
    
    def _init_dynamodb(self):
        """Initialize DynamoDB client (lazy loading)."""
        if self.dynamodb is None:
            try:
                import boto3
                self.dynamodb = boto3.resource("dynamodb")
                self.table = self.dynamodb.Table(self.table_name)
            except ImportError:
                raise ImportError(
                    "boto3 is required for DynamoDB operations. "
                    "Install with: pip install boto3"
                )
            except Exception as e:
                raise RuntimeError(
                    f"Failed to initialize DynamoDB: {e}. "
                    "Ensure AWS credentials are configured."
                )
    
    def seed_dynamodb(self) -> Dict[str, Any]:
        """
        Seed data into DynamoDB table with batch operations.
        
        Returns statistics about seeded data.
        """
        self._init_dynamodb()
        
        print("Loading customer profiles...")
        profiles = self.load_customer_profiles()
        
        print(f"Enriching {len(profiles)} profiles with location and SKU data...")
        enriched_profiles = self.enrichment.enrich_profiles(profiles)
        
        # Batch write to DynamoDB
        print(f"Writing to DynamoDB table '{self.table_name}' in batches of {self.batch_size}...")
        
        total_written = 0
        failed_items = []
        
        for i in range(0, len(enriched_profiles), self.batch_size):
            batch = enriched_profiles[i:i + self.batch_size]
            
            try:
                with self.table.batch_writer() as writer:
                    for item in batch:
                        # Convert to DynamoDB format
                        writer.put_item(Item=item)
                        total_written += 1
                
                if (i + self.batch_size) % 100 == 0:
                    print(f"  Written {total_written}/{len(enriched_profiles)} items...")
            
            except Exception as e:
                print(f"  ⚠️  Batch write failed: {e}")
                failed_items.extend(batch)
        
        stats = {
            "total_customers": len(enriched_profiles),
            "written_successfully": total_written,
            "failed": len(failed_items),
            "table_name": self.table_name,
        }
        
        print(f"\n✅ Seeded {total_written} customers into DynamoDB")
        if failed_items:
            print(f"   ⚠️  {len(failed_items)} items failed to write")
        
        return stats
    
    def query_dynamodb_by_location(self, location: str) -> List[Dict]:
        """Query DynamoDB by location using GSI."""
        self._init_dynamodb()
        
        response = self.table.query(
            IndexName="location-index",  # Requires GSI on location field
            KeyConditionExpression="location = :loc",
            ExpressionAttributeValues={":loc": location},
        )
        
        return response.get("Items", [])
    
    def clear_table(self):
        """Clear all items from DynamoDB table (for demo reset)."""
        self._init_dynamodb()
        
        print(f"Clearing DynamoDB table '{self.table_name}'...")
        
        # Scan and delete all items
        scan = self.table.scan()
        items = scan.get("Items", [])
        
        with self.table.batch_writer() as writer:
            for item in items:
                writer.delete_item(Key={"customer_id": item["customer_id"]})
        
        print(f"✅ Cleared {len(items)} items from table")
