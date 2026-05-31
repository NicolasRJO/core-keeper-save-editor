#!/usr/bin/env python3
"""
Test script to validate the item extraction process
Tests structure, completeness, and data integrity
"""

import json
import logging
import sys
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ItemDataValidator:
    """Validates the generated item-data.json file"""
    
    def __init__(self, json_path: str):
        self.json_path = json_path
        self.data = None
        self.errors = []
        self.warnings = []
        self.stats = {}
        self.test_results = []
    
    def load_json(self) -> bool:
        """Load the JSON file"""
        logger.info(f'Loading item data from {self.json_path}...')
        try:
            with open(self.json_path, 'r') as f:
                self.data = json.load(f)
            logger.info('✓ JSON file loaded successfully')
            return True
        except FileNotFoundError:
            self.errors.append(f'File not found: {self.json_path}')
            logger.error(self.errors[-1])
            return False
        except json.JSONDecodeError as e:
            self.errors.append(f'Invalid JSON: {e}')
            logger.error(self.errors[-1])
            return False
        except Exception as e:
            self.errors.append(f'Unexpected error loading JSON: {e}')
            logger.error(self.errors[-1])
            return False
    
    def validate_structure(self) -> bool:
        """Validate the overall structure of the JSON"""
        logger.info('Validating JSON structure...')
        
        # Check for required top-level keys
        if 'items' not in self.data:
            self.errors.append('Missing "items" key in JSON')
            return False
        
        if 'setBonuses' not in self.data:
            self.errors.append('Missing "setBonuses" key in JSON')
            return False
        
        if not isinstance(self.data['items'], dict):
            self.errors.append('"items" should be a dictionary')
            return False
        
        if not isinstance(self.data['setBonuses'], dict):
            self.errors.append('"setBonuses" should be a dictionary')
            return False
        
        logger.info('✓ JSON structure is valid')
        return True
    
    def validate_items(self) -> bool:
        """Validate individual items"""
        logger.info('Validating items...')
        
        items = self.data['items']
        self.stats['total_items'] = len(items)
        
        if len(items) == 0:
            self.errors.append('No items found in the data')
            return False
        
        required_fields = ['objectID', 'name', 'description', 'initialAmount', 'objectType', 'rarity', 'isStackable', 'iconIndex']
        items_with_missing_fields = []
        items_by_rarity = {}
        items_by_type = {}
        
        for item_id, item in items.items():
            # Check required fields
            for field in required_fields:
                if field not in item:
                    items_with_missing_fields.append((item_id, field))
            
            # Check data types
            if not isinstance(item.get('objectID'), int):
                self.warnings.append(f'Item {item_id}: objectID is not an integer')
            
            if not isinstance(item.get('name'), str):
                self.warnings.append(f'Item {item_id}: name is not a string')
            
            if not isinstance(item.get('iconIndex'), int):
                self.warnings.append(f'Item {item_id}: iconIndex is not an integer')
            
            # Collect statistics
            rarity = item.get('rarity', 'unknown')
            if rarity not in items_by_rarity:
                items_by_rarity[rarity] = 0
            items_by_rarity[rarity] += 1
            
            obj_type = item.get('objectType', 'unknown')
            if obj_type not in items_by_type:
                items_by_type[obj_type] = 0
            items_by_type[obj_type] += 1
        
        self.stats['items_by_rarity'] = items_by_rarity
        self.stats['items_by_type'] = items_by_type
        
        if items_with_missing_fields:
            self.errors.append(f'{len(items_with_missing_fields)} items have missing required fields')
            for item_id, field in items_with_missing_fields[:5]:
                logger.error(f'  Item {item_id} missing field: {field}')
            if len(items_with_missing_fields) > 5:
                logger.error(f'  ... and {len(items_with_missing_fields) - 5} more')
            return False
        
        logger.info(f'✓ All {len(items)} items are valid')
        logger.info(f'  Distribution by rarity: {items_by_rarity}')
        logger.info(f'  Distribution by type: {items_by_type}')
        return True
    
    def validate_set_bonuses(self) -> bool:
        """Validate set bonus data"""
        logger.info('Validating set bonuses...')
        
        set_bonuses = self.data['setBonuses']
        self.stats['total_set_bonuses'] = len(set_bonuses)
        
        required_bonus_fields = ['id', 'rarity', 'data', 'pieces']
        bonuses_with_issues = []
        
        for bonus_id, bonus in set_bonuses.items():
            for field in required_bonus_fields:
                if field not in bonus:
                    bonuses_with_issues.append((bonus_id, f'missing {field}'))
        
        if bonuses_with_issues:
            self.errors.append(f'{len(bonuses_with_issues)} set bonuses have issues')
            for bonus_id, issue in bonuses_with_issues[:5]:
                logger.error(f'  Set Bonus {bonus_id}: {issue}')
            return False
        
        logger.info(f'✓ All {len(set_bonuses)} set bonuses are valid')
        return True
    
    def validate_icon_indices(self) -> bool:
        """Validate that icon indices are sequential and unique"""
        logger.info('Validating icon indices...')
        
        items = self.data['items']
        icon_indices = set()
        max_index = -1
        duplicate_indices = []
        
        for item_id, item in items.items():
            index = item.get('iconIndex')
            if index is not None:
                if index in icon_indices:
                    duplicate_indices.append(index)
                icon_indices.add(index)
                max_index = max(max_index, index)
        
        if duplicate_indices:
            self.errors.append(f'Found {len(duplicate_indices)} duplicate icon indices: {duplicate_indices[:5]}')
            return False
        
        # Check if indices are sequential (0, 1, 2, ...)
        expected_indices = set(range(max_index + 1))
        missing_indices = expected_indices - icon_indices
        
        if missing_indices:
            self.warnings.append(f'Found {len(missing_indices)} gaps in icon indices: {sorted(missing_indices)[:10]}')
        
        logger.info(f'✓ Icon indices are valid (0 to {max_index})')
        self.stats['max_icon_index'] = max_index
        return True
    
    def validate_special_properties(self) -> bool:
        """Validate optional properties like damage, cooldown, etc."""
        logger.info('Validating special properties...')
        
        items = self.data['items']
        items_with_damage = 0
        items_with_cooldown = 0
        items_with_conditions = 0
        items_with_set_bonus = 0
        items_with_ingredients = 0
        
        for item_id, item in items.items():
            if 'damage' in item:
                items_with_damage += 1
            if 'cooldown' in item:
                items_with_cooldown += 1
            if 'whenEquipped' in item:
                items_with_conditions += 1
            if 'setBonusId' in item:
                items_with_set_bonus += 1
            if 'ingredient' in item:
                items_with_ingredients += 1
        
        self.stats['items_with_damage'] = items_with_damage
        self.stats['items_with_cooldown'] = items_with_cooldown
        self.stats['items_with_conditions'] = items_with_conditions
        self.stats['items_with_set_bonus'] = items_with_set_bonus
        self.stats['items_with_ingredients'] = items_with_ingredients
        
        logger.info(f'✓ Special properties found:')
        logger.info(f'  Items with damage: {items_with_damage}')
        logger.info(f'  Items with cooldown: {items_with_cooldown}')
        logger.info(f'  Items with conditions: {items_with_conditions}')
        logger.info(f'  Items with set bonus: {items_with_set_bonus}')
        logger.info(f'  Items with ingredients: {items_with_ingredients}')
        
        return True
    
    def validate_spritesheet(self, spritesheet_path: str) -> bool:
        """Validate that spritesheet file exists and is valid"""
        logger.info(f'Validating spritesheet at {spritesheet_path}...')
        
        try:
            from PIL import Image
            image = Image.open(spritesheet_path)
            
            expected_width = (self.stats.get('max_icon_index', 0) + 1) * 16
            expected_height = 16
            
            if image.width != expected_width:
                self.warnings.append(f'Spritesheet width {image.width} != expected {expected_width}')
            
            if image.height != expected_height:
                self.warnings.append(f'Spritesheet height {image.height} != expected {expected_height}')
            
            logger.info(f'✓ Spritesheet is valid ({image.width}x{image.height})')
            self.stats['spritesheet_size'] = (image.width, image.height)
            return True
        
        except FileNotFoundError:
            self.warnings.append(f'Spritesheet file not found: {spritesheet_path}')
            return True  # Not a critical error
        except Exception as e:
            self.warnings.append(f'Error validating spritesheet: {e}')
            return True  # Not a critical error
    
    def run_all_tests(self, spritesheet_path: str = None) -> bool:
        """Run all validation tests"""
        logger.info('=' * 80)
        logger.info('STARTING ITEM DATA VALIDATION')
        logger.info('=' * 80)
        
        tests = [
            ('JSON Loading', self.load_json()),
            ('JSON Structure', self.validate_structure()),
            ('Items Validation', self.validate_items()),
            ('Set Bonuses Validation', self.validate_set_bonuses()),
            ('Icon Indices Validation', self.validate_icon_indices()),
            ('Special Properties', self.validate_special_properties()),
        ]
        
        self.test_results = tests
        
        if spritesheet_path:
            tests.append(('Spritesheet Validation', self.validate_spritesheet(spritesheet_path)))
        
        return all(result for _, result in tests)
    
    def generate_report(self) -> str:
        """Generate a detailed validation report"""
        report = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    ITEM DATA VALIDATION REPORT                               ║
