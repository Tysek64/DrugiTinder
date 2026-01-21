import os
import argparse
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("DB_NAME", "dating_app_db")

# Default counts
COUNTS = {
    "ADMINS": 10,
    "USERS": 2000,
    "SWIPES": 5000,
    "MATCHES": 1000,
    "MESSAGES": 10000,
    "REPORTS": 200
}

def parse_args():
    parser = argparse.ArgumentParser(description='Populate MongoDB with dating app test data')
    parser.add_argument('--admins', type=int, help='Number of admins to generate')
    parser.add_argument('--users', type=int, help='Number of users to generate')
    parser.add_argument('--swipes', type=int, help='Number of swipes to generate')
    parser.add_argument('--matches', type=int, help='Number of matches to generate')
    parser.add_argument('--messages', type=int, help='Number of messages to generate')
    parser.add_argument('--reports', type=int, help='Number of reports to generate')
    parser.add_argument('--mongo-uri', type=str, help='MongoDB connection URI')
    parser.add_argument('--db-name', type=str, help='Database name')
    return parser.parse_args()

def apply_args():
    global MONGO_URI, DB_NAME, COUNTS
    args = parse_args()
    
    if args.mongo_uri:
        MONGO_URI = args.mongo_uri
    if args.db_name:
        DB_NAME = args.db_name
    
    if args.admins:
        COUNTS["ADMINS"] = args.admins
    if args.users:
        COUNTS["USERS"] = args.users
    if args.swipes:
        COUNTS["SWIPES"] = args.swipes
    if args.matches:
        COUNTS["MATCHES"] = args.matches
    if args.messages:
        COUNTS["MESSAGES"] = args.messages
    if args.reports:
        COUNTS["REPORTS"] = args.reports