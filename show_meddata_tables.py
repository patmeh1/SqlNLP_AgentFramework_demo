"""
Show all tables in MedData database
"""
import pyodbc
import struct
from azure.identity import AzureCliCredential

def show_meddata_tables():
    """Display tables and their contents in MedData database"""
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
        print("📊 MedData Database Tables")
        print("="*80 + "\n")
        
        # Get list of tables
        cursor.execute("""
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_TYPE = 'BASE TABLE'
            ORDER BY TABLE_NAME
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"Found {len(tables)} table(s):\n")
        
        # For each table, show details
        for table_name in tables:
            print("="*80)
            print(f"TABLE: {table_name}")
            print("="*80)
            
            # Get column info
            cursor.execute(f"""
                SELECT 
                    COLUMN_NAME,
                    DATA_TYPE,
                    CHARACTER_MAXIMUM_LENGTH,
                    IS_NULLABLE
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = '{table_name}'
                ORDER BY ORDINAL_POSITION
            """)
            
            columns_info = cursor.fetchall()
            print("\nColumns:")
            for col in columns_info:
                col_name, data_type, max_len, nullable = col
                type_str = data_type
                if max_len:
                    type_str += f"({max_len})"
                print(f"  - {col_name:30} {type_str:20} {'NULL' if nullable == 'YES' else 'NOT NULL'}")
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]
            print(f"\nTotal Rows: {row_count}")
            
            # Show sample data (first 5 rows)
            cursor.execute(f"SELECT TOP 5 * FROM {table_name}")
            rows = cursor.fetchall()
            
            if rows:
                columns = [desc[0] for desc in cursor.description]
                print("\nSample Data (first 5 rows):")
                print("-" * 80)
                
                # Print header
                header = " | ".join(f"{col:20}"[:20] for col in columns)
                print(header)
                print("-" * 80)
                
                # Print rows
                for row in rows:
                    row_str = " | ".join(f"{str(val)[:20]:20}" for val in row)
                    print(row_str)
            
            print("\n")
        
        conn.close()
        
        print("="*80)
        print("✅ Database summary complete")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    show_meddata_tables()
