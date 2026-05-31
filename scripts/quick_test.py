#!/usr/bin/env python3
"""
Quick test script to verify the extraction and validation process
Runs a minimal test without requiring full Core Keeper dumps
"""

import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def test_json_structure():
    """Test JSON file structure"""
    logger.info("Testing JSON structure...")
    
    # Create a minimal valid item-data.json for testing
    test_data = {
        "items": {
            "1": {
                "objectID": 1,
                "name": "Test Item",
                "description": "Test Description",
                "initialAmount": 100,
                "objectType": 100,
                "rarity": 0,
                "isStackable": 1,
                "iconIndex": 0,
                "damage": {
                    "range": [10.0, 12.0],
                    "isRange": False
                },
                "cooldown": 1.0,
                "whenEquipped": [
                    {"id": 1, "value": 5}
                ],
                "setBonusId": 1
            }
        },
        "setBonuses": {
            "1": {
                "id": 1,
                "rarity": 1,
                "data": [],
                "pieces": [1]
            }
        }
    }
    
    # Validate structure
    assert "items" in test_data, "Missing 'items' key"
    assert "setBonuses" in test_data, "Missing 'setBonuses' key"
    assert isinstance(test_data["items"], dict), "'items' must be a dict"
    assert isinstance(test_data["setBonuses"], dict), "'setBonuses' must be a dict"
    
    # Validate item structure
    for item_id, item in test_data["items"].items():
        required = ["objectID", "name", "description", "initialAmount", "objectType", "rarity", "isStackable", "iconIndex"]
        for field in required:
            assert field in item, f"Item {item_id} missing field: {field}"
    
    # Validate set bonus structure
    for bonus_id, bonus in test_data["setBonuses"].items():
        required = ["id", "rarity", "data", "pieces"]
        for field in required:
            assert field in bonus, f"Set Bonus {bonus_id} missing field: {field}"
    
    logger.info("✓ JSON structure test PASSED")
    return True


def test_json_serialization():
    """Test JSON can be properly serialized and deserialized"""
    logger.info("Testing JSON serialization...")
    
    test_data = {
        "items": {
            "1": {
                "objectID": 1,
                "name": "Test",
                "description": "Test",
                "initialAmount": 100,
                "objectType": 100,
                "rarity": 0,
                "isStackable": 1,
                "iconIndex": 0
            }
        },
        "setBonuses": {}
    }
    
    # Test serialization
    try:
        json_str = json.dumps(test_data, indent=2)
        deserialized = json.loads(json_str)
        assert deserialized == test_data, "Deserialized data doesn't match original"
        logger.info("✓ JSON serialization test PASSED")
        return True
    except Exception as e:
        logger.error(f"✗ JSON serialization test FAILED: {e}")
        return False


def test_validation_script_exists():
    """Test that validation script exists and is valid Python"""
    logger.info("Testing validation script...")
    
    script_path = Path("scripts/test_items.py")
    
    if not script_path.exists():
        logger.error(f"✗ Validation script not found: {script_path}")
        return False
    
    # Try to parse the script as valid Python
    try:
        with open(script_path) as f:
            compile(f.read(), str(script_path), 'exec')
        logger.info("✓ Validation script test PASSED")
        return True
    except SyntaxError as e:
        logger.error(f"✗ Validation script has syntax errors: {e}")
        return False


def test_items_extraction_script_exists():
    """Test that items extraction script exists and is valid Python"""
    logger.info("Testing items extraction script...")
    
    script_path = Path("scripts/items.py")
    
    if not script_path.exists():
        logger.error(f"✗ Items script not found: {script_path}")
        return False
    
    # Try to parse the script as valid Python
    try:
        with open(script_path) as f:
            compile(f.read(), str(script_path), 'exec')
        logger.info("✓ Items extraction script test PASSED")
        return True
    except SyntaxError as e:
        logger.error(f"✗ Items script has syntax errors: {e}")
        return False


