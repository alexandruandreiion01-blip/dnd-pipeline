import pandas as pd

def extract_damage_info(spell):
    """
    Damage is the trickiest field because not every spell does damage.
    Healing Word heals, Invisibility does nothing offensive, etc.
    We need to handle all cases gracefully instead of crashing.
    
    This is called a 'helper function' - a small focused function
    that does one job, called by the bigger transform function below.
    """
    damage = spell.get("damage")  # .get() returns None instead of crashing if key missing
    
    if not damage:
        return None, None  # spell has no damage at all
    
    damage_type = damage.get("damage_type", {}).get("name")
    
    # Some spells scale with character level, others with spell slot level
    # We want the base damage (lowest level available)
    damage_at_slot = damage.get("damage_at_slot_level", {})
    damage_at_char = damage.get("damage_at_character_level", {})
    
    if damage_at_slot:
        # get the first (lowest) entry, e.g. "4d4" from {"2": "4d4", "3": "5d4"}
        base_damage = list(damage_at_slot.values())[0]
    elif damage_at_char:
        base_damage = list(damage_at_char.values())[0]
    else:
        base_damage = None
    
    return damage_type, base_damage

def extract_classes(spell):
    """
    Classes is a list of objects like:
    [{"name": "Wizard"}, {"name": "Sorcerer"}]
    
    We flatten it to a simple comma-separated string: "Wizard, Sorcerer"
    Databases prefer simple flat values over nested lists.
    """
    classes = spell.get("classes", [])
    return ", ".join([c["name"] for c in classes])

def transform_spells(raw_spells):
    """
    Main transform function. Loops through all 319 raw spells,
    pulls out the fields we care about, and builds a clean flat table.
    
    Notice we're not crashing on missing data — we're handling it.
    That's the difference between a pipeline that runs once and one
    that runs reliably for months.
    """
    rows = []
    
    for spell in raw_spells:
        damage_type, base_damage = extract_damage_info(spell)
        
        row = {
            "name":         spell["name"],
            "level":        spell["level"],
            "school":       spell["school"]["name"],
            "damage_type":  damage_type,   # None if spell doesn't deal damage
            "base_damage":  base_damage,   # None if spell doesn't deal damage
            "classes":      extract_classes(spell),
            "ritual":       spell.get("ritual", False),
            "concentration":spell.get("concentration", False),
            "casting_time": spell.get("casting_time"),
            "range":        spell.get("range"),
            "description":  " ".join(spell.get("desc", [])),
            "loaded_at":    pd.Timestamp.now()
        }
        rows.append(row)
    
    df = pd.DataFrame(rows)
    
    # Quick summary so we know what we're working with
    total = len(df)
    with_damage = df["damage_type"].notna().sum()
    without_damage = df["damage_type"].isna().sum()
    
    print(f"✓ Transformed {total} spells")
    print(f"  {with_damage} spells deal damage")
    print(f"  {without_damage} spells have no damage (utility, healing, etc)")
    print(f"\nDamage types found:\n{df['damage_type'].value_counts()}")
    print(f"\nSchools of magic:\n{df['school'].value_counts()}")
    
    return df

if __name__ == "__main__":
    # We import extract here only for testing this file directly
    from extract import extract_all_spells
    raw = extract_all_spells()
    df = transform_spells(raw)
    print("\nSample rows:")
    print(df[df["damage_type"].notna()].head(5).to_string(index=False))