import sqlite3
import os
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# Connect to database
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dnd.db")
conn = sqlite3.connect(db_path)

# Set a dark fantasy style
plt.rcParams['figure.facecolor'] = '#1a1a2e'
plt.rcParams['axes.facecolor'] = '#16213e'
plt.rcParams['text.color'] = '#e0e0e0'
plt.rcParams['axes.labelcolor'] = '#e0e0e0'
plt.rcParams['xtick.color'] = '#e0e0e0'
plt.rcParams['ytick.color'] = '#e0e0e0'
plt.rcParams['axes.edgecolor'] = '#444466'

# Color map for damage types — thematic colors
DAMAGE_COLORS = {
    'Fire':        '#ff4500',
    'Radiant':     '#ffd700',
    'Necrotic':    '#6a0dad',
    'Force':       '#00bfff',
    'Lightning':   '#7df9ff',
    'Cold':        '#add8e6',
    'Psychic':     '#ff69b4',
    'Bludgeoning': '#8b7355',
    'Thunder':     '#9370db',
    'Piercing':    '#c0c0c0',
    'Acid':        '#7fff00',
    'Poison':      '#32cd32',
    'Slashing':    '#cd853f',
}

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('D&D 5e Spell Analytics', fontsize=18, fontweight='bold', color='#c9a84c')

# --- CHART 1: Damage types ranked ---
ax1 = axes[0, 0]
cursor = conn.cursor()
cursor.execute("""
    SELECT damage_type, COUNT(*) as count
    FROM spells
    WHERE damage_type IS NOT NULL
    GROUP BY damage_type
    ORDER BY count DESC
""")
data = cursor.fetchall()
types = [row[0] for row in data]
counts = [row[1] for row in data]
colors = [DAMAGE_COLORS.get(t, '#888888') for t in types]

bars = ax1.barh(types, counts, color=colors)
ax1.set_title('Spells by Damage Type', color='#c9a84c', fontweight='bold')
ax1.set_xlabel('Number of Spells')
ax1.invert_yaxis()
for bar, count in zip(bars, counts):
    ax1.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2,
             str(count), va='center', fontsize=9)

# --- CHART 2: Spells per school ---
ax2 = axes[0, 1]
cursor.execute("""
    SELECT school, COUNT(*) as count
    FROM spells
    GROUP BY school
    ORDER BY count DESC
""")
data = cursor.fetchall()
schools = [row[0] for row in data]
counts = [row[1] for row in data]
school_colors = ['#c9a84c', '#9370db', '#00bfff', '#ff4500', 
                 '#32cd32', '#ff69b4', '#add8e6', '#ffd700']

wedges, texts, autotexts = ax2.pie(
    counts, 
    labels=schools, 
    colors=school_colors,
    autopct='%1.0f%%',
    pctdistance=0.75
)
for text in texts:
    text.set_color('#e0e0e0')
for autotext in autotexts:
    autotext.set_color('#1a1a2e')
    autotext.set_fontweight('bold')
ax2.set_title('Spells by School of Magic', color='#c9a84c', fontweight='bold')

# --- CHART 3: Average spell level by school ---
ax3 = axes[1, 0]
cursor.execute("""
    SELECT school, ROUND(AVG(level), 1) as avg_level
    FROM spells
    GROUP BY school
    ORDER BY avg_level DESC
""")
data = cursor.fetchall()
schools = [row[0] for row in data]
avg_levels = [row[1] for row in data]

bars = ax3.bar(schools, avg_levels, color='#9370db')
ax3.set_title('Average Spell Level by School', color='#c9a84c', fontweight='bold')
ax3.set_ylabel('Average Level')
ax3.set_ylim(0, 6)
plt.setp(ax3.xaxis.get_majorticklabels(), rotation=35, ha='right')
for bar, val in zip(bars, avg_levels):
    ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
             str(val), ha='center', fontsize=9)

# --- CHART 4: Fire spells damage scaling ---
ax4 = axes[1, 1]
cursor.execute("""
    SELECT name, level, base_damage
    FROM spells
    WHERE damage_type = 'Fire'
    AND base_damage IS NOT NULL
    ORDER BY level
""")
data = cursor.fetchall()

def parse_avg_damage(damage_str):
    """Convert '8d6' to average damage (8 * 3.5 = 28)"""
    total = 0
    parts = damage_str.lower().replace(' ', '').split('+')
    for part in parts:
        if 'd' in part:
            num, die = part.split('d')
            total += int(num) * (int(die) + 1) / 2
        elif part.isdigit():
            total += int(part)
    return round(total, 1)

names = [row[0] for row in data]
levels = [row[1] for row in data]
avg_damages = [parse_avg_damage(row[2]) for row in data]

scatter = ax4.scatter(levels, avg_damages, color='#ff4500', s=100, zorder=5)
for i, name in enumerate(names):
    ax4.annotate(name, (levels[i], avg_damages[i]),
                textcoords="offset points", xytext=(5, 5),
                fontsize=7, color='#e0e0e0')
ax4.set_title('Fire Spells — Level vs Average Damage', color='#c9a84c', fontweight='bold')
ax4.set_xlabel('Spell Level')
ax4.set_ylabel('Average Damage')
ax4.set_xticks(range(0, 10))

plt.tight_layout()
plt.savefig('spell_analytics.png', dpi=150, bbox_inches='tight',
            facecolor='#1a1a2e')
print("✓ Chart saved as spell_analytics.png")
plt.show()

conn.close()