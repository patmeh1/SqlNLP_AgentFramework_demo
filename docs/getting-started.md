---
layout: default
title: Getting Started
---

# 🚀 Getting Started

## Prerequisites

Before you begin, ensure you have:

- **Python 3.9 or higher**
- **Azure Account** (with active subscription)
- **Azure CLI** installed and authenticated
- **ODBC Driver 18 for SQL Server**
- **Git** for cloning the repository

### Installing ODBC Driver

**Windows:**
- Download from [Microsoft's website](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)
- Run the installer

**macOS:**
```bash
brew tap microsoft/mssql-release https://github.com/Microsoft/homebrew-mssql-release
brew update
brew install msodbcsql18
```

**Linux (Ubuntu/Debian):**
```bash
curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
curl https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list | sudo tee /etc/apt/sources.list.d/mssql-release.list
sudo apt-get update
sudo ACCEPT_EULA=Y apt-get install -y msodbcsql18
```

---

## Step 1: Clone the Repository

```bash
git clone https://github.com/patmeh1/SqlNLP_AgentFramework_demo.git
cd SqlNLP_AgentFramework_demo
```

---

## Step 2: Set Up Azure Resources

### Quick Setup (Automated)

**On macOS/Linux:**
```bash
chmod +x scripts/setup_azure_resources.sh
cd scripts
./setup_azure_resources.sh
cd ..
```

**On Windows:**
```powershell
cd scripts
.\setup_azure_resources.ps1
cd ..
```

**What this script does:**
- Creates a resource group (`NYP_sql_agent`)
- Deploys Azure SQL Server
- Creates Northwind database
- Sets up firewall rules
- Configures Key Vault
- Generates `.env` file

### Manual Setup (If script doesn't work)

1. Create resource group:
```bash
az group create --name NYP_sql_agent --location eastus
```

2. Create SQL Server:
```bash
az sql server create \
  --resource-group NYP_sql_agent \
  --name <your-server-name> \
  --admin-user sqladmin \
  --admin-password "<strong-password>"
```

3. Create database:
```bash
az sql db create \
  --resource-group NYP_sql_agent \
  --server <your-server-name> \
  --name Northwind \
  --edition Basic
```

4. Configure firewall:
```bash
az sql server firewall-rule create \
  --resource-group NYP_sql_agent \
  --server <your-server-name> \
  --name AllowAzure \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0
```

---

## Step 3: Create AI Foundry Project

Since Azure CLI doesn't fully support AI Foundry yet, do this in the Azure Portal:

1. Go to [https://ai.azure.com](https://ai.azure.com)
2. Click **Create new project**
3. Enter project name: `NYP_AIFoundry`
4. Select the hub created by the script
5. Click **Create**

### Deploy GPT-4o Model

1. Go to **Deployments** in your project
2. Click **+ Create deployment**
3. Select **GPT-4o** model
4. Set deployment name to `NYP_demo`
5. Configure settings
6. Click **Create**

### Get Your Credentials

1. In your project, go to **Manage keys and endpoints**
2. Copy your **Endpoint URL**
3. Copy your **API Key (Key 1)**
4. Note your **Deployment name** (should be `NYP_demo`)

---

## Step 4: Load Database

### Option A: Using sqlcmd (Recommended)

```bash
sqlcmd -S <your-server-name>.database.windows.net \
  -d Northwind \
  -U sqladmin \
  -P '<your-password>' \
  -i database/northwind.sql
```

### Option B: Using Azure Data Studio
1. Connect to your Azure SQL Database
2. Open `database/northwind.sql`
3. Execute the entire script

### Option C: Using Python
```bash
python scripts/load_database.py
```

---

## Step 5: Configure Environment

### Create .env file

```bash
cp .env.template .env
```

### Edit .env with your credentials

```
# Database Configuration
SQL_SERVER=your-server-name.database.windows.net
SQL_DATABASE=Northwind
SQL_USERNAME=sqladmin
SQL_PASSWORD=your-password-here
SQL_AUTH_TYPE=sql

# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_DEPLOYMENT=NYP_demo
AZURE_OPENAI_API_VERSION=2024-08-01-preview

# Flask Configuration
FLASK_SECRET_KEY=your-secret-key-here
```

---

## Step 6: Create Python Virtual Environment

### Windows
```bash
python -m venv venv
venv\Scripts\activate
```

### macOS/Linux
```bash
python3 -m venv venv
source venv/bin/activate
```

---

## Step 7: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- Flask (web framework)
- azure-openai (GPT-4o integration)
- pyodbc (database connection)
- python-dotenv (environment variables)
- And other required packages

---

## Step 8: Run the Application

```bash
python app.py
```

You should see:
```
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5002
```

---

## Step 9: Open in Browser

1. Open your browser
2. Go to `http://localhost:5002`
3. You should see the chat interface
4. Try asking a question!

---

## Troubleshooting Setup Issues

### Issue: "ODBC Driver not found"
**Solution**: Install ODBC Driver 18 for SQL Server (see Prerequisites)

### Issue: "Cannot connect to database"
**Solutions**:
- Check firewall rules in Azure Portal
- Verify your IP is whitelisted
- Ensure Azure services can access the server
- Verify SQL credentials in .env

### Issue: "Azure OpenAI API errors"
**Solutions**:
- Verify API key and endpoint in .env
- Check that GPT-4o deployment name matches
- Ensure your Azure OpenAI resource is in the same region
- Verify the API version is correct

### Issue: "Module not found" errors
**Solution**: Ensure virtual environment is activated
```bash
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows
```

### Issue: "Permission denied" on scripts
**Solution**: Make script executable
```bash
chmod +x scripts/setup_azure_resources.sh
```

---

## Verify Everything Works

### Test 1: Application Loads
- Open http://localhost:5002
- Should see chat interface

### Test 2: Sample Query
- Type: "Show me all products"
- Should return product list

### Test 3: Complex Query
- Type: "What are the top 5 most expensive products?"
- Should return formatted results

### Test 4: Execution Tracking
- Right side panel should show steps
- Each step should have a timestamp
- Color should change (blue → green)

---

## Next Steps

1. **Explore the Interface**
   - Try different queries
   - Review generated SQL
   - Check execution steps

2. **Read the Documentation**
   - [Full README](https://github.com/patmeh1/SqlNLP_AgentFramework_demo)
   - [Architecture Guide](architecture.html)
   - [Features & Capabilities](features.html)

3. **Customize for Your Use Case**
   - Replace Northwind database
   - Add custom agents
   - Modify UI styling

4. **Deploy to Production**
   - Use Azure App Service
   - Configure auto-scaling
   - Set up monitoring

---

## Quick Reference Commands

### Activate Virtual Environment
```bash
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### Deactivate Virtual Environment
```bash
deactivate
```

### Run Application
```bash
python app.py
```

### Stop Application
```bash
Ctrl + C
```

### Update Dependencies
```bash
pip install -r requirements.txt --upgrade
```

### View Database Schema
```bash
sqlcmd -S <server>.database.windows.net \
  -U sqladmin \
  -P '<password>' \
  -d Northwind \
  -Q "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES"
```

---

## Environment Variables Reference

| Variable | Description | Example |
|----------|-------------|---------|
| `SQL_SERVER` | Azure SQL hostname | `myserver.database.windows.net` |
| `SQL_DATABASE` | Database name | `Northwind` |
| `SQL_USERNAME` | Database username | `sqladmin` |
| `SQL_PASSWORD` | Database password | `SecurePass123!` |
| `SQL_AUTH_TYPE` | Auth type | `sql` or `azure_ad` |
| `AZURE_OPENAI_ENDPOINT` | OpenAI endpoint | `https://xxx.openai.azure.com/` |
| `AZURE_OPENAI_API_KEY` | OpenAI API key | `xxxxxxx` |
| `AZURE_OPENAI_DEPLOYMENT` | Deployment name | `NYP_demo` |
| `AZURE_OPENAI_API_VERSION` | API version | `2024-08-01-preview` |
| `FLASK_SECRET_KEY` | Flask secret | `auto-generated` |

---

## Getting Help

If you run into issues:

1. **Check the Troubleshooting section above**
2. **Review Azure Documentation**:
   - [Azure SQL Database Help](https://learn.microsoft.com/en-us/azure/azure-sql/)
   - [Azure OpenAI Help](https://learn.microsoft.com/en-us/azure/ai-services/openai/)
3. **Check GitHub Issues**:
   - [SqlNLP_AgentFramework_demo Issues](https://github.com/patmeh1/SqlNLP_AgentFramework_demo/issues)

---

<div style="text-align: center; margin-top: 40px; padding: 20px; background: #f5f5f5; border-radius: 10px;">
  <h3>Ready? Let's Go!</h3>
  <p>Follow the steps above and you'll be up and running in minutes.</p>
  <p><a href="/">← Back to Home</a> | <a href="https://github.com/patmeh1/SqlNLP_AgentFramework_demo">View on GitHub →</a></p>
</div>
