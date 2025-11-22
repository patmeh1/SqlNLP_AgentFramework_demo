"""
Check which Azure AD user is connecting to SQL databases
"""
import pyodbc
import struct
from azure.identity import AzureCliCredential

def check_sql_user(server, database):
    """Connect to SQL and check the authenticated user"""
    try:
        # Get Azure AD token (same way as sql_agent.py)
        credential = AzureCliCredential()
        token = credential.get_token("https://database.windows.net/.default")
        token_bytes = token.token.encode("utf-16-le")
        token_struct = struct.pack(f'<I{len(token_bytes)}s', len(token_bytes), token_bytes)
        
        # Build connection string
        connection_string = (
            f"Driver={{ODBC Driver 18 for SQL Server}};"
            f"Server=tcp:{server},1433;"
            f"Database={database};"
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
        
        # Get current user info
        cursor.execute("SELECT SYSTEM_USER, USER_NAME(), SUSER_NAME()")
        row = cursor.fetchone()
        
        print(f"\n{'='*70}")
        print(f"Database: {database}")
        print(f"Server: {server}")
        print(f"{'='*70}")
        print(f"SYSTEM_USER (login):  {row[0]}")
        print(f"USER_NAME() (user):   {row[1]}")
        print(f"SUSER_NAME() (sid):   {row[2]}")
        print(f"{'='*70}\n")
        
        conn.close()
        
    except Exception as e:
        print(f"Error checking {database}: {e}")

if __name__ == "__main__":
    server = "nyp-sql-1762356746.database.windows.net"
    
    print("\n🔍 Checking Azure AD Authentication for SQL Databases\n")
    print(f"Azure CLI User: admin@MngEnvMCAP737206.onmicrosoft.com")
    print(f"Tenant: Contoso (MngEnvMCAP737206.onmicrosoft.com)")
    print(f"Subscription: ME-MngEnvMCAP737206-patmehta-1\n")
    
    # Check both databases
    check_sql_user(server, "Northwind")
    check_sql_user(server, "MedData")
