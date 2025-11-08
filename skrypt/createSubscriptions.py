# create subscription data for users

import utils
import dbConnection
import datetime
import base64
from createHardcoded import plans
from createCountries import countries
from faker import Faker
from config import config

def createSubscription (userID, userCountry, userCity, creationDate):
    # create subscription data
    selectedPlan = plans[utils.randomChoice(plans, 'users')]
    lastRenewal = Faker().date_between(datetime.datetime.fromisoformat(creationDate), datetime.datetime.now())

    expirationDate = lastRenewal
    if selectedPlan['payment_cycle'] == 'OneTime':
        expirationDate = datetime.date(2038, 1, 19)
    elif selectedPlan['payment_cycle'] == 'Yearly':
        expirationDate = lastRenewal + datetime.timedelta(days=365)
    elif selectedPlan['payment_cycle'] == 'Monthly':
        expirationDate = lastRenewal + datetime.timedelta(days=30)

    active = datetime.date.today() < expirationDate

    autoRenewal = False
    if active and selectedPlan['payment_cycle'] != 'OneTime':
        autoRenewal = utils.randomPercentageConfig('auto_renewal_ratio')

    # create billing address
    billingAddressCity = userCity

    if utils.randomPercentageConfig('domestic_migration_ratio'):
        billingAddressCity = utils.randomFairChoice(countries[userCountry]['cities'])
    if utils.randomPercentageConfig('international_migration_ratio'):
        billingAddressCity = utils.randomFairChoice(countries[utils.randomFairChoice(countries)]['cities'])

    billingAddress = {0: {
                      'fk_city_id': billingAddressCity,
                      'street': utils.getFake(countries[userCountry]['locale'], 'street_address'),
                      'postal_code': utils.getFake(countries[userCountry]['locale'], 'postcode')
    }}
    billingAddressID = dbConnection.insertData('billing_address', billingAddress)[0]

    # create payment data
    paymentData = {0: {
                   'token': base64.b64encode(bytes(hash(utils.getFake(None, 'credit_card_full')).__str__(), 'ascii')).__str__()[2:-2],
                   'fk_billing_address_id': billingAddressID
    }}
    paymentDataID = dbConnection.insertData('payment_data', paymentData)[0]

    # insert subscription data
    fullData = {0: {
                'expiration_date': expirationDate.isoformat(),
                'last_renewal': lastRenewal.isoformat(),
                'is_active': active,
                'auto_renewal': autoRenewal,
                'fk_subscription_plan_id': selectedPlan['id'],
                'fk_payment_data_id': paymentDataID
    }}
    return dbConnection.insertData('subscription', fullData)[0]
