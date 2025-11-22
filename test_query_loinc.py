import pyodbc
import os
from dotenv import load_dotenv

load_dotenv('.env.meddata')

server = os.getenv('SQL_SERVER')
database = os.getenv('SQL_DATABASE')
username = os.getenv('SQL_USERNAME')
password = os.getenv('SQL_PASSWORD')

try:
    conn = pyodbc.connect(f'Driver={{ODBC Driver 18 for SQL Server}};Server={server};Database={database};UID={username};PWD={password};Authentication=ActiveDirectory Password;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30')
    cursor = conn.cursor()
    
    # Get tables
    cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE'")
    tables = cursor.fetchall()
    print('=== TABLES ===')
    for table in tables:
        print(f'- {table[0]}')
    
    # Check MedData table columns
    print('\n=== MedData COLUMNS ===')
    cursor.execute("SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='MedData' ORDER BY ORDINAL_POSITION")
    columns = cursor.fetchall()
    for col in columns:
        print(f'- {col[0]}: {col[1]}')
    
    # Sample data
    print('\n=== SAMPLE DATA (First 3 rows) ===')
    cursor.execute('SELECT TOP 3 * FROM MedData')
    headers = [desc[0] for desc in cursor.description]
    print(f'Columns: {headers}')
    for row in cursor.fetchall():
        print(row)
        
    # Query for LOINC 2947-0
    print('\n=== QUERY: LOINC 2947-0 ===')
    cursor.execute("""
        SELECT DISTINCT 
            [Pt-Problem] as PatientProblem,
            [Pt-Problem-SNOMED] as SNOMED_Code,
            [Test-Code],
            [LOINC-Code]
        FROM MedData 
        WHERE [LOINC-Code] = '2947-0'
        ORDER BY [Pt-Problem]
    """)
    
    rows = cursor.fetchall()
    print(f'Found {len(rows)} rows')
    for row in rows:
        print(row)
        
    conn.close()
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
