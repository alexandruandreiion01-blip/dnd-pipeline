import requests
import time
import json
import os

def get_all_monster_names():
    url = "https://www.dnd5eapi.co/api/monsters"
    response = requests.get(url)
    data = response.json()
    monster_list = [m["index"] for m in data["results"]]
    print(f"✓ Found {len(monster_list)} monsters")
    return monster_list

def get_monster_details(monster_index):
    url = f"https://www.dnd5eapi.co/api/monsters/{monster_index}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"✗ Failed to fetch {monster_index}")
        return None

def save_raw_monsters(monsters, path=None):
    if path is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "raw_monsters.json")
    with open(path, "w") as f:
        json.dump(monsters, f)
    print(f"✓ Saved {len(monsters)} monsters to {path}")

def load_raw_monsters(path=None):
    if path is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "raw_monsters.json")
    with open(path, "r") as f:
        monsters = json.load(f)
    print(f"✓ Loaded {len(monsters)} monsters from {path}")
    return monsters

def extract_all_monsters(use_cache=True):
    cache_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "raw_monsters.json")

    if use_cache and os.path.exists(cache_path):
        print("✓ Cache found, loading monsters from disk")
        return load_raw_monsters(cache_path)

    monster_names = get_all_monster_names()
    all_monsters = []

    for i, monster_index in enumerate(monster_names):
        monster = get_monster_details(monster_index)
        if monster:
            all_monsters.append(monster)
        if (i + 1) % 50 == 0:
            print(f"  Fetched {i + 1}/{len(monster_names)} monsters...")
        time.sleep(0.1)

    print(f"✓ Successfully extracted {len(all_monsters)} monsters")
    save_raw_monsters(all_monsters, cache_path)
    return all_monsters

if __name__ == "__main__":
    monsters = extract_all_monsters(use_cache=False)
    print(f"\nSample monster: {monsters[0]['name']}")
    print(monsters[0])