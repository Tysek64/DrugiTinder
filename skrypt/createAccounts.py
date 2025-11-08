# create accounts and admins

import datetime
import utils
from faker import Faker

uniqueNameProvider = Faker()

def createAccount ():
    username = uniqueNameProvider.unique.user_name()
    email = uniqueNameProvider.unique.email()
    password = hash(uniqueNameProvider.password()).__str__()
    createTime = uniqueNameProvider.date_time_between(datetime.datetime(2004, 9, 5, 13, 0), datetime.datetime.now()).isoformat()

    return {username: {'username': username, 'email': email, 'password_hash': password, 'created_at': createTime}}
