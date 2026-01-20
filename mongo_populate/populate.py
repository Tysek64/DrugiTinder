import db_manager
from mongo_collections import (
    admins, matches, messages, reports, 
    subscription_plans, swipes, users
)

def run():
    db = db_manager.get_database()
    db_manager.reset_database(db)
    
    plan_ids = subscription_plans.create(db)
    admin_ids = admins.create(db)
    user_ids = users.create(db, plan_ids)
    
    matches_data, matched_pairs_set = matches.create(db, user_ids)
    
    swipes.create(db, user_ids, matched_pairs_set)
    
    messages.create(db, matches_data)
    reports.create(db, user_ids, admin_ids)
    
    return True