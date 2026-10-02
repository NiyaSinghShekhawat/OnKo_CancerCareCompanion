# Runs before any test module is imported: point tests at their own SQLite file so running pytest
# never wipes the demo database (onko.db). load_dotenv() doesn't override variables that are already set.
import os

os.environ["DATABASE_URL"] = "sqlite:///./test_onko.db"
for k in ("ANTHROPIC_API_KEY", "GEMINI_API_KEY", "TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN"):
    os.environ[k] = ""
# Deployment switches off, whatever .env says; test_deploy_settings.py turns them on per test.
os.environ["DEMO_ACCESS_CODE"] = ""
os.environ["DEMO_ROUTES_ENABLED"] = "true"
