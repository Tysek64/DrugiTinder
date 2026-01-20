def create(db):
    print("Hardkodowanie planów subskrypcji...")
    plans = [
        {
            "name": "Free", "price_per_month": 0.00, "payment_cycle": "infinite",
            "max_users": 1, "features": ["Basic profile visibility"], "is_active": True
        },
        {
            "name": "Gold", "price_per_month": 19.99, "payment_cycle": "monthly",
            "max_users": 1, "features": ["Unlimited swipes", "See who likes you"], "is_active": True
        },
        {
            "name": "Platinum", "price_per_month": 49.99, "payment_cycle": "monthly",
            "max_users": 1, "features": ["Priority likes", "Travel mode", "No ads"], "is_active": True
        }
    ]
    result = db.subscription_plans.insert_many(plans)
    return list(result.inserted_ids)