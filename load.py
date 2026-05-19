print("load.py started")

import sqlite3
import pandas as pd

def load_spells(df, db_path=None):
    """
    Saves the cleaned spell dataframe to a SQLite database.
    if_exists="replace" because spell data doesn't change daily.
    We're storing current state, not accumulating runs like weather.
    """
    if db_path is None:
        import os
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dnd.db")
    
    conn = sqlite3.connect(db_path)
    
    df.to_sql(
        name="spells",
        con=conn,
        if_exists="replace",
        index=False
    )
    
    conn.close()
    print(f"✓ {len(df)} spells loaded into dnd.db")

def query_spells(db_path=None):
    """
    SQL queries against our database to extract insights.
    SELECT = what columns do I want
    FROM = which table
    WHERE = filter rows
    GROUP BY = aggregate by category
    ORDER BY = sort results
    """
    if db_path is None:
        import os
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dnd.db")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("\n--- DAMAGE TYPES RANKED ---")
    cursor.execute("""
        SELECT damage_type, COUNT(*) as spell_count
        FROM spells
        WHERE damage_type IS NOT NULL
        GROUP BY damage_type
        ORDER BY spell_count DESC
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]:<15} {row[1]} spells")

    print("\n--- AVERAGE SPELL LEVEL BY SCHOOL ---")
    cursor.execute("""
        SELECT school, ROUND(AVG(level), 1) as avg_level, COUNT(*) as total_spells
        FROM spells
        GROUP BY school
        ORDER BY avg_level DESC
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]:<15} avg level {row[1]}  ({row[2]} spells)")

    print("\n--- MOST VERSATILE DAMAGE SPELLS (available to most classes) ---")
    cursor.execute("""
        SELECT name, damage_type, level, classes
        FROM spells
        WHERE damage_type IS NOT NULL
        ORDER BY LENGTH(classes) - LENGTH(REPLACE(classes, ',', '')) DESC
        LIMIT 5
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]:<25} {row[1]:<15} level {row[2]}")
        print(f"    Classes: {row[3]}")

    print("\n--- FIRE SPELLS BY LEVEL ---")
    cursor.execute("""
        SELECT name, level, school, base_damage
        FROM spells
        WHERE damage_type = 'Fire'
        ORDER BY level
    """)
    for row in cursor.fetchall():
        print(f"  Level {row[1]} | {row[0]:<30} {row[3]:<10} ({row[2]})")

    conn.close()

if __name__ == "__main__":
    print("main block triggered")
    from extract import extract_all_spells
    from transform import transform_spells
    
    raw = extract_all_spells(use_cache=True)
    df = transform_spells(raw)
    load_spells(df)
    query_spells()