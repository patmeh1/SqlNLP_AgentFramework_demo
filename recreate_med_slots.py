"""
Recreate MED_SLOTS table with new slot definitions
"""
import pyodbc
import struct
from azure.identity import AzureCliCredential

def recreate_med_slots_table():
    """Drop and recreate MED_SLOTS table with new data"""
    try:
        # Get Azure AD token
        credential = AzureCliCredential()
        token = credential.get_token("https://database.windows.net/.default")
        token_bytes = token.token.encode("utf-16-le")
        token_struct = struct.pack(f'<I{len(token_bytes)}s', len(token_bytes), token_bytes)
        
        # Build connection string
        connection_string = (
            f"Driver={{ODBC Driver 18 for SQL Server}};"
            f"Server=tcp:nyp-sql-1762356746.database.windows.net,1433;"
            f"Database=MedData;"
            f"Encrypt=yes;"
            f"TrustServerCertificate=no;"
            f"Connection Timeout=30;"
        )
        
        # Connect with Azure AD token
        conn = pyodbc.connect(
            connection_string,
            attrs_before={1256: token_struct}
        )
        
        cursor = conn.cursor()
        
        print("\n" + "="*80)
        print("🗑️  Dropping existing MED_SLOTS table...")
        print("="*80)
        
        # Drop existing table
        cursor.execute("DROP TABLE IF EXISTS MED_SLOTS")
        conn.commit()
        print("✅ MED_SLOTS table dropped")
        
        print("\n" + "="*80)
        print("📊 Creating new MED_SLOTS table...")
        print("="*80)
        
        # Create new table
        cursor.execute("""
            CREATE TABLE MED_SLOTS (
                SLOT_NUMBER INT NOT NULL PRIMARY KEY,
                SLOT_NAME NVARCHAR(100) NOT NULL
            )
        """)
        conn.commit()
        print("✅ MED_SLOTS table created")
        
        print("\n" + "="*80)
        print("📥 Inserting slot data...")
        print("="*80)
        
        # Data to insert - everything after first comma goes to SLOT_NAME
        data = [
            (3, "DESCENDANT-OF,SEMANTIC"),
            (4, "SUBCLASS-OF,SEMANTIC"),
            (6, "PRINT-NAME,STRING"),
            (9, "CPMC-LAB-PROC-CODE,STRING"),
            (15, "MEASURED-BY-PROCEDURE,SEMANTIC"),
            (16, "ENTITY-MEASURED,SEMANTIC"),
            (20, "CPMC-LAB-TEST-CODE,STRING"),
            (149, "PT-PROBLEM-(INDICATED-BY)->PROCEDURE,SEMANTIC"),
            (150, "PROCEDURE-(INDICATES)->PT-PROBLEM,SEMANTIC"),
            (212, "LOINC-CODE,STRING"),
            (264, "MILLENNIUM-LAB-CODE,STRING"),
            (266, "SNOMED-CODE,STRING"),
            (277, "EPIC-COMPONENT-ID,STRING"),
        ]
        
        # Insert using executemany
        insert_sql = "INSERT INTO MED_SLOTS (SLOT_NUMBER, SLOT_NAME) VALUES (?, ?)"
        cursor.executemany(insert_sql, data)
        conn.commit()
        
        print(f"✅ Successfully inserted {len(data)} slot definitions")
        
        # Verify the data
        print("\n" + "="*80)
        print("🔍 Verifying MED_SLOTS data...")
        print("="*80)
        
        cursor.execute("SELECT COUNT(*) FROM MED_SLOTS")
        total = cursor.fetchone()[0]
        print(f"\nTotal slots: {total}")
        
        # Show all slots
        cursor.execute("SELECT SLOT_NUMBER, SLOT_NAME FROM MED_SLOTS ORDER BY SLOT_NUMBER")
        rows = cursor.fetchall()
        
        print(f"\n{'SLOT_NUMBER':<15} {'SLOT_NAME':<60}")
        print("-" * 80)
        for row in rows:
            print(f"{row[0]:<15} {row[1]:<60}")
        
        conn.close()
        
        print("\n" + "="*80)
        print("✅ MED_SLOTS table recreated successfully!")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    recreate_med_slots_table()
