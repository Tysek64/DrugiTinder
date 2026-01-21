import random
from pymongo import MongoClient, UpdateOne
import settings

# location bucket size; 10 degrees = ~1100km at equator
GRID_SIZE = 10

def get_location_bucket(coords):
    """Round coordinates to grid bucket (lon, lat) -> (bucket_lon, bucket_lat)"""
    if not coords or len(coords) < 2:
        return (0, 0)
    lon, lat = coords[0], coords[1]
    return (int(lon // GRID_SIZE) * GRID_SIZE, int(lat // GRID_SIZE) * GRID_SIZE)

def fill_potential_swipes():
    client = MongoClient(settings.MONGO_URI)
    db = client[settings.DB_NAME]
    
    print("Step 1: Building location+gender pools (server-side aggregation)...")
    
    # (location_bucket, gender) -> [user_ids]
    # Using aggregation to do grouping server-side
    pipeline = [
        {"$project": {
            "_id": 1,
            "sex": "$profile.sex",
            "lon_bucket": {"$multiply": [{"$floor": {"$divide": [{"$arrayElemAt": ["$profile.location.coordinates", 0]}, GRID_SIZE]}}, GRID_SIZE]},
            "lat_bucket": {"$multiply": [{"$floor": {"$divide": [{"$arrayElemAt": ["$profile.location.coordinates", 1]}, GRID_SIZE]}}, GRID_SIZE]}
        }},
        {"$group": {
            "_id": {"lon": "$lon_bucket", "lat": "$lat_bucket", "sex": "$sex"},
            "users": {"$push": "$_id"},
            "count": {"$sum": 1}
        }}
    ]
    
    # Build pools indexed by (bucket, gender)
    location_gender_pools = {}
    total_buckets = 0
    
    for doc in db.users.aggregate(pipeline, allowDiskUse=True):
        bucket = (doc["_id"]["lon"], doc["_id"]["lat"])
        gender = doc["_id"]["sex"]
        key = (bucket, gender)
        
        # Sample up to 500 per bucket+gender to keep memory reasonable
        users = doc["users"]
        if len(users) > 500:
            users = random.sample(users, 500)
        
        location_gender_pools[key] = users
        total_buckets += 1
    
    print(f"  Created {total_buckets} location+gender buckets")
    
    print("\nStep 2: Bulk updating users with location-aware suggestions...")
    
    BATCH_SIZE = 50000
    processed = 0
    operations = []
    
    cursor = db.users.find(
        {}, 
        {"_id": 1, "search_preferences.preferred_sex": 1, "profile.location.coordinates": 1}
    ).batch_size(BATCH_SIZE)
    
    for user in cursor:
        user_id = user["_id"]
        coords = user.get("profile", {}).get("location", {}).get("coordinates", [0, 0])
        bucket = get_location_bucket(coords)
        preferred_sexes = user.get("search_preferences", {}).get("preferred_sex", ["Male", "Female"])
        
        candidates = []
        
        # First try same location bucket
        for pref in preferred_sexes:
            key = (bucket, pref)
            if key in location_gender_pools and location_gender_pools[key]:
                pool = location_gender_pools[key]
                candidates.extend(random.sample(pool, min(2, len(pool))))
        
        # If not enough, check neighboring buckets
        if len(candidates) < 3:
            for dx in [-GRID_SIZE, 0, GRID_SIZE]:
                for dy in [-GRID_SIZE, 0, GRID_SIZE]:
                    if dx == 0 and dy == 0:
                        continue
                    neighbor = (bucket[0] + dx, bucket[1] + dy)
                    for pref in preferred_sexes:
                        key = (neighbor, pref)
                        if key in location_gender_pools and location_gender_pools[key]:
                            pool = location_gender_pools[key]
                            candidates.extend(random.sample(pool, min(1, len(pool))))
        
        # Remove self and duplicates, pick 3-5
        candidates = list(set(c for c in candidates if c != user_id))
        potential_swipes = candidates[:random.randint(3, 5)]
        
        operations.append(
            UpdateOne(
                {"_id": user_id},
                {"$set": {"potential_swipes": potential_swipes}}
            )
        )
        
        if len(operations) >= BATCH_SIZE:
            db.users.bulk_write(operations, ordered=False)
            processed += len(operations)
            print(f"  Processed {processed} users...")
            operations = []
    
    if operations:
        db.users.bulk_write(operations, ordered=False)
        processed += len(operations)
    
    print(f"\nDone! Updated {processed} users.")

if __name__ == "__main__":
    settings.apply_args()
    fill_potential_swipes()
