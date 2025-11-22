"""
Query MED table for LOINC code 2947-0
"""
import pyodbc
import struct
from azure.identity import AzureCliCredential

def query_loinc_2947():
    """Query tests with LOINC code 2947-0"""
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
        print("🔍 Tests with LOINC code 2947-0 (Sodium)")
        print("="*80 + "\n")
        
        # Find all CODEs that have LOINC 2947-0 in slot 212
        query = """
            SELECT DISTINCT m1.CODE, m2.SLOT_VALUE as TestName
            FROM MED m1
            JOIN MED m2 ON m1.CODE = m2.CODE AND m2.SLOT_NUMBER = 6
            WHERE m1.SLOT_NUMBER = 212 AND m1.SLOT_VALUE = '2947-0'
            ORDER BY m1.CODE
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        print(f"Found {len(rows)} tests with LOINC code 2947-0:\n")
        for row in rows:
            print(f"CODE: {row[0]:<10} | Test Name: {row[1]}")
        
        print("\n" + "="*80)
        print("✅ Query completed")
        print("="*80 + "\n")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    query_loinc_2947()
