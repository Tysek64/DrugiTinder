import random
from faker import Faker
import settings

fake = Faker(['pl_PL', 'en_US']) 

def normalize(text):
    replacements = {
        'ą': 'a', 'ć': 'c', 'ę': 'e', 'ł': 'l', 'ń': 'n',
        'ó': 'o', 'ś': 's', 'ź': 'z', 'ż': 'z', ' ': ''
    }
    text = text.lower()
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text

def generate_identity(fname, lname):
    f = normalize(fname)
    l = normalize(lname)
    
    format_choice = random.choices(
        population=['standard', 'number', 'short', 'reversed', 'random'], 
        weights=[30, 30, 15, 10, 15], 
        k=1
    )[0]

    if format_choice == 'standard':
        sep = random.choice(['.', '_', ''])
        username = f"{f}{sep}{l}"
        
    elif format_choice == 'number':
        num = random.randint(1, 999)
        sep = random.choice(['.', '_', ''])
        base = random.choice([f"{f}{l}", f"{f}{sep}{l[0]}", f"{f}"])
        username = f"{base}{num}"
        
    elif format_choice == 'short':
        username = f"{f[0]}.{l}"
        
    elif format_choice == 'reversed':
        username = f"{l}.{f}"
        
    else: 
        username = fake.user_name()

    email_domain = fake.free_email_domain()
    email_choice = random.choices(['match_user', 'match_name', 'random'], weights=[50, 40, 10], k=1)[0]

    if email_choice == 'match_user':
        email_user = username
    elif email_choice == 'match_name':
        email_user = f"{f}.{l}"
    else:
        email_user = fake.user_name() + str(random.randint(1, 99))

    return username, f"{email_user}@{email_domain}"

def create(db, plan_ids):
    count = settings.COUNTS["USERS"]
    print(f"Generowanie {count} użytkowników (realistyczny chaos)...")
    users = []
    interests_pool = ['Hiking', 'Cooking', 'Gaming', 'Netflix', 'Gym', 'Travel', 'Music', 'Art', 'Coding', 'Dancing']
    
    for _ in range(count):
        sex = random.choice(['Male', 'Female'])
        pref_sex = 'Female' if sex == 'Male' else 'Male'
        
        if sex == 'Male':
            fname = fake.first_name_male()
            lname = fake.last_name_male()
        else:
            fname = fake.first_name_female()
            lname = fake.last_name_female()
            
        username, email = generate_identity(fname, lname)

        user = {
            "username": username,
            "email": email,
            "password_hash": fake.sha256(),
            "profile": {
                "name": fname,
                "surname": lname,
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
                    for i in random.sample(interests_pool, k=random.randint(2, 4))
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
        }
        users.append(user)
        
    result = db.users.insert_many(users)
    return list(result.inserted_ids)