"""
Recreate MED table with new data
"""
import pyodbc
import struct
from azure.identity import AzureCliCredential

def recreate_med_table():
    """Drop and recreate MED table with new data"""
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
        print("🗑️  Dropping existing MED table...")
        print("="*80)
        
        # Drop existing table
        cursor.execute("DROP TABLE IF EXISTS MED")
        conn.commit()
        print("✅ MED table dropped")
        
        print("\n" + "="*80)
        print("📊 Creating new MED table...")
        print("="*80)
        
        # Create new table with updated schema
        # CODE and SLOT_NUMBER remain the same
        # SLOT_VALUE can be numeric or string, so using NVARCHAR
        cursor.execute("""
            CREATE TABLE MED (
                CODE NVARCHAR(50) NOT NULL,
                SLOT_NUMBER INT NOT NULL,
                SLOT_VALUE NVARCHAR(200) NOT NULL,
                PRIMARY KEY (CODE, SLOT_NUMBER, SLOT_VALUE)
            )
        """)
        conn.commit()
        print("✅ MED table created")
        
        print("\n" + "="*80)
        print("📥 Inserting data...")
        print("="*80)
        
        # Data to insert
        data = [
            (1302, 150, "19928"),
            (1302, 150, "3668"),
            (1302, 20, ""),
            (1302, 212, "2947-0"),
            (1302, 266, ""),
            (1302, 277, ""),
            (1302, 3, "32180"),
            (1302, 4, "32180"),
            (1302, 6, "Stat Whole Blood Sodium Ion Measurement"),
            (1611, 150, "19928"),
            (1611, 150, "3668"),
            (1611, 20, ""),
            (1611, 212, "2947-0"),
            (1611, 266, ""),
            (1611, 277, ""),
            (1611, 3, "32180"),
            (1611, 4, "32180"),
            (1611, 6, "Presbyterian Whole Blood Sodium Ion Measurement"),
            (1612, 150, "19928"),
            (1612, 150, "3668"),
            (1612, 20, ""),
            (1612, 212, "2951-2"),
            (1612, 266, ""),
            (1612, 277, ""),
            (1612, 3, "32698"),
            (1612, 4, "32698"),
            (1612, 6, "Serum Sodium Ion Measurement"),
            (1662, 150, "19928"),
            (1662, 150, "3668"),
            (1662, 20, ""),
            (1662, 212, ""),
            (1662, 266, ""),
            (1662, 277, ""),
            (1662, 3, "32180"),
            (1662, 4, "32180"),
            (1662, 6, "Allen Whole Blood Sodium Ion Measurement"),
            (3668, 266, "39355002"),
            (3668, 3, "42484"),
            (3668, 4, "42484"),
            (3668, 6, "Hypernatremia"),
            (3670, 266, "238115004"),
            (3670, 3, "19928"),
            (3670, 3, "42484"),
            (3670, 4, "19928"),
            (3670, 6, "True Sodium (Na) Deficiency"),
            (19928, 266, "89627008"),
            (19928, 3, "42484"),
            (19928, 4, "42484"),
            (19928, 6, "Hyponatremia"),
            (32180, 150, "19928"),
            (32180, 150, "3668"),
            (32180, 212, ""),
            (32180, 266, ""),
            (32180, 277, ""),
            (32180, 6, "Whole Blood Sodium Tests"),
            (32698, 150, "19928"),
            (32698, 150, "3668"),
            (32698, 212, ""),
            (32698, 266, ""),
            (32698, 277, ""),
            (32698, 6, "Serum Sodium Ion Tests"),
            (32712, 150, "19928"),
            (32712, 150, "3668"),
            (32712, 20, ""),
            (32712, 212, "2951-2"),
            (32712, 266, ""),
            (32712, 277, ""),
            (32712, 3, "32698"),
            (32712, 4, "32698"),
            (32712, 6, "Serum Sodium Ion Measurement 2"),
            (35978, 150, "19928"),
            (35978, 150, "3668"),
            (35978, 20, "INA"),
            (35978, 212, "2947-0"),
            (35978, 266, ""),
            (35978, 277, ""),
            (35978, 3, "32180"),
            (35978, 4, "32180"),
            (35978, 6, "CPMC Laboratory Test: Sodium, Whole Blood"),
            (36066, 150, "19928"),
            (36066, 150, "3668"),
            (36066, 20, "NAWBZ"),
            (36066, 212, "2947-0"),
            (36066, 266, ""),
            (36066, 277, ""),
            (36066, 3, "32180"),
            (36066, 4, "32180"),
            (36066, 6, "CPMC Laboratory Test: Sodium Whole Blood"),
            (36067, 150, "19928"),
            (36067, 150, "3668"),
            (36067, 20, "NAZ"),
            (36067, 212, "2951-2"),
            (36067, 266, ""),
            (36067, 277, ""),
            (36067, 3, "32698"),
            (36067, 4, "32698"),
            (36067, 6, "CPMC Laboratory Test: Sodium"),
            (36067, 9, "NAZ"),
            (42484, 266, ""),
            (42484, 6, "Abnormal Blood Level of Sodium"),
            (50013, 150, "19928"),
            (50013, 150, "3668"),
            (50013, 212, "2951-2"),
            (50013, 266, ""),
            (50013, 277, ""),
            (50013, 3, "32698"),
            (50013, 4, "32698"),
            (50013, 6, "NYH Lab Procedure: Sodium"),
            (50228, 150, "19928"),
            (50228, 150, "3668"),
            (50228, 212, ""),
            (50228, 266, ""),
            (50228, 277, ""),
            (50228, 3, "32180"),
            (50228, 4, "32180"),
            (50228, 6, "NYH Lab Procedure: Sodium , W/B"),
            (56253, 150, "19928"),
            (56253, 150, "3668"),
            (56253, 20, "SOD"),
            (56253, 212, "2951-2"),
            (56253, 266, ""),
            (56253, 277, ""),
            (56253, 3, "32698"),
            (56253, 4, "32698"),
            (56253, 6, "CPMC Laboratory Test: Serum Sodium Measurement"),
            (56253, 9, "SOD"),
            (59949, 150, "19928"),
            (59949, 150, "3668"),
            (59949, 20, "ISNA"),
            (59949, 212, "32717-1"),
            (59949, 266, ""),
            (59949, 277, ""),
            (59949, 3, "32180"),
            (59949, 4, "32180"),
            (59949, 6, "CPMC Laboratory Test: Sodium Istat"),
            (59949, 9, "ISNA"),
            (66253, 150, "19928"),
            (66253, 150, "3668"),
            (66253, 20, "NAM"),
            (66253, 212, "2947-0"),
            (66253, 266, ""),
            (66253, 277, ""),
            (66253, 3, "32180"),
            (66253, 4, "32180"),
            (66253, 6, "CPMC Laboratory Test: Sodium Whole Blood (2)"),
            (66253, 9, "NAM"),
            (66254, 150, "19928"),
            (66254, 150, "3668"),
            (66254, 20, "NAMZ"),
            (66254, 212, "2947-0"),
            (66254, 266, ""),
            (66254, 277, ""),
            (66254, 3, "32180"),
            (66254, 4, "32180"),
            (66254, 6, "CPMC Laboratory Test: Sodium Whole Blood (allen)"),
            (66254, 9, "NAMZ"),
            (100031, 150, "19928"),
            (100031, 150, "3668"),
            (100031, 212, "2951-2"),
            (100031, 264, "317298"),
            (100031, 266, ""),
            (100031, 277, "29512"),
            (100031, 3, "32698"),
            (100031, 4, "32698"),
            (100031, 6, "BKR (CM) RESULT: SODIUM LEVEL"),
            (111465, 150, "19928"),
            (111465, 150, "3668"),
            (111465, 212, "2947-0"),
            (111465, 264, "4272034"),
            (111465, 266, ""),
            (111465, 277, "5658"),
            (111465, 3, "32180"),
            (111465, 4, "32180"),
            (111465, 6, "BKR (CM) Result: Sodium Whole Blood POC"),
            (112423, 150, "19928"),
            (112423, 150, "3668"),
            (112423, 212, "2947-0"),
            (112423, 264, "4329535"),
            (112423, 266, ""),
            (112423, 277, "29470"),
            (112423, 3, "32180"),
            (112423, 4, "32180"),
            (112423, 6, "BKR (CM) Result: Sodium WB"),
            (125598, 150, "19928"),
            (125598, 150, "3668"),
            (125598, 212, "2947-0"),
            (125598, 264, "7853268"),
            (125598, 266, ""),
            (125598, 277, "6484"),
            (125598, 3, "32180"),
            (125598, 4, "32180"),
            (125598, 6, "BKR (CM) Result: Sodium W/B - EPOC"),
            (128428, 150, "19928"),
            (128428, 150, "3668"),
            (128428, 20, "EPNA"),
            (128428, 212, ""),
            (128428, 266, ""),
            (128428, 277, ""),
            (128428, 3, "32180"),
            (128428, 4, "32180"),
            (128428, 6, "CPMC Laboratory Test: Sodium Whole Blood POC"),
            (129704, 150, "19928"),
            (129704, 150, "3668"),
            (129704, 212, "32717-1"),
            (129704, 264, "11682263"),
            (129704, 266, ""),
            (129704, 277, "21027"),
            (129704, 3, "32180"),
            (129704, 4, "32180"),
            (129704, 6, "BKR (CM) Result: Sodium BGA"),
            (129713, 150, "19928"),
            (129713, 150, "3668"),
            (129713, 212, "39791-9"),
            (129713, 264, "11682403"),
            (129713, 266, ""),
            (129713, 277, "21035"),
            (129713, 3, "169652"),
            (129713, 3, "32180"),
            (129713, 4, "169652"),
            (129713, 6, "BKR (CM) Result: Sodium BGV"),
            (133171, 150, "19928"),
            (133171, 150, "3668"),
            (133171, 212, "2947-0"),
            (133171, 264, "18710951"),
            (133171, 266, ""),
            (133171, 277, "21189"),
            (133171, 3, "32180"),
            (133171, 4, "32180"),
            (133171, 6, "BKR (CM) Result: Sodium POC IL"),
            (169623, 150, "19928"),
            (169623, 150, "3668"),
            (169623, 212, "2947-0"),
            (169623, 264, "72986158"),
            (169623, 266, ""),
            (169623, 277, "22319"),
            (169623, 3, "169652"),
            (169623, 3, "32180"),
            (169623, 4, "169652"),
            (169623, 6, "Cerner ME DTA: Sodium POC"),
            (169652, 150, "19928"),
            (169652, 150, "3668"),
            (169652, 212, ""),
            (169652, 266, ""),
            (169652, 277, ""),
            (169652, 3, "32180"),
            (169652, 4, "32180"),
            (169652, 6, "Venous Blood Sodium Tests"),
            (170063, 150, "19928"),
            (170063, 150, "3668"),
            (170063, 212, "2951-2"),
            (170063, 266, ""),
            (170063, 277, ""),
            (170063, 3, "32698"),
            (170063, 4, "32698"),
            (170063, 6, "Meditech Result: SODIUM"),
            (181985, 150, "19928"),
            (181985, 150, "3668"),
            (181985, 212, "2951-2"),
            (181985, 266, ""),
            (181985, 277, ""),
            (181985, 3, "32698"),
            (181985, 4, "32698"),
            (181985, 6, "LabCorp Result: Sodium, Serum (1198)"),
            (197005, 150, "19928"),
            (197005, 150, "3668"),
            (197005, 212, "2951-2"),
            (197005, 266, ""),
            (197005, 277, ""),
            (197005, 3, "32698"),
            (197005, 4, "32698"),
            (197005, 6, "LabCorp Result: Sodium, Serum (132258)"),
            (201232, 150, "19928"),
            (201232, 150, "3668"),
            (201232, 212, "2951-2"),
            (201232, 266, ""),
            (201232, 277, ""),
            (201232, 3, "32698"),
            (201232, 4, "32698"),
            (201232, 6, "Meditech Order: Sodium (Retired)"),
            (228458, 150, "19928"),
            (228458, 150, "3668"),
            (228458, 212, "2951-2"),
            (228458, 266, ""),
            (228458, 277, ""),
            (228458, 3, "32698"),
            (228458, 4, "32698"),
            (228458, 6, "Quest Result: SODIUM"),
        ]
        
        # Insert data in batches
        insert_sql = "INSERT INTO MED (CODE, SLOT_NUMBER, SLOT_VALUE) VALUES (?, ?, ?)"
        
        row_count = 0
        for code, slot_num, slot_val in data:
            cursor.execute(insert_sql, str(code), slot_num, str(slot_val))
            row_count += 1
            if row_count % 50 == 0:
                print(f"  Inserted {row_count} rows...")
        
        conn.commit()
        
        print(f"\n✅ Successfully inserted {row_count} rows")
        
        # Verify the data
        print("\n" + "="*80)
        print("🔍 Verifying data...")
        print("="*80)
        
        cursor.execute("SELECT COUNT(*) FROM MED")
        total = cursor.fetchone()[0]
        print(f"Total rows in MED table: {total}")
        
        cursor.execute("SELECT COUNT(DISTINCT CODE) FROM MED")
        unique_codes = cursor.fetchone()[0]
        print(f"Unique CODE values: {unique_codes}")
        
        cursor.execute("SELECT COUNT(DISTINCT SLOT_NUMBER) FROM MED")
        unique_slots = cursor.fetchone()[0]
        print(f"Unique SLOT_NUMBER values: {unique_slots}")
        
        # Show sample data
        print("\n" + "="*80)
        print("📋 Sample data (first 10 rows):")
        print("="*80)
        cursor.execute("SELECT TOP 10 * FROM MED ORDER BY CODE, SLOT_NUMBER")
        rows = cursor.fetchall()
        print(f"\n{'CODE':<15} {'SLOT_NUMBER':<15} {'SLOT_VALUE':<50}")
        print("-" * 80)
        for row in rows:
            print(f"{row[0]:<15} {row[1]:<15} {row[2]:<50}")
        
        conn.close()
        
        print("\n" + "="*80)
        print("✅ MED table recreated successfully!")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    recreate_med_table()
