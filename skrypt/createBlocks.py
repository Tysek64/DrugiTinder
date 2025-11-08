# create blocks between users

import utils
import dbConnection
import datetime
from createUsers import users
from faker import Faker
from config import config

blocks = {}

def generateBlock (blockingID, blockedID, minDate=None, maxDifference=None):
    startDate = min(datetime.date.today(), Faker().date_between(minDate, datetime.date.today() if maxDifference is None else minDate + datetime.timedelta(days=maxDifference)))
    duration = utils.randomNumber(config['min_block_length'], config['max_block_length'])
    endDate = startDate + datetime.timedelta(days=duration)

    block = {
		'fk_blocking_user_id': blockingID,
		'fk_blocked_user_id': blockedID,
        'start_date': startDate.isoformat(),
        'is_active': endDate >= datetime.date.today()
    }

    dbConnection.insertData('block', {0: block}, returnID=False)

    if blockingID not in blocks.keys():
        blocks[blockingID] = {}

    blocks[blockingID][blockedID] = (startDate, endDate)