╚══════════════════════════════════════════════════════════════════════════════╝

📋 TEST RESULTS
─────────────────────────────────────────────────────────────────────────────────
"""
        
        for test_name, result in self.test_results:
            status = '✓ PASS' if result else '✗ FAIL'
            report += f"{test_name:<40} {status}\n"
        
        report += f"""
📊 STATISTICS
─────────────────────────────────────────────────────────────────────────────────
Total Items:                       {self.stats.get('total_items', 'N/A')}
Total Set Bonuses:                 {self.stats.get('total_set_bonuses', 'N/A')}
Max Icon Index:                    {self.stats.get('max_icon_index', 'N/A')}
Spritesheet Size:                  {self.stats.get('spritesheet_size', 'N/A')}

Items by Rarity:
"""
        for rarity, count in sorted(self.stats.get('items_by_rarity', {}).items()):
            report += f"  Rarity {rarity}: {count} items\n"
        
        report += f"""
Items by Type:
"""
        for obj_type, count in sorted(self.stats.get('items_by_type', {}).items()):
            report += f"  Type {obj_type}: {count} items\n"
        
        report += f"""
Special Properties:
  Items with damage:               {self.stats.get('items_with_damage', 0)}
  Items with cooldown:             {self.stats.get('items_with_cooldown', 0)}
  Items with conditions:           {self.stats.get('items_with_conditions', 0)}
  Items with set bonus:            {self.stats.get('items_with_set_bonus', 0)}
  Items with ingredients:          {self.stats.get('items_with_ingredients', 0)}

