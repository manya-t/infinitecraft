import sqlite3
import psycopg2
import json

sqlite_conn = sqlite3.connect('db.sqlite3')
sqlite_conn.row_factory = sqlite3.Row
sqlite_cursor = sqlite_conn.cursor()

# Your Railway Postgres connection string
pg_conn = psycopg2.connect('postgresql://postgres:AXoDAVYYrFicDvoSfwRTDBaquCpCCTKC@yamanote.proxy.rlwy.net:32972/railway')
pg_cursor = pg_conn.cursor()
pg_cursor.execute('SET session_replication_role = replica;')

# Fetch all data from your table
sqlite_cursor.execute('SELECT * FROM items_transformation')
rows = sqlite_cursor.fetchall()

# Insert into Postgres

for row in rows:
        row_dict = dict(row)
        for key, value in row_dict.items():
            if key in ['isReal', 'canCombine']:
                row_dict[key] = bool(value)
        

        # Build your INSERT statement
        columns = ', '.join(f'"{col}"' for col in row_dict.keys())
        values = ', '.join(['%s'] * len(row_dict))
        sql = f"INSERT INTO items_transformation ({columns}) VALUES ({values})"
        try:
            pg_cursor.execute(sql, tuple(row_dict.values()))
        except Exception as e:
            print(f"Error inserting row: {e}")
            pg_conn.rollback()
            continue
        
        if row_dict["id"] % 500 == 0:
            pg_conn.commit()
            print(f'Committed row: {row_dict["id"]}')

pg_cursor.execute('SET session_replication_role = default;')
pg_conn.commit()
sqlite_conn.close()
pg_conn.close()
print("Done!")