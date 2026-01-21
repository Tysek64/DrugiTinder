from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client['tinder_big']

stats = db.command('dbstats')
print(f"Database size: {stats['dataSize'] / 1024 / 1024:.2f} MB")
print(f"Storage size: {stats['storageSize'] / 1024 / 1024:.2f} MB")

for collection_name in db.list_collection_names():
    coll_stats = db.command('collStats', collection_name)
    print(f"{collection_name}: {coll_stats['size'] / 1024 / 1024:.2f} MB")