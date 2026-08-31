"""
Unit tests for Repairability Index DB and Product Lifecycle Tracker.
"""
import pytest
from repairability_index_db import RepairabilityIndexDB
from product_lifecycle_tracker import ProductLifecycleTracker

def test_db_retrieval():
    db = RepairabilityIndexDB()
    details = db.get_product_details("framework_laptop")
    
    assert details is not None
    assert details["name"] == "Framework Laptop"
    assert details["repairability_score"] == 9.5
    assert "battery degradation" in details["common_failures"]

def test_db_category_filter():
    db = RepairabilityIndexDB()
    electronics = db.get_products_by_category("electronics")
    
    assert "framework_laptop" in electronics
    assert "iphone_standard" in electronics
    assert "washing_machine_basic" not in electronics

def test_tracker_successful_repair():
    tracker = ProductLifecycleTracker()
    # Framework laptop embodied carbon: 250. Battery part cost: 15. Net saved: 235.
    record = tracker.log_repair("framework_laptop", "battery", successful=True)
    
    assert record["status"] == "Successful"
    assert record["embodied_carbon_avoided_kg"] == 235.0
    assert record["part_carbon_cost_kg"] == 15.0

def test_tracker_failed_repair():
    tracker = ProductLifecycleTracker()
    record = tracker.log_repair("iphone_standard", "screen", successful=False)
    
    assert record["status"] == "Failed"
    assert record["embodied_carbon_avoided_kg"] == 0.0

def test_tracker_cumulative_impact():
    tracker = ProductLifecycleTracker()
    tracker.log_repair("framework_laptop", "battery", successful=True)  # Saves 235
    tracker.log_repair("washing_machine_basic", "pump", successful=True)  # Saves 400 - 8 = 392
    tracker.log_repair("iphone_standard", "screen", successful=False)  # Saves 0
    
    impact = tracker.get_cumulative_impact()
    
    assert impact["total_repairs_attempted"] == 3
    assert impact["successful_repairs"] == 2
    assert impact["total_carbon_saved_kg"] == 627.0  # 235 + 392
    assert impact["estimated_waste_diverted_kg"] == 4.0  # 2 successful * 2kg

def test_tracker_unknown_product():
    tracker = ProductLifecycleTracker()
    with pytest.raises(ValueError, match="Unknown product"):
        tracker.log_repair("magic_unobtanium", "core", successful=True)
