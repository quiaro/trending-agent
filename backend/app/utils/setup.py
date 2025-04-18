from dotenv import load_dotenv, find_dotenv
import os
import sys

def setup():
    """
    Set up the environment for the application.
    
    This function:
    1. Loads environment variables from a .env file
    2. Verifies the presence of required API keys
    3. Configures API keys in the environment
    
    Raises:
        SystemExit: If the .env file is not found or required environment variables are missing
    """
    dotenv_path = find_dotenv(usecwd=True)
    if not dotenv_path:
        print("Error: .env file not found in the current directory or parent directories.")
        sys.exit(1)

    load_dotenv(dotenv_path)

    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("Error: OPENAI_API_KEY environment variable not set.")
        sys.exit(1)

    serp_api_key = os.getenv("SERPAPI_API_KEY")
    if not serp_api_key:
        print("Error: SERPAPI_API_KEY environment variable not set.")
        sys.exit(1)

    os.environ["OPENAI_API_KEY"] = openai_api_key
    os.environ["SERPAPI_API_KEY"] = serp_api_key