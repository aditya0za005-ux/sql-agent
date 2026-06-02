import sqlite3
import os

DB_PATH = "data/company.db"

def get_connection():
    os.makedirs("data", exist_ok=True)
    return sqlite3.connect(DB_PATH)

def setup_database():
    """Create sample company database with realistic data."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS customers (
            customer_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT,
            city TEXT,
            country TEXT,
            signup_date TEXT
        );

        CREATE TABLE IF NOT EXISTS products (
            product_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT,
            price REAL,
            stock INTEGER
        );

        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY,
            customer_id INTEGER,
            order_date TEXT,
            status TEXT,
            total_amount REAL,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        );

        CREATE TABLE IF NOT EXISTS order_items (
            item_id INTEGER PRIMARY KEY,
            order_id INTEGER,
            product_id INTEGER,
            quantity INTEGER,
            unit_price REAL,
            FOREIGN KEY (order_id) REFERENCES orders(order_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        );

        CREATE TABLE IF NOT EXISTS employees (
            employee_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            department TEXT,
            salary REAL,
            hire_date TEXT,
            manager_id INTEGER
        );
    """)

    # Insert sample data only if tables are empty
    cursor.execute("SELECT COUNT(*) FROM customers")
    if cursor.fetchone()[0] == 0:
        cursor.executescript("""
            INSERT INTO customers VALUES
            (1,'Rahul Sharma','rahul@email.com','Mumbai','India','2022-01-15'),
            (2,'Priya Patel','priya@email.com','Pune','India','2022-03-20'),
            (3,'John Smith','john@email.com','New York','USA','2021-11-05'),
            (4,'Emily Chen','emily@email.com','San Francisco','USA','2023-02-10'),
            (5,'Arjun Mehta','arjun@email.com','Bangalore','India','2022-07-18'),
            (6,'Sara Khan','sara@email.com','Delhi','India','2023-01-08'),
            (7,'Mike Johnson','mike@email.com','Chicago','USA','2021-09-30'),
            (8,'Neha Gupta','neha@email.com','Pune','India','2023-04-22');

            INSERT INTO products VALUES
            (1,'Laptop Pro 15','Electronics',85000.00,45),
            (2,'Wireless Mouse','Electronics',1200.00,200),
            (3,'Office Chair','Furniture',12000.00,30),
            (4,'Standing Desk','Furniture',25000.00,15),
            (5,'Python Course','Education',4999.00,999),
            (6,'Headphones ANC','Electronics',8500.00,80),
            (7,'Mechanical Keyboard','Electronics',5500.00,60),
            (8,'Monitor 4K','Electronics',32000.00,25);

            INSERT INTO orders VALUES
            (1,1,'2024-01-10','completed',86200.00),
            (2,2,'2024-01-15','completed',13200.00),
            (3,3,'2024-02-01','completed',94500.00),
            (4,4,'2024-02-14','shipped',8500.00),
            (5,5,'2024-03-05','completed',37500.00),
            (6,1,'2024-03-20','completed',5500.00),
            (7,6,'2024-04-01','pending',4999.00),
            (8,7,'2024-04-10','completed',65500.00),
            (9,2,'2024-04-18','shipped',32000.00),
            (10,8,'2024-05-02','completed',9700.00);

            INSERT INTO order_items VALUES
            (1,1,1,1,85000.00),(2,1,2,1,1200.00),
            (3,2,3,1,12000.00),(4,2,2,1,1200.00),
            (5,3,1,1,85000.00),(6,3,6,1,8500.00),(7,3,2,1,1000.00),
            (8,4,6,1,8500.00),
            (9,5,4,1,25000.00),(10,5,7,2,5500.00),(11,5,2,1,1200.00),
            (12,6,7,1,5500.00),
            (13,7,5,1,4999.00),
            (14,8,1,1,60000.00),(15,8,3,1,5500.00),
            (16,9,8,1,32000.00),
            (17,10,6,1,8500.00),(18,10,2,1,1200.00);

            INSERT INTO employees VALUES
            (1,'Vikram Singh','Engineering',95000.00,'2020-06-01',NULL),
            (2,'Ananya Rao','Engineering',75000.00,'2021-03-15',1),
            (3,'Ravi Kumar','Sales',65000.00,'2021-07-20',NULL),
            (4,'Meena Joshi','Sales',58000.00,'2022-01-10',3),
            (5,'Suresh Nair','HR',60000.00,'2020-11-05',NULL),
            (6,'Pooja Mishra','Engineering',80000.00,'2021-09-01',1),
            (7,'Karan Bhatia','Sales',62000.00,'2022-05-15',3),
            (8,'Deepa Iyer','HR',55000.00,'2023-02-20',5);
        """)

    conn.commit()
    conn.close()

def get_full_schema():
    """Returns full schema as a string for LLM context."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]

    schema_parts = []
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        col_str = ", ".join([f"{col[1]} {col[2]}" for col in columns])
        schema_parts.append(f"Table: {table} ({col_str})")

        # Foreign keys
        cursor.execute(f"PRAGMA foreign_key_list({table})")
        fks = cursor.fetchall()
        for fk in fks:
            schema_parts.append(f"  FK: {table}.{fk[3]} -> {fk[2]}.{fk[4]}")

    conn.close()
    return "\n".join(schema_parts)

def get_table_metadata():
    """Returns per-table metadata dict for vector store."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]

    metadata = {}
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        cursor.execute(f"SELECT * FROM {table} LIMIT 2")
        samples = cursor.fetchall()

        metadata[table] = {
            "columns": [{"name": col[1], "type": col[2]} for col in columns],
            "sample_rows": samples
        }

    conn.close()
    return metadata
