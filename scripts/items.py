#!/usr/bin/env python3

import json
import logging
import math
import os
import textwrap
from glob import glob, iglob
from datetime import datetime

import yaml
from PIL import Image
from unityparser import UnityDocument

import blacklist
import util
from util import get_translations


# Configure logging with timestamps
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ItemExtractionReport:
    """Track and generate reports for item extraction process"""
    
    def __init__(self):
        self.total_objects = 0
        self.total_items_processed = 0
        self.skipped_objects = {
            'no_translation': [],
            'no_image': [],
            'duplicate': {},
            'blacklisted': [],
            'wrong_type': [],
            'invalid_icon': []
        }
        self.warnings = []
        self.errors = []
        self.start_time = datetime.now()
    
    def add_warning(self, message):
        self.warnings.append(message)
        logger.warning(message)
    
    def add_error(self, message):
        self.errors.append(message)
        logger.error(message)
    
    def report_skipped_no_translation(self, object_name, object_id):
        self.skipped_objects['no_translation'].append((object_name, object_id))
    
    def report_skipped_no_image(self, object_id):
        self.skipped_objects['no_image'].append(object_id)
    
    def report_skipped_duplicate(self, object_id):
        if object_id not in self.skipped_objects['duplicate']:
            self.skipped_objects['duplicate'][object_id] = 0
        self.skipped_objects['duplicate'][object_id] += 1
    
    def report_blacklisted(self, object_id):
        self.skipped_objects['blacklisted'].append(object_id)
    
    def report_wrong_type(self, object_id, object_type):
        self.skipped_objects['wrong_type'].append((object_id, object_type))
    
    def report_invalid_icon(self, object_id):
        self.skipped_objects['invalid_icon'].append(object_id)
    
    def generate_report(self):
        """Generate a detailed report of the extraction process"""
        duration = (datetime.now() - self.start_time).total_seconds()
        
        report = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    ITEM EXTRACTION REPORT                                    ║
╚══════════════════════════════════════════════════════════════════════════════╝

📊 EXTRACTION STATISTICS
─────────────────────────────────────────────────────────────────────────────────
Total Objects Found:               {self.total_objects}
Total Items Successfully Processed: {self.total_items_processed}
Processing Time:                   {duration:.2f}s

📋 SKIPPED ITEMS BREAKDOWN
─────────────────────────────────────────────────────────────────────────────────
No Translation:                    {len(self.skipped_objects['no_translation'])} items
  {', '.join([f"{name}({id})" for name, id in self.skipped_objects['no_translation'][:5]])}
  {f"... and {len(self.skipped_objects['no_translation']) - 5} more" if len(self.skipped_objects['no_translation']) > 5 else ""}

No Image Found:                    {len(self.skipped_objects['no_image'])} items
  {', '.join(map(str, self.skipped_objects['no_image'][:10]))}
  {f"... and {len(self.skipped_objects['no_image']) - 10} more" if len(self.skipped_objects['no_image']) > 10 else ""}

Duplicates Skipped:                {len(self.skipped_objects['duplicate'])} items
  {sum(self.skipped_objects['duplicate'].values())} duplicate entries ignored

Blacklisted Items:                 {len(self.skipped_objects['blacklisted'])} items

Wrong Object Type:                 {len(self.skipped_objects['wrong_type'])} items

Invalid Icon:                      {len(self.skipped_objects['invalid_icon'])} items

⚠️  WARNINGS ({len(self.warnings)} total)
─────────────────────────────────────────────────────────────────────────────────
{chr(10).join(self.warnings[:10])}
{f"... and {len(self.warnings) - 10} more warnings" if len(self.warnings) > 10 else ""}

❌ ERRORS ({len(self.errors)} total)
─────────────────────────────────────────────────────────────────────────────────
{chr(10).join(self.errors[:10]) if self.errors else "No errors encountered"}
{f"... and {len(self.errors) - 10} more errors" if len(self.errors) > 10 else ""}

✅ SUCCESS
─────────────────────────────────────────────────────────────────────────────────
Generated spritesheet and item-data.json successfully!

