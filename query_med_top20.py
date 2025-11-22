"""
Query to show top 20 rows from MED table in MedData database
"""

import pyodbc
import struct
from azure.identity import AzureCliCredential
from dotenv import load_dotenv
import os

load_dotenv()

def show_med_top20():
    """Display top 20 rows from MED table."""
    
    # Get Azure AD token
    credential = AzureCliCredential()
    token = credential.get_token("https://database.windows.net/.default")
    token_bytes = token.token.encode("utf-16-le")
    token_struct = struct.pack(f'<I{len(token_bytes)}s', len(token_bytes), token_bytes)
    
    # Connection string
    connection_string = (
        f"Driver={{ODBC Driver 18 for SQL Server}};"
        f"Server=tcp:{os.getenv('MEDDATA_SQL_SERVER')},1433;"
        f"Database={os.getenv('MEDDATA_SQL_DATABASE')};"
        f"Encrypt=yes;"
        f"TrustServerCertificate=no;"
        f"Connection Timeout=30;"
    )
    
    try:
        # Connect with Azure AD token
        SQL_COPT_SS_ACCESS_TOKEN = 1256
        conn = pyodbc.connect(connection_string, attrs_before={SQL_COPT_SS_ACCESS_TOKEN: token_struct})
        cursor = conn.cursor()
        
        print("=" * 100)
        print("TOP 20 ROWS FROM MED TABLE")
        print("=" * 100)
        print()
        
        # Query top 20 rows with slot names
        query = """
        SELECT TOP 20 
            m.CODE,
            m.SLOT_NUMBER,
            s.SLOT_NAME,
            m.SLOT_VALUE
        FROM MED m
        LEFT JOIN MED_SLOTS s ON m.SLOT_NUMBER = s.SLOT_NUMBER
        ORDER BY m.CODE, m.SLOT_NUMBER
        """
        
        cursor.execute(query)
        
        print(f"{'CODE':<15} {'SLOT #':<8} {'SLOT NAME':<40} {'SLOT VALUE':<50}")
        print("-" * 100)
        
        row_count = 0
        for row in cursor.fetchall():
            code = row[0] or ''
            slot_num = str(row[1]) if row[1] is not None else ''
            slot_name = row[2] or ''
            slot_value = row[3] or ''
            
            # Truncate long values
            if len(slot_value) > 47:
                slot_value = slot_value[:47] + "..."
            
            print(f"{code:<15} {slot_num:<8} {slot_name:<40} {slot_value:<50}")
            row_count += 1
        
        print("-" * 100)
        print(f"\nTotal rows displayed: {row_count}")
        
        # Show total count in table
        cursor.execute("SELECT COUNT(*) FROM MED")
        total = cursor.fetchone()[0]
        print(f"Total rows in MED table: {total}")
        
        # Show unique codes
        cursor.execute("SELECT COUNT(DISTINCT CODE) FROM MED")
        unique_codes = cursor.fetchone()[0]
        print(f"Unique medical codes: {unique_codes}")
        
        conn.close()
        print("\n✅ Query completed successfully")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    show_med_top20()
