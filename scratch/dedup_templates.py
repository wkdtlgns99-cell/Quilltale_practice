import json
import os
import glob
from pathlib import Path

def deduplicate_json_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return False, 0

    if not isinstance(data, list):
        print(f"Skipping {filepath} (Not a list)")
        return False, 0

    original_count = len(data)
    
    unique_items = []
    seen_ids = set()
    seen_hashes = set()

    for item in data:
        if isinstance(item, dict):
            # Check by ID if exists
            item_id = item.get("id")
            if item_id:
                if item_id in seen_ids:
                    continue
                seen_ids.add(item_id)
            
            # Fallback to checking full stringified dict to catch exact duplicates without ID
            item_str = json.dumps(item, sort_keys=True)
            if item_str in seen_hashes:
                continue
            seen_hashes.add(item_str)
            
            unique_items.append(item)
        else:
            # For non-dict items in list
            item_str = str(item)
            if item_str not in seen_hashes:
                seen_hashes.add(item_str)
                unique_items.append(item)

    new_count = len(unique_items)
    removed_count = original_count - new_count

    if removed_count > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(unique_items, f, ensure_ascii=False, indent=2)
        print(f"Updated {filepath}: removed {removed_count} duplicates. (Total left: {new_count})")
        return True, removed_count
    else:
        print(f"No duplicates found in {filepath}. (Total: {original_count})")
        return False, 0

def main():
    template_dir = r"C:\Quilltale\data\templates"
    json_files = glob.glob(os.path.join(template_dir, "*.json"))
    
    total_removed = 0
    for f in json_files:
        _, removed = deduplicate_json_file(f)
        total_removed += removed
        
    print(f"\nScan complete. Total duplicates removed across all files: {total_removed}")

if __name__ == '__main__':
    main()
