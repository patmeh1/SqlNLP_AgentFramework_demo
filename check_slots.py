"""
Check if slot 150 is used at all in the database, or if we should use a different slot
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
print("CHECK 1: Count of records for each slot number")
print("=" * 80)

query = """
SELECT TOP 50 SLOT_NUMBER, COUNT(*) as Count
FROM MED
GROUP BY SLOT_NUMBER
ORDER BY SLOT_NUMBER
"""

cursor.execute(query)
results = cursor.fetchall()
for row in results:
    slot_num, count = row[0], row[1]
    slot_names = {
        6: "PRINT-NAME",
        149: "PT-PROBLEM-(INDICATED-BY)->PROCEDURE",
        150: "PROCEDURE-(INDICATES)->PT-PROBLEM",
        212: "LOINC-CODE",
        266: "SNOMED-CODE"
    }
    slot_name = slot_names.get(slot_num, "UNKNOWN")
    print(f"Slot {slot_num:3d}: {count:7d} records - {slot_name}")

print()
print("=" * 80)
print("CHECK 2: How many records with slot 150?")
print("=" * 80)

query2 = "SELECT COUNT(*) FROM MED WHERE SLOT_NUMBER = 150"
cursor.execute(query2)
result = cursor.fetchone()
print(f"Total records with slot 150: {result[0]}")

if result[0] > 0:
    print("\nSample slot 150 records:")
    query3 = "SELECT TOP 5 CODE, SLOT_VALUE FROM MED WHERE SLOT_NUMBER = 150"
    cursor.execute(query3)
    for row in cursor.fetchall():
        print(f"  CODE: {row[0]}, SLOT_VALUE (related code): {row[1]}")

print()
print("=" * 80)
print("CHECK 3: How many records with slot 149?")
print("=" * 80)

query4 = "SELECT COUNT(*) FROM MED WHERE SLOT_NUMBER = 149"
cursor.execute(query4)
result = cursor.fetchone()
print(f"Total records with slot 149: {result[0]}")

if result[0] > 0:
    print("\nSample slot 149 records:")
    query5 = "SELECT TOP 5 CODE, SLOT_VALUE FROM MED WHERE SLOT_NUMBER = 149"
    cursor.execute(query5)
    for row in cursor.fetchall():
        print(f"  CODE: {row[0]}, SLOT_VALUE (related code): {row[1]}")

print()
print("=" * 80)
print("CHECK 4: What slots exist for procedure 1302 (one of the LOINC 2947-0 codes)?")
print("=" * 80)

query6 = """
SELECT m.SLOT_NUMBER, ms.SLOT_NAME, m.SLOT_VALUE
FROM MED m
LEFT JOIN MED_SLOTS ms ON m.SLOT_NUMBER = ms.SLOT_NUMBER
WHERE m.CODE = '1302'
ORDER BY m.SLOT_NUMBER
"""

cursor.execute(query6)
results = cursor.fetchall()
print(f"Total slots for procedure 1302: {len(results)}")
for row in results:
    slot_num, slot_name, slot_value = row[0], row[1] or "?", row[2]
    print(f"  Slot {slot_num:3d}: {slot_name:50s} = {slot_value}")

conn.close()
