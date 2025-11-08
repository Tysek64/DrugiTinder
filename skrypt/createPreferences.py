# create search preferences

import utils
import dbConnection
from createHardcoded import sexes, interests

def createSearchPreference ():
    return {None: {'search_description': 'Ja nawet nie wiem, co tu wpisac...'}}

def populateSearchPreference (preferenceID, userSex):
    # create SP sexes
    sexesNumber = {
            0: {'freq': 5},
            1: {'freq': 80},
            2: {'freq': 20},
            3: {'freq': 10},
            4: {'freq': 5},
            5: {'freq': 2}
    }

    parsedSexes = {sexName:
                   {'totalNazo': 
                       int(sex['nazoNumber3']) if (int(sexes[userSex]['nazoNumber0']) > 3) else (
                       int(sex['nazoNumber1']) if (int(sexes[userSex]['nazoNumber0']) < -3) else
                       int(sex['nazoNumber2']))
                   } for sexName, sex in sexes.items()}

    interestedSexes = {sex: {
        'fk_search_preference_id': preferenceID,
        'fk_sex_id': sexes[sex]['id'],
        'priorty': j
    } for j, sex in enumerate([utils.randomChoice(parsedSexes, 'totalNazo') for i in range(utils.randomChoice(sexesNumber, 'freq'))], start=1)}

    dbConnection.insertData('search_preference_sex', interestedSexes)

    # create SP interests
    interestsNumber = {i: {'freq': -0.6 * ((i - 5) ** 2) + 20} for i in range(11)}

    interestedInterests = {interest: {
        'fk_search_preference_id': preferenceID,
        'fk_interest_id': interests[interest]['id'],
        'level_of_interest': utils.randomNumber(1, 10),
        'is_positive': utils.randomNumber(0, 1) == 0
    } for j, interest in enumerate([utils.randomFairChoice(interests) for i in range(utils.randomChoice(interestsNumber, 'freq'))], start=1)}

    dbConnection.insertData('search_preference_interest', interestedInterests)

    return [sex['fk_sex_id'] for sex in interestedSexes.values()]
