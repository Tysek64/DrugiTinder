import random
from datetime import timedelta
from faker import Faker
import settings

fake = Faker()

def create(db, user_ids):
    count = settings.COUNTS["MATCHES"]
    print(f"Generowanie {count} meczów...")
    matches = []
    
    for _ in range(count):
        u1, u2 = random.sample(user_ids, 2)
        match_date = fake.date_time_between(start_date='-1y', end_date='now')
        
        matches.append({
            "members": [u1, u2],
            "status": random.choice(["active", "active", "ended"]),
            "date_formed": match_date,
            "date_ended": None if random.random() > 0.3 else match_date + timedelta(days=5),
            "chat_theme": random.choice(["default", "dark-mode"]),
            "last_message": None
        })
    
    db.matches.insert_many(matches)
    return list(db.matches.find())