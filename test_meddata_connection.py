"""
Test MedData database connection and verify it uses Azure AD authentication
similar to the Northwind database.

This script:
1. Checks if MedData is configured
2. Verifies authentication method (Azure AD vs SQL Auth)
3. Tests database connection
4. Executes sample queries
5. Compares with Northwind configuration
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sql_agent import SQLAgent
from agents.create_meddata_agent import is_meddata_configured, create_meddata_agent_from_env


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_northwind_config():
    """Display Northwind database configuration."""
    print_section("NORTHWIND DATABASE CONFIGURATION")
    
    sql_server = os.getenv('SQL_SERVER')
    sql_database = os.getenv('SQL_DATABASE', 'Northwind')
    sql_username = os.getenv('SQL_USERNAME')
    sql_password = os.getenv('SQL_PASSWORD')
    use_azure_ad_str = os.getenv('USE_AZURE_AD', 'true').lower()
    use_azure_ad = use_azure_ad_str in ('true', '1', 'yes')
    
    print(f"Server:   {sql_server or 'NOT SET'}")
    print(f"Database: {sql_database}")
    print(f"Auth:     {'Azure AD (Windows Authentication)' if use_azure_ad else 'SQL Authentication'}")
    
    if not use_azure_ad:
        print(f"Username: {sql_username or 'NOT SET'}")
        print(f"Password: {'***' if sql_password else 'NOT SET'}")
    
    return {
        'server': sql_server,
        'database': sql_database,
        'use_azure_ad': use_azure_ad
    }


def test_meddata_config():
    """Display MedData database configuration."""
    print_section("MEDDATA DATABASE CONFIGURATION")
    
    if not is_meddata_configured():
        print("❌ MedData is NOT configured")
        print("\nTo configure MedData, add these variables to your .env file:")
        print("  MEDDATA_SQL_SERVER=your-server.database.windows.net")
        print("  MEDDATA_SQL_DATABASE=MedData")
        print("  MEDDATA_USE_AZURE_AD=true")
        return None
    
    sql_server = os.getenv('MEDDATA_SQL_SERVER')
    sql_database = os.getenv('MEDDATA_SQL_DATABASE', 'MedData')
    sql_username = os.getenv('MEDDATA_SQL_USERNAME')
    sql_password = os.getenv('MEDDATA_SQL_PASSWORD')
    use_azure_ad_str = os.getenv('MEDDATA_USE_AZURE_AD', 'true').lower()
    use_azure_ad = use_azure_ad_str in ('true', '1', 'yes')
    
    print(f"✅ MedData IS configured")
    print(f"\nServer:   {sql_server}")
    print(f"Database: {sql_database}")
    print(f"Auth:     {'Azure AD (Windows Authentication)' if use_azure_ad else 'SQL Authentication'}")
    
    if not use_azure_ad:
        print(f"Username: {sql_username or 'NOT SET'}")
        print(f"Password: {'***' if sql_password else 'NOT SET'}")
    
    return {
        'server': sql_server,
        'database': sql_database,
        'use_azure_ad': use_azure_ad
    }


def compare_configs(northwind_config, meddata_config):
    """Compare Northwind and MedData configurations."""
    print_section("CONFIGURATION COMPARISON")
    
    if not meddata_config:
        print("⚠️  Cannot compare - MedData not configured")
        return
    
    print(f"{'Aspect':<20} {'Northwind':<30} {'MedData':<30}")
    print("-" * 80)
    
    # Server
    server_match = "✅ Different servers" if northwind_config['server'] != meddata_config['server'] else "⚠️  Same server"
    print(f"{'Server':<20} {northwind_config['server'] or 'N/A':<30} {meddata_config['server']:<30}")
    print(f"{'':<20} {server_match}")
    print()
    
    # Database
    db_match = "✅ Different databases" if northwind_config['database'] != meddata_config['database'] else "⚠️  Same database"
    print(f"{'Database':<20} {northwind_config['database']:<30} {meddata_config['database']:<30}")
    print(f"{'':<20} {db_match}")
    print()
    
    # Authentication
    auth_northwind = "Azure AD" if northwind_config['use_azure_ad'] else "SQL Auth"
    auth_meddata = "Azure AD" if meddata_config['use_azure_ad'] else "SQL Auth"
    auth_match = "✅ SAME AUTH METHOD" if northwind_config['use_azure_ad'] == meddata_config['use_azure_ad'] else "⚠️  Different auth methods"
    print(f"{'Authentication':<20} {auth_northwind:<30} {auth_meddata:<30}")
    print(f"{'':<20} {auth_match}")
    
    # Summary
    print("\n" + "-" * 80)
    if northwind_config['use_azure_ad'] and meddata_config['use_azure_ad']:
        print("✅ BOTH databases use Azure AD (Windows Authentication)")
        print("   This provides integrated security without storing passwords")
    elif not northwind_config['use_azure_ad'] and not meddata_config['use_azure_ad']:
        print("✅ BOTH databases use SQL Authentication")
    else:
        print("⚠️  Databases use DIFFERENT authentication methods")


def test_meddata_connection():
    """Test actual connection to MedData database."""
    print_section("MEDDATA CONNECTION TEST")
    
    if not is_meddata_configured():
        print("⚠️  Skipping connection test - MedData not configured")
        return False
    
    try:
        print("Creating MedData agent...")
        meddata_agent = create_meddata_agent_from_env()
        print("✅ MedData agent created successfully")
        
        # Access the underlying SQL agent
        sql_agent = meddata_agent.sql_agent
        
        print("\nTesting database connection...")
        conn = sql_agent._get_connection()
        cursor = conn.cursor()
        
        # Test 1: Check database name
        cursor.execute("SELECT DB_NAME()")
        db_name = cursor.fetchone()[0]
        print(f"✅ Connected to database: {db_name}")
        
        # Test 2: Check authentication method
        cursor.execute("SELECT SUSER_NAME(), SYSTEM_USER")
        user_info = cursor.fetchone()
        print(f"✅ Current user: {user_info[0]}")
        print(f"   System user: {user_info[1]}")
        
        # Test 3: List tables
        cursor.execute("""
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_TYPE = 'BASE TABLE'
            ORDER BY TABLE_NAME
        """)
        tables = [row[0] for row in cursor.fetchall()]
        print(f"✅ Found {len(tables)} tables: {', '.join(tables)}")
        
        # Test 4: Query MED_SLOTS
        if 'MED_SLOTS' in tables:
            cursor.execute("SELECT COUNT(*) FROM MED_SLOTS")
            count = cursor.fetchone()[0]
            print(f"✅ MED_SLOTS table has {count} rows")
            
            # Get sample data
            cursor.execute("SELECT TOP 3 SLOT_NUMBER, SLOT_NAME FROM MED_SLOTS ORDER BY SLOT_NUMBER")
            print(f"   Sample slots:")
            for row in cursor.fetchall():
                print(f"     {row[0]}: {row[1]}")
        
        # Test 5: Query MED
        if 'MED' in tables:
            cursor.execute("SELECT COUNT(*) FROM MED")
            count = cursor.fetchone()[0]
            print(f"✅ MED table has {count} rows")
            
            # Get sample data
            cursor.execute("SELECT TOP 3 CODE, SLOT_NUMBER, SLOT_VALUE FROM MED ORDER BY CODE")
            print(f"   Sample medical codes:")
            for row in cursor.fetchall():
                print(f"     {row[0]} - Slot {row[1]}: {row[2]}")
        
        cursor.close()
        conn.close()
        
        print("\n✅ All connection tests PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Connection test FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_meddata_query():
    """Test querying MedData through the agent."""
    print_section("MEDDATA AGENT QUERY TEST")
    
    if not is_meddata_configured():
        print("⚠️  Skipping query test - MedData not configured")
        return False
    
    try:
        print("Creating MedData agent...")
        meddata_agent = create_meddata_agent_from_env()
        
        # Test natural language query
        import asyncio
        
        async def run_query():
            print("\nExecuting query: 'How many medical codes are in the database?'")
            result = await meddata_agent.process_query("How many medical codes are in the database?")
            
            print(f"\nSQL Generated: {result.get('sql', 'N/A')}")
            print(f"Success: {result.get('success', False)}")
            
            if result.get('success'):
                print(f"✅ Response: {result.get('response', 'No response')}")
            else:
                print(f"❌ Error: {result.get('error', 'Unknown error')}")
            
            return result.get('success', False)
        
        success = asyncio.run(run_query())
        return success
        
    except Exception as e:
        print(f"\n❌ Query test FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main test function."""
    print("\n" + "╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "MEDDATA DATABASE VERIFICATION" + " " * 23 + "║")
    print("╚" + "=" * 68 + "╝")
    
    # Test 1: Show configurations
    northwind_config = test_northwind_config()
    meddata_config = test_meddata_config()
    
    # Test 2: Compare configurations
    compare_configs(northwind_config, meddata_config)
    
    # Test 3: Test connection
    if meddata_config:
        connection_ok = test_meddata_connection()
        
        # Test 4: Test query
        if connection_ok:
            test_meddata_query()
    
    # Summary
    print_section("VERIFICATION SUMMARY")
    
    if not meddata_config:
        print("❌ MedData is NOT configured")
        print("\n📝 To configure MedData with Windows Authentication (like Northwind):")
        print("   Add to your .env file:")
        print("   MEDDATA_SQL_SERVER=your-server.database.windows.net")
        print("   MEDDATA_SQL_DATABASE=MedData")
        print("   MEDDATA_USE_AZURE_AD=true")
        print("\n   Then run: python scripts/setup_meddata_database.py")
    else:
        if northwind_config['use_azure_ad'] and meddata_config['use_azure_ad']:
            print("✅ MedData uses Azure AD authentication (Windows Authentication)")
            print("✅ This matches the Northwind database configuration")
            print("✅ Both databases use integrated security")
        elif not meddata_config['use_azure_ad']:
            print("⚠️  MedData uses SQL Authentication")
            print("   To use Windows Authentication like Northwind, set:")
            print("   MEDDATA_USE_AZURE_AD=true")
        
        print("\n📊 Database Status:")
        print(f"   Northwind: {northwind_config['database']} on {northwind_config['server'] or 'N/A'}")
        print(f"   MedData:   {meddata_config['database']} on {meddata_config['server']}")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
