import sqlite3
import pandas as pd
from flask import Flask, jsonify
from datetime import datetime

# Step 1: Create three regional databases (simulating distributed systems)
def setup_database(db_name, data):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS machines (
        machine_id INTEGER PRIMARY KEY,
        status TEXT,
        last_maintenance TEXT,
        region TEXT
    )
    ''')
    cursor.execute('DELETE FROM machines')
    cursor.executemany('INSERT INTO machines VALUES (?, ?, ?, ?)', data)
    conn.commit()
    conn.close()

# Sample data for three regions
lagos_data = [(i, 'Operational' if i % 2 == 0 else 'Needs Repair', '2024-07-01', 'Lagos') for i in range(1, 301)]
abuja_data = [(i, 'Operational' if i % 3 == 0 else 'Needs Repair', '2024-07-02', 'Abuja') for i in range(301, 601)]
ph_data = [(i, 'Operational' if i % 4 == 0 else 'Needs Repair', '2024-07-03', 'Port Harcourt') for i in range(601, 1001)]
setup_database('lagos.db', lagos_data)
setup_database('abuja.db', abuja_data)
setup_database('ph.db', ph_data)

# Step 2: Slow query (manual fetch from each database)
def slow_query():
    start = datetime.now()
    df_lagos = pd.read_sql_query("SELECT * FROM machines WHERE status = 'Needs Repair'", sqlite3.connect('lagos.db'))
    df_abuja = pd.read_sql_query("SELECT * FROM machines WHERE status = 'Needs Repair'", sqlite3.connect('abuja.db'))
    df_ph = pd.read_sql_query("SELECT * FROM machines WHERE status = 'Needs Repair'", sqlite3.connect('ph.db'))
    df = pd.concat([df_lagos, df_abuja, df_ph])
    end = datetime.now()
    print(f"Slow query time: {(end - start).total_seconds()} seconds")
    return df

print("Before API (Manual Query):")
print(slow_query().head())

# Step 3: Create API to integrate distributed databases
app = Flask(__name__)

@app.route('/api/machines', methods=['GET'])
def get_machines():
    start = datetime.now()
    df_lagos = pd.read_sql_query("SELECT * FROM machines WHERE status = 'Needs Repair'", sqlite3.connect('lagos.db'))
    df_abuja = pd.read_sql_query("SELECT * FROM machines WHERE status = 'Needs Repair'", sqlite3.connect('abuja.db'))
    df_ph = pd.read_sql_query("SELECT * FROM machines WHERE status = 'Needs Repair'", sqlite3.connect('ph.db'))
    df = pd.concat([df_lagos, df_abuja, df_ph])
    end = datetime.now()
    print(f"API query time: {(end - start).total_seconds()} seconds")
    return jsonify(df.to_dict(orient='records'))

# Step 4: Save API results to central database for dashboard and traceability
conn_central = sqlite3.connect('fieldfix_central.db')
cursor = conn_central.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS maintenance_insights (
    machine_id INTEGER PRIMARY KEY,
    status TEXT,
    last_maintenance TEXT,
    region TEXT,
    fetch_time TEXT
)
''')
cursor.execute('DELETE FROM maintenance_insights')
df = slow_query()  # Simulate API data
df['fetch_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
df.to_sql('maintenance_insights', conn_central, if_exists='append', index=False)
conn_central.commit()

# Step 5: Query for dashboard
def fetch_dashboard_data():
    start = datetime.now()
    df = pd.read_sql_query('SELECT * FROM maintenance_insights', conn_central)
    end = datetime.now()
    print(f"Dashboard query time: {(end - start).total_seconds()} seconds")
    return df

print("\nDashboard Data:")
print(fetch_dashboard_data().head())

# Step 6: Simulate dashboard output
def show_dashboard(df):
    repair_count = df[df['status'] == 'Needs Repair']['machine_id'].count()
    regions = df['region'].unique()
    print(f"\nDashboard Metrics:\nMachines Needing Repair: {repair_count}\nRegions: {', '.join(regions)}")

show_dashboard(fetch_dashboard_data())

# Clean up
conn_central.close()

# Note: To run Flask API, uncomment below and run in a separate process
# if __name__ == '__main__':
#     app.run(debug=True)