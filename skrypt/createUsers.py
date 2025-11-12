# create users and all(?) additional tables

from config import config
from faker import Faker
from createCountries import countries
from createHardcoded import sexes, interests
from createPreferences import createSearchPreference, populateSearchPreference
from createSubscriptions import createSubscription
import datetime
import createAccounts
import utils
import dbConnection

uniquePathProvider = Faker()

users = {}

def checkIfCompatible (user1, user2):
    return users[user2]['fk_sex_id'] in users[user1]['interested_sexes']

def populateInterests (userID):
    interestsNumber = {i: {'freq': -0.15 * ((i - 10) ** 2) + 20} for i in range(21)}

    userInterests = {interest: {
        'fk_user_details_id': userID,
        'fk_interest_id': interests[interest]['id'],
        'level_of_interest': utils.randomNumber(1, 10),
        'is_positive': utils.randomNumber(0, 1) == 0
    } for j, interest in enumerate([utils.randomFairChoice(interests) for i in range(utils.randomChoice(interestsNumber, 'freq'))], start=1)}

    dbConnection.insertData('user_interest', userInterests)

def populateImages (userID, creationDate):
    imagesNumber = {i: {'freq': -0.15 * ((i - 10) ** 2) + 20} for i in range(21)}

    userImages = {j: {
        'file_path': uniquePathProvider.unique.file_path(depth=2, absolute=False, category='image'),
        'uploaded_at': uploadDate.isoformat(),
        'is_current': utils.randomNumber(0, config['oldest_current_photo']) > (datetime.datetime.now() - uploadDate).days,
        'file_size_bytes': utils.randomNumber(500 * 1024, 5 * 1024 * 1024),
        'is_verified': utils.randomNumber(0, config['oldest_unverified_photo']) < (datetime.datetime.now() - uploadDate).days,
        'fk_user_details_id': userID
    } for j, uploadDate in enumerate([
            Faker().date_time_between(datetime.datetime.fromisoformat(creationDate), datetime.datetime.now())
        for i in range(utils.randomChoice(imagesNumber, 'freq'))])}

    dbConnection.insertData('image', userImages)

def populateUsers ():
    print('Populating users...')

    for i in range(config['users_number']):
        newAccount = createAccounts.createAccount()
        accountID = dbConnection.insertData('"user"', newAccount)[0]

        searchPreference = createSearchPreference()
        preferenceID = dbConnection.insertData('search_preference', searchPreference)[0]

        currentCountry = utils.randomChoice(countries, 'population')
        countryID = countries[currentCountry]['id']
        currentLocale = countries[currentCountry]['locale'] if utils.randomPercentageConfig('migration_ratio') else None

        cities = countries[currentCountry]['cities']

        newUser = {}

        newUser['name'] = utils.getFake(currentLocale, 'first_name')
        newUser['surname'] = utils.getFake(currentLocale, 'last_name')

        userSex = utils.randomChoice(sexes, 'frequencyIGuess')
        newUser['fk_city_id'] = utils.randomFairChoice(cities)
        newUser['fk_sex_id'] = sexes[userSex]['id']
        newUser['fk_user_id'] = accountID
        newUser['fk_search_preference_id'] = preferenceID

        userID = dbConnection.insertData('user_details', {0: newUser})[0]

        newUser['interested_sexes'] = populateSearchPreference(preferenceID, userSex)
        populateInterests(userID)
        populateImages(userID, list(newAccount.values())[0]['created_at'])

        if utils.randomPercentageConfig('subscription_ratio'):
            newUser['fk_subscription_id'] = createSubscription(userID, currentCountry, newUser['fk_city_id'], list(newAccount.values())[0]['created_at'])
            dbConnection.updateData('user_details', {userID: newUser['fk_subscription_id']}, 'id', 'fk_subscription_id')
        newUser['creation_date'] = list(newAccount.values())[0]['created_at']

        users[userID] = newUser

        if (i % 100) == 0 and i > 0:
            print(f'{i} / {config['users_number']}')
