import sqlite3

# 1. Connect to a database (creates a file named 'my_database.db' if not found)
try:
    conn = sqlite3.connect('my_database.db')
    cursor = conn.cursor()
    print("Database connected and cursor created.")

    # 2. Create a table
    create_table_query = '''
    CREATE TABLE IF NOT EXISTS Employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        department TEXT
    );
    '''
    cursor.execute(create_table_query)
    print("Table 'Employees' created successfully.")

    # 3. Insert some data
    cursor.execute("INSERT INTO Employees (name, department) VALUES ('Alice', 'Engineering')")
    cursor.execute("INSERT INTO Employees (name, department) VALUES ('Bob', 'Sales')")
    conn.commit() # Commit changes to make them persistent
    print("Data inserted and committed.")

    # 4. Query the data
    cursor.execute("SELECT * FROM Employees")
    rows = cursor.fetchall()
    print("\nData in Employees table:")
    for row in rows:
        print(row)

except sqlite3.Error as e:
    print(f"An error occurred: {e}")

finally:
    # 5. Close the connection
    if conn:
        conn.close()
        print("\nDatabase connection closed.")
