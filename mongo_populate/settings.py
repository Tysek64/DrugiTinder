import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("DB_NAME", "dating_app_db")

COUNTS = {
    "ADMINS": 10,
    "USERS": 2000,
    "SWIPES": 5000,
    "MATCHES": 1000,
    "MESSAGES": 10000,
    "REPORTS": 200
}