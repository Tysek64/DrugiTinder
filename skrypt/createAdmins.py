# create administrators

from config import config
from faker import Faker
import datetime
import createAccounts
import utils
import dbConnection

admins = {}

def populateAdmins ():
    print('Populating administrators...')

    for i in range(config['admins_number']):
        newAccount = createAccounts.createAccount()
        accountID = dbConnection.insertData('"user"', newAccount)[0]

        newAdmin = {}

        newAdmin['fk_user_id'] = accountID
        hiringTime = min(datetime.datetime.fromisoformat(list(newAccount.values())[0]['created_at']) + datetime.timedelta(days=utils.randomNumber(-1 * config['max_admin_hiring_difference'], config['max_admin_hiring_difference'])), datetime.datetime.now())
        newAdmin['hiring_date'] = datetime.date(hiringTime.year, hiringTime.month, hiringTime.day).isoformat()

        adminID = dbConnection.insertData('administrator', {0: newAdmin})[0]

        newAdmin['creation_date'] = list(newAccount.values())[0]['created_at']

        admins[accountID] = newAdmin

        if (i % 100) == 0 and i > 0:
            print(f'{i} / {config['admins_number']}')
