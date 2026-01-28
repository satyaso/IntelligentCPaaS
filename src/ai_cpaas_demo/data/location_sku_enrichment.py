"""Enrich customer profiles with location and SKU/product data for demo filtering."""

import random
from typing import Dict, List
from uuid import UUID

from ..core.models import CustomerProfile


class LocationSKUEnrichment:
    """Enriches customer profiles with location and product preference data."""
    
    # Indian cities for location data
    INDIAN_CITIES = [
        "Bangalore", "Mumbai", "Delhi", "Hyderabad", "Chennai",
        "Kolkata", "Pune", "Ahmedabad", "Jaipur", "Lucknow"
    ]
    
    # Product SKUs for demo
    PRODUCT_SKUS = [
        "SKU-LAPTOP-001", "SKU-PHONE-002", "SKU-TABLET-003",
        "SKU-WATCH-004", "SKU-HEADPHONE-005", "SKU-CAMERA-006",
        "SKU-SPEAKER-007", "SKU-MONITOR-008", "SKU-KEYBOARD-009",
        "SKU-MOUSE-010"
    ]
    
    # Product categories
    PRODUCT_CATEGORIES = {
        "SKU-LAPTOP-001": "Electronics",
        "SKU-PHONE-002": "Electronics",
        "SKU-TABLET-003": "Electronics",
        "SKU-WATCH-004": "Wearables",
        "SKU-HEADPHONE-005": "Audio",
        "SKU-CAMERA-006": "Photography",
        "SKU-SPEAKER-007": "Audio",
        "SKU-MONITOR-008": "Electronics",
        "SKU-KEYBOARD-009": "Accessories",
        "SKU-MOUSE-010": "Accessories",
    }
    
    def __init__(self, seed: int = 42):
        """Initialize enrichment with seed for reproducibility."""
        random.seed(seed)
    
    def enrich_profile(self, profile: CustomerProfile) -> Dict:
        """
        Enrich a customer profile with location and SKU data.
        
        Returns a dictionary with additional fields that can be stored in DynamoDB.
        """
        # Assign location (40% Bangalore for demo filtering)
        location = "Bangalore" if random.random() < 0.4 else random.choice(self.INDIAN_CITIES)
        
        # Assign 2-5 product interests based on customer value
        num_interests = random.randint(2, 5)
        product_interests = random.sample(self.PRODUCT_SKUS, num_interests)
        
        # Assign purchase history (0-3 past purchases)
        num_purchases = random.randint(0, 3)
        purchase_history = random.sample(self.PRODUCT_SKUS, num_purchases) if num_purchases > 0 else []
        
        # Assign browsing history (3-8 products viewed)
        num_browsed = random.randint(3, 8)
        browsing_history = random.sample(self.PRODUCT_SKUS, num_browsed)
        
        # Assign cart items (0-2 items in cart)
        num_cart = random.randint(0, 2)
        cart_items = random.sample(self.PRODUCT_SKUS, num_cart) if num_cart > 0 else []
        
        # Assign preferred categories
        preferred_categories = list(set(
            self.PRODUCT_CATEGORIES[sku] for sku in product_interests
        ))
        
        # Extract names from profile metadata (added during generation)
        first_name = getattr(profile, '_first_name', 'Valued')
        last_name = getattr(profile, '_last_name', 'Customer')
        
        return {
            "customer_id": str(profile.id),
            "external_id": profile.external_id,
            "first_name": first_name,
            "last_name": last_name,
            "location": location,
            "city": location,
            "country": "India",
            "product_interests": product_interests,
            "purchase_history": purchase_history,
            "browsing_history": browsing_history,
            "cart_items": cart_items,
            "preferred_categories": preferred_categories,
            "total_purchases": len(purchase_history),
            "is_bangalore_user": location == "Bangalore",
        }
    
    def enrich_profiles(self, profiles: List[CustomerProfile]) -> List[Dict]:
        """Enrich multiple customer profiles."""
        return [self.enrich_profile(profile) for profile in profiles]
    
    def filter_by_location(
        self, enriched_profiles: List[Dict], location: str
    ) -> List[Dict]:
        """Filter enriched profiles by location."""
        return [p for p in enriched_profiles if p["location"] == location]
    
    def filter_by_sku(
        self, enriched_profiles: List[Dict], sku: str
    ) -> List[Dict]:
        """Filter enriched profiles by SKU interest or purchase history."""
        return [
            p for p in enriched_profiles
            if sku in p["product_interests"]
            or sku in p["purchase_history"]
            or sku in p["browsing_history"]
            or sku in p["cart_items"]
        ]
    
    def filter_by_location_and_sku(
        self, enriched_profiles: List[Dict], location: str, sku: str
    ) -> List[Dict]:
        """Filter enriched profiles by both location and SKU."""
        location_filtered = self.filter_by_location(enriched_profiles, location)
        return self.filter_by_sku(location_filtered, sku)
    
    def get_bangalore_users_for_sku(
        self, enriched_profiles: List[Dict], sku: str
    ) -> List[Dict]:
        """Get Bangalore users interested in a specific SKU (for demo)."""
        return self.filter_by_location_and_sku(enriched_profiles, "Bangalore", sku)
