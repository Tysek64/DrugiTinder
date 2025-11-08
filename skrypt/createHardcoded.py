# create hardcoded data, such as sexes, interests and subscription plans

import utils
import dbConnection

sexes = utils.readCSV('sexes.csv')
interests = utils.readCSV('interests.csv')
plans = utils.readCSV('plans.csv')

def populateHardcodedData ():
    print('Populating sexes...')

    ids = dbConnection.insertData('sex', sexes, ['name'])

    for (id, (k, v)) in zip(ids, sexes.items()):
        v['id'] = id

    print('Populating interests...')

    ids = dbConnection.insertData('interest', interests)

    for (id, (k, v)) in zip(ids, interests.items()):
        v['id'] = id

    print('Populating subscription plans...')

    ids = dbConnection.insertData('subscription_plan', plans, ['name', 'price', 'payment_cycle', 'benefits'])

    for (id, (k, v)) in zip(ids, plans.items()):
        v['id'] = id
