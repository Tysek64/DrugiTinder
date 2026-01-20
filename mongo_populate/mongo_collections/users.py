import random
from faker import Faker
import settings

fake = Faker(['pl_PL', 'en_US'])

def create(db, plan_ids):
    count = settings.COUNTS["USERS"]
    print(f"Generowanie {count} użytkowników...")
    users = []
    interests_pool = ['Hiking', 'Cooking', 'Gaming', 'Netflix', 'Gym', 'Travel', 'Music', 'Art']
    
    for _ in range(count):
        sex = random.choice(['Male', 'Female'])
        pref_sex = 'Female' if sex == 'Male' else 'Male'
        
        users.append({
            "username": fake.unique.user_name(),
            "email": fake.unique.email(),
            "password_hash": fake.sha256(),
            "profile": {
                "name": fake.first_name_male() if sex == 'Male' else fake.first_name_female(),
                "surname": fake.last_name(),
                "sex": sex,
                "location": {
                    "type": "Point",
                    "coordinates": [float(fake.longitude()), float(fake.latitude())]
                },
                "images": [
                    {"file_path": f"/img/{fake.uuid4()}.jpg", "is_current": True, "is_verified": True},
                    {"file_path": f"/img/{fake.uuid4()}.jpg", "is_current": False, "is_verified": False}
                ],
                "interests": [
                    {"name": i, "level": random.randint(1, 10), "is_positive": True} 
                    for i in random.sample(interests_pool, k=2)
                ]
            },
            "search_preferences": {
                "description": fake.sentence(),
                "preferred_sex": [pref_sex],
                "interests": [{"name": random.choice(interests_pool), "level": 5, "is_positive": True}]
            },
            "subscription": {
                "plan_id": random.choice(plan_ids),
                "expiration_date": fake.date_time_between(start_date='now', end_date='+1y'),
                "is_active": True
            },
            "payment_data": {
                "token": f"tok_{fake.uuid4()}",
                "billing_info": {"billing_address": fake.address(), "postal_code": fake.postcode()}
            },
            "potential_swipes": [],
            "is_banned": False,
            "created_at": fake.date_time_between(start_date='-2y', end_date='-1y')
        })
        
    result = db.users.insert_many(users)
    return list(result.inserted_ids)