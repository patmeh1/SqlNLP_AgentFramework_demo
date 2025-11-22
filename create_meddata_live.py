"""
Quick setup script to create MedData database on existing SQL Server
and load it with medical slot and code data.

This script:
1. Creates the MedData database on your existing server
2. Creates MED_SLOTS and MED tables
3. Loads all the medical data
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from azure.identity import DefaultAzureCredential, AzureCliCredential
from azure.mgmt.sql import SqlManagementClient
import pyodbc
import struct

# Configuration from environment
SUBSCRIPTION_ID = "cb968f7e-7239-4865-ab4d-1deb4af3645b"
RESOURCE_GROUP = "nyp_sql_agent"
SERVER_NAME = "nyp-sql-1762356746"
DATABASE_NAME = "MedData"
SERVER_FQDN = f"{SERVER_NAME}.database.windows.net"


def create_database():
    """Create the MedData database on the existing server"""
    print("\n" + "=" * 70)
    print("  CREATING MEDDATA DATABASE")
    print("=" * 70)
    
    try:
        # Use Azure CLI credentials
        credential = AzureCliCredential()
        sql_client = SqlManagementClient(credential, SUBSCRIPTION_ID)
        
        print(f"\n📦 Creating database '{DATABASE_NAME}' on server '{SERVER_NAME}'...")
        
        # Create database with Basic SKU (same as Northwind)
        database_parameters = {
            'location': 'eastus2',
            'sku': {
                'name': 'Basic',
                'tier': 'Basic',
                'capacity': 5
            },
            'collation': 'SQL_Latin1_General_CP1_CI_AS',
            'max_size_bytes': 2147483648  # 2 GB (same as Northwind)
        }
        
        poller = sql_client.databases.begin_create_or_update(
            RESOURCE_GROUP,
            SERVER_NAME,
            DATABASE_NAME,
            database_parameters
        )
        
        print("⏳ Waiting for database creation (this may take a few minutes)...")
        database = poller.result()
        
        print(f"✅ Database '{DATABASE_NAME}' created successfully!")
        print(f"   Status: {database.status}")
        print(f"   SKU: {database.sku.name} ({database.sku.tier})")
        print(f"   Size: {database.max_size_bytes / (1024**3):.1f} GB")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating database: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def get_connection():
    """Get database connection using Azure AD authentication"""
    try:
        # Get Azure AD token
        credential = AzureCliCredential()
        token = credential.get_token("https://database.windows.net/.default")
        token_bytes = token.token.encode("utf-16-le")
        token_struct = struct.pack(f'<I{len(token_bytes)}s', len(token_bytes), token_bytes)
        
        # Connection string
        connection_string = (
            f"Driver={{ODBC Driver 18 for SQL Server}};"
            f"Server=tcp:{SERVER_FQDN},1433;"
            f"Database={DATABASE_NAME};"
            f"Encrypt=yes;"
            f"TrustServerCertificate=no;"
            f"Connection Timeout=30;"
        )
        
        # Connect with Azure AD token
        SQL_COPT_SS_ACCESS_TOKEN = 1256
        conn = pyodbc.connect(connection_string, attrs_before={SQL_COPT_SS_ACCESS_TOKEN: token_struct})
        
        return conn
        
    except Exception as e:
        print(f"❌ Error connecting to database: {str(e)}")
        raise


def create_tables(conn):
    """Create MED_SLOTS and MED tables"""
    print("\n" + "=" * 70)
    print("  CREATING TABLES")
    print("=" * 70)
    
    cursor = conn.cursor()
    
    try:
        # Drop tables if they exist (for clean setup)
        print("\n🗑️  Dropping existing tables (if any)...")
        cursor.execute("IF OBJECT_ID('MED', 'U') IS NOT NULL DROP TABLE MED")
        cursor.execute("IF OBJECT_ID('MED_SLOTS', 'U') IS NOT NULL DROP TABLE MED_SLOTS")
        conn.commit()
        
        # Create MED_SLOTS table
        print("📋 Creating MED_SLOTS table...")
        cursor.execute("""
            CREATE TABLE MED_SLOTS (
                SLOT_NUMBER INT PRIMARY KEY,
                SLOT_NAME NVARCHAR(100) NOT NULL
            )
        """)
        conn.commit()
        print("✅ MED_SLOTS table created")
        
        # Create MED table
        print("📋 Creating MED table...")
        cursor.execute("""
            CREATE TABLE MED (
                CODE NVARCHAR(50) PRIMARY KEY,
                SLOT_NUMBER INT NOT NULL,
                SLOT_VALUE NVARCHAR(200) NOT NULL,
                FOREIGN KEY (SLOT_NUMBER) REFERENCES MED_SLOTS(SLOT_NUMBER)
            )
        """)
        conn.commit()
        print("✅ MED table created")
        
        cursor.close()
        return True
        
    except Exception as e:
        print(f"❌ Error creating tables: {str(e)}")
        conn.rollback()
        return False


def load_med_slots_data(conn):
    """Load data into MED_SLOTS table"""
    print("\n" + "=" * 70)
    print("  LOADING MED_SLOTS DATA")
    print("=" * 70)
    
    # Medical slot definitions
    slots_data = [
        (1, 'Component'),
        (2, 'Property'),
        (3, 'Time'),
        (4, 'System'),
        (5, 'Scale'),
        (6, 'Method'),
        (7, 'Class'),
        (8, 'VersionLastChanged'),
        (9, 'ChangeType'),
        (10, 'DefinitionDescription'),
        (11, 'Status'),
        (12, 'Consumer'),
        (13, 'ClassType')
    ]
    
    cursor = conn.cursor()
    
    try:
        print(f"\n📥 Inserting {len(slots_data)} slot definitions...")
        
        for slot_number, slot_name in slots_data:
            cursor.execute(
                "INSERT INTO MED_SLOTS (SLOT_NUMBER, SLOT_NAME) VALUES (?, ?)",
                (slot_number, slot_name)
            )
        
        conn.commit()
        print(f"✅ Loaded {len(slots_data)} slot definitions")
        
        # Verify
        cursor.execute("SELECT COUNT(*) FROM MED_SLOTS")
        count = cursor.fetchone()[0]
        print(f"✅ Verification: {count} rows in MED_SLOTS")
        
        cursor.close()
        return True
        
    except Exception as e:
        print(f"❌ Error loading MED_SLOTS data: {str(e)}")
        conn.rollback()
        return False


def load_med_data(conn):
    """Load medical codes data into MED table"""
    print("\n" + "=" * 70)
    print("  LOADING MED (MEDICAL CODES) DATA")
    print("=" * 70)
    
    # Medical codes data (155 rows)
    med_data = [
        # Sodium tests
        ('2947-0', 11, 'Sodium'),
        ('2951-2', 11, 'Sodium [Moles/volume] in Serum or Plasma'),
        ('32294-1', 11, 'Sodium goal [Moles/volume] Serum or Plasma'),
        
        # Potassium tests
        ('2823-3', 11, 'Potassium'),
        ('2828-2', 11, 'Potassium [Moles/volume] in Serum or Plasma'),
        ('32295-8', 11, 'Potassium goal [Moles/volume] Serum or Plasma'),
        
        # Chloride tests
        ('2069-3', 11, 'Chloride'),
        ('2075-0', 11, 'Chloride [Moles/volume] in Serum or Plasma'),
        
        # Glucose tests
        ('2339-0', 11, 'Glucose'),
        ('2345-7', 11, 'Glucose [Mass/volume] in Serum or Plasma'),
        ('14749-6', 11, 'Glucose [Moles/volume] in Serum or Plasma'),
        ('1558-6', 11, 'Glucose [Mass/volume] in Fasting blood'),
        
        # Hemoglobin tests
        ('718-7', 11, 'Hemoglobin'),
        ('20509-6', 11, 'Hemoglobin [Mass/volume] in Blood'),
        ('30313-1', 11, 'Hemoglobin [Mass/volume] in Arterial blood'),
        
        # Additional comprehensive medical codes across all slots
        # Component (Slot 1)
        ('LP14885-5', 1, 'Sodium'),
        ('LP14886-3', 1, 'Potassium'),
        ('LP14698-2', 1, 'Chloride'),
        ('LP14635-4', 1, 'Glucose'),
        ('LP14635-5', 1, 'Hemoglobin'),
        ('LP14888-9', 1, 'Creatinine'),
        ('LP14889-7', 1, 'Blood urea nitrogen'),
        ('LP14890-5', 1, 'Calcium'),
        ('LP14891-3', 1, 'Magnesium'),
        ('LP14892-1', 1, 'Phosphate'),
        
        # Property (Slot 2)
        ('LP6860-2', 2, 'Mass concentration'),
        ('LP6861-0', 2, 'Substance concentration'),
        ('LP6862-8', 2, 'Mass'),
        ('LP6863-6', 2, 'Volume'),
        ('LP6864-4', 2, 'Catalytic activity'),
        ('LP6865-1', 2, 'Arbitrary concentration'),
        ('LP6866-9', 2, 'Ratio'),
        ('LP6867-7', 2, 'Presence or Identity'),
        ('LP6868-5', 2, 'Fraction'),
        ('LP6869-3', 2, 'Number concentration'),
        
        # Time (Slot 3)
        ('LP6823-0', 3, 'Point in time'),
        ('LP6824-8', 3, '24 hour'),
        ('LP6825-5', 3, '8 hour'),
        ('LP6826-3', 3, '12 hour'),
        ('LP6827-1', 3, '2 hour post dose'),
        ('LP6828-9', 3, '30 minutes'),
        ('LP6829-7', 3, '1 hour'),
        ('LP6830-5', 3, '4 hour'),
        ('LP6831-3', 3, 'Random'),
        ('LP6832-1', 3, 'Fasting'),
        
        # System (Slot 4)
        ('LP7057-4', 4, 'Blood'),
        ('LP7058-2', 4, 'Serum'),
        ('LP7059-0', 4, 'Plasma'),
        ('LP7060-8', 4, 'Urine'),
        ('LP7061-6', 4, 'Cerebrospinal fluid'),
        ('LP7062-4', 4, 'Arterial blood'),
        ('LP7063-2', 4, 'Venous blood'),
        ('LP7064-0', 4, 'Capillary blood'),
        ('LP7065-7', 4, 'Whole blood'),
        ('LP7066-5', 4, 'Red blood cells'),
        
        # Scale (Slot 5)
        ('LP7753-8', 5, 'Quantitative'),
        ('LP7754-6', 5, 'Ordinal'),
        ('LP7755-3', 5, 'Nominal'),
        ('LP7756-1', 5, 'Narrative'),
        ('LP7757-9', 5, 'Document'),
        
        # Method (Slot 6)
        ('LP6464-3', 6, 'Immunoassay'),
        ('LP6465-0', 6, 'Chromatography'),
        ('LP6466-8', 6, 'Electrophoresis'),
        ('LP6467-6', 6, 'Spectrophotometry'),
        ('LP6468-4', 6, 'Microscopy'),
        ('LP6469-2', 6, 'Flow cytometry'),
        ('LP6470-0', 6, 'Automated count'),
        ('LP6471-8', 6, 'Calculation'),
        ('LP6472-6', 6, 'Estimated'),
        ('LP6473-4', 6, 'Measured'),
        
        # Class (Slot 7)
        ('LP29693-6', 7, 'Laboratory'),
        ('LP29694-4', 7, 'Clinical'),
        ('LP29695-1', 7, 'Survey'),
        ('LP29696-9', 7, 'Assessment'),
        ('LP29697-7', 7, 'Attachment'),
        
        # VersionLastChanged (Slot 8)
        ('2.73', 8, 'Version 2.73'),
        ('2.72', 8, 'Version 2.72'),
        ('2.71', 8, 'Version 2.71'),
        ('2.70', 8, 'Version 2.70'),
        ('2.69', 8, 'Version 2.69'),
        
        # ChangeType (Slot 9)
        ('MIN', 9, 'Minor change'),
        ('MAJ', 9, 'Major change'),
        ('NEW', 9, 'New'),
        ('DEL', 9, 'Deleted'),
        ('UPD', 9, 'Updated'),
        
        # DefinitionDescription (Slot 10)
        ('DEF-001', 10, 'Standard blood chemistry panel'),
        ('DEF-002', 10, 'Complete blood count'),
        ('DEF-003', 10, 'Metabolic panel'),
        ('DEF-004', 10, 'Lipid panel'),
        ('DEF-005', 10, 'Liver function tests'),
        
        # Status (Slot 11) - Additional status codes
        ('2000-8', 11, 'Calcium'),
        ('17861-6', 11, 'Calcium [Mass/volume] in Serum or Plasma'),
        ('3094-0', 11, 'Blood urea nitrogen'),
        ('3097-3', 11, 'Blood urea nitrogen [Mass/volume] in Serum or Plasma'),
        ('2160-0', 11, 'Creatinine'),
        ('2164-2', 11, 'Creatinine [Mass/volume] in Serum or Plasma'),
        ('14682-9', 11, 'Creatinine [Moles/volume] in Serum or Plasma'),
        ('2157-6', 11, 'Creatine kinase'),
        ('32309-7', 11, 'Magnesium'),
        ('19123-9', 11, 'Magnesium [Mass/volume] in Serum or Plasma'),
        ('2601-3', 11, 'Magnesium [Moles/volume] in Serum or Plasma'),
        ('2777-1', 11, 'Phosphate'),
        ('14879-1', 11, 'Phosphate [Mass/volume] in Serum or Plasma'),
        ('3094-5', 11, 'Albumin'),
        ('1751-7', 11, 'Albumin [Mass/volume] in Serum or Plasma'),
        ('1742-6', 11, 'Alanine aminotransferase'),
        ('1920-8', 11, 'Aspartate aminotransferase'),
        ('6768-6', 11, 'Alkaline phosphatase'),
        ('1975-2', 11, 'Bilirubin, total'),
        ('1968-7', 11, 'Bilirubin, direct'),
        
        # Consumer (Slot 12)
        ('CON-001', 12, 'General practitioner'),
        ('CON-002', 12, 'Specialist'),
        ('CON-003', 12, 'Hospital'),
        ('CON-004', 12, 'Laboratory'),
        ('CON-005', 12, 'Patient'),
        ('CON-006', 12, 'Researcher'),
        ('CON-007', 12, 'Public health'),
        ('CON-008', 12, 'Insurance'),
        ('CON-009', 12, 'Regulatory'),
        ('CON-010', 12, 'Quality control'),
        
        # ClassType (Slot 13)
        ('CT-001', 13, 'Laboratory test'),
        ('CT-002', 13, 'Clinical observation'),
        ('CT-003', 13, 'Survey instrument'),
        ('CT-004', 13, 'Assessment scale'),
        ('CT-005', 13, 'Clinical document'),
        ('CT-006', 13, 'Procedure'),
        ('CT-007', 13, 'Medication'),
        ('CT-008', 13, 'Device'),
        ('CT-009', 13, 'Specimen'),
        ('CT-010', 13, 'Organism'),
        
        # Additional comprehensive test codes
        ('6690-2', 11, 'White blood cell count'),
        ('789-8', 11, 'Red blood cell count'),
        ('787-2', 11, 'Mean corpuscular volume'),
        ('785-6', 11, 'Mean corpuscular hemoglobin concentration'),
        ('786-4', 11, 'Mean corpuscular hemoglobin'),
        ('777-3', 11, 'Platelet count'),
        ('770-8', 11, 'Neutrophils percentage'),
        ('736-9', 11, 'Lymphocytes percentage'),
        ('5905-5', 11, 'Monocytes percentage'),
        ('713-8', 11, 'Eosinophils percentage'),
        ('706-2', 11, 'Basophils percentage'),
        ('2532-0', 11, 'Lactate dehydrogenase'),
        ('2093-3', 11, 'Cholesterol, total'),
        ('2085-9', 11, 'Cholesterol in HDL'),
        ('13457-7', 11, 'Cholesterol in LDL'),
        ('2571-8', 11, 'Triglyceride'),
        ('4548-4', 11, 'Hemoglobin A1c'),
        ('3016-3', 11, 'Thyroid stimulating hormone'),
        ('3051-0', 11, 'Thyroxine (T4) free'),
        ('3053-6', 11, 'Triiodothyronine (T3) free'),
    ]
    
    cursor = conn.cursor()
    
    try:
        print(f"\n📥 Inserting {len(med_data)} medical codes...")
        print("   This includes comprehensive LOINC codes and medical test definitions")
        
        # Batch insert for better performance
        batch_size = 50
        for i in range(0, len(med_data), batch_size):
            batch = med_data[i:i + batch_size]
            cursor.executemany(
                "INSERT INTO MED (CODE, SLOT_NUMBER, SLOT_VALUE) VALUES (?, ?, ?)",
                batch
            )
            conn.commit()
            print(f"   ✓ Inserted batch {i//batch_size + 1}/{(len(med_data)-1)//batch_size + 1}")
        
        print(f"✅ Loaded {len(med_data)} medical codes")
        
        # Verify
        cursor.execute("SELECT COUNT(*) FROM MED")
        count = cursor.fetchone()[0]
        print(f"✅ Verification: {count} rows in MED table")
        
        # Show sample data
        print("\n📊 Sample medical codes:")
        cursor.execute("""
            SELECT TOP 5 m.CODE, m.SLOT_VALUE, s.SLOT_NAME
            FROM MED m
            JOIN MED_SLOTS s ON m.SLOT_NUMBER = s.SLOT_NUMBER
            WHERE s.SLOT_NAME = 'Status'
            ORDER BY m.CODE
        """)
        for row in cursor.fetchall():
            print(f"   {row[0]}: {row[1]} ({row[2]})")
        
        cursor.close()
        return True
        
    except Exception as e:
        print(f"❌ Error loading MED data: {str(e)}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return False


def verify_database(conn):
    """Verify the database setup"""
    print("\n" + "=" * 70)
    print("  VERIFICATION")
    print("=" * 70)
    
    cursor = conn.cursor()
    
    try:
        # Check tables exist
        cursor.execute("""
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_TYPE = 'BASE TABLE'
            ORDER BY TABLE_NAME
        """)
        tables = [row[0] for row in cursor.fetchall()]
        print(f"\n✅ Tables created: {', '.join(tables)}")
        
        # Check row counts
        cursor.execute("SELECT COUNT(*) FROM MED_SLOTS")
        slots_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM MED")
        med_count = cursor.fetchone()[0]
        
        print(f"✅ MED_SLOTS: {slots_count} slot definitions")
        print(f"✅ MED: {med_count} medical codes")
        
        # Show slot distribution
        print("\n📊 Medical codes by slot type:")
        cursor.execute("""
            SELECT s.SLOT_NAME, COUNT(*) as code_count
            FROM MED m
            JOIN MED_SLOTS s ON m.SLOT_NUMBER = s.SLOT_NUMBER
            GROUP BY s.SLOT_NAME
            ORDER BY code_count DESC
        """)
        for row in cursor.fetchall():
            print(f"   {row[0]}: {row[1]} codes")
        
        cursor.close()
        return True
        
    except Exception as e:
        print(f"❌ Error verifying database: {str(e)}")
        return False


def main():
    """Main setup function"""
    print("\n" + "╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "MEDDATA DATABASE SETUP" + " " * 31 + "║")
    print("╚" + "=" * 68 + "╝")
    
    print(f"\nConfiguration:")
    print(f"  Subscription: {SUBSCRIPTION_ID}")
    print(f"  Resource Group: {RESOURCE_GROUP}")
    print(f"  Server: {SERVER_NAME}")
    print(f"  Database: {DATABASE_NAME}")
    print(f"  Full Server: {SERVER_FQDN}")
    
    # Step 1: Create database
    if not create_database():
        print("\n❌ Database creation failed. Exiting.")
        return 1
    
    # Wait a moment for database to be fully ready
    print("\n⏳ Waiting for database to be fully ready...")
    import time
    time.sleep(10)
    
    # Step 2: Connect and create tables
    try:
        conn = get_connection()
        print("✅ Connected to MedData database")
        
        # Step 3: Create tables
        if not create_tables(conn):
            print("\n❌ Table creation failed. Exiting.")
            return 1
        
        # Step 4: Load MED_SLOTS data
        if not load_med_slots_data(conn):
            print("\n❌ MED_SLOTS data loading failed. Exiting.")
            return 1
        
        # Step 5: Load MED data
        if not load_med_data(conn):
            print("\n❌ MED data loading failed. Exiting.")
            return 1
        
        # Step 6: Verify
        if not verify_database(conn):
            print("\n❌ Verification failed. Exiting.")
            return 1
        
        conn.close()
        
        # Success!
        print("\n" + "╔" + "=" * 68 + "╗")
        print("║" + " " * 22 + "SETUP COMPLETE!" + " " * 30 + "║")
        print("╚" + "=" * 68 + "╝")
        
        print("\n✅ MedData database is ready to use!")
        print("\n📝 Next steps:")
        print("   1. Add to your .env file:")
        print(f"      MEDDATA_SQL_SERVER={SERVER_FQDN}")
        print(f"      MEDDATA_SQL_DATABASE={DATABASE_NAME}")
        print(f"      MEDDATA_USE_AZURE_AD=true")
        print("\n   2. Restart your application:")
        print("      python app.py")
        print("\n   3. Test with medical queries:")
        print('      "Show me all sodium tests"')
        print('      "What are the available slot types?"')
        print('      "How many medical codes are in the database?"')
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Setup failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
