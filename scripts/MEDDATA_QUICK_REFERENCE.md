# MedData Database - Quick Command Reference

## 🚀 Quick Setup (Easiest)
```powershell
cd c:\CSA-demo-projects\MAF_SqlAgent_demo_v3-custom-data
.\scripts\setup_meddata.ps1
```

## 📋 Manual Setup Commands

### 1. Install Dependencies
```powershell
pip install -r scripts/meddata_requirements.txt
```

### 2. Login to Azure
```powershell
az login
az account set --subscription "YOUR_SUBSCRIPTION_ID"
```

### 3. Set Environment Variables
```powershell
$env:AZURE_SUBSCRIPTION_ID = "your-subscription-id"
$env:RESOURCE_GROUP = "meddata-rg"
$env:SQL_SERVER_NAME = "meddata-sql-server"
$env:AZURE_LOCATION = "eastus"
$env:SQL_ADMIN_USERNAME = "sqladmin"
$env:SQL_ADMIN_PASSWORD = "YourSecurePassword123!"
```

### 4. Run Setup
```powershell
python scripts/setup_meddata_database.py
```

## ✅ Verify Installation
```powershell
$env:SQL_SERVER_NAME = "your-server-name"
$env:SQL_ADMIN_PASSWORD = "your-password"
python scripts/test_meddata.py
```

## 🔍 Quick Queries (via sqlcmd or Azure Data Studio)

### Connect
```powershell
sqlcmd -S your-server.database.windows.net -d MedData -U sqladmin -P YourPassword
```

### Count Records
```sql
SELECT 'MED_SLOTS' as Table, COUNT(*) as Rows FROM MED_SLOTS
UNION ALL
SELECT 'MED', COUNT(*) FROM MED;
```

### View Sample Data
```sql
SELECT TOP 10 
    m.CODE, 
    s.SLOT_NAME, 
    m.SLOT_VALUE
FROM MED m
JOIN MED_SLOTS s ON m.SLOT_NUMBER = s.SLOT_NUMBER
ORDER BY m.CODE;
```

## 🔧 Troubleshooting Commands

### Check if logged into Azure
```powershell
az account show
```

### List your subscriptions
```powershell
az account list --output table
```

### Check if resource group exists
```powershell
az group show --name meddata-rg
```

### Check if SQL server exists
```powershell
az sql server show --name meddata-sql-server --resource-group meddata-rg
```

### List databases on server
```powershell
az sql db list --server meddata-sql-server --resource-group meddata-rg --output table
```

### Add firewall rule for your IP
```powershell
$myIp = (Invoke-WebRequest -Uri "https://api.ipify.org").Content
az sql server firewall-rule create `
    --resource-group meddata-rg `
    --server meddata-sql-server `
    --name AllowMyIP `
    --start-ip-address $myIp `
    --end-ip-address $myIp
```

## 🗑️ Cleanup Commands (if needed)

### Delete database only
```powershell
az sql db delete `
    --name MedData `
    --resource-group meddata-rg `
    --server meddata-sql-server `
    --yes
```

### Delete entire resource group
```powershell
az group delete --name meddata-rg --yes
```

## 📊 Check Database Size
```sql
SELECT 
    DB_NAME() AS DatabaseName,
    SUM(size) * 8 / 1024 AS SizeMB
FROM sys.database_files;
```

## 🔐 Connection Strings

### Python (pyodbc)
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

### .NET (ADO.NET)
```
Server=tcp:your-server.database.windows.net,1433;
Database=MedData;
User ID=sqladmin;
Password=your-password;
Encrypt=True;
TrustServerCertificate=False;
Connection Timeout=30;
```

### JDBC
```
jdbc:sqlserver://your-server.database.windows.net:1433;
database=MedData;
user=sqladmin;
password=your-password;
encrypt=true;
trustServerCertificate=false;
```

## 📈 Monitor Performance
```sql
-- Check query performance
SELECT 
    qs.execution_count,
    qs.total_elapsed_time / 1000000 as total_elapsed_time_sec,
    SUBSTRING(qt.text, (qs.statement_start_offset/2)+1,
        ((CASE qs.statement_end_offset
            WHEN -1 THEN DATALENGTH(qt.text)
            ELSE qs.statement_end_offset
        END - qs.statement_start_offset)/2) + 1) AS statement_text
FROM sys.dm_exec_query_stats qs
CROSS APPLY sys.dm_exec_sql_text(qs.sql_handle) qt
ORDER BY qs.total_elapsed_time DESC;
```

## 🎯 Quick Reference URLs
- Azure Portal: https://portal.azure.com
- SQL Server: `https://portal.azure.com/#resource/subscriptions/YOUR_SUB/resourceGroups/meddata-rg/providers/Microsoft.Sql/servers/your-server`
- Azure Data Studio Download: https://learn.microsoft.com/sql/azure-data-studio/download

---
**Tip:** Save your server name and password for easy access!
