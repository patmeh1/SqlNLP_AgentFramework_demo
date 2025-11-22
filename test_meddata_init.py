"""Test if MedData is configured and can be initialized"""
from dotenv import load_dotenv
import os
import sys

# Load environment variables
load_dotenv()

print("\n" + "="*70)
print("  MEDDATA AGENT INITIALIZATION TEST")
print("="*70)

# Check environment variables
print("\n1. Environment Variables:")
server = os.getenv('MEDDATA_SQL_SERVER')
database = os.getenv('MEDDATA_SQL_DATABASE')
use_ad = os.getenv('MEDDATA_USE_AZURE_AD')

print(f"   MEDDATA_SQL_SERVER: {server}")
print(f"   MEDDATA_SQL_DATABASE: {database}")
print(f"   MEDDATA_USE_AZURE_AD: {use_ad}")

# Check is_meddata_configured
print("\n2. Testing is_meddata_configured():")
try:
    from agents.create_meddata_agent import is_meddata_configured
    is_configured = is_meddata_configured()
    print(f"   Result: {is_configured}")
    if is_configured:
        print("   ✅ MedData IS configured")
    else:
        print("   ❌ MedData is NOT configured")
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

# Try to create MedData agent
print("\n3. Testing create_meddata_agent_from_env():")
try:
    from agents.create_meddata_agent import create_meddata_agent_from_env
    agent = create_meddata_agent_from_env()
    print(f"   ✅ MedData agent created successfully!")
    print(f"   Agent type: {type(agent)}")
except Exception as e:
    print(f"   ❌ Error creating MedData agent: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70 + "\n")
