"""
Helper functions to create MedData SQL Agent from environment variables
"""

import os
from sql_agent import SQLAgent
from agents.meddata_agent_wrapper import MedDataAgentWrapper


def create_meddata_agent_from_env() -> MedDataAgentWrapper:
    """
    Create a MedData SQL Agent from environment variables.
    
    Environment variables required:
        - MEDDATA_SQL_SERVER: Azure SQL Server name (e.g., meddata-sql-server.database.windows.net)
        - MEDDATA_SQL_DATABASE: Database name (default: MedData)
        - MEDDATA_SQL_USERNAME: SQL admin username (optional if using Azure AD)
        - MEDDATA_SQL_PASSWORD: SQL admin password (optional if using Azure AD)
        - AZURE_OPENAI_ENDPOINT: Azure OpenAI endpoint
        - AZURE_OPENAI_API_KEY: Azure OpenAI API key
        - AZURE_OPENAI_DEPLOYMENT: Azure OpenAI deployment name
        - MEDDATA_USE_AZURE_AD: Set to 'false' to use SQL authentication (default: true)
    
    Returns:
        MedDataAgentWrapper instance configured for MedData database
    
    Raises:
        ValueError: If required environment variables are missing
    """
    # Get MedData database configuration
    sql_server = os.getenv('MEDDATA_SQL_SERVER')
    sql_database = os.getenv('MEDDATA_SQL_DATABASE', 'MedData')
    sql_username = os.getenv('MEDDATA_SQL_USERNAME')
    sql_password = os.getenv('MEDDATA_SQL_PASSWORD')
    
    # Azure OpenAI configuration
    azure_openai_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
    azure_openai_api_key = os.getenv('AZURE_OPENAI_API_KEY')
    azure_openai_deployment = os.getenv('AZURE_OPENAI_DEPLOYMENT', 'gpt-4o')
    
    # Determine authentication method
    use_azure_ad_str = os.getenv('MEDDATA_USE_AZURE_AD', 'true').lower()
    use_azure_ad = use_azure_ad_str in ('true', '1', 'yes')
    
    # Validate required configuration
    if not sql_server:
        raise ValueError(
            "MEDDATA_SQL_SERVER environment variable is required. "
            "Example: meddata-sql-server.database.windows.net"
        )
    
    if not use_azure_ad and (not sql_username or not sql_password):
        raise ValueError(
            "When MEDDATA_USE_AZURE_AD is false, both MEDDATA_SQL_USERNAME "
            "and MEDDATA_SQL_PASSWORD are required"
        )
    
    if not azure_openai_endpoint or not azure_openai_api_key:
        raise ValueError(
            "AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY are required"
        )
    
    # Create the SQL Agent for MedData
    sql_agent = SQLAgent(
        sql_server=sql_server,
        sql_database=sql_database,
        sql_username=sql_username,
        sql_password=sql_password,
        azure_openai_endpoint=azure_openai_endpoint,
        azure_openai_api_key=azure_openai_api_key,
        azure_openai_deployment=azure_openai_deployment,
        use_azure_ad=use_azure_ad
    )
    
    # Wrap in MedDataAgentWrapper
    meddata_agent_wrapper = MedDataAgentWrapper(sql_agent)
    
    print(f"✓ MedData Agent initialized")
    print(f"  Server: {sql_server}")
    print(f"  Database: {sql_database}")
    print(f"  Auth: {'Azure AD' if use_azure_ad else 'SQL Authentication'}")
    
    return meddata_agent_wrapper


def is_meddata_configured() -> bool:
    """
    Check if MedData agent environment variables are configured.
    
    Returns:
        True if MedData can be initialized, False otherwise
    """
    sql_server = os.getenv('MEDDATA_SQL_SERVER')
    azure_openai_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
    azure_openai_api_key = os.getenv('AZURE_OPENAI_API_KEY')
    
    use_azure_ad_str = os.getenv('MEDDATA_USE_AZURE_AD', 'true').lower()
    use_azure_ad = use_azure_ad_str in ('true', '1', 'yes')
    
    # Check basic requirements
    if not sql_server or not azure_openai_endpoint or not azure_openai_api_key:
        return False
    
    # If using SQL auth, check for credentials
    if not use_azure_ad:
        sql_username = os.getenv('MEDDATA_SQL_USERNAME')
        sql_password = os.getenv('MEDDATA_SQL_PASSWORD')
        if not sql_username or not sql_password:
            return False
    
    return True
