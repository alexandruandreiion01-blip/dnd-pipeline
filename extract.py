import requests
import time
import json
import os

def get_all_spell_names():
    """
    First we hit the /spells endpoint which gives us a list of all spell names
    and their individual URLs. Think of it as a table of contents.
    """
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
    """
    For each spell index (like "fireball"), we hit a separate endpoint
    that returns the full details of that one spell.
    """
    url = f"https://www.dnd5eapi.co/api/spells/{spell_index}"
    response = requests.get(url)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"✗ Failed to fetch {spell_index}")
        return None

def save_raw_spells(spells, path="raw_spells.json"):
    """
    Save the raw API response to a local JSON file.
    This means we only hit the API once — after that we load from disk.
    In real pipelines this is called a 'raw layer' or 'landing zone'.
    """
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
    """
    use_cache=True means: if we already have raw_spells.json, use it.
    use_cache=False means: always fetch fresh from the API.
    
    This is a pattern you'll see everywhere in data engineering.
    During development you use the cache. In production you set
    use_cache=False so you always get fresh data.
    """
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