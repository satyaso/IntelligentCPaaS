"""Integration tests for data seeding and querying."""

import pytest
from ai_cpaas_demo.data import DataSeeder, LocationSKUEnrichment


class TestDataSeeding:
    """Test data seeding and query functionality."""
    
    @pytest.fixture
    def seeder(self):
        """Create a data seeder instance."""
        seeder = DataSeeder()
        seeder.seed_in_memory()
        return seeder
    
    def test_seed_in_memory(self, seeder):
        """Test that data is seeded correctly."""
        assert len(seeder.customers) == 1000
        assert len(seeder.customers_by_location) > 0
        assert len(seeder.customers_by_sku) > 0
    
    def test_query_by_location(self, seeder):
        """Test querying customers by location."""
        bangalore_users = seeder.query_by_location("Bangalore")
        
        # Should have ~40% Bangalore users (400 out of 1000)
        assert len(bangalore_users) > 300
        assert len(bangalore_users) < 600
        
        # All should be from Bangalore
        for user in bangalore_users:
            assert user["location"] == "Bangalore"
            assert user["is_bangalore_user"] is True
    
    def test_query_by_sku(self, seeder):
        """Test querying customers by SKU."""
        laptop_users = seeder.query_by_sku("SKU-LAPTOP-001")
        
        # Should have significant number of laptop interested users
        assert len(laptop_users) > 500
        
        # All should have laptop in their interests/history
        for user in laptop_users:
            all_skus = (
                user["product_interests"]
                + user["purchase_history"]
                + user["browsing_history"]
                + user["cart_items"]
            )
            assert "SKU-LAPTOP-001" in all_skus
    
    def test_query_by_location_and_sku(self, seeder):
        """Test querying by both location and SKU."""
        bangalore_laptop = seeder.query_by_location_and_sku(
            "Bangalore", "SKU-LAPTOP-001"
        )
        
        # Should have intersection of Bangalore and laptop users
        assert len(bangalore_laptop) > 200
        assert len(bangalore_laptop) < 500
        
        # All should match both criteria
        for user in bangalore_laptop:
            assert user["location"] == "Bangalore"
            all_skus = (
                user["product_interests"]
                + user["purchase_history"]
                + user["browsing_history"]
                + user["cart_items"]
            )
            assert "SKU-LAPTOP-001" in all_skus
    
    def test_get_customer(self, seeder):
        """Test getting a single customer."""
        # Get first customer ID
        customer_id = list(seeder.customers.keys())[0]
        customer = seeder.get_customer(customer_id)
        
        assert customer is not None
        assert customer["customer_id"] == customer_id
        assert "location" in customer
        assert "product_interests" in customer
    
    def test_get_statistics(self, seeder):
        """Test getting data statistics."""
        stats = seeder.get_statistics()
        
        assert stats["total_customers"] == 1000
        assert "locations" in stats
        assert "bangalore_users" in stats
        assert "skus_tracked" in stats
        assert "top_skus" in stats
        
        # Should have 10 locations
        assert len(stats["locations"]) == 10
        
        # Should have 10 SKUs
        assert stats["skus_tracked"] == 10
    
    def test_enrichment_structure(self, seeder):
        """Test that enriched data has correct structure."""
        customer = list(seeder.customers.values())[0]
        
        # Required fields
        assert "customer_id" in customer
        assert "external_id" in customer
        assert "location" in customer
        assert "city" in customer
        assert "country" in customer
        assert "product_interests" in customer
        assert "purchase_history" in customer
        assert "browsing_history" in customer
        assert "cart_items" in customer
        assert "preferred_categories" in customer
        assert "total_purchases" in customer
        assert "is_bangalore_user" in customer
        
        # Data types
        assert isinstance(customer["product_interests"], list)
        assert isinstance(customer["purchase_history"], list)
        assert isinstance(customer["browsing_history"], list)
        assert isinstance(customer["cart_items"], list)
        assert isinstance(customer["preferred_categories"], list)
        assert isinstance(customer["total_purchases"], int)
        assert isinstance(customer["is_bangalore_user"], bool)
        
        # Country should be India
        assert customer["country"] == "India"


class TestLocationSKUEnrichment:
    """Test location and SKU enrichment functionality."""
    
    @pytest.fixture
    def enrichment(self):
        """Create enrichment instance."""
        return LocationSKUEnrichment(seed=42)
    
    def test_indian_cities(self, enrichment):
        """Test that Indian cities are defined."""
        assert len(enrichment.INDIAN_CITIES) == 10
        assert "Bangalore" in enrichment.INDIAN_CITIES
        assert "Mumbai" in enrichment.INDIAN_CITIES
    
    def test_product_skus(self, enrichment):
        """Test that product SKUs are defined."""
        assert len(enrichment.PRODUCT_SKUS) == 10
        assert "SKU-LAPTOP-001" in enrichment.PRODUCT_SKUS
        assert "SKU-PHONE-002" in enrichment.PRODUCT_SKUS
    
    def test_product_categories(self, enrichment):
        """Test that product categories are defined."""
        assert len(enrichment.PRODUCT_CATEGORIES) == 10
        assert enrichment.PRODUCT_CATEGORIES["SKU-LAPTOP-001"] == "Electronics"
        assert enrichment.PRODUCT_CATEGORIES["SKU-WATCH-004"] == "Wearables"
    
    def test_filter_by_location(self, enrichment):
        """Test filtering by location."""
        # Create mock enriched profiles
        profiles = [
            {"location": "Bangalore", "customer_id": "1"},
            {"location": "Mumbai", "customer_id": "2"},
            {"location": "Bangalore", "customer_id": "3"},
        ]
        
        bangalore = enrichment.filter_by_location(profiles, "Bangalore")
        assert len(bangalore) == 2
        assert all(p["location"] == "Bangalore" for p in bangalore)
    
    def test_filter_by_sku(self, enrichment):
        """Test filtering by SKU."""
        profiles = [
            {
                "customer_id": "1",
                "product_interests": ["SKU-LAPTOP-001"],
                "purchase_history": [],
                "browsing_history": [],
                "cart_items": [],
            },
            {
                "customer_id": "2",
                "product_interests": ["SKU-PHONE-002"],
                "purchase_history": [],
                "browsing_history": [],
                "cart_items": [],
            },
        ]
        
        laptop = enrichment.filter_by_sku(profiles, "SKU-LAPTOP-001")
        assert len(laptop) == 1
        assert laptop[0]["customer_id"] == "1"
