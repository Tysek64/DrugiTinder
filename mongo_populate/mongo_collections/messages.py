import random
from faker import Faker
import settings
from datetime import timedelta
from pymongo import UpdateOne
from datetime import datetime

fake = Faker()

def create(db, matches_data):
    count = settings.COUNTS["MESSAGES"]
    print(f"Generowanie {count} wiadomości...")
    
    if not matches_data:
        print("Nie wygenerowano matchów")
        return

    messages = []
    last_msg_map = {} 

    for _ in range(count):
        match = random.choice(matches_data)
        
        sender_id = random.choice(match['members'])
        
        match_start = match['date_formed']
        
        match_end = match.get('date_ended') or datetime.now()
        
        if match_end <= match_start:
            match_end = match_start + timedelta(hours=1)
            
        send_time = fake.date_time_between(start_date=match_start, end_date=match_end)
        
        text = fake.sentence()

        message = {
            "match_id": match['_id'],
            "sender_id": sender_id,
            "contents": text,
            "send_time": send_time
        }
        
        # Only add reaction if not None (avoid null fields)
        reaction = random.choice([None, None, None, 1, 2])
        if reaction is not None:
            message["reaction"] = reaction
        
        messages.append(message)
        
        last_msg_map[match['_id']] = {
            "sender_id": sender_id, "text": text, "timestamp": send_time
        }

        # batchowanie - larger batch for better performance with 15M messages
        BATCH_SIZE = 50000
        if len(messages) >= BATCH_SIZE:
            db.messages.insert_many(messages)
            messages = []

    if messages:
        db.messages.insert_many(messages)

    print("Aktualizacja 'last_message' w matches...")
    operations = []
    for m_id, l_msg in last_msg_map.items():
        operations.append(
            UpdateOne({"_id": m_id}, {"$set": {"last_message": l_msg}})
        )
    
    if operations:
        db.matches.bulk_write(operations)