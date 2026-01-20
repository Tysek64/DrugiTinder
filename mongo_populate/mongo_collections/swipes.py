import random
from faker import Faker
import settings

fake = Faker()

def create(db, user_ids):
    count = settings.COUNTS["SWIPES"]
    print(f"Generowanie {count} swipe'ów...")
    swipes = []
    
    for _ in range(count):
        u1, u2 = random.sample(user_ids, 2)
        swipes.append({
            "swiper_id": u1,
            "swiped_id": u2,
            "result": random.choice([True, False]),
            "swipe_time": fake.date_time_between(start_date='-1y', end_date='now')
        })
    db.swipes.insert_many(swipes)