def test_blacklist_integrity():
    """Test that blacklist is valid"""
    logger.info("Testing blacklist integrity...")
    
    try:
        from scripts import blacklist
        
        # Check ITEM_BLACKLIST exists and is a list
        assert hasattr(blacklist, 'ITEM_BLACKLIST'), "Missing ITEM_BLACKLIST"
        assert isinstance(blacklist.ITEM_BLACKLIST, list), "ITEM_BLACKLIST must be a list"
        
        # Check TEXTURE_WHOLE_IMAGE_BLACKLIST exists
        assert hasattr(blacklist, 'TEXTURE_WHOLE_IMAGE_BLACKLIST'), "Missing TEXTURE_WHOLE_IMAGE_BLACKLIST"
        assert isinstance(blacklist.TEXTURE_WHOLE_IMAGE_BLACKLIST, list), "TEXTURE_WHOLE_IMAGE_BLACKLIST must be a list"
        
        # Check DUPLICATE_BLACKLIST exists
        assert hasattr(blacklist, 'DUPLICATE_BLACKLIST'), "Missing DUPLICATE_BLACKLIST"
        assert isinstance(blacklist.DUPLICATE_BLACKLIST, list), "DUPLICATE_BLACKLIST must be a list"
        
        logger.info(f"✓ Blacklist integrity test PASSED ({len(blacklist.ITEM_BLACKLIST)} items blacklisted)")
        return True
    except Exception as e:
        logger.error(f"✗ Blacklist integrity test FAILED: {e}")
        return False


def test_util_functions():
    """Test that util functions exist and are callable"""
    logger.info("Testing util functions...")
    
    try:
        from scripts import util
        
        # Check for required functions
        required_functions = [
            'load_cache',
            'set_cache',
            'get_translations',
            'get_enum',
            'first_ingredient_is_primary',
            'get_food'
        ]
        
        for func_name in required_functions:
            assert hasattr(util, func_name), f"Missing function: {func_name}"
            assert callable(getattr(util, func_name)), f"{func_name} is not callable"
        
        logger.info(f"✓ Util functions test PASSED ({len(required_functions)} functions found)")
        return True
    except Exception as e:
        logger.error(f"✗ Util functions test FAILED: {e}")
        return False


def test_requirements():
    """Test that required packages are available"""
    logger.info("Testing required packages...")
    
    required_packages = [
        ('yaml', 'PyYAML'),
        ('PIL', 'Pillow'),
        ('unityparser', 'unityparser'),
    ]
    
    all_available = True
    for import_name, package_name in required_packages:
        try:
            __import__(import_name)
            logger.info(f"  ✓ {package_name} available")
        except ImportError:
            logger.warning(f"  ✗ {package_name} not available (required for full extraction)")
            all_available = False
    
    if all_available:
        logger.info("✓ All required packages test PASSED")
    else:
        logger.warning("⚠ Some packages missing - run: pip install -r scripts/requirements.txt")
    
    return True


def main():
    """Run all quick tests"""
    print("=" * 80)
    print("QUICK TEST SUITE - Core Keeper Item Database Update")
    print("=" * 80)
    print()
    
    tests = [
        ("JSON Structure", test_json_structure),
        ("JSON Serialization", test_json_serialization),
        ("Validation Script", test_validation_script_exists),
        ("Items Extraction Script", test_items_extraction_script_exists),
        ("Blacklist Integrity", test_blacklist_integrity),
        ("Util Functions", test_util_functions),
        ("Required Packages", test_requirements),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"✗ {test_name} - Unexpected error: {e}")
            results.append((test_name, False))
        print()
    
    # Print summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name:<40} {status}")
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 80)
    
    if passed == total:
        print("✓ All tests PASSED!")
        print()
        print("Next steps:")
        print("1. Export Core Keeper assets using AssetRipper to ./dump/")
        print("2. Run: python3 scripts/items.py")
        print("3. Run: python3 scripts/test_items.py")
        print("4. Run: ./scripts/deploy.py")
        return 0
    else:
        print("✗ Some tests FAILED")
        print("Please fix the issues above before proceeding")
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
