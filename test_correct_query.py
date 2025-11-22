"""
Test the CORRECT query logic for finding Pt-Problems indicated by LOINC 2947-0
"""
import pyodbc
import os
from azure.identity import AzureCliCredential
import struct
from dotenv import load_dotenv

load_dotenv()

sql_server = os.getenv('MEDDATA_SQL_SERVER')
sql_database = os.getenv('MEDDATA_SQL_DATABASE', 'MedData')

connection_string = (
    f"Driver={{ODBC Driver 18 for SQL Server}};"
    f"Server=tcp:{sql_server},1433;"
    f"Database={sql_database};"
    f"Encrypt=yes;"
    f"TrustServerCertificate=no;"
    f"Connection Timeout=30;"
)

credential = AzureCliCredential()
token = credential.get_token("https://database.windows.net/.default")
token_bytes = token.token.encode("utf-16-le")
token_struct = struct.pack(f'<I{len(token_bytes)}s', len(token_bytes), token_bytes)

SQL_COPT_SS_ACCESS_TOKEN = 1256
conn = pyodbc.connect(connection_string, attrs_before={SQL_COPT_SS_ACCESS_TOKEN: token_struct})
cursor = conn.cursor()

print("=" * 80)
print("CORRECT QUERY: Find Pt-Problems indicated by procedures with LOINC 2947-0")
print("=" * 80)
print()

# The correct logic:
# 1. Find procedures with LOINC 2947-0 (where SLOT_NUMBER=212, SLOT_VALUE='2947-0')
# 2. For those procedures, get their SLOT_NUMBER=150 relationships (which point to problems)
# 3. Get the problem details (name, SNOMED code)

query = """
-- Find problems indicated by procedures with LOINC code 2947-0
SELECT DISTINCT 
  prob.CODE,
  MAX(CASE WHEN prob_name.SLOT_NUMBER = 6 THEN prob_name.SLOT_VALUE END) AS Problem_Name,
  MAX(CASE WHEN prob_snomed.SLOT_NUMBER = 266 THEN prob_snomed.SLOT_VALUE END) AS Problem_SNOMED
FROM MED loinc_ref        -- Find procedures with LOINC 2947-0
INNER JOIN MED indicates ON loinc_ref.CODE = indicates.CODE AND indicates.SLOT_NUMBER = 150
INNER JOIN MED prob ON indicates.SLOT_VALUE = prob.CODE
LEFT JOIN MED prob_name ON prob.CODE = prob_name.CODE AND prob_name.SLOT_NUMBER = 6
LEFT JOIN MED prob_snomed ON prob.CODE = prob_snomed.CODE AND prob_snomed.SLOT_NUMBER = 266
WHERE loinc_ref.SLOT_NUMBER = 212 AND loinc_ref.SLOT_VALUE = '2947-0'
GROUP BY prob.CODE
ORDER BY Problem_Name
"""

print("Query:")
print(query)
print()

cursor.execute(query)
results = cursor.fetchall()

print(f"RESULTS: {len(results)} problems found")
print()

if results:
    for i, row in enumerate(results, 1):
        code, name, snomed = row[0], row[1], row[2]
        print(f"{i}. Code: {code:6s} | Name: {name:50s} | SNOMED: {snomed}")
else:
    print("❌ No results!")

conn.close()