═════════════════════════════════════════════════════════════════════════════════
Report generated at: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
═════════════════════════════════════════════════════════════════════════════════
"""
        return report


def get_objectinfo_monobehaviour() -> [dict]:
    """Extract object information from PugDatabase"""
    objectinfo_monobehaviour = util.load_cache('objectinfo_monobehaviour')
    if objectinfo_monobehaviour is not None:
        logger.info('Loaded objectinfo_monobehaviour from cache')
        return objectinfo_monobehaviour

    logger.info('Extracting objectinfo_monobehaviour from PugDatabase...')
    
    try:
        pug_database_doc = UnityDocument.load_yaml(
            'dump/CoreKeeper/ExportedProject/Assets/PrefabInstance/PugDatabase.prefab'
        )
    except Exception as e:
        logger.error(f'Failed to load PugDatabase: {e}')
        return []
    
    pug_database_mono_behaviour = pug_database_doc.filter(class_names=('MonoBehaviour',))[0]
    object_id_guids: [str] = []
    
    for prefab in pug_database_mono_behaviour.prefabList:
        object_id_guids.append(prefab['guid'])

    left_object_id_guids = object_id_guids.copy()
    prefab_paths: [str] = []

    for prefab_meta_path in glob("dump/CoreKeeper/ExportedProject/Assets/PrefabInstance/*.meta"):
        with open(prefab_meta_path) as file:
            content = file.read()
            for i, guid in enumerate(left_object_id_guids):
                if guid in content:
                    prefab_paths.append(prefab_meta_path[:-5])
                    del left_object_id_guids[i]
                    break

    if len(left_object_id_guids) > 0:
        logger.warning(
            f'Found {len(left_object_id_guids)} objects with missing/corrupted files'
        )

    objectinfo_monobehaviour = []
    
    for prefab_path in prefab_paths:
        try:
            prefab_doc = UnityDocument.load_yaml(prefab_path)
            prefab_monobehaviour_list = prefab_doc.filter(class_names=('MonoBehaviour',), attributes=('objectInfo',))
            
            if len(prefab_monobehaviour_list) > 1:
                logger.warning(
                    f'Prefab has {len(prefab_monobehaviour_list)} Monobehaviour with objectInfo: "{prefab_path}"'
                )
            
            if len(prefab_monobehaviour_list) == 0:
                continue
                
            prefab_monobehaviour = prefab_monobehaviour_list[0]
            prefab_objectinfo = prefab_monobehaviour.objectInfo

            object_id = prefab_objectinfo['objectID']
            object_type = prefab_objectinfo['objectType']
            file_id = prefab_objectinfo['icon']['fileID']
            
            if object_type in (900, 6000) or file_id == 0 or object_id in blacklist.ITEM_BLACKLIST:
                continue

            # Extract conditions
            monobehaviour_gives_conditions_when_equipped = prefab_doc.filter(
                class_names=('MonoBehaviour',), attributes=('givesConditionsWhenEquipped',)
            )

            if len(monobehaviour_gives_conditions_when_equipped) > 1:
                logger.debug(f'Multiple Conditions MonoBehaviour found in {prefab_path}')
            
            if len(monobehaviour_gives_conditions_when_equipped) > 0:
                gives_conditions_when_equipped = []
                for mono_behaviour_with_conditions in monobehaviour_gives_conditions_when_equipped:
                    for condition in mono_behaviour_with_conditions.givesConditionsWhenEquipped:
                        gives_conditions_when_equipped.append(condition)
                prefab_objectinfo['givesConditionsWhenEquipped'] = gives_conditions_when_equipped

            # Extract damage
            monobehaviour_damage = prefab_doc.filter(class_names=('MonoBehaviour',), attributes=('damage', 'isRange'))

            if len(monobehaviour_damage) > 1:
                logger.debug(f'Multiple Damage MonoBehaviour found in {prefab_path}')
            
            if len(monobehaviour_damage) > 0:
                prefab_objectinfo['damage'] = monobehaviour_damage[0].damage
                prefab_objectinfo['isRange'] = monobehaviour_damage[0].isRange

            # Extract cooldown
            monobehaviour_cooldown = prefab_doc.filter(class_names=('MonoBehaviour',), attributes=('cooldown',))
            if len(monobehaviour_cooldown) > 1:
                logger.debug(f'Multiple Cooldown MonoBehaviour found in {prefab_path}')
            if len(monobehaviour_cooldown) > 0:
                prefab_objectinfo['cooldown'] = monobehaviour_cooldown[0].cooldown

            # Extract ingredient data
            monobehaviour_turns_into_food = prefab_doc.filter(class_names=('MonoBehaviour',), attributes=('turnsIntoFood',))
            if len(monobehaviour_turns_into_food) > 1:
                logger.debug(f'Multiple TurnsIntoFood MonoBehaviour found in {prefab_path}')

            if len(monobehaviour_turns_into_food) > 0:
                monobehaviour_values = prefab_doc.filter(class_names=('MonoBehaviour',), attributes=('Values',))
                if len(monobehaviour_values) > 1:
                    logger.debug(f'Multiple Values MonoBehaviour found in {prefab_path}')

                prefab_objectinfo['ingredient'] = {
                    'brightColor': monobehaviour_turns_into_food[0].brightColor,
                    'brightestColor': monobehaviour_turns_into_food[0].brightestColor,
                    'darkColor': monobehaviour_turns_into_food[0].darkColor,
                    'darkestColor': monobehaviour_turns_into_food[0].darkestColor,
                    'turnsIntoFood': monobehaviour_turns_into_food[0].turnsIntoFood,
                    'values': monobehaviour_values[0].Values
                }

            objectinfo_monobehaviour.append(prefab_objectinfo)
        
        except Exception as e:
            logger.error(f'Error processing prefab {prefab_path}: {e}')
            continue

    util.set_cache('objectinfo_monobehaviour', objectinfo_monobehaviour)
    logger.info(f'Extracted {len(objectinfo_monobehaviour)} objects from prefabs')
    return objectinfo_monobehaviour


def get_textures() -> dict:
    """Load texture metadata"""
    textures = util.load_cache('textures')
    if textures is not None:
        logger.info('Loaded textures from cache')
        return textures
    
    logger.info('Loading texture metadata...')
    textures = {}
    
    try:
        for filepath in iglob(os.path.join('dump/CoreKeeper/ExportedProject/Assets/Texture2D/*.png.meta')):
            with open(filepath, 'r') as stream:
                metadata = yaml.safe_load(stream)
                if metadata and 'guid' in metadata:
                    textures[metadata['guid']] = {
                        'metadata': metadata,
                        'filepath': filepath[:len(filepath) - 5]
                    }
    except Exception as e:
        logger.error(f'Error loading textures: {e}')
        return {}

    util.set_cache('textures', textures)
    logger.info(f'Loaded {len(textures)} textures')
    return textures


def get_item_translations():
    """Extract item translations from game data"""
    logger.info('Extracting item translations...')
    
    try:
        translations = get_translations()
    except Exception as e:
        logger.error(f'Error getting translations: {e}')
        return {}
    
    item_and_desc_translations = {}
    for translation in translations:
        term = translation['term']
        text = translation['value']
        if term.startswith('Items/'):
            item_and_desc_translations[term[6:]] = text

    item_translations = {}
    for item in item_and_desc_translations:
        text = item_and_desc_translations[item]
        if item.endswith('Desc'):
            key = item[:len(item) - 4]
            is_description = True
        else:
            key = item
            is_description = False

        if item_translations.get(key) is None:
            item_translations[key] = {}

        if is_description:
            item_translations[key]['description'] = text
        else:
            item_translations[key]['text'] = text

    logger.info(f'Extracted {len(item_translations)} item translations')
    return item_translations


def get_object_ids() -> dict:
    """Get object ID enum mapping"""
    logger.info('Loading object IDs...')
    
    try:
        enum = util.get_enum('dump/CoreKeeper/ExportedProject/Assets/MonoScript/Pug.Base/ObjectID.cs')
        # Edge cases for variant items
        enum[5502] = 'GiantMushroom'
        enum[5503] = 'AmberLarva'
        logger.info(f'Loaded {len(enum)} object IDs')
        return enum
    except Exception as e:
        logger.error(f'Error loading object IDs: {e}')
        return {}


def get_set_bonuses():
    """Extract set bonus data"""
    logger.info('Extracting set bonuses...')
    
    try:
        set_bonuses_doc = UnityDocument.load_yaml('dump/CoreKeeper/ExportedProject/Assets/Resources/SetBonusesTable.asset')
        mono_behaviour = set_bonuses_doc.data[0]
        mono_behvaiour_set_bonuses = mono_behaviour.setBonuses
        set_bonuses = {}
        
        for set_bonus in mono_behvaiour_set_bonuses:
            pieces = []
            object_id_hex = textwrap.wrap(str(set_bonus['availablePieces']), 8)
            
            for hex_string in object_id_hex:
                hex_list = textwrap.wrap(hex_string, 2)
                hex_list.reverse()
                object_id = int("0x%s" % ''.join(hex_list), 0)
                pieces.append(object_id)

            set_bonus_datas = set_bonus['setBonusDatas']
            for set_bonus_data in set_bonus_datas:
                set_bonus_data['conditionData'].pop('duration', None)

            set_bonus_id = set_bonus['setBonusID']
            set_bonuses[set_bonus_id] = {
                'id': set_bonus_id,
                'rarity': set_bonus['rarity'],
                'data': set_bonus_datas,
                'pieces': pieces
            }
        
        logger.info(f'Extracted {len(set_bonuses)} set bonuses')
        return set_bonuses
    
    except Exception as e:
        logger.error(f'Error extracting set bonuses: {e}')
        return {}


if __name__ == '__main__':
    logger.info('=' * 80)
    logger.info('Starting Core Keeper item extraction process')
    logger.info('=' * 80)
    
    report = ItemExtractionReport()
    
    # Load all required data
    objectinfo_monobehaviour = get_objectinfo_monobehaviour()
    textures = get_textures()
    item_translations = get_item_translations()
    object_ids = get_object_ids()
    set_bonuses = get_set_bonuses()
    
    report.total_objects = len(objectinfo_monobehaviour)
    logger.info(f'Starting item processing for {report.total_objects} objects')
    
    item_data = {}
    images: [Image] = []
    icon_index = 0

    # Create a dict to map object_id to set_bonus_id
    set_bonus_ids = {}
    for set_bonus_id, set_bonus in set_bonuses.items():
        for piece in set_bonus['pieces']:
            set_bonus_ids[piece] = set_bonus_id

    # Process each object
    for objectinfo in objectinfo_monobehaviour:
        object_id = objectinfo['objectID']
        
        if object_id not in object_ids:
            report.add_warning(f'Object ID {object_id} not found in ObjectID enum')
            continue
        
        object_name = object_ids[object_id]

        # Special handler for Rare and Epic versions of food
        if object_name.startswith('Cooked') and (object_name.endswith('Rare') or object_name.endswith('Epic')):
            translation = item_translations.get(object_name[:-4])
        else:
            translation = item_translations.get(object_name)

        if translation is None:
            report.report_skipped_no_translation(object_name, object_id)
            continue

        # Build item data structure
        single_data = {
            'objectID': object_id,
            'name': translation['text'],
            'description': translation.get('description'),
            'initialAmount': objectinfo['initialAmount'],
            'objectType': objectinfo['objectType'],
            'rarity': objectinfo['rarity'],
            'isStackable': objectinfo['isStackable'],
            'iconIndex': icon_index
        }

        # Add conditions if equipped
        conditions = objectinfo.get('givesConditionsWhenEquipped')
        if conditions is not None and len(conditions) > 0:
            single_data['whenEquipped'] = []
            for condition in conditions:
                single_data['whenEquipped'].append({
                    'id': condition['id'],
                    'value': condition['value']
                })

        # Add damage if present
        damage = objectinfo.get('damage')
        if damage is not None:
            is_range = objectinfo.get('isRange')
            damage_tenth = damage * 0.1
            damage_min = damage - math.floor(damage_tenth)
            damage_max = damage + math.floor(damage_tenth)
            single_data['damage'] = {
                'range': [damage_min, damage_max],
                'isRange': is_range == 1
            }

        # Add cooldown if present
        cooldown = objectinfo.get('cooldown')
        if cooldown is not None:
            single_data['cooldown'] = round(1 / cooldown, 2)

        # Add set bonus if applicable
        set_bonus_id = set_bonus_ids.get(object_id)
        if set_bonus_id is not None:
            single_data['setBonusId'] = set_bonus_id

        # Process icon
        icon = objectinfo['icon']
        icon_offset = objectinfo['iconOffset']
        icon_offset_x = icon_offset['x']
        icon_offset_y = icon_offset['y']

        # Get texture and extract icon
        if icon['guid'] not in textures:
            report.report_skipped_no_image(object_id)
            continue
        
        texture = textures[icon['guid']]
        
        # Find correct sprite in spritesheet
        found_image = False
        cropped_image = None
        
        try:
            for sprite in texture['metadata']['TextureImporter']['spriteSheet']['sprites']:
                if sprite['internalID'] == icon['fileID']:
                    found_image = True
                    rect = sprite['rect']
                    x = rect['x']
                    y = rect['y']
                    width = rect['width']
                    height = rect['height']
                    sprite_pixels_to_units = texture['metadata']['TextureImporter']['spritePixelsToUnits']
                    offset_x = icon_offset_x * sprite_pixels_to_units
                    offset_y = icon_offset_y * sprite_pixels_to_units

                    image = Image.open(texture['filepath'])
                    diff = (width - 16) / 2
                    cropped_x = x + diff
                    cropped_y = image.height - y - width + diff + offset_y
                    cropped_x2 = x + width - diff + offset_x
                    cropped_y2 = image.height - y - diff

                    area = (cropped_x, cropped_y, cropped_x2, cropped_y2)
                    cropped_image = image.crop(area)
                    break
        except Exception as e:
            logger.debug(f'Error extracting sprite for object {object_id}: {e}')

        # Fallback: use whole image if sprite not found
        if not found_image and cropped_image is None:
            try:
                if object_id not in blacklist.TEXTURE_WHOLE_IMAGE_BLACKLIST:
                    logger.debug(f"Using whole image for object {object_id}")
                found_image = True
                image = Image.open(texture['filepath'])
                cropped_image = image.crop((1, 0, 17, 16))
            except Exception as e:
                logger.debug(f'Error loading whole image for object {object_id}: {e}')
                report.report_skipped_no_image(object_id)
                continue

        # Skip if no image found
        if not found_image or cropped_image is None:
            report.report_skipped_no_image(object_id)
            continue

        # Check for duplicates
        if item_data.get(object_id) is not None:
            report.report_skipped_duplicate(object_id)
            continue

        # Add to final data
        item_data[object_id] = single_data
        images.append(cropped_image)
        icon_index += 1
        report.total_items_processed += 1

    # Create output directory
    os.makedirs('out/item', exist_ok=True)
    
    # Create and save spritesheet
    logger.info(f'Creating spritesheet with {len(images)} items...')
    try:
        image = Image.new('RGBA', (icon_index * 16, 16))
        for index, single_image in enumerate(images):
            image.paste(single_image, (index * 16, 0))
        image.save('out/item/item-spritesheet.png')
        logger.info('Spritesheet saved successfully')
    except Exception as e:
        report.add_error(f'Error creating spritesheet: {e}')

    # Sort by key (objectID)
    sorted_item_data = dict(sorted(item_data.items(), key=lambda x: x[0]))

    # Create final JSON
    logger.info('Writing item-data.json...')
    try:
        with open('out/item/item-data.json', 'w') as file:
            result_json = json.dumps({
                'items': sorted_item_data,
                'setBonuses': set_bonuses,
            }, indent=2)
            file.write(result_json)
        logger.info('item-data.json saved successfully')
    except Exception as e:
        report.add_error(f'Error writing item-data.json: {e}')

    # Print detailed report
    print(report.generate_report())
    
    # Save report to file
    try:
        with open('out/item/extraction_report.txt', 'w') as f:
            f.write(report.generate_report())
        logger.info('Report saved to extraction_report.txt')
    except Exception as e:
        logger.error(f'Error saving report: {e}')

    logger.info('=' * 80)
    logger.info('Item extraction process completed!')
    logger.info('=' * 80)
