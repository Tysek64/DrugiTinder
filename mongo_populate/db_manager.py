from pymongo import MongoClient
import settings

def get_database():
    try:
        client = MongoClient(settings.MONGO_URI)
        return client[settings.DB_NAME]
    except Exception as e:
        print(f"Halo baza: {e}")
        exit()

def reset_database(db):
    collections = [
        'admins', 'subscription_plans', 'users', 
        'swipes', 'matches', 'messages', 'reports'
    ]
    for col in collections:
        db[col].drop()
    print(f"Usuwanie '{settings.DB_NAME}' .")