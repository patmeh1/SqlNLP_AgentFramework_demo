"""
Setup script for MedData Azure SQL Database
Creates database, tables, and loads medical slot and code data
"""

import os
import sys
import pyodbc
from azure.identity import DefaultAzureCredential, ClientSecretCredential
from azure.mgmt.sql import SqlManagementClient
from azure.mgmt.resource import ResourceManagementClient
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MedDataDatabaseSetup:
    """Setup Azure SQL Database for medical data storage"""
    
    def __init__(self, subscription_id, resource_group, server_name, database_name, location='eastus'):
        """
        Initialize the database setup
        
        Args:
            subscription_id: Azure subscription ID
            resource_group: Resource group name
            server_name: SQL Server name
            database_name: Database name (MedData)
            location: Azure region
        """
        self.subscription_id = subscription_id
        self.resource_group = resource_group
        self.server_name = server_name
        self.database_name = database_name
        self.location = location
        
        # Use DefaultAzureCredential for authentication (supports Managed Identity, Azure CLI, etc.)
        self.credential = DefaultAzureCredential()
        
        # Initialize management clients
        self.sql_client = SqlManagementClient(self.credential, self.subscription_id)
        self.resource_client = ResourceManagementClient(self.credential, self.subscription_id)
    
    def create_resource_group(self):
        """Create resource group if it doesn't exist"""
        try:
            logger.info(f"Checking if resource group '{self.resource_group}' exists...")
            self.resource_client.resource_groups.create_or_update(
                self.resource_group,
                {'location': self.location}
            )
            logger.info(f"Resource group '{self.resource_group}' is ready")
        except Exception as e:
            logger.error(f"Error creating resource group: {e}")
            raise
    
    def create_sql_server(self, admin_username, admin_password):
        """
        Create SQL Server if it doesn't exist
        
        Args:
            admin_username: Server admin username
            admin_password: Server admin password
        """
        try:
            logger.info(f"Creating SQL Server '{self.server_name}'...")
            
            server_parameters = {
                'location': self.location,
                'administrator_login': admin_username,
                'administrator_login_password': admin_password,
                'version': '12.0',  # SQL Server 2022
                'public_network_access': 'Enabled',
                'minimal_tls_version': '1.2'
            }
            
            poller = self.sql_client.servers.begin_create_or_update(
                self.resource_group,
                self.server_name,
                server_parameters
            )
            
            server = poller.result()
            logger.info(f"SQL Server '{self.server_name}' created successfully")
            
            # Add firewall rule to allow Azure services
            logger.info("Adding firewall rule for Azure services...")
            self.sql_client.firewall_rules.create_or_update(
                self.resource_group,
                self.server_name,
                'AllowAzureServices',
                {
                    'start_ip_address': '0.0.0.0',
                    'end_ip_address': '0.0.0.0'
                }
            )
            
            return server
            
        except Exception as e:
            logger.error(f"Error creating SQL Server: {e}")
            raise
    
    def create_database(self):
        """Create the MedData database"""
        try:
            logger.info(f"Creating database '{self.database_name}'...")
            
            database_parameters = {
                'location': self.location,
                'sku': {
                    'name': 'Basic',  # Start with Basic tier
                    'tier': 'Basic'
                },
                'collation': 'SQL_Latin1_General_CP1_CI_AS',
                'max_size_bytes': 2147483648,  # 2GB
            }
            
            poller = self.sql_client.databases.begin_create_or_update(
                self.resource_group,
                self.server_name,
                self.database_name,
                database_parameters
            )
            
            database = poller.result()
            logger.info(f"Database '{self.database_name}' created successfully")
            
            # Wait for database to be fully ready
            time.sleep(10)
            
            return database
            
        except Exception as e:
            logger.error(f"Error creating database: {e}")
            raise
    
    def get_connection_string(self, admin_username, admin_password):
        """
        Build connection string for the database
        
        Args:
            admin_username: Server admin username
            admin_password: Server admin password
        """
        server_fqdn = f"{self.server_name}.database.windows.net"
        
        # ODBC connection string with encryption
        connection_string = (
            f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={server_fqdn};"
            f"DATABASE={self.database_name};"
            f"UID={admin_username};"
            f"PWD={admin_password};"
            f"Encrypt=yes;"
            f"TrustServerCertificate=no;"
            f"Connection Timeout=30;"
        )
        
        return connection_string
    
    def create_tables(self, connection_string):
        """Create MED_SLOTS and MED tables"""
        try:
            logger.info("Connecting to database...")
            conn = pyodbc.connect(connection_string)
            cursor = conn.cursor()
            
            # Create MED_SLOTS table
            logger.info("Creating MED_SLOTS table...")
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'MED_SLOTS')
                BEGIN
                    CREATE TABLE MED_SLOTS (
                        SLOT_NUMBER INT PRIMARY KEY,
                        SLOT_NAME NVARCHAR(100) NOT NULL,
                        SLOT_TYPE NVARCHAR(50) NOT NULL
                    );
                END
            """)
            conn.commit()
            logger.info("MED_SLOTS table created")
            
            # Create MED table
            logger.info("Creating MED table...")
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'MED')
                BEGIN
                    CREATE TABLE MED (
                        ID INT IDENTITY(1,1) PRIMARY KEY,
                        CODE INT NOT NULL,
                        SLOT_NUMBER INT NOT NULL,
                        SLOT_VALUE NVARCHAR(500),
                        FOREIGN KEY (SLOT_NUMBER) REFERENCES MED_SLOTS(SLOT_NUMBER)
                    );
                    
                    -- Create index on CODE for faster queries
                    CREATE INDEX IX_MED_CODE ON MED(CODE);
                    
                    -- Create index on SLOT_NUMBER for joins
                    CREATE INDEX IX_MED_SLOT_NUMBER ON MED(SLOT_NUMBER);
                END
            """)
            conn.commit()
            logger.info("MED table created with indexes")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            raise
    
    def load_med_slots_data(self, connection_string):
        """Load data into MED_SLOTS table"""
        try:
            logger.info("Loading MED_SLOTS data...")
            conn = pyodbc.connect(connection_string)
            cursor = conn.cursor()
            
            # MED_SLOTS data
            slots_data = [
                (3, 'DESCENDANT-OF', 'SEMANTIC'),
                (4, 'SUBCLASS-OF', 'SEMANTIC'),
                (6, 'PRINT-NAME', 'STRING'),
                (9, 'CPMC-LAB-PROC-CODE', 'STRING'),
                (15, 'MEASURED-BY-PROCEDURE', 'SEMANTIC'),
                (16, 'ENTITY-MEASURED', 'SEMANTIC'),
                (20, 'CPMC-LAB-TEST-CODE', 'STRING'),
                (149, 'PT-PROBLEM-(INDICATED-BY)->PROCEDURE', 'SEMANTIC'),
                (150, 'PROCEDURE-(INDICATES)->PT-PROBLEM', 'SEMANTIC'),
                (212, 'LOINC-CODE', 'STRING'),
                (264, 'MILLENNIUM-LAB-CODE', 'STRING'),
                (266, 'SNOMED-CODE', 'STRING'),
                (277, 'EPIC-COMPONENT-ID', 'STRING')
            ]
            
            # Clear existing data
            cursor.execute("DELETE FROM MED_SLOTS")
            
            # Insert data with retry logic
            for slot_number, slot_name, slot_type in slots_data:
                retry_count = 0
                max_retries = 3
                
                while retry_count < max_retries:
                    try:
                        cursor.execute(
                            "INSERT INTO MED_SLOTS (SLOT_NUMBER, SLOT_NAME, SLOT_TYPE) VALUES (?, ?, ?)",
                            slot_number, slot_name, slot_type
                        )
                        break
                    except Exception as e:
                        retry_count += 1
                        if retry_count >= max_retries:
                            raise
                        time.sleep(1)
            
            conn.commit()
            logger.info(f"Loaded {len(slots_data)} rows into MED_SLOTS")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error loading MED_SLOTS data: {e}")
            raise
    
    def load_med_data(self, connection_string):
        """Load data into MED table"""
        try:
            logger.info("Loading MED data...")
            conn = pyodbc.connect(connection_string)
            cursor = conn.cursor()
            
            # MED data - (CODE, SLOT_NUMBER, SLOT_VALUE)
            med_data = [
                (1302, 150, '19928'), (1302, 150, '3668'), (1302, 20, ''), (1302, 212, '2947-0'),
                (1302, 266, ''), (1302, 277, ''), (1302, 3, '32180'), (1302, 4, '32180'),
                (1302, 6, 'Stat Whole Blood Sodium Ion Measurement'),
                (1611, 150, '19928'), (1611, 150, '3668'), (1611, 20, ''), (1611, 212, '2947-0'),
                (1611, 266, ''), (1611, 277, ''), (1611, 3, '32180'), (1611, 4, '32180'),
                (1611, 6, 'Presbyterian Whole Blood Sodium Ion Measurement'),
                (1612, 150, '19928'), (1612, 150, '3668'), (1612, 20, ''), (1612, 212, '2951-2'),
                (1612, 266, ''), (1612, 277, ''), (1612, 3, '32698'), (1612, 4, '32698'),
                (1612, 6, 'Serum Sodium Ion Measurement'),
                (1662, 150, '19928'), (1662, 150, '3668'), (1662, 20, ''), (1662, 212, ''),
                (1662, 266, ''), (1662, 277, ''), (1662, 3, '32180'), (1662, 4, '32180'),
                (1662, 6, 'Allen Whole Blood Sodium Ion Measurement'),
                (3668, 266, '39355002'), (3668, 3, '42484'), (3668, 4, '42484'), (3668, 6, 'Hypernatremia'),
                (3670, 266, '238115004'), (3670, 3, '19928'), (3670, 3, '42484'), (3670, 4, '19928'),
                (3670, 6, 'True Sodium (Na) Deficiency'),
                (19928, 266, '89627008'), (19928, 3, '42484'), (19928, 4, '42484'), (19928, 6, 'Hyponatremia'),
                (32180, 150, '19928'), (32180, 150, '3668'), (32180, 212, ''), (32180, 266, ''),
                (32180, 277, ''), (32180, 6, 'Whole Blood Sodium Tests'),
                (32698, 150, '19928'), (32698, 150, '3668'), (32698, 212, ''), (32698, 266, ''),
                (32698, 277, ''), (32698, 6, 'Serum Sodium Ion Tests'),
                (32712, 150, '19928'), (32712, 150, '3668'), (32712, 20, ''), (32712, 212, '2951-2'),
                (32712, 266, ''), (32712, 277, ''), (32712, 3, '32698'), (32712, 4, '32698'),
                (32712, 6, 'Serum Sodium Ion Measurement 2'),
                (35978, 150, '19928'), (35978, 150, '3668'), (35978, 20, 'INA'), (35978, 212, '2947-0'),
                (35978, 266, ''), (35978, 277, ''), (35978, 3, '32180'), (35978, 4, '32180'),
                (35978, 6, 'CPMC Laboratory Test: Sodium, Whole Blood'),
                (36066, 150, '19928'), (36066, 150, '3668'), (36066, 20, 'NAWBZ'), (36066, 212, '2947-0'),
                (36066, 266, ''), (36066, 277, ''), (36066, 3, '32180'), (36066, 4, '32180'),
                (36066, 6, 'CPMC Laboratory Test: Sodium Whole Blood'),
                (36067, 150, '19928'), (36067, 150, '3668'), (36067, 20, 'NAZ'), (36067, 212, '2951-2'),
                (36067, 266, ''), (36067, 277, ''), (36067, 3, '32698'), (36067, 4, '32698'),
                (36067, 6, 'CPMC Laboratory Test: Sodium'), (36067, 9, 'NAZ'),
                (42484, 266, ''), (42484, 6, 'Abnormal Blood Level of Sodium'),
                (50013, 150, '19928'), (50013, 150, '3668'), (50013, 212, '2951-2'), (50013, 266, ''),
                (50013, 277, ''), (50013, 3, '32698'), (50013, 4, '32698'), (50013, 6, 'NYH Lab Procedure: Sodium'),
                (50228, 150, '19928'), (50228, 150, '3668'), (50228, 212, ''), (50228, 266, ''),
                (50228, 277, ''), (50228, 3, '32180'), (50228, 4, '32180'), (50228, 6, 'NYH Lab Procedure: Sodium , W/B'),
                (56253, 150, '19928'), (56253, 150, '3668'), (56253, 20, 'SOD'), (56253, 212, '2951-2'),
                (56253, 266, ''), (56253, 277, ''), (56253, 3, '32698'), (56253, 4, '32698'),
                (56253, 6, 'CPMC Laboratory Test: Serum Sodium Measurement'), (56253, 9, 'SOD'),
                (59949, 150, '19928'), (59949, 150, '3668'), (59949, 20, 'ISNA'), (59949, 212, '32717-1'),
                (59949, 266, ''), (59949, 277, ''), (59949, 3, '32180'), (59949, 4, '32180'),
                (59949, 6, 'CPMC Laboratory Test: Sodium Istat'), (59949, 9, 'ISNA'),
                (66253, 150, '19928'), (66253, 150, '3668'), (66253, 20, 'NAM'), (66253, 212, '2947-0'),
                (66253, 266, ''), (66253, 277, ''), (66253, 3, '32180'), (66253, 4, '32180'),
                (66253, 6, 'CPMC Laboratory Test: Sodium Whole Blood (2)'), (66253, 9, 'NAM'),
                (66254, 150, '19928'), (66254, 150, '3668'), (66254, 20, 'NAMZ'), (66254, 212, '2947-0'),
                (66254, 266, ''), (66254, 277, ''), (66254, 3, '32180'), (66254, 4, '32180'),
                (66254, 6, 'CPMC Laboratory Test: Sodium Whole Blood (allen)'), (66254, 9, 'NAMZ'),
                (100031, 150, '19928'), (100031, 150, '3668'), (100031, 212, '2951-2'), (100031, 264, '317298'),
                (100031, 266, ''), (100031, 277, '29512'), (100031, 3, '32698'), (100031, 4, '32698'),
                (100031, 6, 'BKR (CM) RESULT: SODIUM LEVEL'),
                (111465, 150, '19928'), (111465, 150, '3668'), (111465, 212, '2947-0'), (111465, 264, '4272034'),
                (111465, 266, ''), (111465, 277, '5658'), (111465, 3, '32180'), (111465, 4, '32180'),
                (111465, 6, 'BKR (CM) Result: Sodium Whole Blood POC'),
                (112423, 150, '19928'), (112423, 150, '3668'), (112423, 212, '2947-0'), (112423, 264, '4329535'),
                (112423, 266, ''), (112423, 277, '29470'), (112423, 3, '32180'), (112423, 4, '32180'),
                (112423, 6, 'BKR (CM) Result: Sodium WB'),
                (125598, 150, '19928'), (125598, 150, '3668'), (125598, 212, '2947-0'), (125598, 264, '7853268'),
                (125598, 266, ''), (125598, 277, '6484'), (125598, 3, '32180'), (125598, 4, '32180'),
                (125598, 6, 'BKR (CM) Result: Sodium W/B - EPOC'),
                (128428, 150, '19928'), (128428, 150, '3668'), (128428, 20, 'EPNA'), (128428, 212, ''),
                (128428, 266, ''), (128428, 277, ''), (128428, 3, '32180'), (128428, 4, '32180'),
                (128428, 6, 'CPMC Laboratory Test: Sodium Whole Blood POC'),
                (129704, 150, '19928'), (129704, 150, '3668'), (129704, 212, '32717-1'), (129704, 264, '11682263'),
                (129704, 266, ''), (129704, 277, '21027'), (129704, 3, '32180'), (129704, 4, '32180'),
                (129704, 6, 'BKR (CM) Result: Sodium BGA'),
                (129713, 150, '19928'), (129713, 150, '3668'), (129713, 212, '39791-9'), (129713, 264, '11682403'),
                (129713, 266, ''), (129713, 277, '21035'), (129713, 3, '169652'), (129713, 3, '32180'),
                (129713, 4, '169652'), (129713, 6, 'BKR (CM) Result: Sodium BGV'),
                (133171, 150, '19928'), (133171, 150, '3668'), (133171, 212, '2947-0'), (133171, 264, '18710951'),
                (133171, 266, ''), (133171, 277, '21189'), (133171, 3, '32180'), (133171, 4, '32180'),
                (133171, 6, 'BKR (CM) Result: Sodium POC IL'),
                (169623, 150, '19928'), (169623, 150, '3668'), (169623, 212, '2947-0'), (169623, 264, '72986158'),
                (169623, 266, ''), (169623, 277, '22319'), (169623, 3, '169652'), (169623, 3, '32180'),
                (169623, 4, '169652'), (169623, 6, 'Cerner ME DTA: Sodium POC'),
                (169652, 150, '19928'), (169652, 150, '3668'), (169652, 212, ''), (169652, 266, ''),
                (169652, 277, ''), (169652, 3, '32180'), (169652, 4, '32180'), (169652, 6, 'Venous Blood Sodium Tests'),
                (170063, 150, '19928'), (170063, 150, '3668'), (170063, 212, '2951-2'), (170063, 266, ''),
                (170063, 277, ''), (170063, 3, '32698'), (170063, 4, '32698'), (170063, 6, 'Meditech Result: SODIUM'),
                (181985, 150, '19928'), (181985, 150, '3668'), (181985, 212, '2951-2'), (181985, 266, ''),
                (181985, 277, ''), (181985, 3, '32698'), (181985, 4, '32698'),
                (181985, 6, 'LabCorp Result: Sodium, Serum (1198)'),
                (197005, 150, '19928'), (197005, 150, '3668'), (197005, 212, '2951-2'), (197005, 266, ''),
                (197005, 277, ''), (197005, 3, '32698'), (197005, 4, '32698'),
                (197005, 6, 'LabCorp Result: Sodium, Serum (132258)'),
                (201232, 150, '19928'), (201232, 150, '3668'), (201232, 212, '2951-2'), (201232, 266, ''),
                (201232, 277, ''), (201232, 3, '32698'), (201232, 4, '32698'),
                (201232, 6, 'Meditech Order: Sodium (Retired)'),
                (228458, 150, '19928'), (228458, 150, '3668'), (228458, 212, '2951-2'), (228458, 266, ''),
                (228458, 277, ''), (228458, 3, '32698'), (228458, 4, '32698'), (228458, 6, 'Quest Result: SODIUM')
            ]
            
            # Clear existing data
            cursor.execute("DELETE FROM MED")
            
            # Batch insert for better performance
            batch_size = 100
            for i in range(0, len(med_data), batch_size):
                batch = med_data[i:i + batch_size]
                
                retry_count = 0
                max_retries = 3
                
                while retry_count < max_retries:
                    try:
                        for code, slot_number, slot_value in batch:
                            cursor.execute(
                                "INSERT INTO MED (CODE, SLOT_NUMBER, SLOT_VALUE) VALUES (?, ?, ?)",
                                code, slot_number, slot_value if slot_value else None
                            )
                        conn.commit()
                        break
                    except Exception as e:
                        retry_count += 1
                        if retry_count >= max_retries:
                            raise
                        time.sleep(1)
                
                logger.info(f"Loaded batch {i // batch_size + 1} ({min(i + batch_size, len(med_data))} / {len(med_data)} rows)")
            
            logger.info(f"Loaded {len(med_data)} rows into MED table")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error loading MED data: {e}")
            raise


