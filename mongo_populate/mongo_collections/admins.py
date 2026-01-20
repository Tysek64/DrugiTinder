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

def generate_admin_identity(fname, lname):
    f = normalize(fname)
    l = normalize(lname)
    
    domains = ['corp.datingapp.com', 'admin.tinderclone.net', 'staff.company.com']
    domain = random.choice(domains)
    
    strategy = random.choices(
        ['standard', 'short', 'role_based', 'technical'],
        weights=[40, 30, 20, 10], 
        k=1
    )[0]
    
    if strategy == 'standard':
        username = f"{f}.{l}"
        
    elif strategy == 'short':
        username = f"{f[0]}{l}"
        
    elif strategy == 'role_based':
        prefix = random.choice(['admin', 'mod', 'support', 'staff'])
        username = f"{prefix}_{f}"
        
    else: 
        prefix = random.choice(['root', 'dev', 'sysops'])
        username = f"{prefix}_{l}"

    email = f"{f}.{l}@{domain}"
    
    return username, email

def create(db):
    count = settings.COUNTS["ADMINS"]
    print(f"Generowanie {count} administratorów...")
    admins = []
    
    for _ in range(count):
        fname = fake.first_name()
        lname = fake.last_name()
        
        username, email = generate_admin_identity(fname, lname)
        
        admins.append({
            "username": username,
            "email": email,
            "password_hash": fake.sha256(),
            "name": fname,
            "surname": lname,
            "hiring_date": fake.date_time_between(start_date='-5y', end_date='-2y'),
            "created_at": fake.date_time_between(start_date='-2y', end_date='now')
        })
        
    result = db.admins.insert_many(admins)
    return list(result.inserted_ids)