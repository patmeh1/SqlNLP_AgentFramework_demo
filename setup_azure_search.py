"""
Azure AI Search Resource Setup Helper
Helps create Azure AI Search service for MedData vectorization
"""
import os
import subprocess
import json
from dotenv import load_dotenv

load_dotenv()


def check_azure_cli():
    """Check if Azure CLI is installed"""
    try:
        result = subprocess.run(
            ["az", "--version"],
            capture_output=True,
            text=True,
            shell=True
        )
        return result.returncode == 0
    except:
        return False


def get_current_subscription():
    """Get current Azure subscription"""
    try:
        result = subprocess.run(
            ["az", "account", "show"],
            capture_output=True,
            text=True,
            shell=True
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
        return None
    except:
        return None


def list_resource_groups():
    """List available resource groups"""
    try:
        result = subprocess.run(
            ["az", "group", "list"],
            capture_output=True,
            text=True,
            shell=True
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
        return []
    except:
        return []


def create_search_service(service_name, resource_group, location="eastus"):
    """Create Azure AI Search service"""
    print(f"\n📊 Creating Azure AI Search service '{service_name}'...")
    
    cmd = [
        "az", "search", "service", "create",
        "--name", service_name,
        "--resource-group", resource_group,
        "--location", location,
        "--sku", "basic",
        "--partition-count", "1",
        "--replica-count", "1"
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            shell=True
        )
        
        if result.returncode == 0:
            print(f"✅ Search service created successfully!")
            return True
        else:
            print(f"❌ Error creating search service:")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def get_search_admin_key(service_name, resource_group):
    """Get admin key for search service"""
    print(f"\n🔑 Retrieving admin key...")
    
    cmd = [
        "az", "search", "admin-key", "show",
        "--service-name", service_name,
        "--resource-group", resource_group
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            shell=True
        )
        
        if result.returncode == 0:
            keys = json.loads(result.stdout)
            return keys.get("primaryKey")
        else:
            print(f"❌ Error retrieving key:")
            print(result.stderr)
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def update_env_file(endpoint, key):
    """Update .env file with search service details"""
    print("\n📝 Updating .env file...")
    
    env_path = ".env"
    
    try:
        # Read current .env
        with open(env_path, 'r') as f:
            lines = f.readlines()
        
        # Update or add search endpoint and key
        updated = False
        endpoint_found = False
        key_found = False
        
        for i, line in enumerate(lines):
            if line.startswith("AZURE_SEARCH_ENDPOINT="):
                lines[i] = f"AZURE_SEARCH_ENDPOINT={endpoint}\n"
                endpoint_found = True
            elif line.startswith("AZURE_SEARCH_KEY="):
                lines[i] = f"AZURE_SEARCH_KEY={key}\n"
                key_found = True
        
        # Add if not found
        if not endpoint_found:
            # Find the Azure AI Search Configuration section
            for i, line in enumerate(lines):
                if "Azure AI Search Configuration" in line:
                    lines.insert(i + 1, f"AZURE_SEARCH_ENDPOINT={endpoint}\n")
                    break
        
        if not key_found:
            for i, line in enumerate(lines):
                if "Azure AI Search Configuration" in line:
                    lines.insert(i + 2, f"AZURE_SEARCH_KEY={key}\n")
                    break
        
        # Write back
        with open(env_path, 'w') as f:
            f.writelines(lines)
        
        print("✅ .env file updated successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error updating .env: {e}")
        return False


def main():
    """Main setup flow"""
    print("="*80)
    print("Azure AI Search Setup for MedData Vector Search")
    print("="*80)
    
    # Check if already configured
    search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
    search_key = os.getenv("AZURE_SEARCH_KEY")
    
    if search_endpoint and search_key and not search_endpoint.startswith("<your"):
        print("\n✅ Azure AI Search is already configured!")
        print(f"   Endpoint: {search_endpoint}")
        print(f"   Key: {search_key[:10]}...")
        
        response = input("\nDo you want to reconfigure? (y/n): ")
        if response.lower() != 'y':
            print("\nSetup cancelled.")
            return
    
    # Check Azure CLI
    if not check_azure_cli():
        print("\n❌ Azure CLI is not installed or not in PATH")
        print("   Please install from: https://docs.microsoft.com/cli/azure/install-azure-cli")
        return
    
    print("\n✅ Azure CLI detected")
    
    # Check subscription
    subscription = get_current_subscription()
    if not subscription:
        print("\n❌ Not logged in to Azure CLI")
        print("   Please run: az login")
        return
    
    print(f"\n✅ Logged in to Azure")
    print(f"   Subscription: {subscription.get('name')}")
    print(f"   Tenant: {subscription.get('tenantDisplayName')}")
    
    # List resource groups
    print("\n📋 Available Resource Groups:")
    resource_groups = list_resource_groups()
    
    if not resource_groups:
        print("   No resource groups found")
        return
    
    for i, rg in enumerate(resource_groups, 1):
        print(f"   {i}. {rg['name']} ({rg['location']})")
    
    # Get user input
    print("\n" + "="*80)
    print("Setup Configuration")
    print("="*80)
    
    # Resource group
    rg_choice = input(f"\nSelect resource group (1-{len(resource_groups)}): ")
    try:
        rg_index = int(rg_choice) - 1
        resource_group = resource_groups[rg_index]['name']
        location = resource_groups[rg_index]['location']
    except:
        print("Invalid selection")
        return
    
    # Service name
    default_name = "meddata-search-service"
    service_name = input(f"\nEnter search service name [{default_name}]: ") or default_name
    
    print(f"\n📋 Configuration:")
    print(f"   Service Name: {service_name}")
    print(f"   Resource Group: {resource_group}")
    print(f"   Location: {location}")
    print(f"   SKU: Basic (1 partition, 1 replica)")
    print(f"   Estimated Cost: ~$75/month")
    
    response = input("\nProceed with creation? (y/n): ")
    if response.lower() != 'y':
        print("\nSetup cancelled.")
        return
    
    # Create search service
    if not create_search_service(service_name, resource_group, location):
        return
    
    # Get admin key
    admin_key = get_search_admin_key(service_name, resource_group)
    if not admin_key:
        print("\n⚠️  Service created but could not retrieve admin key")
        print("   Please get the key manually from Azure Portal")
        return
    
    # Build endpoint
    endpoint = f"https://{service_name}.search.windows.net"
    
    print(f"\n✅ Setup complete!")
    print(f"   Endpoint: {endpoint}")
    print(f"   Admin Key: {admin_key[:10]}...{admin_key[-4:]}")
    
    # Update .env file
    response = input("\nUpdate .env file automatically? (y/n): ")
    if response.lower() == 'y':
        update_env_file(endpoint, admin_key)
    else:
        print("\n📝 Add these to your .env file:")
        print(f"   AZURE_SEARCH_ENDPOINT={endpoint}")
        print(f"   AZURE_SEARCH_KEY={admin_key}")
    
    print("\n" + "="*80)
    print("✅ Azure AI Search service is ready!")
    print("\nNext steps:")
    print("1. Run: python setup_meddata_vector.py")
    print("2. This will vectorize your MedData database")
    print("3. Test with: python agents/vector_enhanced_meddata_agent.py")
    print("="*80)


if __name__ == "__main__":
    main()
