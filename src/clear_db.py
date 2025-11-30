import sqlite3
from pathlib import Path

db_path = Path(__file__).parent / "data" / "travel.db"

conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Zähle vorher
cur.execute("SELECT COUNT(*) FROM destinations")
before = cur.fetchone()[0]
print(f"Vorher: {before} Einträge")

# Lösche alle
cur.execute("DELETE FROM destinations")
conn.commit()

# Zähle nachher
cur.execute("SELECT COUNT(*) FROM destinations")
after = cur.fetchone()[0]
print(f"Nachher: {after} Einträge")

conn.close()
print("Fertig!  Jetzt CSV neu importieren.")