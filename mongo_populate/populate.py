import db_manager
from mongo_collections import (
    admins, matches, messages, reports, 
    subscription_plans, swipes, users
)

def run(reset_db=True):
    db = db_manager.get_database()
    if reset_db: db_manager.reset_database(db)
    
    plan_ids = subscription_plans.create(db)
    admin_ids = admins.create(db)
    
    user_ids = users.create(db, plan_ids)
    
    swipes.create(db, user_ids)
    matches_data = matches.create(db, user_ids)
    
    messages.create(db, matches_data)
    
    reports.create(db, user_ids, admin_ids)
    
    return True