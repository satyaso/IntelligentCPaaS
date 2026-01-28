"""Interactive demo query utility for campaign demonstrations."""

import sys
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ai_cpaas_demo.data.data_seeder import DataSeeder
from ai_cpaas_demo.core.models import FatigueLevel, SentimentType
from ai_cpaas_demo.engines.adaptation.message_generator import CampaignMessageGenerator


class DemoQueryEngine:
    """
    Query engine for interactive campaign demonstrations.
    
    Simulates the user's demo goal:
    - Enter: "Run campaign for Bangalore users for SKU X"
    - Show: Suppressed users, WhatsApp routing, time optimization, before/after metrics
    - Show: Promotion data from RAG knowledge base
    """
    
    # Available dimensions in customer data
    AVAILABLE_DIMENSIONS = {
        'location': {'type': 'string', 'example': 'Bangalore'},
        'city': {'type': 'string', 'example': 'Bangalore'},
        'country': {'type': 'string', 'example': 'India'},
        'product_interests': {'type': 'array', 'example': 'SKU-LAPTOP-001'},
        'total_purchases': {'type': 'number', 'example': '5'},
        'preferred_categories': {'type': 'array', 'example': 'Electronics'},
        'cart_items': {'type': 'array', 'example': 'SKU-PHONE-002'},
        'browsing_history': {'type': 'array', 'example': 'SKU-TABLET-003'},
    }
    
    def __init__(self):
        """Initialize demo query engine with seeded data."""
        self.seeder = DataSeeder()
        print("Loading demo data...")
        self.seeder.seed_in_memory()
        
        # Load RAG promotion data
        self.promotions_rag = self._load_promotions_rag()
        
        # Initialize message generator
        self.message_generator = CampaignMessageGenerator()
        
        # Segment storage file path
        self.segments_file = Path(__file__).parent.parent.parent.parent / "data" / "demo" / "segments.json"
        
        # Load existing segments from file (persisted across restarts)
        self.segments = self._load_segments()
        
        # Load full customer profiles with channel preferences
        self._load_full_profiles()
        
        print("✅ Demo data ready!\n")
    
    def _load_promotions_rag(self) -> Dict:
        """Load promotion data from RAG knowledge base JSON."""
        rag_file = Path(__file__).parent.parent.parent.parent / "data" / "demo" / "sku_promotions_rag.json"
        
        try:
            with open(rag_file, 'r') as f:
                promotions = json.load(f)
            print(f"✅ Loaded {len(promotions)} SKU promotions from RAG knowledge base")
            return promotions
        except Exception as e:
            print(f"⚠️  Warning: Could not load RAG promotions: {e}")
            return {}
    
    def _load_segments(self) -> Dict:
        """Load segments from persistent storage (JSON file)."""
        try:
            if self.segments_file.exists():
                with open(self.segments_file, 'r') as f:
                    segments = json.load(f)
                print(f"✅ Loaded {len(segments)} existing segments from storage")
                return segments
            else:
                print("📋 No existing segments found, starting fresh")
                return {}
        except Exception as e:
            print(f"⚠️  Warning: Could not load segments: {e}")
            return {}
    
    def _load_full_profiles(self):
        """Load full customer profiles with channel preferences from customer_profiles.json."""
        profiles_file = Path(__file__).parent.parent.parent.parent / "data" / "demo" / "customer_profiles.json"
        
        try:
            with open(profiles_file, 'r') as f:
                profiles = json.load(f)
            
            # Create a mapping from external_id to full profile (since customer_ids don't match)
            self.full_profiles_by_external_id = {}
            for profile in profiles:
                external_id = profile.get('external_id')
                if external_id:
                    self.full_profiles_by_external_id[external_id] = profile
            
            print(f"✅ Loaded {len(self.full_profiles_by_external_id)} full profiles with channel preferences")
        except Exception as e:
            print(f"⚠️  Warning: Could not load full profiles: {e}")
            self.full_profiles_by_external_id = {}
    
    def _save_segments(self):
        """Save segments to persistent storage (JSON file)."""
        try:
            # Ensure directory exists
            self.segments_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.segments_file, 'w') as f:
                json.dump(self.segments, f, indent=2)
            print(f"💾 Saved {len(self.segments)} segments to storage")
        except Exception as e:
            print(f"⚠️  Warning: Could not save segments: {e}")
    
    def _get_promotion_data(self, sku: str, location: str) -> Optional[Dict]:
        """
        Get promotion data for a specific SKU and location from RAG knowledge base.
        
        Args:
            sku: Product SKU
            location: Target location
        
        Returns:
            Promotion data dictionary or None if not found
        """
        if sku not in self.promotions_rag:
            return None
        
        sku_data = self.promotions_rag[sku]
        
        # Check if there's an active promotion for this location
        active_promotions = []
        for promo in sku_data.get('active_promotions', []):
            target_locations = promo.get('target_locations', [])
            if location in target_locations:
                active_promotions.append(promo)
        
        # Return simplified promotion data for the campaign
        return {
            'sku': sku,
            'product_name': sku_data.get('product_name', 'Unknown Product'),
            'promotion_score': sku_data.get('promotion_score', 0),
            'promotion_score_explanation': sku_data.get('promotion_score_explanation', ''),
            'active_promotions': active_promotions,
            'deepar_forecast': sku_data.get('deepar_forecast', {}),
            'inventory_status': sku_data.get('inventory_status', {}),
            'cannibalization_risk': sku_data.get('cannibalization_analysis', {}).get('risk_level', 'unknown'),
        }
    
    def _get_or_create_segment_id(self, location: str, sku: str, eligible_count: int, additional_filters: Dict = None) -> tuple:
        """
        Get existing segment ID if criteria match, or create new one.
        
        Args:
            location: Target location
            sku: Target SKU
            eligible_count: Number of eligible users
            additional_filters: Optional additional filters
        
        Returns:
            Tuple of (segment_id, is_reused)
        """
        # Create criteria hash for deduplication
        criteria_str = f"{location}|{sku}|{json.dumps(additional_filters or {}, sort_keys=True)}"
        criteria_hash = hashlib.md5(criteria_str.encode()).hexdigest()
        
        # Check if segment with same criteria exists
        if criteria_hash in self.segments:
            segment_id = self.segments[criteria_hash]
            print(f"♻️  Reusing existing segment: {segment_id}")
            return segment_id, True
        
        # Generate new segment ID
        segment_id = self._generate_segment_id(location, sku, eligible_count)
        self.segments[criteria_hash] = segment_id
        
        # Persist to storage
        self._save_segments()
        
        print(f"✅ Created new segment: {segment_id}")
        return segment_id, False
    
    def _generate_segment_id(self, location: str, sku: str, eligible_count: int) -> str:
        """
        Generate a unique segment ID for the campaign.
        
        Format: SEG-{LOCATION_CODE}-{SKU_CODE}-{TIMESTAMP}-{HASH}
        Example: SEG-BLR-LAP001-20260120143022-A3F9
        
        Args:
            location: Target location
            sku: Target SKU
            eligible_count: Number of eligible users in segment
        
        Returns:
            Unique segment ID string
        """
        # Create location code (first 3 letters, uppercase)
        location_code = location[:3].upper()
        
        # Create SKU code (extract product type and number)
        # SKU-LAPTOP-001 -> LAP001
        sku_parts = sku.split('-')
        if len(sku_parts) >= 3:
            product_type = sku_parts[1][:3].upper()  # LAP, PHO, TAB, etc.
            product_num = sku_parts[2]  # 001, 002, etc.
            sku_code = f"{product_type}{product_num}"
        else:
            sku_code = sku.replace('-', '')[:6].upper()
        
        # Create timestamp (YYYYMMDDHHMMSS)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # Create hash for uniqueness (first 4 chars of MD5)
        hash_input = f"{location}{sku}{timestamp}{eligible_count}"
        hash_value = hashlib.md5(hash_input.encode()).hexdigest()[:4].upper()
        
        # Combine into segment ID
        segment_id = f"SEG-{location_code}-{sku_code}-{timestamp}-{hash_value}"
        
        return segment_id
    
    def _fuzzy_match_sku(self, query_text: str) -> Optional[str]:
        """
        Fuzzy match SKU from partial input.
        
        Args:
            query_text: User input (e.g., "LAP", "laptop", "SKU-LAP")
        
        Returns:
            Matched SKU or None
        """
        query_upper = query_text.upper().strip()
        
        # Available SKUs in the system
        available_skus = [
            "SKU-LAPTOP-001",
            "SKU-PHONE-002",
            "SKU-TABLET-003",
            "SKU-WATCH-004",
            "SKU-HEADPHONE-005",
            "SKU-CAMERA-006",
            "SKU-SPEAKER-007",
            "SKU-MONITOR-008",
            "SKU-KEYBOARD-009",
            "SKU-MOUSE-010",
        ]
        
        # Exact match
        if query_upper in available_skus:
            return query_upper
        
        # Partial match (e.g., "LAP" -> "SKU-LAPTOP-001")
        for sku in available_skus:
            if query_upper in sku:
                return sku
        
        # Product name match (e.g., "laptop" -> "SKU-LAPTOP-001")
        product_map = {
            "LAPTOP": "SKU-LAPTOP-001",
            "PHONE": "SKU-PHONE-002",
            "TABLET": "SKU-TABLET-003",
            "WATCH": "SKU-WATCH-004",
            "HEADPHONE": "SKU-HEADPHONE-005",
            "CAMERA": "SKU-CAMERA-006",
            "SPEAKER": "SKU-SPEAKER-007",
            "MONITOR": "SKU-MONITOR-008",
            "KEYBOARD": "SKU-KEYBOARD-009",
            "MOUSE": "SKU-MOUSE-010",
        }
        
        for product_name, sku in product_map.items():
            if product_name in query_upper:
                return sku
        
        return None
    
    def _match_customer_id(self, query_text: str) -> Optional[str]:
        """
        Match customer ID from input.
        
        Args:
            query_text: User input (e.g., "CUST-001", "85822412")
        
        Returns:
            Matched customer external_id or None
        """
        query_upper = query_text.upper().strip()
        
        # Check if it looks like a customer ID
        if "CUST-" in query_upper:
            # Search for exact match in loaded customers
            for customer in self.seeder.customers.values():
                if customer.get("external_id") == query_upper:
                    return query_upper
            
            # Partial match (e.g., "CUST-858" matches "CUST-85822412")
            for customer in self.seeder.customers.values():
                if customer.get("external_id", "").startswith(query_upper):
                    return customer.get("external_id")
        
        # Check if it's just the numeric part
        if query_upper.isdigit():
            for customer in self.seeder.customers.values():
                external_id = customer.get("external_id", "")
                if external_id.endswith(query_upper):
                    return external_id
        
        return None
    
    def _get_skus_by_category(self, category: str) -> List[str]:
        """
        Get all SKUs in a product category.
        
        Args:
            category: Product category (e.g., "Electronics", "Accessories")
        
        Returns:
            List of SKUs in that category
        """
        category_map = {
            "Electronics": ["SKU-LAPTOP-001", "SKU-PHONE-002", "SKU-TABLET-003", "SKU-MONITOR-008"],
            "Accessories": ["SKU-KEYBOARD-009", "SKU-MOUSE-010"],
            "Wearables": ["SKU-WATCH-004"],
            "Photography": ["SKU-CAMERA-006"],
            "Audio": ["SKU-HEADPHONE-005", "SKU-SPEAKER-007"],
        }
        
        return category_map.get(category, [])
    
    def _parse_natural_language_filters(self, query_text: str) -> tuple:
        """
        Parse natural language query to extract filter dimensions.
        
        Args:
            query_text: Natural language query
        
        Returns:
            Tuple of (filters_dict, unsupported_dimensions, suggestions, parsed_dimensions)
        """
        filters = {}
        unsupported = []
        suggestions = []
        parsed_dimensions = []  # Track all parsed dimensions for display
        
        query_lower = query_text.lower()
        
        # Parse age (NOT SUPPORTED - suggest alternative)
        if 'age' in query_lower:
            import re
            # Try multiple patterns: "age > 40", "more than age 40", "age 40+", etc.
            age_match = re.search(r'(?:age\s*(?:>|greater than|more than|above)\s*(\d+)|(?:more than|greater than|above)\s*age\s*(\d+)|age\s*(\d+)\s*(?:\+|and above|or more))', query_lower)
            if age_match:
                # Get the age value from whichever group matched
                age_value = age_match.group(1) or age_match.group(2) or age_match.group(3)
                unsupported.append(f"age > {age_value}")
                parsed_dimensions.append(f"age > {age_value} (unsupported)")
                suggestions.append("💡 'age' dimension is not available. Try filtering by 'total_purchases' or 'preferred_categories' instead.")
            else:
                # Fallback: if "age" is mentioned but pattern doesn't match, still flag it
                unsupported.append("age")
                parsed_dimensions.append("age (unsupported)")
                suggestions.append("💡 'age' dimension is not available. Try filtering by 'total_purchases' or 'preferred_categories' instead.")
        
        # Parse total_purchases
        if 'purchase' in query_lower:
            import re
            # "more than X purchases" or "at least X purchases"
            purchase_match = re.search(r'(?:more than|at least|minimum)\s*(\d+)\s*purchase', query_lower)
            if purchase_match:
                value = int(purchase_match.group(1))
                filters['min_purchases'] = value
                parsed_dimensions.append(f"min_purchases >= {value}")
        
        # Parse category
        categories = ['Electronics', 'Accessories', 'Wearables', 'Photography', 'Audio', 'Computing']
        for cat in categories:
            if cat.lower() in query_lower:
                filters['category'] = cat
                parsed_dimensions.append(f"category = {cat}")
                break
        
        # Parse country
        if 'india' in query_lower:
            filters['country'] = 'India'
            parsed_dimensions.append("country = India")
        
        # Parse cart items requirement
        if 'cart' in query_lower or 'items in cart' in query_lower:
            filters['has_cart_items'] = True
            parsed_dimensions.append("has_cart_items = true")
        
        return filters, unsupported, suggestions, parsed_dimensions
    
    def _generate_sql_query(self, location: str, sku: str, additional_filters: Dict = None) -> str:
        """
        Generate a SQL SELECT query based on campaign parameters.
        
        Args:
            location: Target location
            sku: Target product SKU
            additional_filters: Optional dict with additional filter dimensions
        
        Returns:
            SQL query string
        """
        # Base SELECT clause
        sql = "SELECT customer_id, external_id, location, product_interests, purchase_history\n"
        sql += "FROM customers\n"
        
        # WHERE clause - always include location and SKU
        where_clauses = []
        where_clauses.append(f"location = '{location}'")
        where_clauses.append(f"'{sku}' IN product_interests")
        
        # Add additional filters if provided
        if additional_filters:
            for key, value in additional_filters.items():
                if key == 'min_purchases':
                    where_clauses.append(f"total_purchases >= {value}")
                elif key == 'max_purchases':
                    where_clauses.append(f"total_purchases <= {value}")
                elif key == 'category':
                    where_clauses.append(f"'{value}' IN preferred_categories")
                elif key == 'has_cart_items':
                    if value:
                        where_clauses.append("cart_items IS NOT NULL AND LENGTH(cart_items) > 0")
                elif key == 'country':
                    where_clauses.append(f"country = '{value}'")
        
        sql += "WHERE " + " AND ".join(where_clauses)
        sql += ";"
        
        return sql
    
    def parse_intelligent_query(self, query_text: str) -> Dict:
        """
        Intelligently parse user query to extract location, SKU, customer ID, or category.
        
        Args:
            query_text: Natural language query
        
        Returns:
            Dictionary with parsed parameters and suggestions
        """
        result = {
            "location": None,
            "sku": None,
            "customer_id": None,
            "category": None,
            "additional_filters": {},
            "suggestions": [],
            "parsed_successfully": False,
        }
        
        query_lower = query_text.lower()
        
        # Check for customer ID first (highest priority)
        customer_id = self._match_customer_id(query_text)
        if customer_id:
            result["customer_id"] = customer_id
            result["parsed_successfully"] = True
            result["suggestions"].append(f"✅ Found customer: {customer_id}")
            return result
        
        # Check for category
        categories = ['Electronics', 'Accessories', 'Wearables', 'Photography', 'Audio']
        for cat in categories:
            if cat.lower() in query_lower:
                result["category"] = cat
                result["parsed_successfully"] = True
                result["suggestions"].append(f"✅ Found category: {cat}")
                # Get all SKUs in this category
                skus = self._get_skus_by_category(cat)
                if skus:
                    result["suggestions"].append(f"   Includes {len(skus)} products: {', '.join(skus)}")
                break
        
        # Try to extract SKU (fuzzy matching)
        sku = self._fuzzy_match_sku(query_text)
        if sku:
            result["sku"] = sku
            result["parsed_successfully"] = True
            result["suggestions"].append(f"✅ Matched SKU: {sku}")
        
        # Try to extract location
        locations = ['Bangalore', 'Mumbai', 'Delhi', 'Hyderabad', 'Chennai', 'Kolkata', 'Pune', 'Jaipur']
        for loc in locations:
            if loc.lower() in query_lower:
                result["location"] = loc
                result["parsed_successfully"] = True
                result["suggestions"].append(f"✅ Found location: {loc}")
                break
        
        # Parse additional filters
        filters, unsupported, filter_suggestions, parsed_dims = self._parse_natural_language_filters(query_text)
        result["additional_filters"] = filters
        result["suggestions"].extend(filter_suggestions)
        
        # If nothing was parsed, provide helpful suggestions
        if not result["parsed_successfully"]:
            result["suggestions"].append("❌ Could not parse query. Please try:")
            result["suggestions"].append("   • Specify a location: 'Bangalore', 'Mumbai', etc.")
            result["suggestions"].append("   • Specify a product: 'laptop', 'phone', 'SKU-LAPTOP-001', etc.")
            result["suggestions"].append("   • Specify a category: 'Electronics', 'Accessories', etc.")
            result["suggestions"].append("   • Specify a customer: 'CUST-85822412', etc.")
        
        return result
    
    def run_intelligent_campaign(self, query_text: str) -> Dict:
        """
        Run campaign based on intelligent query parsing.
        Handles partial SKUs, categories, and single customer IDs.
        
        Args:
            query_text: Natural language query
        
        Returns:
            Campaign analysis results
        """
        print("=" * 80)
        print(f"Intelligent Campaign Query: '{query_text}'")
        print("=" * 80)
        print()
        
        # Parse the query intelligently
        parsed = self.parse_intelligent_query(query_text)
        
        # Display parsing results
        print("🔍 QUERY PARSING:")
        print("-" * 80)
        for suggestion in parsed["suggestions"]:
            print(f"   {suggestion}")
        print()
        
        if not parsed["parsed_successfully"]:
            return {
                "error": "Could not parse query",
                "suggestions": parsed["suggestions"],
            }
        
        # Handle single customer ID query
        if parsed["customer_id"]:
            return self._run_single_customer_campaign(parsed["customer_id"], query_text)
        
        # Handle category-based query
        if parsed["category"] and not parsed["sku"]:
            return self._run_category_campaign(
                parsed["location"] or "Bangalore",  # Default to Bangalore if not specified
                parsed["category"],
                parsed["additional_filters"],
                query_text
            )
        
        # Handle standard location + SKU query
        if parsed["location"] and parsed["sku"]:
            return self.run_campaign_query(
                parsed["location"],
                parsed["sku"],
                parsed["additional_filters"],
                query_text
            )
        
        # If we have SKU but no location, default to Bangalore
        if parsed["sku"] and not parsed["location"]:
            print("💡 No location specified, defaulting to Bangalore")
            print()
            return self.run_campaign_query(
                "Bangalore",
                parsed["sku"],
                parsed["additional_filters"],
                query_text
            )
        
        return {
            "error": "Incomplete query - need either (location + SKU), category, or customer ID",
            "parsed": parsed,
        }
    
    def _run_single_customer_campaign(self, customer_id: str, query_text: str) -> Dict:
        """
        Run campaign for a single customer by ID.
        
        Args:
            customer_id: Customer external ID
            query_text: Original query
        
        Returns:
            Campaign analysis for single customer
        """
        print(f"📋 SINGLE CUSTOMER CAMPAIGN")
        print("-" * 80)
        print(f"Target: {customer_id}")
        print()
        
        # Find customer in loaded data
        customer = None
        for c in self.seeder.customers.values():
            if c.get("external_id") == customer_id:
                customer = c
                break
        
        if not customer:
            return {
                "error": f"Customer {customer_id} not found",
                "total_matched": 0,
            }
        
        # Display customer details
        print(f"📊 CUSTOMER PROFILE:")
        print(f"   Location: {customer.get('location', 'N/A')}")
        print(f"   Product Interests: {', '.join(customer.get('product_interests', [])[:3])}...")
        print(f"   Preferred Categories: {', '.join(customer.get('preferred_categories', []))}")
        print(f"   Total Purchases: {customer.get('total_purchases', 0)}")
        print()
        
        # Create results for single customer
        results = {
            "total_matched": 1,
            "location": customer.get("location"),
            "sku": "N/A (single customer)",
            "customer_id": customer_id,
            "sql_query": f"SELECT * FROM customers WHERE external_id = '{customer_id}';",
            "unsupported_dimensions": [],
            "suggestions": [],
            "parsed_dimensions": [f"customer_id = {customer_id}"],
            "promotion": None,
            "suppressed_users": [],
            "whatsapp_routing": [],
            "time_optimized": [],
            "eligible_users": [customer_id],
            "before_metrics": self._calculate_before_metrics(1),
            "after_metrics": {},
        }
        
        # Check suppression for this customer
        full_profile = self._get_full_profile(customer.get("customer_id"))
        suppression_reason = self._check_suppression(full_profile, customer)
        
        if suppression_reason:
            results["suppressed_users"].append({
                "customer_id": customer_id,
                "reason": suppression_reason["reason"],
                "icon": suppression_reason["icon"],
                "details": suppression_reason["details"],
            })
            results["eligible_users"] = []
        else:
            # Determine channel and timing
            channel = self._determine_channel(full_profile)
            if channel == "whatsapp":
                results["whatsapp_routing"].append({
                    "customer_id": customer_id,
                    "reason": "High WhatsApp preference",
                    "preference_score": self._get_channel_preference(full_profile, "whatsapp"),
                })
            
            optimal_time = self._determine_optimal_time(full_profile)
            results["time_optimized"].append({
                "customer_id": customer_id,
                "optimal_time": optimal_time,
                "timezone": full_profile.communication_frequency.timezone,
            })
        
        # Calculate after metrics
        results["after_metrics"] = self._calculate_after_metrics(results)
        
        # Display results
        self._display_results(results)
        
        return results
    
    def _run_category_campaign(self, location: str, category: str, additional_filters: Dict, query_text: str) -> Dict:
        """
        Run campaign for all products in a category.
        
        Args:
            location: Target location
            category: Product category
            additional_filters: Additional filter dimensions
            query_text: Original query
        
        Returns:
            Aggregated campaign analysis for category
        """
        print(f"📦 CATEGORY CAMPAIGN")
        print("-" * 80)
        print(f"Category: {category}")
        print(f"Location: {location}")
        print()
        
        # Get all SKUs in category
        skus = self._get_skus_by_category(category)
        
        if not skus:
            return {
                "error": f"No products found in category '{category}'",
                "total_matched": 0,
            }
        
        print(f"📊 PRODUCTS IN CATEGORY:")
        for sku in skus:
            print(f"   • {sku}")
        print()
        
        # Run campaign for each SKU and aggregate results
        all_customers = set()
        all_suppressed = []
        all_whatsapp = []
        all_time_optimized = []
        all_eligible = []
        
        for sku in skus:
            # Query customers for this SKU
            matching = self.seeder.query_by_location_and_sku(location, sku)
            
            for customer_data in matching:
                customer_id = customer_data["external_id"]
                
                if customer_id in all_customers:
                    continue  # Skip duplicates
                
                all_customers.add(customer_id)
                
                # Check suppression
                full_profile = self._get_full_profile(customer_data["customer_id"])
                suppression_reason = self._check_suppression(full_profile, customer_data)
                
                if suppression_reason:
                    all_suppressed.append({
                        "customer_id": customer_id,
                        "reason": suppression_reason["reason"],
                        "icon": suppression_reason["icon"],
                        "details": suppression_reason["details"],
                    })
                else:
                    all_eligible.append(customer_id)
                    
                    # Channel routing
                    channel = self._determine_channel(full_profile)
                    if channel == "whatsapp":
                        all_whatsapp.append({
                            "customer_id": customer_id,
                            "reason": "High WhatsApp preference",
                            "preference_score": self._get_channel_preference(full_profile, "whatsapp"),
                        })
                    
                    # Time optimization
                    optimal_time = self._determine_optimal_time(full_profile)
                    all_time_optimized.append({
                        "customer_id": customer_id,
                        "optimal_time": optimal_time,
                        "timezone": full_profile.communication_frequency.timezone,
                    })
        
        # Create aggregated results
        results = {
            "total_matched": len(all_customers),
            "location": location,
            "category": category,
            "skus": skus,
            "sql_query": f"SELECT * FROM customers WHERE location = '{location}' AND preferred_categories CONTAINS '{category}';",
            "unsupported_dimensions": [],
            "suggestions": [],
            "parsed_dimensions": [f"location = {location}", f"category = {category}"],
            "promotion": None,
            "suppressed_users": all_suppressed,
            "whatsapp_routing": all_whatsapp,
            "time_optimized": all_time_optimized,
            "eligible_users": all_eligible,
            "before_metrics": self._calculate_before_metrics(len(all_customers)),
            "after_metrics": {},
        }
        
        # Calculate after metrics
        results["after_metrics"] = self._calculate_after_metrics(results)
        
        # Display results
        self._display_results(results)
        
        return results
    
    def run_campaign_query(self, location: str, sku: str, additional_filters: Dict = None, natural_language_query: str = None) -> Dict:
        """
        Run a campaign query for a specific location and SKU.
        
        Args:
            location: Target location (e.g., "Bangalore")
            sku: Target product SKU (e.g., "SKU-LAPTOP-001")
            additional_filters: Optional dict with additional filter dimensions
            natural_language_query: Original natural language query for parsing
        
        Returns:
            Dictionary with campaign analysis results including promotion data
        """
        print("=" * 80)
        print(f"Campaign Query: {location} users for {sku}")
        print("=" * 80)
        print()
        
        # Parse natural language for additional dimensions
        unsupported_dims = []
        suggestions = []
        parsed_dims = []
        if natural_language_query:
            parsed_filters, unsupported_dims, suggestions, parsed_dims = self._parse_natural_language_filters(natural_language_query)
            # Merge parsed filters with provided filters
            if additional_filters:
                parsed_filters.update(additional_filters)
            additional_filters = parsed_filters
        
        # Display warnings for unsupported dimensions
        if unsupported_dims:
            print("⚠️  UNSUPPORTED DIMENSIONS DETECTED:")
            print("-" * 80)
            for dim in unsupported_dims:
                print(f"   ❌ {dim}")
            print()
            
            print("💡 AVAILABLE DIMENSIONS:")
            print("-" * 80)
            for dim_name, dim_info in self.AVAILABLE_DIMENSIONS.items():
                print(f"   ✅ {dim_name} ({dim_info['type']}) - Example: {dim_info['example']}")
            print()
            
            if suggestions:
                print("💡 SUGGESTIONS:")
                print("-" * 80)
                for suggestion in suggestions:
                    print(f"   {suggestion}")
                print()
        
        # Generate and display SQL query
        sql_query = self._generate_sql_query(location, sku, additional_filters)
        print("📊 GENERATED SQL QUERY:")
        print("-" * 80)
        print(sql_query)
        print("-" * 80)
        print()
        
        # Get promotion data from RAG knowledge base
        promotion_data = self._get_promotion_data(sku, location)
        
        # Query matching customers
        matching_customers = self.seeder.query_by_location_and_sku(location, sku)
        
        if not matching_customers:
            return {
                "total_matched": 0,
                "error": f"No customers found in {location} interested in {sku}",
                "promotion": promotion_data,
            }
        
        print(f"📊 Found {len(matching_customers)} matching customers")
        if promotion_data:
            print(f"🎯 Promotion Score: {promotion_data.get('promotion_score', 0):.2f}")
            print(f"   {promotion_data.get('promotion_score_explanation', 'N/A')}")
        print()
        
        # Load full customer profiles to analyze sentiment and fatigue
        results = {
            "total_matched": len(matching_customers),
            "location": location,
            "sku": sku,
            "sql_query": sql_query,  # Include generated SQL query
            "unsupported_dimensions": unsupported_dims,  # Include unsupported dimensions
            "suggestions": suggestions,  # Include suggestions
            "parsed_dimensions": parsed_dims,  # Include all parsed dimensions
            "promotion": promotion_data,
            "suppressed_users": [],
            "whatsapp_routing": [],
            "time_optimized": [],
            "eligible_users": [],
            "before_metrics": {},
            "after_metrics": {},
        }
        
        # Analyze each customer
        for customer_data in matching_customers:
            customer_id = customer_data["customer_id"]
            
            # Get full profile from original data
            full_profile = self._get_full_profile(customer_id)
            
            if not full_profile:
                continue
            
            # Check suppression criteria
            suppression_reason = self._check_suppression(full_profile, customer_data)
            
            if suppression_reason:
                results["suppressed_users"].append({
                    "customer_id": customer_data["external_id"],
                    "reason": suppression_reason["reason"],
                    "icon": suppression_reason["icon"],
                    "details": suppression_reason["details"],
                    "fatigue_level": full_profile.fatigue_level.value,
                    "recent_sentiment": self._get_recent_sentiment(full_profile),
                })
            else:
                # Eligible for campaign
                results["eligible_users"].append(customer_data["external_id"])
                
                # Determine channel routing
                channel = self._determine_channel(full_profile)
                
                if channel == "whatsapp":
                    results["whatsapp_routing"].append({
                        "customer_id": customer_data["external_id"],
                        "reason": "High WhatsApp preference score",
                        "preference_score": self._get_channel_preference(full_profile, "whatsapp"),
                    })
                
                # Determine optimal send time
                optimal_time = self._determine_optimal_time(full_profile)
                results["time_optimized"].append({
                    "customer_id": customer_data["external_id"],
                    "optimal_time": optimal_time,
                    "timezone": full_profile.communication_frequency.timezone,
                })
        
        # Generate sample messages for first 3 eligible customers
        results["sample_messages"] = []
        if results["eligible_users"] and promotion_data:
            eligible_customers = [c for c in matching_customers if c["external_id"] in results["eligible_users"]]
            sample_customers = eligible_customers[:3]  # First 3 for demo
            
            for customer_data in sample_customers:
                # Determine channel for this customer
                full_profile = self._get_full_profile(customer_data["customer_id"])
                channel = self._determine_channel(full_profile)
                
                # Generate personalized message
                message = self.message_generator.generate_message(
                    customer_data=customer_data,
                    promotion_data=promotion_data,
                    channel=channel,
                    query_text=natural_language_query or f"{location} {sku}"
                )
                
                results["sample_messages"].append({
                    "customer_id": customer_data["external_id"],
                    "first_name": customer_data.get("first_name", "Valued Customer"),
                    "location": customer_data.get("location"),
                    "channel": channel,
                    **message
                })
        
        # Generate or reuse segment ID for eligible users
        segment_id = None
        segment_reused = False
        if results["eligible_users"]:
            segment_id, segment_reused = self._get_or_create_segment_id(
                location, sku, len(results["eligible_users"]), additional_filters
            )
            results["segment_id"] = segment_id
            results["segment_reused"] = segment_reused
            print(f"📋 Segment ID: {segment_id}")
            if segment_reused:
                print("   (Reused from previous query with same criteria)")
            print()
        
        # Calculate before/after metrics
        results["before_metrics"] = self._calculate_before_metrics(len(matching_customers))
        results["after_metrics"] = self._calculate_after_metrics(results)
        
        # Display results
        self._display_results(results)
        
        return results
    
    def _get_full_profile(self, customer_id: str):
        """Get full customer profile from loaded data."""
        # First get the enriched customer
        enriched_customer = self.seeder.customers.get(customer_id)
        
        if not enriched_customer:
            return self._create_mock_profile()
        
        external_id = enriched_customer.get('external_id')
        if not external_id:
            return self._create_mock_profile()
        
        # Try to load from full_profiles using external_id mapping
        customer_profile = self.full_profiles_by_external_id.get(external_id)
        
        if customer_profile and customer_profile.get('channel_preferences'):
            # Use real channel preferences from customer_profiles.json
            return self._create_profile_from_data(customer_profile)
        else:
            # Generate realistic channel preferences based on customer behavior
            return self._generate_profile_with_preferences(enriched_customer)
    
    def _create_profile_from_data(self, profile_data):
        """Create profile object from customer_profiles.json data."""
        class CustomerProfile:
            def __init__(self, data):
                self.fatigue_level = FatigueLevel.LOW
                self.sentiment_history = []
                
                # Convert channel preferences from dict to objects
                self.channel_preferences = []
                for pref in data.get('channel_preferences', []):
                    pref_obj = type('ChannelPreference', (object,), {
                        'channel': type('Channel', (object,), {'value': pref['channel']})(),
                        'preference_score': pref['preference_score'],
                        'engagement_count': pref['engagement_count']
                    })()
                    self.channel_preferences.append(pref_obj)
                
                # Communication frequency
                self.communication_frequency = type('obj', (object,), {
                    'preferred_time_start': 9,
                    'preferred_time_end': 17,
                    'timezone': 'Asia/Kolkata'
                })()
        
        return CustomerProfile(profile_data)
    
    def _generate_profile_with_preferences(self, enriched_customer):
        """Generate realistic channel preferences based on customer behavior."""
        import random
        
        # Use customer_id as seed for consistent preferences
        customer_id = enriched_customer.get('customer_id', '')
        random.seed(hash(customer_id))
        
        # Generate varied channel preferences
        # 30% prefer WhatsApp (high engagement)
        # 40% prefer Email
        # 20% prefer SMS
        # 10% prefer Voice
        
        rand_val = random.random()
        
        if rand_val < 0.30:  # WhatsApp preference
            preferences = [
                {'channel': 'whatsapp', 'preference_score': random.uniform(0.65, 0.95), 'engagement_count': random.randint(12, 50)},
                {'channel': 'email', 'preference_score': random.uniform(0.40, 0.70), 'engagement_count': random.randint(5, 20)},
                {'channel': 'sms', 'preference_score': random.uniform(0.20, 0.50), 'engagement_count': random.randint(0, 10)},
                {'channel': 'voice', 'preference_score': random.uniform(0.30, 0.60), 'engagement_count': random.randint(2, 15)},
            ]
        elif rand_val < 0.70:  # Email preference
            preferences = [
                {'channel': 'email', 'preference_score': random.uniform(0.70, 0.95), 'engagement_count': random.randint(20, 60)},
                {'channel': 'whatsapp', 'preference_score': random.uniform(0.30, 0.60), 'engagement_count': random.randint(0, 10)},
                {'channel': 'sms', 'preference_score': random.uniform(0.20, 0.50), 'engagement_count': random.randint(0, 8)},
                {'channel': 'voice', 'preference_score': random.uniform(0.25, 0.55), 'engagement_count': random.randint(1, 12)},
            ]
        elif rand_val < 0.90:  # SMS preference
            preferences = [
                {'channel': 'sms', 'preference_score': random.uniform(0.60, 0.85), 'engagement_count': random.randint(15, 40)},
                {'channel': 'email', 'preference_score': random.uniform(0.40, 0.65), 'engagement_count': random.randint(10, 25)},
                {'channel': 'whatsapp', 'preference_score': random.uniform(0.25, 0.55), 'engagement_count': random.randint(0, 8)},
                {'channel': 'voice', 'preference_score': random.uniform(0.30, 0.60), 'engagement_count': random.randint(2, 15)},
            ]
        else:  # Voice preference
            preferences = [
                {'channel': 'voice', 'preference_score': random.uniform(0.65, 0.90), 'engagement_count': random.randint(18, 45)},
                {'channel': 'email', 'preference_score': random.uniform(0.45, 0.70), 'engagement_count': random.randint(12, 30)},
                {'channel': 'sms', 'preference_score': random.uniform(0.30, 0.60), 'engagement_count': random.randint(5, 15)},
                {'channel': 'whatsapp', 'preference_score': random.uniform(0.35, 0.65), 'engagement_count': random.randint(3, 12)},
            ]
        
        # Create profile object
        class CustomerProfile:
            def __init__(self, prefs):
                self.fatigue_level = FatigueLevel.LOW
                self.sentiment_history = []
                
                # Convert preferences to objects
                self.channel_preferences = []
                for pref in prefs:
                    pref_obj = type('ChannelPreference', (object,), {
                        'channel': type('Channel', (object,), {'value': pref['channel']})(),
                        'preference_score': pref['preference_score'],
                        'engagement_count': pref['engagement_count']
                    })()
                    self.channel_preferences.append(pref_obj)
                
                # Communication frequency
                self.communication_frequency = type('obj', (object,), {
                    'preferred_time_start': 9,
                    'preferred_time_end': 17,
                    'timezone': 'Asia/Kolkata'
                })()
        
        return CustomerProfile(preferences)
    
    def _check_suppression(self, profile, customer_data) -> Optional[Dict]:
        """
        Check if customer should be suppressed from campaign.
        
        Returns detailed suppression data or None if eligible.
        """
        # Simulate suppression logic based on enriched data
        # In production, would check actual profile data
        
        # For demo, randomly suppress some users based on patterns
        customer_id = customer_data["customer_id"]
        
        # Simulate: 10% angry customers (negative sentiment)
        if hash(customer_id + "sentiment") % 10 == 0:
            return {
                "reason": "Negative sentiment detected",
                "icon": "😞",
                "details": {
                    "complaint_filed": "3 days ago",
                    "sentiment_score": 0.15,
                    "threshold": 0.40,
                    "ignored_messages": 5,
                    "last_positive_interaction": "21 days ago"
                }
            }
        
        # Simulate: 15% fatigued customers
        if hash(customer_id + "fatigue") % 7 == 0:
            messages_count = 5 + (hash(customer_id) % 5)  # 5-9 messages
            hours_since = 2 + (hash(customer_id) % 20)  # 2-21 hours
            return {
                "reason": "High fatigue level",
                "icon": "⚠️",
                "details": {
                    "messages_last_7_days": messages_count,
                    "last_message": f"{hours_since} hours ago",
                    "fatigue_score": 0.75 + (hash(customer_id) % 15) / 100,  # 0.75-0.89
                    "threshold": 0.70,
                    "messages_last_24h": 2 if hours_since < 12 else 1
                }
            }
        
        # Simulate: 5% recent unsubscribe signals
        if hash(customer_id + "unsubscribe") % 20 == 0:
            hours_since = 12 + (hash(customer_id) % 36)  # 12-47 hours
            return {
                "reason": "High frequency (recent contact)",
                "icon": "🔄",
                "details": {
                    "last_contacted": f"{hours_since} hours ago",
                    "active_campaign": "New Year Sale" if hours_since < 24 else "Holiday Promo",
                    "waiting_period_remaining": f"{48 - hours_since} hours",
                    "messages_in_queue": 1 if hours_since < 30 else 0
                }
            }
        
        return None
    
    def _get_recent_sentiment(self, profile) -> str:
        """Get most recent sentiment."""
        if profile and profile.sentiment_history:
            return profile.sentiment_history[-1].sentiment.value
        return "neutral"
    
    def _determine_channel(self, profile) -> str:
        """
        Determine optimal channel for customer based on preference score AND engagement.
        
        Priority: WhatsApp if customer is active on it (high opens/engagement)
        """
        if profile and profile.channel_preferences:
            # Find WhatsApp preference
            whatsapp_pref = None
            for pref in profile.channel_preferences:
                if pref.channel.value == "whatsapp":
                    whatsapp_pref = pref
                    break
            
            # If WhatsApp preference exists and customer is active (score > 0.6 AND engagement_count > 10)
            if whatsapp_pref and whatsapp_pref.preference_score > 0.6 and whatsapp_pref.engagement_count > 10:
                return "whatsapp"
            
            # Otherwise, return channel with highest preference score
            best_channel = max(
                profile.channel_preferences,
                key=lambda p: p.preference_score
            )
            return best_channel.channel.value
        return "email"  # Default
    
    def _get_channel_preference(self, profile, channel: str) -> float:
        """Get preference score for a specific channel."""
        if profile and profile.channel_preferences:
            for pref in profile.channel_preferences:
                if pref.channel.value == channel:
                    return pref.preference_score
        return 0.5  # Default
    
    def _determine_optimal_time(self, profile) -> str:
        """Determine optimal send time for customer."""
        if profile and profile.communication_frequency:
            start = profile.communication_frequency.preferred_time_start
            end = profile.communication_frequency.preferred_time_end
            optimal = (start + end) // 2
            return f"{optimal:02d}:00"
        return "14:00"  # Default 2 PM
    
    def _calculate_before_metrics(self, total_customers: int) -> Dict:
        """Calculate spray-and-pray metrics (before AI)."""
        return {
            "total_sent": total_customers,
            "channel": "SMS (cheapest)",
            "cost_per_message": 0.0075,
            "total_cost": total_customers * 0.0075,
            "expected_engagement": total_customers * 0.12,  # 12% engagement
            "expected_unsubscribes": total_customers * 0.08,  # 8% unsubscribe
            "expected_complaints": total_customers * 0.05,  # 5% complaints
        }
    
    def _calculate_after_metrics(self, results: Dict) -> Dict:
        """Calculate AI-optimized metrics (after AI)."""
        eligible = len(results["eligible_users"])
        suppressed = len(results["suppressed_users"])
        whatsapp_users = len(results["whatsapp_routing"])
        
        # Count email users from time_optimized list (which has full user data)
        email_users = 0
        for user in results.get("time_optimized", []):
            if isinstance(user, dict) and user.get("selected_channel") == "email":
                email_users += 1
        
        sms_users = eligible - whatsapp_users - email_users
        
        # Calculate costs using correct AWS pricing
        # WhatsApp: $0.005 per message (cheaper than SMS!)
        # SMS: $0.0075 per message
        # Email: $0.0001 per message (cheapest)
        whatsapp_cost = whatsapp_users * 0.005
        sms_cost = sms_users * 0.0075
        email_cost = email_users * 0.0001
        total_cost = whatsapp_cost + sms_cost + email_cost
        
        return {
            "total_sent": eligible,
            "suppressed": suppressed,
            "channel_mix": {
                "whatsapp": whatsapp_users,
                "sms": sms_users,
                "email": email_users,
            },
            "total_cost": total_cost,
            "expected_engagement": eligible * 0.62,  # 62% engagement with AI
            "expected_unsubscribes": eligible * 0.005,  # 0.5% unsubscribe
            "expected_complaints": eligible * 0.002,  # 0.2% complaints
            "cost_savings": results["before_metrics"]["total_cost"] - total_cost,
            "engagement_improvement": (0.62 - 0.12) * 100,  # 50% improvement
        }
    
    def _display_results(self, results: Dict):
        """Display campaign analysis results."""
        
        # Display promotion information first
        if results.get('promotion'):
            promo = results['promotion']
            print("🎯 PROMOTION INTELLIGENCE (from RAG Knowledge Base)")
            print("-" * 80)
            print(f"Product: {promo.get('product_name', 'N/A')}")
            print(f"Promotion Score: {promo.get('promotion_score', 0):.2f}")
            print(f"Explanation: {promo.get('promotion_score_explanation', 'N/A')}")
            
            if promo.get('active_promotions'):
                print(f"\nActive Promotions: {len(promo['active_promotions'])}")
                for p in promo['active_promotions']:
                    print(f"  • {p.get('name', 'N/A')}: {p.get('discount_percentage', 0)}% off")
                    print(f"    Valid: {p.get('valid_from', 'N/A')} to {p.get('valid_until', 'N/A')}")
                    print(f"    Expected Lift: +{p.get('expected_lift', 0)*100:.1f}%")
            
            if promo.get('deepar_forecast'):
                forecast = promo['deepar_forecast']
                print(f"\nDeepAR Forecast (30-day):")
                print(f"  Predicted Demand: {forecast.get('predicted_demand_30d', 0)} units")
                print(f"  Trend: {forecast.get('trend', 'N/A')}")
            
            if promo.get('inventory_status'):
                inv = promo['inventory_status']
                print(f"\nInventory Status:")
                print(f"  Available: {inv.get('available', 0)} units")
                print(f"  Reserved: {inv.get('reserved', 0)} units")
            
            print(f"\nCannibalization Risk: {promo.get('cannibalization_risk', 'unknown').upper()}")
            print()
        
        print("🚫 SUPPRESSED USERS")
        print("-" * 80)
        print(f"Total suppressed: {len(results['suppressed_users'])}")
        
        if results["suppressed_users"]:
            print("\nSample suppressed customers (with details):")
            for user in results["suppressed_users"][:5]:
                print(f"\n  {user['icon']} {user['customer_id']}: {user['reason']}")
                details = user.get('details', {})
                for key, value in details.items():
                    formatted_key = key.replace('_', ' ').title()
                    print(f"     • {formatted_key}: {value}")
        print()
        
        print("💬 WHATSAPP-FIRST ROUTING")
        print("-" * 80)
        print(f"Total WhatsApp routing: {len(results['whatsapp_routing'])}")
        
        if results["whatsapp_routing"]:
            print("\nSample WhatsApp users:")
            for user in results["whatsapp_routing"][:5]:
                print(f"  • {user['customer_id']}: Score {user['preference_score']:.2f}")
        print()
        
        print("⏰ TIME-OPTIMIZED SENDS")
        print("-" * 80)
        print(f"Total time-optimized: {len(results['time_optimized'])}")
        
        if results["time_optimized"]:
            print("\nSample optimal times:")
            for user in results["time_optimized"][:5]:
                print(f"  • {user['customer_id']}: {user['optimal_time']} {user['timezone']}")
        print()
        
        # Display sample generated messages
        if results.get("sample_messages"):
            print("✉️  SAMPLE GENERATED MESSAGES")
            print("-" * 80)
            print(f"Showing {len(results['sample_messages'])} personalized message examples:\n")
            
            for i, msg in enumerate(results["sample_messages"], 1):
                print(f"Message {i}:")
                print(f"  Customer: {msg['first_name']} ({msg['customer_id']})")
                print(f"  Location: {msg['location']}")
                print(f"  Channel: {msg['channel'].upper()}")
                
                if msg.get('subject'):
                    print(f"  Subject: {msg['subject']}")
                
                print(f"  Content:")
                # Display content with indentation
                content_lines = msg['content'].split('\n')
                for line in content_lines[:10]:  # Show first 10 lines
                    print(f"    {line}")
                
                if len(content_lines) > 10:
                    print(f"    ... ({len(content_lines) - 10} more lines)")
                
                print()
        
        print("📊 BEFORE vs AFTER METRICS")
        print("-" * 80)
        
        before = results["before_metrics"]
        after = results["after_metrics"]
        
        print("\nBEFORE (Spray-and-Pray):")
        print(f"  Total sent: {before['total_sent']}")
        print(f"  Channel: {before['channel']}")
        print(f"  Total cost: ${before['total_cost']:.2f}")
        print(f"  Expected engagement: {before['expected_engagement']:.0f} ({before['expected_engagement']/before['total_sent']*100:.1f}%)")
        print(f"  Expected unsubscribes: {before['expected_unsubscribes']:.0f}")
        print(f"  Expected complaints: {before['expected_complaints']:.0f}")
        
        print("\nAFTER (AI-Optimized):")
        print(f"  Total sent: {after['total_sent']}")
        print(f"  Suppressed: {after['suppressed']}")
        print(f"  Channel mix: {after['channel_mix']['whatsapp']} WhatsApp, {after['channel_mix']['sms']} SMS")
        print(f"  Total cost: ${after['total_cost']:.2f}")
        
        if after['total_sent'] > 0:
            engagement_pct = after['expected_engagement']/after['total_sent']*100
            print(f"  Expected engagement: {after['expected_engagement']:.0f} ({engagement_pct:.1f}%)")
        else:
            print(f"  Expected engagement: 0 (0.0%)")
        
        print(f"  Expected unsubscribes: {after['expected_unsubscribes']:.0f}")
        print(f"  Expected complaints: {after['expected_complaints']:.0f}")
        
        print("\n💰 SAVINGS:")
        savings_pct = after['cost_savings']/before['total_cost']*100 if before['total_cost'] > 0 else 0
        print(f"  Cost savings: ${after['cost_savings']:.2f} ({savings_pct:.1f}%)")
        print(f"  Engagement improvement: +{after['engagement_improvement']:.1f}%")
        print(f"  Unsubscribes prevented: {before['expected_unsubscribes'] - after['expected_unsubscribes']:.0f}")
        print(f"  Complaints prevented: {before['expected_complaints'] - after['expected_complaints']:.0f}")
        print()


def main():
    """Run interactive demo queries."""
    engine = DemoQueryEngine()
    
    # Demo query 1: Bangalore users for SKU-LAPTOP-001
    print("\n" + "=" * 80)
    print("DEMO 1: Run campaign for Bangalore users for SKU-LAPTOP-001")
    print("=" * 80)
    print()
    
    results1 = engine.run_campaign_query("Bangalore", "SKU-LAPTOP-001")
    
    # Demo query 2: Bangalore users for SKU-PHONE-002
    print("\n" + "=" * 80)
    print("DEMO 2: Run campaign for Bangalore users for SKU-PHONE-002")
    print("=" * 80)
    print()
    
    results2 = engine.run_campaign_query("Bangalore", "SKU-PHONE-002")
    
    print("\n" + "=" * 80)
    print("Demo Complete!")
    print("=" * 80)
    print("\n✅ Interactive demo queries executed successfully")
    print("\n💡 Next steps:")
    print("   - Complete Task 3 (AWS infrastructure) to enable DynamoDB storage")
    print("   - Complete Task 11 (Orchestration + UI) for full interactive demo")
    print()


if __name__ == "__main__":
    main()
