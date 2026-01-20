from faker import Faker
import settings

fake = Faker(['pl_PL'])

def create(db):
    count = settings.COUNTS["ADMINS"]
    print(f"Generowanie {count} administratorów...")
    admins = []
    for _ in range(count):
        admins.append({
            "username": fake.user_name(),
            "email": fake.company_email(),
            "password_hash": fake.sha256(),
            "name": fake.first_name(),
            "surname": fake.last_name(),
            "hiring_date": fake.date_time_between(start_date='-5y', end_date='-1y'),
            "created_at": fake.date_time_between(start_date='-1y', end_date='now')
        })
    result = db.admins.insert_many(admins)
    return list(result.inserted_ids)