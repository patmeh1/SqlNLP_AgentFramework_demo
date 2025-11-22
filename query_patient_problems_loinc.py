"""
Query to find Patient Problems (by name and SNOMED code) for all tests with LOINC code 2947-0
"""

import pyodbc
import struct
from azure.identity import AzureCliCredential
from dotenv import load_dotenv
import os

load_dotenv()

def query_patient_problems_for_loinc():
    """Find patient problems for tests with LOINC 2947-0."""
    
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
        
        print("=" * 120)
        print("PATIENT PROBLEMS FOR TESTS WITH LOINC CODE 2947-0")
        print("=" * 120)
        print()
        
        # Step 1: Find all test codes that have LOINC 2947-0
        print("Step 1: Finding all tests with LOINC code 2947-0...")
        print()
        
        query_tests = """
        SELECT DISTINCT m1.CODE, m2.SLOT_VALUE as TEST_NAME
        FROM MED m1
        LEFT JOIN MED m2 ON m1.CODE = m2.CODE AND m2.SLOT_NUMBER = 6  -- PRINT-NAME
        WHERE m1.SLOT_NUMBER = 212  -- LOINC-CODE
        AND m1.SLOT_VALUE = '2947-0'
        """
        
        cursor.execute(query_tests)
        test_codes = cursor.fetchall()
        
        print(f"Found {len(test_codes)} test(s) with LOINC 2947-0:\n")
        for code, name in test_codes:
            print(f"  - Code {code}: {name}")
        print()
        
        # Step 2: Find patient problems indicated by these tests
        print("=" * 120)
        print("Step 2: Finding Patient Problems indicated by these tests...")
        print("=" * 120)
        print()
        
        # Get all problem codes from slot 150
        test_code_list = ','.join([f"'{code}'" for code, _ in test_codes])
        
        query_problems = f"""
        SELECT DISTINCT 
            m1.CODE as TEST_CODE,
            test_name.SLOT_VALUE as TEST_NAME,
            m1.SLOT_VALUE as PROBLEM_CODE,
            problem_name.SLOT_VALUE as PROBLEM_NAME,
            problem_snomed.SLOT_VALUE as PROBLEM_SNOMED
        FROM MED m1
        LEFT JOIN MED test_name ON m1.CODE = test_name.CODE AND test_name.SLOT_NUMBER = 6
        LEFT JOIN MED problem_name ON m1.SLOT_VALUE = problem_name.CODE AND problem_name.SLOT_NUMBER = 6
        LEFT JOIN MED problem_snomed ON m1.SLOT_VALUE = problem_snomed.CODE AND problem_snomed.SLOT_NUMBER = 266
        WHERE m1.SLOT_NUMBER = 150  -- PROCEDURE-(INDICATES)->PT-PROBLEM
        AND m1.CODE IN ({test_code_list})
        ORDER BY m1.SLOT_VALUE, m1.CODE
        """
        
        cursor.execute(query_problems)
        problems = cursor.fetchall()
        
        if not problems:
            print("⚠️  No patient problems found for these tests.")
        else:
            print(f"{'TEST CODE':<12} {'TEST NAME':<45} {'PROBLEM CODE':<15} {'PROBLEM NAME':<40} {'SNOMED':<15}")
            print("-" * 120)
            
            for test_code, test_name, prob_code, prob_name, prob_snomed in problems:
                test_code_str = test_code or ''
                test_name_str = (test_name or '')[:44]
                prob_code_str = prob_code or ''
                prob_name_str = (prob_name or '')[:39]
                prob_snomed_str = prob_snomed or 'N/A'
                
                print(f"{test_code_str:<12} {test_name_str:<45} {prob_code_str:<15} {prob_name_str:<40} {prob_snomed_str:<15}")
            
            print("-" * 120)
            print(f"\nTotal patient problem associations found: {len(problems)}")
        
        # Step 3: Summary of unique patient problems
        print()
        print("=" * 120)
        print("SUMMARY: Unique Patient Problems")
        print("=" * 120)
        print()
        
        query_unique = f"""
        SELECT DISTINCT 
            m1.SLOT_VALUE as PROBLEM_CODE,
            problem_name.SLOT_VALUE as PROBLEM_NAME,
            problem_snomed.SLOT_VALUE as PROBLEM_SNOMED
        FROM MED m1
        LEFT JOIN MED problem_name ON m1.SLOT_VALUE = problem_name.CODE AND problem_name.SLOT_NUMBER = 6
        LEFT JOIN MED problem_snomed ON m1.SLOT_VALUE = problem_snomed.CODE AND problem_snomed.SLOT_NUMBER = 266
        WHERE m1.SLOT_NUMBER = 150  -- PROCEDURE-(INDICATES)->PT-PROBLEM
        AND m1.CODE IN ({test_code_list})
        ORDER BY m1.SLOT_VALUE
        """
        
        cursor.execute(query_unique)
        unique_problems = cursor.fetchall()
        
        print(f"{'PROBLEM CODE':<15} {'PROBLEM NAME':<60} {'SNOMED CODE':<15}")
        print("-" * 95)
        
        for prob_code, prob_name, prob_snomed in unique_problems:
            prob_code_str = prob_code or ''
            prob_name_str = (prob_name or '')[:59]
            prob_snomed_str = prob_snomed or 'N/A'
            
            print(f"{prob_code_str:<15} {prob_name_str:<60} {prob_snomed_str:<15}")
        
        print("-" * 95)
        print(f"\nTotal unique patient problems: {len(unique_problems)}")
        
        conn.close()
        print("\n✅ Query completed successfully")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    query_patient_problems_for_loinc()
