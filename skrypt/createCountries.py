# create countries and cities in these countries

from config import config
from faker import Faker
import dbConnection
import math
import utils

countries = utils.readCSV('parsedCountries.csv')

def populateGeoData():
    print('Populating countries...')

    ids = dbConnection.insertData('country', countries, ['name', 'iso_code'])

    for (id, (k, v)) in zip(ids, countries.items()):
        v['id'] = id
        if not config['enable_locale']:
            v['locale'] = None

    print('Populating cities...')
    for v, j in zip(countries.values(), range(len(countries.values()))):
        fake = Faker(v['locale'])

        citiesToInsert = {}
        for i in range(int(10 * math.log10(int(v['population'])))):
            try:
                cityName = fake.unique.city()
            except:
                cityName = fake.city()
            citiesToInsert[i] = {'name': cityName, 'fk_country_id': v['id']}
        ids = dbConnection.insertData('city', citiesToInsert)
        countries[v['name']]['cities'] = {id: city for (id, city) in zip(ids, citiesToInsert.values())}

        if j % 10 == 0 and j > 0:
            print(f'{j} / {len(countries.values())}')
