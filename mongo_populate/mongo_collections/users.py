import random
from faker import Faker
import settings
from datetime import timedelta

fake = Faker(['pl_PL', 'en_US']) 

# Gender definitions with weights (normalized to sum ~100 for main genders)
# 60% Male, 35% Female, 5% others
GENDERS = [
    ("Male", 60),
    ("Female", 35),
    ("Agender", 0.4),
    ("Ambigender", 0.2),
    ("Androgynous", 0.6),
    ("Bigender", 0.5),
    ("Binary", 0.3),
    ("Genderfluid", 0.4),
    ("Genderless", 0.3),
    ("Gender nonconforming", 0.3),
    ("Neither", 0.5),
    ("Non-binary", 0.5),
    ("Non-binary man", 0.2),
    ("Non-binary transgender", 0.15),
    ("Non-binary woman", 0.2),
    ("Omnigender", 0.1),
    ("Other", 0.3),
    ("Queer", 0.4),
    ("Third gender", 0.15),
    ("Transgender", 0.3),
    ("Transfeminine", 0.15),
    ("Transmasculine", 0.15),
    ("Transandrogynous", 0.1),
    ("Transsexual", 0.15),
]

GENDER_NAMES = [g[0] for g in GENDERS]
GENDER_WEIGHTS = [g[1] for g in GENDERS]

# Groups for name generation
MASCULINE_GENDERS = {"Male", "Non-binary man", "Transmasculine", "Binary"}
FEMININE_GENDERS = {"Female", "Non-binary woman", "Transfeminine"}
# Others will use random gender for name generation

def pick_gender():
    return random.choices(GENDER_NAMES, weights=GENDER_WEIGHTS, k=1)[0]

def generate_preferences(user_gender):
    """
    Generate preferred genders list.
    - ~70% choose exactly 1 main gender (Male or Female)
    - ~20% choose both main genders
    - ~10% add some non-binary/other options
    """
    pref_choice = random.random()
    
    if pref_choice < 0.70:
        # Single main gender preference
        if user_gender in MASCULINE_GENDERS:
            return ["Female"]
        elif user_gender in FEMININE_GENDERS:
            return ["Male"]
        else:
            return [random.choice(["Male", "Female"])]
    
    elif pref_choice < 0.90:
        # Both main genders
        return ["Male", "Female"]
    
    else:
        # Include some non-binary options
        base = ["Male", "Female"] if random.random() < 0.5 else [random.choice(["Male", "Female"])]
        others = [g for g in GENDER_NAMES if g not in ("Male", "Female")]
        extras = random.sample(others, k=random.randint(1, 3))
        return list(set(base + extras))

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

def create(db, plan_ids, admin_ids):
    count = settings.COUNTS["USERS"]
    print(f"Generowanie {count} użytkowników...")
    users = []
    interests_pool = ['Hiking', 'Cooking', 'Gaming', 'Netflix', 'Gym', 'Travel', 'Music', 'Art', 'Coding', 'Dancing']
    ban_reasons = [
        "Repeated harassment", 
        "Fake profile", 
        "Scam activity", 
        "Inappropriate photos", 
        "Hate speech"
    ]
    for _ in range(count):
        sex = pick_gender()
        pref_sex = generate_preferences(sex)
        
        # Generate name based on gender category
        if sex in MASCULINE_GENDERS:
            fname = fake.first_name_male()
            lname = fake.last_name_male()
        elif sex in FEMININE_GENDERS:
            fname = fake.first_name_female()
            lname = fake.last_name_female()
        else:
            # Random for non-binary/other genders
            if random.random() < 0.5:
                fname = fake.first_name_male()
                lname = fake.last_name_male()
            else:
                fname = fake.first_name_female()
                lname = fake.last_name_female()
            
        username, email = generate_identity(fname, lname)

        is_banned = random.random() < 0.001  # 0.1% of users are banned
        ban_details = None

        if is_banned:
            ban_date = fake.date_time_between(start_date='-1m', end_date='now')
            ban_details = {
                "reason": random.choice(ban_reasons),
                # Ban wygasa za 1 do 365 dni od momentu nałożenia
                "expires_at": ban_date + timedelta(days=random.randint(1, 365)),
                "issued_by": random.choice(admin_ids)
            }

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
                "preferred_sex": pref_sex,
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
            "is_banned": is_banned,
            **({"ban_details": ban_details} if is_banned else {}),
            "created_at": fake.date_time_between(start_date='-2y', end_date='-1y')
        }
        users.append(user)
        
    result = db.users.insert_many(users)
    return list(result.inserted_ids)