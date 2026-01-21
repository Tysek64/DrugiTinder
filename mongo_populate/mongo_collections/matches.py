import random
from datetime import timedelta
from faker import Faker
import settings

fake = Faker()

def create(db, user_ids):
    count = settings.COUNTS["MATCHES"]
    print(f"Generowanie {count} matchow...")
    
    matches = []
    required_swipes = []
    
    matched_pairs = set()

    for _ in range(count):
        u1, u2 = random.sample(user_ids, 2)
        
        pair_key = tuple(sorted([str(u1), str(u2)]))
        if pair_key in matched_pairs:
            continue
        matched_pairs.add(pair_key)

        match_date = fake.date_time_between(start_date='-1y', end_date='now')

        swipe_time_1 = match_date - timedelta(hours=random.randint(1, 48))
        swipe_time_2 = match_date - timedelta(minutes=random.randint(1, 59))

        required_swipes.append({
            "swiper_id": u1,
            "swiped_id": u2,
            "result": True, 
            "swipe_time": swipe_time_1
        })
        required_swipes.append({
            "swiper_id": u2,
            "swiped_id": u1,
            "result": True, 
            "swipe_time": swipe_time_2
        })

        match_obj = {
            "members": [u1, u2],
            "status": random.choice(["active", "active", "ended"]), 
            "date_formed": match_date,
            "date_ended": None,
            "chat_theme": random.choice(["default", "dark-mode", "love-theme"]),
            "last_message": None
        }

        if match_obj["status"] == "ended":
             match_obj["date_ended"] = match_date + timedelta(days=random.randint(1, 30))
        
        matches.append(match_obj)

    if matches:
        db.matches.insert_many(matches)
    if required_swipes:
        db.swipes.insert_many(required_swipes)
        
    print(f"Utworzono {len(matches)} matchow i {len(required_swipes)} swipów sukcesu.")
    
    return list(db.matches.find()), matched_pairs