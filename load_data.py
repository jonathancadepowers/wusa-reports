# load_data.py
import pandas as pd
import sqlite3

# Read CSV from scheduler
df = pd.read_csv('test_schedule.csv')  # ← Changed filename

# Create database
conn = sqlite3.connect('wusa_schedule.db')

# Load into database
df.to_sql('games', conn, if_exists='replace', index=False)

print(f"✅ Loaded {len(df)} games into database")
print(f"📊 Columns: {list(df.columns)}")
print(f"🗓️  Weeks: {df['Week'].min()} - {df['Week'].max()}")
print(f"🏟️  Fields: {df['Field'].nunique()}")
print(f"👥 Divisions: {', '.join(df['Division'].unique())}")

conn.close()