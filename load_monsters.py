import sqlite3
import os

def load_monsters(df, db_path=None):
    if db_path is None:
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dnd.db")
    
    conn = sqlite3.connect(db_path)
    
    df.to_sql(
        name="monsters",
        con=conn,
        if_exists="replace",
        index=False
    )
    
    conn.close()
    print(f"✓ {len(df)} monsters loaded into dnd.db")

def query_monsters(db_path=None):
    if db_path is None:
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dnd.db")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("\n--- MONSTER TYPES RANKED ---")
    cursor.execute("""
        SELECT type, COUNT(*) as count
        FROM monsters
        GROUP BY type
        ORDER BY count DESC
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]:<15} {row[1]}")

    print("\n--- LEGENDARY MONSTERS BY TYPE ---")
    cursor.execute("""
        SELECT type, COUNT(*) as count
        FROM monsters
        WHERE legendary = 1
        GROUP BY type
        ORDER BY count DESC
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]:<15} {row[1]}")

    print("\n--- MOST COMMON DAMAGE IMMUNITIES ---")
    cursor.execute("""
        SELECT damage_immunities, COUNT(*) as count
        FROM monsters
        WHERE damage_immunities IS NOT NULL
        GROUP BY damage_immunities
        ORDER BY count DESC
        LIMIT 10
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]:<40} {row[1]}")

    print("\n--- HIGHEST CR MONSTERS ---")
    cursor.execute("""
        SELECT name, type, challenge_rating, hit_points, legendary
        FROM monsters
        ORDER BY challenge_rating DESC
        LIMIT 10
    """)
    for row in cursor.fetchall():
        legendary_str = "⭐ LEGENDARY" if row[4] else ""
        print(f"  CR {row[2]:<5} {row[0]:<30} {row[1]:<15} HP:{row[3]} {legendary_str}")

    conn.close()

if __name__ == "__main__":
    from extract_monsters import extract_all_monsters
    from transform_monsters import transform_monsters
    
    raw = extract_all_monsters(use_cache=True)
    df = transform_monsters(raw)
    load_monsters(df)
    query_monsters()