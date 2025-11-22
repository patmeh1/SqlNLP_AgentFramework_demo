# MedData Azure SQL Database Setup

This folder contains scripts to create and populate the **MedData** Azure SQL Database with medical slot and code information.

## Database Schema

### Table 1: MED_SLOTS
Stores slot definitions for medical coding system.

| Column | Type | Description |
|--------|------|-------------|
| SLOT_NUMBER | INT (PK) | Unique slot identifier |
| SLOT_NAME | NVARCHAR(100) | Name/description of the slot |
| SLOT_TYPE | NVARCHAR(50) | Type (SEMANTIC or STRING) |

**13 rows** of slot definitions including LOINC-CODE, SNOMED-CODE, EPIC-COMPONENT-ID, etc.

### Table 2: MED
Stores medical code-slot-value relationships.

| Column | Type | Description |
|--------|------|-------------|
| ID | INT (IDENTITY, PK) | Auto-incrementing primary key |
| CODE | INT | Medical code identifier |
| SLOT_NUMBER | INT (FK) | References MED_SLOTS |
| SLOT_VALUE | NVARCHAR(500) | Value for the slot |

**155 rows** of medical data with indexes on CODE and SLOT_NUMBER for query performance.

## Prerequisites

1. **Azure Subscription** - Active Azure subscription
2. **Azure CLI** - Installed and configured ([Download](https://learn.microsoft.com/cli/azure/install-azure-cli))
3. **Python 3.8+** - Python installed on your system
4. **ODBC Driver 18 for SQL Server** - Required for database connections
   - Windows: [Download](https://learn.microsoft.com/sql/connect/odbc/download-odbc-driver-for-sql-server)
   - Run: `msiexec /i msodbcsql.msi`

## Quick Start

### Option 1: PowerShell Script (Recommended)

```powershell
# Run the automated setup script
.\scripts\setup_meddata.ps1
```

The script will prompt you for:
- Azure Subscription ID
- Resource Group name (default: meddata-rg)
- SQL Server name (default: meddata-sql-server)
- Azure region (default: eastus)
- SQL admin username (default: sqladmin)
- SQL admin password (must be strong)

### Option 2: Manual Setup

1. **Install dependencies:**
   ```powershell
   pip install -r scripts/meddata_requirements.txt
   ```

2. **Login to Azure:**
   ```powershell
   az login
   az account set --subscription YOUR_SUBSCRIPTION_ID
   ```

3. **Set environment variables:**
   ```powershell
   $env:AZURE_SUBSCRIPTION_ID = "your-subscription-id"
   $env:RESOURCE_GROUP = "meddata-rg"
   $env:SQL_SERVER_NAME = "meddata-sql-server"
   $env:AZURE_LOCATION = "eastus"
   $env:SQL_ADMIN_USERNAME = "sqladmin"
   $env:SQL_ADMIN_PASSWORD = "YourSecurePassword123!"
   ```

4. **Run the setup script:**
   ```powershell
   python scripts/setup_meddata_database.py
   ```

## What the Setup Does

1. ✓ Creates Azure Resource Group
2. ✓ Creates Azure SQL Server with TLS 1.2 encryption
3. ✓ Configures firewall rules for Azure services
4. ✓ Creates **MedData** database (Basic tier, 2GB)
5. ✓ Creates **MED_SLOTS** table with slot definitions
6. ✓ Creates **MED** table with foreign key constraint and indexes
7. ✓ Loads 13 rows into MED_SLOTS
8. ✓ Loads 155 rows into MED table

## Security Features

- **Managed Identity Support** - Uses DefaultAzureCredential for authentication
- **Encrypted Connections** - TLS 1.2 enforced
- **Parameterized Queries** - Prevents SQL injection
- **No Hardcoded Credentials** - Environment variables for sensitive data
- **Retry Logic** - Handles transient failures with exponential backoff

## Connection Information

After setup, connect to your database using:

**Server:** `your-server-name.database.windows.net`  
**Database:** `MedData`  
**Username:** Your admin username  
**Password:** Your admin password  

### Connection String (Python with pyodbc):
```python
connection_string = (
    f"DRIVER={{ODBC Driver 18 for SQL Server}};"
    f"SERVER=your-server.database.windows.net;"
    f"DATABASE=MedData;"
    f"UID=sqladmin;"
    f"PWD=your-password;"
    f"Encrypt=yes;"
    f"TrustServerCertificate=no;"
)
```

### Connection String (ADO.NET):
```
Server=tcp:your-server.database.windows.net,1433;Database=MedData;User ID=sqladmin;Password=your-password;Encrypt=True;TrustServerCertificate=False;
```

## Sample Queries

### Query 1: Get all slot definitions
```sql
SELECT * FROM MED_SLOTS ORDER BY SLOT_NUMBER;
```

### Query 2: Get all data for a specific medical code
```sql
SELECT 
    m.CODE,
    s.SLOT_NAME,
    s.SLOT_TYPE,
    m.SLOT_VALUE
FROM MED m
JOIN MED_SLOTS s ON m.SLOT_NUMBER = s.SLOT_NUMBER
WHERE m.CODE = 1302
ORDER BY s.SLOT_NUMBER;
```

### Query 3: Find all codes with LOINC codes
```sql
SELECT DISTINCT 
    m.CODE,
    m.SLOT_VALUE as LOINC_CODE
FROM MED m
JOIN MED_SLOTS s ON m.SLOT_NUMBER = s.SLOT_NUMBER
WHERE s.SLOT_NAME = 'LOINC-CODE'
  AND m.SLOT_VALUE != ''
ORDER BY m.CODE;
```

### Query 4: Get codes with their print names
```sql
SELECT 
    m.CODE,
    m.SLOT_VALUE as PRINT_NAME
FROM MED m
WHERE m.SLOT_NUMBER = 6  -- PRINT-NAME slot
ORDER BY m.CODE;
```

## Troubleshooting

### Issue: ODBC Driver not found
**Solution:** Install ODBC Driver 18 for SQL Server
```powershell
# Download and install from Microsoft
# https://learn.microsoft.com/sql/connect/odbc/download-odbc-driver-for-sql-server
```

### Issue: Authentication failed
**Solution:** Ensure you're logged into Azure CLI
```powershell
az login
az account show
```

### Issue: Firewall blocking connection
**Solution:** Add your client IP to SQL Server firewall rules
```powershell
az sql server firewall-rule create \
  --resource-group meddata-rg \
  --server meddata-sql-server \
  --name AllowMyIP \
  --start-ip-address YOUR_IP \
  --end-ip-address YOUR_IP
```

### Issue: Password doesn't meet complexity requirements
**Solution:** Use a password with:
- At least 8 characters
- Uppercase and lowercase letters
- Numbers
- Special characters (!@#$%^&*)

## Integration with Your SQL Agent

To integrate this database with your existing SQL Agent demo:

1. **Update connection configuration** in your app:
   ```python
   MEDDATA_CONNECTION = {
       'server': 'your-server.database.windows.net',
       'database': 'MedData',
       'username': 'sqladmin',
       'password': os.getenv('SQL_ADMIN_PASSWORD')
   }
   ```

2. **Add MedData queries** to your SQL agent capabilities

3. **Update the orchestrator** to route medical queries to MedData

## Cost Estimates

- **SQL Database (Basic tier):** ~$5/month
- **SQL Server:** No additional cost
- **Data egress:** Minimal for small datasets

## Next Steps

1. ✅ Database created and populated
2. 📝 Test queries and verify data
3. 🔧 Integrate with your SQL Agent application
4. 🔒 Configure Azure Key Vault for credentials (recommended for production)
5. 📊 Set up monitoring and alerts

## Files in this Folder

- `setup_meddata_database.py` - Main Python setup script
- `setup_meddata.ps1` - PowerShell automation script
- `meddata_requirements.txt` - Python dependencies
- `MEDDATA_README.md` - This file

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review Azure SQL Database documentation
3. Check application logs for detailed error messages

## References

- [Azure SQL Database Documentation](https://learn.microsoft.com/azure/azure-sql/database/)
- [pyodbc Documentation](https://github.com/mkleehammer/pyodbc/wiki)
- [Azure SDK for Python](https://learn.microsoft.com/python/api/overview/azure/)
