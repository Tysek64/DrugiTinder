import random
from faker import Faker
import settings

fake = Faker()

def create(db, user_ids, admin_ids):
    count = settings.COUNTS["REPORTS"]
    print(f"Generowanie {count} reports...")
    reports = []
    reasons = ["Harassment", "Fake Profile", "Spam", "Hate Speech", "Inappropriate Content"]
    decisions = ["warning", "ban", "dismissed"]
    
    for _ in range(count):
        reporter, reported = random.sample(user_ids, 2)
        report_date = fake.date_time_between(start_date='-2m', end_date='-1m')
        
        # 30% pending, 10% dismissed, 60% resolved
        status_choice = random.random()
        if status_choice < 0.3:
            status = "pending"
        elif status_choice < 0.4:
            status = "dismissed"
        else:
            status = "resolved"
        
        report = {
            "reporting_user_id": reporter,
            "reported_user_id": reported,
            "reason": random.choice(reasons),
            "status": status,
            "report_date": report_date
        }
        
        # Only add admin_action for resolved/dismissed reports (not pending)
        if status != "pending":
            report["admin_action"] = {
                "administrator_id": random.choice(admin_ids),
                "decision": random.choice(decisions),
                "reviewed_at": fake.date_time_between(start_date=report_date, end_date='now')
            }
        
        reports.append(report)
    
    db.reports.insert_many(reports)