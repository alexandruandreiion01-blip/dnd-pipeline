import requests
import time
import json
import os

def get_all_spell_names():
    
    url = "https://www.dnd5eapi.co/api/spells"
    response = requests.get(url)
    data = response.json()
    
    # data["results"] is a list like:
    # [{"name": "Fireball", "index": "fireball"}, ...]
    # we only need the index (used to build the individual spell URL)
    spell_list = [spell["index"] for spell in data["results"]]
    
    print(f"✓ Found {len(spell_list)} spells")
    return spell_list

def get_spell_details(spell_index):
   
    url = f"https://www.dnd5eapi.co/api/spells/{spell_index}"
    response = requests.get(url)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"✗ Failed to fetch {spell_index}")
        return None

def save_raw_spells(spells, path="raw_spells.json"):
    
    with open(path, "w") as f:
        json.dump(spells, f)
    print(f"✓ Saved {len(spells)} spells to {path}")

def load_raw_spells(path="raw_spells.json"):
    """
    Load previously saved spell data from disk instead of the API.
    """
    with open(path, "r") as f:
        spells = json.load(f)
    print(f"✓ Loaded {len(spells)} spells from {path}")
    return spells

def extract_all_spells(use_cache=True):
    
    cache_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "raw_spells.json")
    
    if use_cache and os.path.exists(cache_path):
        print("✓ Cache found, loading from disk (skipping API calls)")
        return load_raw_spells(cache_path)
    
    # No cache — fetch from API
    spell_names = get_all_spell_names()
    all_spells = []
    
    for i, spell_index in enumerate(spell_names):
        spell = get_spell_details(spell_index)
        if spell:
            all_spells.append(spell)
        if (i + 1) % 50 == 0:
            print(f"  Fetched {i + 1}/{len(spell_names)} spells...")
        time.sleep(0.1)
    
    print(f"✓ Successfully extracted {len(all_spells)} spells")
    save_raw_spells(all_spells, cache_path)  # save for next time
    return all_spells

if __name__ == "__main__":
    spells = extract_all_spells(use_cache=False)  # force fresh fetch
    print(f"\nSample spell: {spells[0]['name']}")