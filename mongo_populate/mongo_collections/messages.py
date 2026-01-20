import random
from faker import Faker
import settings

fake = Faker()

def create(db, matches_data):
    count = settings.COUNTS["MESSAGES"]
    print(f"Generowanie {count} wiadomości...")
    messages = []
    last_msg_map = {}

    for _ in range(count):
        match = random.choice(matches_data)
        sender_id = random.choice(match['members'])
        send_time = fake.date_time_between(start_date=match['date_formed'], end_date='now')
        text = fake.sentence()

        messages.append({
            "match_id": match['_id'],
            "sender_id": sender_id,
            "contents": text,
            "send_time": send_time,
            "reaction": random.choice([None, 1, 2])
        })
        
        last_msg_map[match['_id']] = {
            "sender_id": sender_id, "text": text, "timestamp": send_time
        }

        if len(messages) >= 2000:
            db.messages.insert_many(messages)
            messages = []

    if messages:
        db.messages.insert_many(messages)

    print("Aktualizacja statusów ostatnich wiadomości...")
    for m_id, l_msg in last_msg_map.items():
        db.matches.update_one({"_id": m_id}, {"$set": {"last_message": l_msg}})