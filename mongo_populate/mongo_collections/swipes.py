import random
from faker import Faker
import settings

fake = Faker()

def create(db, user_ids, matched_pairs_set):
    count = settings.COUNTS["SWIPES"]
    print(f"Generowanie {count} swipes...")
    swipes = []
    
    user_pool = list(user_ids)
    
    # For 1:12 ratio (True:False), ~7.7% should be True
    # Using weighted choice: 1 True, 12 False
    LIKE_PROBABILITY = 1 / 13  # approximately 7.7%
    
    # Larger batch size for handling 30M swipes efficiently
    BATCH_SIZE = 50000
    
    attempts = 0
    while len(swipes) < count and attempts < count * 2:
        attempts += 1
        u1, u2 = random.sample(user_pool, 2)
        
        pair_key = tuple(sorted([str(u1), str(u2)]))
        if pair_key in matched_pairs_set:
            continue
        
        result = random.random() < LIKE_PROBABILITY  # 1:12 ratio True:False
        
        swipes.append({
            "swiper_id": u1,
            "swiped_id": u2,
            "result": result,
            "swipe_time": fake.date_time_between(start_date='-1y', end_date='now')
        })
        
        # batchowanie - larger batch for better performance with 30M swipes
        if len(swipes) >= BATCH_SIZE:
            db.swipes.insert_many(swipes)
            swipes = []
    
    if swipes:
        db.swipes.insert_many(swipes)