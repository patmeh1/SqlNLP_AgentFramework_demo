"""
Test script to verify MedData database setup
Runs sample queries and displays results
"""

import os
import pyodbc
import sys
from tabulate import tabulate


def test_database_connection(connection_string):
    """Test database connection and run sample queries"""
    
    try:
        print("\n" + "="*80)
        print("MedData Database Verification")
        print("="*80 + "\n")
        
        print("Connecting to database...")
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        print("✓ Connected successfully\n")
        
        # Test 1: Count rows in MED_SLOTS
        print("-" * 80)
        print("Test 1: MED_SLOTS Table")
        print("-" * 80)
        cursor.execute("SELECT COUNT(*) FROM MED_SLOTS")
        count = cursor.fetchone()[0]
        print(f"Total rows: {count}")
        
        cursor.execute("SELECT SLOT_NUMBER, SLOT_NAME, SLOT_TYPE FROM MED_SLOTS ORDER BY SLOT_NUMBER")
        rows = cursor.fetchall()
        print(tabulate(rows, headers=['Slot #', 'Slot Name', 'Type'], tablefmt='grid'))
        
        # Test 2: Count rows in MED
        print("\n" + "-" * 80)
        print("Test 2: MED Table")
        print("-" * 80)
        cursor.execute("SELECT COUNT(*) FROM MED")
        count = cursor.fetchone()[0]
        print(f"Total rows: {count}\n")
        
        cursor.execute("SELECT COUNT(DISTINCT CODE) FROM MED")
        unique_codes = cursor.fetchone()[0]
        print(f"Unique medical codes: {unique_codes}\n")
        
        # Test 3: Sample data for code 1302
        print("-" * 80)
        print("Test 3: Sample Data for Medical Code 1302")
        print("-" * 80)
        query = """
        SELECT 
            m.CODE,
            s.SLOT_NAME,
            m.SLOT_VALUE
        FROM MED m
        JOIN MED_SLOTS s ON m.SLOT_NUMBER = s.SLOT_NUMBER
        WHERE m.CODE = 1302
        ORDER BY s.SLOT_NUMBER
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        print(tabulate(rows, headers=['Code', 'Slot Name', 'Value'], tablefmt='grid'))
        
        # Test 4: Codes with LOINC codes
        print("\n" + "-" * 80)
        print("Test 4: Medical Codes with LOINC Codes (Sample)")
        print("-" * 80)
        query = """
        SELECT TOP 10
            m.CODE,
            m.SLOT_VALUE as LOINC_CODE,
            (SELECT SLOT_VALUE FROM MED WHERE CODE = m.CODE AND SLOT_NUMBER = 6) as PRINT_NAME
        FROM MED m
        WHERE m.SLOT_NUMBER = 212
          AND m.SLOT_VALUE != ''
        ORDER BY m.CODE
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        print(tabulate(rows, headers=['Code', 'LOINC Code', 'Print Name'], tablefmt='grid'))
        
        # Test 5: Check foreign key constraint
        print("\n" + "-" * 80)
        print("Test 5: Foreign Key Constraint Test")
        print("-" * 80)
        try:
            cursor.execute("INSERT INTO MED (CODE, SLOT_NUMBER, SLOT_VALUE) VALUES (99999, 999, 'TEST')")
            print("✗ Foreign key constraint NOT working (this is bad)")
        except pyodbc.IntegrityError as e:
            print("✓ Foreign key constraint working correctly")
            print(f"  Expected error: {str(e)[:100]}...")
        
        # Test 6: Check indexes
        print("\n" + "-" * 80)
        print("Test 6: Index Information")
        print("-" * 80)
        query = """
        SELECT 
            i.name AS IndexName,
            c.name AS ColumnName,
            i.type_desc AS IndexType
        FROM sys.indexes i
        JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
        JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
        WHERE i.object_id = OBJECT_ID('MED')
        ORDER BY i.name, ic.key_ordinal
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        print(tabulate(rows, headers=['Index Name', 'Column', 'Type'], tablefmt='grid'))
        
        cursor.close()
        conn.close()
        
        print("\n" + "="*80)
        print("✓ All tests completed successfully!")
        print("="*80 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        return False


def main():
    """Main function"""
    
    # Get connection details from environment variables
    server_name = os.getenv('SQL_SERVER_NAME', 'meddata-sql-server')
    database_name = 'MedData'
    username = os.getenv('SQL_ADMIN_USERNAME', 'sqladmin')
    password = os.getenv('SQL_ADMIN_PASSWORD')
    
    if not password:
        print("Error: SQL_ADMIN_PASSWORD environment variable not set")
        print("Usage: $env:SQL_ADMIN_PASSWORD='YourPassword'; python test_meddata.py")
        sys.exit(1)
    
    # Build connection string
    connection_string = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={server_name}.database.windows.net;"
        f"DATABASE={database_name};"
        f"UID={username};"
        f"PWD={password};"
        f"Encrypt=yes;"
        f"TrustServerCertificate=no;"
        f"Connection Timeout=30;"
    )
    
    print(f"Testing database: {server_name}.database.windows.net/{database_name}")
    
    success = test_database_connection(connection_string)
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
