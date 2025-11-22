"""
Show all tables and data in MedData database
"""
import pyodbc
import struct
from azure.identity import AzureCliCredential

def show_all_meddata():
    """Connect to MedData and show all tables and data"""
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
            attrs_before={1256: token_struct}  # SQL_COPT_SS_ACCESS_TOKEN
        )
        
        cursor = conn.cursor()
        
        print("\n" + "="*80)
        print("📊 MedData Database - All Tables and Data")
        print("="*80 + "\n")
        
        # Get list of tables
        cursor.execute("""
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_TYPE = 'BASE TABLE'
            ORDER BY TABLE_NAME
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"Found {len(tables)} table(s): {', '.join(tables)}\n")
        
        # For each table, show schema and data
        for table in tables:
            print("\n" + "="*80)
            print(f"TABLE: {table}")
            print("="*80)
            
            # Get column info
            cursor.execute(f"""
                SELECT 
                    COLUMN_NAME,
                    DATA_TYPE,
                    CHARACTER_MAXIMUM_LENGTH,
                    IS_NULLABLE
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = '{table}'
                ORDER BY ORDINAL_POSITION
            """)
            
            columns_info = cursor.fetchall()
            print("\nSchema:")
            for col in columns_info:
                col_name, data_type, max_len, nullable = col
                type_str = data_type
                if max_len:
                    type_str += f"({max_len})"
                print(f"  - {col_name:30} {type_str:20} Nullable: {nullable}")
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            row_count = cursor.fetchone()[0]
            print(f"\nTotal Rows: {row_count}")
            
            # Get all data
            cursor.execute(f"SELECT * FROM {table}")
            rows = cursor.fetchall()
            
            if rows:
                columns = [desc[0] for desc in cursor.description]
                print("\nData:")
                print("-" * 120)
                # Print header
                header = " | ".join(f"{col:25}" for col in columns)
                print(header)
                print("-" * 120)
                # Print rows
                for row in rows:
                    row_str = " | ".join(f"{str(val)[:25]:25}" for val in row)
                    print(row_str)
            else:
                print("\nNo data in this table.")
            
            print("\n")
        
        conn.close()
        
        print("="*80)
        print("✅ Query completed successfully")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    show_all_meddata()