⚠️  WARNINGS ({len(self.warnings)} total)
─────────────────────────────────────────────────────────────────────────────────
"""
        
        if self.warnings:
            for warning in self.warnings[:10]:
                report += f"  ⚠ {warning}\n"
            if len(self.warnings) > 10:
                report += f"  ... and {len(self.warnings) - 10} more warnings\n"
        else:
            report += "  No warnings\n"
        
        report += f"""
❌ ERRORS ({len(self.errors)} total)
─────────────────────────────────────────────────────────────────────────────────
"""
        
        if self.errors:
            for error in self.errors:
                report += f"  ✗ {error}\n"
        else:
            report += "  No errors\n"
        
        overall_status = '✓ PASSED' if not self.errors else '✗ FAILED'
        report += f"""
═════════════════════════════════════════════════════════════════════════════════
OVERALL STATUS: {overall_status}
Report generated at: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
═════════════════════════════════════════════════════════════════════════════════
"""
        return report


def main():
    """Main test function"""
    # Check if output files exist
    json_path = 'out/item/item-data.json'
    spritesheet_path = 'out/item/item-spritesheet.png'
    
    if not Path(json_path).exists():
        logger.error(f'Output file not found: {json_path}')
        logger.info('Please run: python3 scripts/items.py')
        return 1
    
    # Run validation
    validator = ItemDataValidator(json_path)
    success = validator.run_all_tests(spritesheet_path)
    
    # Print and save report
    report = validator.generate_report()
    print(report)
    
    try:
        Path('out/item').mkdir(parents=True, exist_ok=True)
        with open('out/item/validation_report.txt', 'w') as f:
            f.write(report)
        logger.info('Validation report saved to out/item/validation_report.txt')
    except Exception as e:
        logger.error(f'Error saving validation report: {e}')
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
