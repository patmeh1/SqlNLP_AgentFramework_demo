"""Verify MedData configuration is loaded"""
from dotenv import load_dotenv
import os

load_dotenv()

print("\n" + "="*70)
print("  MEDDATA ENVIRONMENT VARIABLES")
print("="*70)

server = os.getenv('MEDDATA_SQL_SERVER')
database = os.getenv('MEDDATA_SQL_DATABASE')
use_ad = os.getenv('MEDDATA_USE_AZURE_AD')

print(f"\nMEDDATA_SQL_SERVER: {server}")
print(f"MEDDATA_SQL_DATABASE: {database}")
print(f"MEDDATA_USE_AZURE_AD: {use_ad}")

if server and database:
    print("\n✅ MedData is configured!")
else:
    print("\n❌ MedData is NOT configured!")

print("="*70 + "\n")
