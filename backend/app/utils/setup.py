from dotenv import load_dotenv, find_dotenv
import os
import sys

def setup():
    """
    Set up the environment for the application.
    
    This function:
    1. In development mode, loads environment variables from a .env file
    2. In production mode, verifies the presence of required API keys
    3. Configures API keys in the environment
    
    Raises:
        SystemExit: If the .env file is not found or required environment variables are missing
    """
    if os.getenv("ENV", "development").lower() == "development":
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

    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        print("Error: GOOGLE_API_KEY environment variable not set.")
        sys.exit(1)

    google_cse_id = os.getenv("GOOGLE_CSE_ID")
    if not google_cse_id:
        print("Error: GOOGLE_CSE_ID environment variable not set.")
        sys.exit(1)

    reddit_client_id = os.getenv("REDDIT_CLIENT_ID")
    if not reddit_client_id:
        print("Error: REDDIT_CLIENT_ID environment variable not set.")
        sys.exit(1)

    reddit_client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    if not reddit_client_secret:  
        print("Error: REDDIT_CLIENT_SECRET environment variable not set.")
        sys.exit(1)

    reddit_user_agent = os.getenv("REDDIT_USER_AGENT")
    if not reddit_user_agent:
        print("Error: REDDIT_USER_AGENT environment variable not set.")
        sys.exit(1) 

    os.environ["OPENAI_API_KEY"] = openai_api_key
    os.environ["SERPAPI_API_KEY"] = serp_api_key
    os.environ["GOOGLE_API_KEY"] = google_api_key
    os.environ["GOOGLE_CSE_ID"] = google_cse_id
    os.environ["REDDIT_CLIENT_ID"] = reddit_client_id
    os.environ["REDDIT_CLIENT_SECRET"] = reddit_client_secret
    os.environ["REDDIT_USER_AGENT"] = reddit_user_agent

