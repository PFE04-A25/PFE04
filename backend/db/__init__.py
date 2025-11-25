import os
from dotenv import load_dotenv

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception as e:
    print(f"[DB INIT] dotenv non chargé : {e}")

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")