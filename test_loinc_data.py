"""
Test script to verify LOINC 2947-0 data exists in the database
"""
import pyodbc
import os
from azure.identity import AzureCliCredential
import struct
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Get environment variables
sql_server = os.getenv('MEDDATA_SQL_SERVER')
sql_database = os.getenv('MEDDATA_SQL_DATABASE', 'MedData')
use_azure_ad = os.getenv('MEDDATA_USE_AZURE_AD', 'true').lower() == 'true'

# Build connection string
connection_string = (
    f"Driver={{ODBC Driver 18 for SQL Server}};"
    f"Server=tcp:{sql_server},1433;"
    f"Database={sql_database};"
    f"Encrypt=yes;"
    f"TrustServerCertificate=no;"
    f"Connection Timeout=30;"
)

# Get Azure AD token
credential = AzureCliCredential()
token = credential.get_token("https://database.windows.net/.default")
token_bytes = token.token.encode("utf-16-le")
token_struct = struct.pack(f'<I{len(token_bytes)}s', len(token_bytes), token_bytes)

# Connect
SQL_COPT_SS_ACCESS_TOKEN = 1256
conn = pyodbc.connect(connection_string, attrs_before={SQL_COPT_SS_ACCESS_TOKEN: token_struct})
cursor = conn.cursor()

print("=" * 80)
print("TEST 1: Find all procedures with LOINC code 2947-0")
print("=" * 80)

query1 = """
SELECT DISTINCT m.CODE, m.SLOT_NUMBER, m.SLOT_VALUE
FROM MED m
WHERE m.SLOT_NUMBER = 212 AND m.SLOT_VALUE = '2947-0'
"""

cursor.execute(query1)
results1 = cursor.fetchall()
print(f"Found {len(results1)} procedures with LOINC 2947-0")
for row in results1:
    print(f"  CODE: {row[0]}, SLOT: {row[1]}, VALUE: {row[2]}")

if not results1:
    print("❌ No procedures found with LOINC 2947-0!")
    print("\nLet's check what LOINC codes exist...")
    query_check = "SELECT DISTINCT m.SLOT_VALUE FROM MED m WHERE m.SLOT_NUMBER = 212 LIMIT 10"
    cursor.execute(query_check)
    loinc_samples = cursor.fetchall()
    print(f"Sample LOINC codes in database: {[r[0] for r in loinc_samples]}")

print()
print("=" * 80)
print("TEST 2: For each procedure, find what problems it indicates (slot 150)")
print("=" * 80)

if results1:
    for procedure_row in results1:
        procedure_code = procedure_row[0]
        print(f"\nProcedure CODE: {procedure_code}")
        
        # Find problems indicated by this procedure
        query2 = f"""
        SELECT DISTINCT indicates.CODE, indicates.SLOT_VALUE
        FROM MED indicates
        WHERE indicates.SLOT_NUMBER = 150 AND indicates.SLOT_VALUE = '{procedure_code}'
        """
        
        cursor.execute(query2)
        results2 = cursor.fetchall()
        print(f"  Found {len(results2)} problems indicated by this procedure")
        for row in results2:
            print(f"    Relation CODE: {row[0]}, Problem CODE (SLOT_VALUE): {row[1]}")
            
            # Get the problem's name and SNOMED code
            problem_code = row[1]
            query3 = f"""
            SELECT m.SLOT_NUMBER, m.SLOT_VALUE
            FROM MED m
            WHERE m.CODE = '{problem_code}' AND (m.SLOT_NUMBER = 6 OR m.SLOT_NUMBER = 266)
            """
            
            cursor.execute(query3)
            results3 = cursor.fetchall()
            print(f"      Problem details:")
            for detail_row in results3:
                slot = detail_row[0]
                value = detail_row[1]
                slot_name = "Name" if slot == 6 else "SNOMED Code"
                print(f"        {slot_name}: {value}")

print()
print("=" * 80)
print("TEST 3: Try the full query from the system prompt")
print("=" * 80)

full_query = """
SELECT DISTINCT prob.CODE, 
  MAX(CASE WHEN pname.SLOT_NUMBER = 6 THEN pname.SLOT_VALUE END) AS [Problem Name], 
  MAX(CASE WHEN psnomed.SLOT_NUMBER = 266 THEN psnomed.SLOT_VALUE END) AS [Problem SNOMED Code] 
FROM MED procedure_med 
INNER JOIN MED indicates ON procedure_med.CODE = indicates.SLOT_VALUE AND indicates.SLOT_NUMBER = 150 
INNER JOIN MED prob ON indicates.CODE = prob.CODE 
LEFT JOIN MED pname ON prob.CODE = pname.CODE AND pname.SLOT_NUMBER = 6 
LEFT JOIN MED psnomed ON prob.CODE = psnomed.CODE AND psnomed.SLOT_NUMBER = 266 
WHERE procedure_med.SLOT_NUMBER = 212 AND procedure_med.SLOT_VALUE = '2947-0' 
GROUP BY prob.CODE
"""

print("Query:")
print(full_query)
print()

cursor.execute(full_query)
results = cursor.fetchall()
print(f"Result: {len(results)} rows")
for row in results:
    print(f"  Problem CODE: {row[0]}, Name: {row[1]}, SNOMED: {row[2]}")

conn.close()
print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
