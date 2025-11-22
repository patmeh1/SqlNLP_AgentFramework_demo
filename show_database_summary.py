"""
Show complete MedData database summary
"""
import pyodbc
import struct
from azure.identity import AzureCliCredential

def show_database_summary():
    """Show summary of MedData database"""
    try:
        credential = AzureCliCredential()
        token = credential.get_token("https://database.windows.net/.default")
        token_bytes = token.token.encode("utf-16-le")
        token_struct = struct.pack(f'<I{len(token_bytes)}s', len(token_bytes), token_bytes)
        
        connection_string = (
            f"Driver={{ODBC Driver 18 for SQL Server}};"
            f"Server=tcp:nyp-sql-1762356746.database.windows.net,1433;"
            f"Database=MedData;"
            f"Encrypt=yes;"
            f"TrustServerCertificate=no;"
            f"Connection Timeout=30;"
        )
        
        conn = pyodbc.connect(connection_string, attrs_before={1256: token_struct})
        cursor = conn.cursor()
        
        print("\n" + "="*80)
        print("📊 MedData Database Summary")
        print("="*80 + "\n")
        
        # Table counts
        cursor.execute("SELECT COUNT(*) FROM MED_SLOTS")
        slots_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM MED")
        med_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT CODE) FROM MED")
        unique_codes = cursor.fetchone()[0]
        
        print(f"MED_SLOTS Table: {slots_count} slot definitions")
        print(f"MED Table:       {med_count} rows, {unique_codes} unique CODEs")
        
        # Show slot definitions
        print("\n" + "="*80)
        print("Slot Definitions:")
        print("="*80)
        cursor.execute("SELECT SLOT_NUMBER, SLOT_NAME FROM MED_SLOTS ORDER BY SLOT_NUMBER")
        for row in cursor.fetchall():
            print(f"  {row[0]:>3} - {row[1]}")
        
        # Show key slot usage
        print("\n" + "="*80)
        print("Slot Usage in MED Table:")
        print("="*80)
        cursor.execute("""
            SELECT m.SLOT_NUMBER, ms.SLOT_NAME, COUNT(*) as UsageCount
            FROM MED m
            JOIN MED_SLOTS ms ON m.SLOT_NUMBER = ms.SLOT_NUMBER
            GROUP BY m.SLOT_NUMBER, ms.SLOT_NAME
            ORDER BY m.SLOT_NUMBER
        """)
        for row in cursor.fetchall():
            print(f"  Slot {row[0]:>3} ({row[1]:<45}): {row[2]:>4} entries")
        
        # Sample query: Find tests with LOINC code 2947-0
        print("\n" + "="*80)
        print("Sample: Tests with LOINC 2947-0 (Sodium, Whole Blood):")
        print("="*80)
        cursor.execute("""
            SELECT DISTINCT m1.CODE, m2.SLOT_VALUE as TestName
            FROM MED m1
            JOIN MED m2 ON m1.CODE = m2.CODE AND m2.SLOT_NUMBER = 6
            WHERE m1.SLOT_NUMBER = 212 AND m1.SLOT_VALUE = '2947-0'
            ORDER BY m1.CODE
        """)
        rows = cursor.fetchall()
        print(f"Found {len(rows)} tests:")
        for i, row in enumerate(rows[:5], 1):
            print(f"  {i}. CODE {row[0]}: {row[1]}")
        if len(rows) > 5:
            print(f"  ... and {len(rows) - 5} more")
        
        conn.close()
        
        print("\n" + "="*80)
        print("✅ Database is ready for queries!")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    show_database_summary()