def main():
    """Main execution function"""
    
    # Configuration - Update these values
    SUBSCRIPTION_ID = os.getenv('AZURE_SUBSCRIPTION_ID', 'YOUR_SUBSCRIPTION_ID')
    RESOURCE_GROUP = os.getenv('RESOURCE_GROUP', 'meddata-rg')
    SERVER_NAME = os.getenv('SQL_SERVER_NAME', 'meddata-sql-server')
    DATABASE_NAME = 'MedData'
    LOCATION = os.getenv('AZURE_LOCATION', 'eastus')
    
    # SQL Server credentials - Should be stored in Azure Key Vault in production
    ADMIN_USERNAME = os.getenv('SQL_ADMIN_USERNAME', 'sqladmin')
    ADMIN_PASSWORD = os.getenv('SQL_ADMIN_PASSWORD')
    
    if not ADMIN_PASSWORD:
        logger.error("SQL_ADMIN_PASSWORD environment variable not set!")
        logger.info("Please set it using: $env:SQL_ADMIN_PASSWORD='YourSecurePassword123!'")
        return
    
    if SUBSCRIPTION_ID == 'YOUR_SUBSCRIPTION_ID':
        logger.error("Please update SUBSCRIPTION_ID in the script or set AZURE_SUBSCRIPTION_ID environment variable")
        return
    
    try:
        # Initialize setup
        setup = MedDataDatabaseSetup(
            subscription_id=SUBSCRIPTION_ID,
            resource_group=RESOURCE_GROUP,
            server_name=SERVER_NAME,
            database_name=DATABASE_NAME,
            location=LOCATION
        )
        
        # Step 1: Create resource group
        setup.create_resource_group()
        
        # Step 2: Create SQL Server
        setup.create_sql_server(ADMIN_USERNAME, ADMIN_PASSWORD)
        
        # Step 3: Create database
        setup.create_database()
        
        # Step 4: Get connection string
        connection_string = setup.get_connection_string(ADMIN_USERNAME, ADMIN_PASSWORD)
        
        # Step 5: Create tables
        setup.create_tables(connection_string)
        
        # Step 6: Load MED_SLOTS data
        setup.load_med_slots_data(connection_string)
        
        # Step 7: Load MED data
        setup.load_med_data(connection_string)
        
        logger.info("=" * 80)
        logger.info("MedData database setup completed successfully!")
        logger.info("=" * 80)
        logger.info(f"Server: {SERVER_NAME}.database.windows.net")
        logger.info(f"Database: {DATABASE_NAME}")
        logger.info(f"Tables created: MED_SLOTS, MED")
        logger.info(f"Connection string available for your application")
        
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
