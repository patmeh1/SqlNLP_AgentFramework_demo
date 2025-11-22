"""Quick script to check MedData database contents"""
import pyodbc
import struct
from azure.identity import AzureCliCredential

# Connect to database
credential = AzureCliCredential()
token = credential.get_token('https://database.windows.net/.default')
token_bytes = token.token.encode('utf-16-le')
token_struct = struct.pack(f'<I{len(token_bytes)}s', len(token_bytes), token_bytes)

conn = pyodbc.connect(
    'Driver={ODBC Driver 18 for SQL Server};'
    'Server=tcp:nyp-sql-1762356746.database.windows.net,1433;'
    'Database=MedData;'
    'Encrypt=yes;'
    'TrustServerCertificate=no;'
    'Connection Timeout=30;',
    attrs_before={1256: token_struct}
)

cursor = conn.cursor()

print("\n" + "="*70)
print("  MEDDATA DATABASE STATUS")
print("="*70)

# Check database name
cursor.execute("SELECT DB_NAME()")
print(f"\n✅ Connected to database: {cursor.fetchone()[0]}")

# List tables
print("\n📋 Checking tables...")
cursor.execute("""
    SELECT TABLE_NAME 
    FROM INFORMATION_SCHEMA.TABLES 
    WHERE TABLE_TYPE = 'BASE TABLE'
    ORDER BY TABLE_NAME
""")
tables = [row[0] for row in cursor.fetchall()]

if tables:
    print(f"✅ Found {len(tables)} table(s): {', '.join(tables)}")
else:
    print("❌ No tables found!")
    cursor.close()
    conn.close()
    exit(1)

# Check MED_SLOTS
if 'MED_SLOTS' in tables:
    cursor.execute("SELECT COUNT(*) FROM MED_SLOTS")
    count = cursor.fetchone()[0]
    print(f"\n📊 MED_SLOTS table:")
    print(f"   Rows: {count}")
    
    if count > 0:
        cursor.execute("SELECT TOP 5 SLOT_NUMBER, SLOT_NAME FROM MED_SLOTS ORDER BY SLOT_NUMBER")
        print(f"   Sample data:")
        for row in cursor.fetchall():
            print(f"     {row[0]}: {row[1]}")
else:
    print("\n❌ MED_SLOTS table not found!")

# Check MED
if 'MED' in tables:
    cursor.execute("SELECT COUNT(*) FROM MED")
    count = cursor.fetchone()[0]
    print(f"\n📊 MED table:")
    print(f"   Rows: {count}")
    
    if count > 0:
        cursor.execute("SELECT TOP 5 CODE, SLOT_NUMBER, SLOT_VALUE FROM MED ORDER BY CODE")
        print(f"   Sample data:")
        for row in cursor.fetchall():
            print(f"     {row[0]} - Slot {row[1]}: {row[2]}")
        
        # Count by slot type
        print(f"\n   Distribution by slot type:")
        cursor.execute("""
            SELECT s.SLOT_NAME, COUNT(*) as count
            FROM MED m
            JOIN MED_SLOTS s ON m.SLOT_NUMBER = s.SLOT_NUMBER
            GROUP BY s.SLOT_NAME
            ORDER BY count DESC
        """)
        for row in cursor.fetchall():
            print(f"     {row[0]}: {row[1]} codes")
else:
    print("\n❌ MED table not found!")

print("\n" + "="*70)

# Summary
if 'MED_SLOTS' in tables and 'MED' in tables:
    cursor.execute("SELECT COUNT(*) FROM MED_SLOTS")
    slots_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM MED")
    med_count = cursor.fetchone()[0]
    
    if slots_count > 0 and med_count > 0:
        print("✅ MedData database is FULLY LOADED and ready to use!")
        print(f"   - {slots_count} slot definitions")
        print(f"   - {med_count} medical codes")
    else:
        print("⚠️  Tables exist but are empty - data loading may still be in progress")
else:
    print("❌ Database structure incomplete - setup may still be running")

print("="*70 + "\n")

cursor.close()
conn.close()
