#!/usr/bin/env python3
"""
Upgrade tables_config.json from old schema to new schema.
Maintains all existing data while adding new fields (keywords, exclude_keywords).
Each project keeps its own table data - only format/structure is upgraded.
"""

import json
import sys
from pathlib import Path

def upgrade_config(config_data):
    """
    Convert old schema to new schema while preserving all data.
    
    Changes:
    - Add 'keywords' and 'exclude_keywords' arrays to metadata if missing
    - Ensure business_rules structure is correct
    - Preserve all fields and usage_examples
    """
    
    upgraded = {}
    
    for table_id, table_config in config_data.items():
        new_table = {
            "metadata": {}
        }
        
        # Handle metadata
        if "metadata" in table_config:
            new_table["metadata"] = table_config["metadata"].copy()
        else:
            # If no metadata object, extract from top level
            new_table["metadata"]["table_id"] = table_config.get("table_id", table_id)
            new_table["metadata"]["bigquery_table"] = table_config.get("bigquery_table", "")
            new_table["metadata"]["description"] = table_config.get("description", "")
            new_table["metadata"]["domain"] = table_config.get("domain", "")
            new_table["metadata"]["last_updated"] = table_config.get("last_updated", "")
        
        # Add keywords if missing
        if "keywords" not in new_table["metadata"]:
            new_table["metadata"]["keywords"] = []
        
        # Add exclude_keywords if missing
        if "exclude_keywords" not in new_table["metadata"]:
            new_table["metadata"]["exclude_keywords"] = []
        
        # Copy business_rules
        if "business_rules" in table_config:
            new_table["business_rules"] = table_config["business_rules"].copy()
        else:
            new_table["business_rules"] = {
                "critical_rules": [],
                "query_rules": []
            }
        
        # Copy fields
        if "fields" in table_config:
            new_table["fields"] = table_config["fields"].copy()
        
        # Copy usage_examples
        if "usage_examples" in table_config:
            new_table["usage_examples"] = table_config["usage_examples"].copy()
        
        upgraded[table_id] = new_table
    
    return upgraded

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 upgrade_config_schema.py <config_file_path> [--dry-run]")
        print("\nExample:")
        print("  python3 upgrade_config_schema.py /home/Junio/fa_sqllm/config/tables_config.json")
        print("  python3 upgrade_config_schema.py /home/Junio/fa_sqllm/config/tables_config.json --dry-run")
        sys.exit(1)
    
    config_path = Path(sys.argv[1])
    dry_run = "--dry-run" in sys.argv
    
    if not config_path.exists():
        print(f"❌ Error: File not found: {config_path}")
        sys.exit(1)
    
    print(f"📖 Reading config from: {config_path}")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in {config_path}: {e}")
        sys.exit(1)
    
    print(f"📊 Found {len(config_data)} table(s)")
    
    upgraded = upgrade_config(config_data)
    
    if dry_run:
        print("\n🔍 DRY RUN MODE - showing changes (not writing)")
        print("\nUpgraded structure (first 500 chars):")
        print(json.dumps(upgraded, indent=2, ensure_ascii=False)[:500])
    else:
        # Backup original
        backup_path = config_path.with_suffix('.json.bak')
        print(f"\n💾 Backing up original to: {backup_path}")
        import shutil
        shutil.copy(config_path, backup_path)
        
        # Write upgraded config
        print(f"✍️  Writing upgraded config to: {config_path}")
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(upgraded, f, indent=2, ensure_ascii=False)
        
        print("✅ Config upgraded successfully!")
        print("\nChecking result:")
        with open(config_path, 'r', encoding='utf-8') as f:
            result = json.load(f)
        
        for table_id, table_config in result.items():
            meta = table_config.get("metadata", {})
            keywords_count = len(meta.get("keywords", []))
            exclude_keywords_count = len(meta.get("exclude_keywords", []))
            print(f"  ✓ {table_id}: {keywords_count} keywords, {exclude_keywords_count} exclude_keywords")

if __name__ == "__main__":
    main()
