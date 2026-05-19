
import pandas as pd

def extract_armor_class(monster):
    ac_list = monster.get("armor_class", [])
    if ac_list:
        return ac_list[0].get("value")
    return None

def extract_speed(monster):
    speed = monster.get("speed", {})
    return speed.get("walk", "0 ft.").replace(" ft.", "").strip()

def extract_list_field(monster, field):
    """
    damage_immunities, damage_resistances, damage_vulnerabilities
    are lists of strings like ["Fire", "Cold"]
    We join them to a comma separated string.
    """
    items = monster.get(field, [])
    if not items:
        return None
    # sometimes they're strings, sometimes dicts
    result = []
    for item in items:
        if isinstance(item, str):
            result.append(item)
        elif isinstance(item, dict):
            result.append(item.get("name", ""))
    return ", ".join(result) if result else None

def extract_actions_damage(monster):
    """
    Pull all damage types this monster deals through its actions.
    Useful for knowing what kind of threat it is offensively.
    """
    damage_types = set()
    for action in monster.get("actions", []):
        for dmg in action.get("damage", []):
            dt = dmg.get("damage_type", {}).get("name")
            if dt:
                damage_types.add(dt)
    return ", ".join(sorted(damage_types)) if damage_types else None

def is_legendary(monster):
    return len(monster.get("legendary_actions", [])) > 0

def transform_monsters(raw_monsters):
    rows = []

    for monster in raw_monsters:
        row = {
            "name":                 monster["name"],
            "size":                 monster.get("size"),
            "type":                 monster.get("type"),
            "alignment":            monster.get("alignment"),
            "challenge_rating":     monster.get("challenge_rating"),
            "xp":                   monster.get("xp"),
            "armor_class":          extract_armor_class(monster),
            "hit_points":           monster.get("hit_points"),
            "speed_walk":           extract_speed(monster),
            "strength":             monster.get("strength"),
            "dexterity":            monster.get("dexterity"),
            "constitution":         monster.get("constitution"),
            "intelligence":         monster.get("intelligence"),
            "wisdom":               monster.get("wisdom"),
            "charisma":             monster.get("charisma"),
            "damage_immunities":    extract_list_field(monster, "damage_immunities"),
            "damage_resistances":   extract_list_field(monster, "damage_resistances"),
            "damage_vulnerabilities": extract_list_field(monster, "damage_vulnerabilities"),
            "damage_dealt":         extract_actions_damage(monster),
            "legendary":            is_legendary(monster),
            "languages":            monster.get("languages"),
            "image_url": f"https://www.dnd5eapi.co{monster.get('image', '')}",
            "description": monster.get("desc", None),
            "loaded_at":            pd.Timestamp.now()
        }
        rows.append(row)

    df = pd.DataFrame(rows)

    print(f"✓ Transformed {len(df)} monsters")
    print(f"  Legendary monsters: {df['legendary'].sum()}")
    print(f"\nMonster types:")
    print(df["type"].value_counts().head(8))
    print(f"\nChallenge rating distribution:")
    print(df["challenge_rating"].value_counts().sort_index().head(10))

    return df

if __name__ == "__main__":
    print("main block triggered")
    from extract_monsters import extract_all_monsters
    raw = extract_all_monsters(use_cache=True)
    df = transform_monsters(raw)
    print("\nSample row:")
    print(df[df["name"] == "Aboleth"].to_string())