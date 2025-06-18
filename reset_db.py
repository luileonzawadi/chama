import os
import sqlite3

# Delete the database file
db_path = 'instance/chama.db'
if os.path.exists(db_path):
    os.remove(db_path)
    print(f"Database file {db_path} has been deleted.")
else:
    print(f"Database file {db_path} does not exist.")

print("Database has been reset. Run fixed_app.py to create a new database.")