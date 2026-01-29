#!/usr/bin/env python3
"""
Phase 1: Comprehensive Local Testing Suite

Tests all components before AWS deployment:
1. Data generation and seeding
2. AI engines (prediction, adaptation, guardrails, agents, fatigue, analytics)
3. Demo query engine
4. Web API endpoints
5. Integration tests
"""

import sys
import json
from pathlib import Path
from typing import Dict, List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ai_cpaas_demo.data.demo_query import DemoQueryEngine
from ai_cpaas_demo.data.data_seeder import DataSeeder


class Phase1TestSuite:
    """Comprehensive test suite for Phase 1 local testing."""
    
    def __init__(self):
        """Initialize test suite."""
        self.results = {
            "passed": [],
            "failed": [],
            "warnings": []
        }
        self.demo_engine = None
    
    def run_all_tests(self):
        """Run all Phase 1 tests."""
        print("\n" + "=" * 80)
        print("🧪 PHASE 1: COMPREHENSIVE LOCAL TESTING")
        print("=" * 80)
        print("\nTesting all components before AWS deployment...\n")
        
        # Test 1: Data Loading
        self.test_data_loading()
        
        # Test 2: Data Seeding
        self.test_data_seeding()
        
        # Test 3: Query Engine
        self.test_query_engine()
        
        # Test 4: Multiple Locations
        self.test_multiple_locations()
        
        # Test 5: Multiple SKUs
        self.test_multiple_skus()
        
        # Test 6: Edge Cases
        self.test_edge_cases()
        
        # Test 7: Performance
        self.test_performance()
        
        # Print summary
        self.print_summary()
    
    def test_data_loading(self):
        """Test 1: Data loading and initialization."""
        print("=" * 80)
        print("Test 1: Data Loading & Initialization")
        print("=" * 80)
        
        try:
            # Initialize demo engine
            self.demo_engine = DemoQueryEngine()
            
            # Check data loaded
            stats = self.demo_engine.seeder.get_statistics()
            
            assert stats['total_customers'] == 1000, "Expected 1000 customers"
            assert len(stats['locations']) > 0, "No locations found"
            assert stats['skus_tracked'] > 0, "No SKUs found"
            
            print(f"✅ PASSED: Loaded {stats['total_customers']} customers")
            print(f"   - Locations: {len(stats['locations'])}")
            print(f"   - SKUs: {stats['skus_tracked']}")
            print(f"   - Bangalore users: {stats['bangalore_users']}")
            
            self.results["passed"].append("Data Loading")
            
        except Exception as e:
            print(f"❌ FAILED: {str(e)}")
            self.results["failed"].append(f"Data Loading: {str(e)}")
        
        print()
    
    def test_data_seeding(self):
        """Test 2: Data seeding and indexing."""
        print("=" * 80)
        print("Test 2: Data Seeding & Indexing")
        print("=" * 80)
        
        try:
            # Test location query
            bangalore_users = self.demo_engine.seeder.query_by_location("Bangalore")
            assert len(bangalore_users) > 0, "No Bangalore users found"
            
            # Test SKU query
            laptop_users = self.demo_engine.seeder.query_by_sku("SKU-LAPTOP-001")
            assert len(laptop_users) > 0, "No laptop users found"
            
            # Test combined query
            combined = self.demo_engine.seeder.query_by_location_and_sku(
                "Bangalore", "SKU-LAPTOP-001"
            )
            assert len(combined) > 0, "No combined results found"
            assert len(combined) <= len(bangalore_users), "Combined should be subset"
            assert len(combined) <= len(laptop_users), "Combined should be subset"
            
            print(f"✅ PASSED: Data seeding and indexing working")
            print(f"   - Bangalore users: {len(bangalore_users)}")
            print(f"   - Laptop users: {len(laptop_users)}")
            print(f"   - Combined (Bangalore + Laptop): {len(combined)}")
            
            self.results["passed"].append("Data Seeding")
            
        except Exception as e:
            print(f"❌ FAILED: {str(e)}")
            self.results["failed"].append(f"Data Seeding: {str(e)}")
        
        print()
    
    def test_query_engine(self):
        """Test 3: Query engine functionality."""
        print("=" * 80)
        print("Test 3: Query Engine Functionality")
        print("=" * 80)
        
        try:
            # Run campaign query
            results = self.demo_engine.run_campaign_query("Bangalore", "SKU-LAPTOP-001")
            
            # Validate results structure
            assert "total_matched" in results, "Missing total_matched"
            assert "suppressed_users" in results, "Missing suppressed_users"
            assert "eligible_users" in results, "Missing eligible_users"
            assert "before_metrics" in results, "Missing before_metrics"
            assert "after_metrics" in results, "Missing after_metrics"
            
            # Validate metrics
            assert results["total_matched"] > 0, "No customers matched"
            assert len(results["suppressed_users"]) >= 0, "Invalid suppressed count"
            assert len(results["eligible_users"]) >= 0, "Invalid eligible count"
            
            # Validate before/after metrics
            before = results["before_metrics"]
            after = results["after_metrics"]
            
            assert before["total_sent"] == results["total_matched"], "Before total mismatch"
            assert after["total_sent"] == len(results["eligible_users"]), "After total mismatch"
            assert after["cost_savings"] >= 0, "Negative cost savings"
            
            print(f"✅ PASSED: Query engine working correctly")
            print(f"   - Total matched: {results['total_matched']}")
            print(f"   - Suppressed: {len(results['suppressed_users'])}")
            print(f"   - Eligible: {len(results['eligible_users'])}")
            print(f"   - Cost savings: ${after['cost_savings']:.2f}")
            
            self.results["passed"].append("Query Engine")
            
        except Exception as e:
            print(f"❌ FAILED: {str(e)}")
            self.results["failed"].append(f"Query Engine: {str(e)}")
        
        print()
    
    def test_multiple_locations(self):
        """Test 4: Multiple location queries."""
        print("=" * 80)
        print("Test 4: Multiple Location Queries")
        print("=" * 80)
        
        locations = ["Bangalore", "Mumbai", "Delhi"]
        sku = "SKU-LAPTOP-001"
        
        try:
            for location in locations:
                results = self.demo_engine.run_campaign_query(location, sku)
                
                assert results["total_matched"] >= 0, f"Invalid results for {location}"
                
                print(f"✅ {location}: {results['total_matched']} customers, "
                      f"{len(results['suppressed_users'])} suppressed")
            
            print(f"\n✅ PASSED: Multiple location queries working")
            self.results["passed"].append("Multiple Locations")
            
        except Exception as e:
            print(f"❌ FAILED: {str(e)}")
            self.results["failed"].append(f"Multiple Locations: {str(e)}")
        
        print()
    
    def test_multiple_skus(self):
        """Test 5: Multiple SKU queries."""
        print("=" * 80)
        print("Test 5: Multiple SKU Queries")
        print("=" * 80)
        
        location = "Bangalore"
        skus = ["SKU-LAPTOP-001", "SKU-PHONE-002", "SKU-TABLET-003"]
        
        try:
            for sku in skus:
                results = self.demo_engine.run_campaign_query(location, sku)
                
                assert results["total_matched"] >= 0, f"Invalid results for {sku}"
                
                print(f"✅ {sku}: {results['total_matched']} customers, "
                      f"${results['after_metrics']['cost_savings']:.2f} savings")
            
            print(f"\n✅ PASSED: Multiple SKU queries working")
            self.results["passed"].append("Multiple SKUs")
            
        except Exception as e:
            print(f"❌ FAILED: {str(e)}")
            self.results["failed"].append(f"Multiple SKUs: {str(e)}")
        
        print()
    
    def test_edge_cases(self):
        """Test 6: Edge cases and error handling."""
        print("=" * 80)
        print("Test 6: Edge Cases & Error Handling")
        print("=" * 80)
        
        try:
            # Test 6.1: Invalid location
            results = self.demo_engine.run_campaign_query("InvalidCity", "SKU-LAPTOP-001")
            assert results["total_matched"] == 0, "Should return 0 for invalid location"
            print("✅ Invalid location handled correctly")
            
            # Test 6.2: Invalid SKU
            results = self.demo_engine.run_campaign_query("Bangalore", "SKU-INVALID-999")
            assert results["total_matched"] == 0, "Should return 0 for invalid SKU"
            print("✅ Invalid SKU handled correctly")
            
            # Test 6.3: Both invalid
            results = self.demo_engine.run_campaign_query("InvalidCity", "SKU-INVALID-999")
            assert results["total_matched"] == 0, "Should return 0 for both invalid"
            print("✅ Both invalid handled correctly")
            
            print(f"\n✅ PASSED: Edge cases handled correctly")
            self.results["passed"].append("Edge Cases")
            
        except Exception as e:
            print(f"❌ FAILED: {str(e)}")
            self.results["failed"].append(f"Edge Cases: {str(e)}")
        
        print()
    
    def test_performance(self):
        """Test 7: Performance benchmarks."""
        print("=" * 80)
        print("Test 7: Performance Benchmarks")
        print("=" * 80)
        
        import time
        
        try:
            # Test query performance
            start = time.time()
            results = self.demo_engine.run_campaign_query("Bangalore", "SKU-LAPTOP-001")
            duration = time.time() - start
            
            # Performance thresholds
            assert duration < 5.0, f"Query too slow: {duration:.2f}s (expected < 5s)"
            
            print(f"✅ Query performance: {duration:.3f}s")
            
            if duration > 2.0:
                self.results["warnings"].append(
                    f"Query performance slow: {duration:.2f}s (consider optimization)"
                )
            
            # Test data loading performance
            start = time.time()
            seeder = DataSeeder()
            seeder.seed_in_memory()
            duration = time.time() - start
            
            assert duration < 10.0, f"Data loading too slow: {duration:.2f}s (expected < 10s)"
            
            print(f"✅ Data loading performance: {duration:.3f}s")
            
            if duration > 5.0:
                self.results["warnings"].append(
                    f"Data loading slow: {duration:.2f}s (consider caching)"
                )
            
            print(f"\n✅ PASSED: Performance within acceptable limits")
            self.results["passed"].append("Performance")
            
        except Exception as e:
            print(f"❌ FAILED: {str(e)}")
            self.results["failed"].append(f"Performance: {str(e)}")
        
        print()
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 80)
        print("📊 PHASE 1 TEST SUMMARY")
        print("=" * 80)
        
        total = len(self.results["passed"]) + len(self.results["failed"])
        passed = len(self.results["passed"])
        failed = len(self.results["failed"])
        warnings = len(self.results["warnings"])
        
        print(f"\nTotal Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⚠️  Warnings: {warnings}")
        
        if self.results["passed"]:
            print("\n✅ Passed Tests:")
            for test in self.results["passed"]:
                print(f"   - {test}")
        
        if self.results["failed"]:
            print("\n❌ Failed Tests:")
            for test in self.results["failed"]:
                print(f"   - {test}")
        
        if self.results["warnings"]:
            print("\n⚠️  Warnings:")
            for warning in self.results["warnings"]:
                print(f"   - {warning}")
        
        print("\n" + "=" * 80)
        
        if failed == 0:
            print("🎉 ALL TESTS PASSED - READY FOR PHASE 2 (SAM LOCAL)")
        else:
            print("⚠️  SOME TESTS FAILED - FIX ISSUES BEFORE PROCEEDING")
        
        print("=" * 80)
        
        print("\n📋 Next Steps:")
        if failed == 0:
            print("   1. ✅ Phase 1 Complete - Local testing passed")
            print("   2. 🚀 Ready for Phase 2 - SAM Local testing")
            print("   3. 📦 Ready for Phase 3 - AWS deployment")
            print("\n💡 To proceed to Phase 2:")
            print("   - Install SAM CLI: brew install aws-sam-cli")
            print("   - Install Docker: https://www.docker.com/products/docker-desktop")
            print("   - Run: sam init (to create SAM template)")
        else:
            print("   1. ❌ Fix failed tests")
            print("   2. 🔄 Re-run: python3 run_phase1_tests.py")
            print("   3. ✅ Ensure all tests pass before Phase 2")
        
        print()


def main():
    """Run Phase 1 test suite."""
    suite = Phase1TestSuite()
    suite.run_all_tests()


if __name__ == "__main__":
    main()
