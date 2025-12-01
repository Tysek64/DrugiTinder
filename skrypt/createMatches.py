# create swipes and matches

import utils
import dbConnection
import datetime
from createUsers import users, checkIfCompatible
from createReports import bans, checkIfBanned, getLowestNotBannedDate
from createBlocks import blocks, generateBlock
from faker import Faker
from config import config

print('Populating swipes...')
swipes = {}
swiped = {}
matches = {}

def selectSwipedUser (swipingID):
    if len(swiped[swipingID]) == 0:
        return None

    swipedUser = swiped[swipingID][utils.randomNumber(0, len(swiped[swipingID]) - 1)]

    swiped[swipingID].remove(swipedUser)

    return swipedUser

def selectBlockedUser (blockingID):
    blockedUser = blockingID
    stepCounter = 0

    while blockedUser == blockingID or (blockingID in swipes.keys() and blockedUser in swipes[blockingID].keys() and swipes[blockingID][blockedUser]) or (blockingID in blocks.keys() and blockedUser in blocks[blockingID].keys()):
        blockedUser = utils.randomFairChoice(users)
        stepCounter += 1
        if stepCounter > config['users_number']:
            return None

    return blockedUser

def createMatch (user1, user2):
    # generate start time
    # it has to be greater than the maximum of account create times
    # no user can be banned or blocked at start time
    minTime = max(datetime.datetime.fromisoformat(users[user1]['creation_date']), datetime.datetime.fromisoformat(users[user2]['creation_date']))
    minDate = datetime.date(minTime.year, minTime.month, minTime.day)

    matchStartDate = minDate - datetime.timedelta(days=1)
    stepCounter = 0

    while matchStartDate < minDate or checkIfBanned(user1, matchStartDate) or checkIfBanned(user2, matchStartDate):
        matchStartDate = Faker().date_between(minDate, datetime.date.today())
        stepCounter += 1
        if stepCounter > (datetime.date.today() - minDate).days:
            matchStartDate = min(getLowestNotBannedDate(user1, minDate), getLowestNotBannedDate(user2, minDate))
            break

    # generate end time
    # it has to be greater than the start time
    # it has to end when:
    #   - any user gets banned
    #   - any user gets blocked
    #   - just like that

    matchEndDate = matchStartDate - datetime.timedelta(days=1)

    while matchEndDate < matchStartDate:
        matchEndDate = Faker().date_between(matchStartDate, datetime.date.today())

    if checkIfBanned(user1, matchEndDate) or checkIfBanned(user2, matchEndDate):
        matchEndDate = min(getLowestNotBannedDate(user1, matchEndDate), getLowestNotBannedDate(user2, matchEndDate))
        print('Ojoj - ktos tu zostal zbanowany')

    if matchEndDate > datetime.date.today():
        matchEndDate = None

    if utils.randomPercentageConfig('match_block_ratio'):
        generateBlock(user1, user2, matchEndDate, utils.randomNumber(0, config['max_match_block_difference']))

    currentMatch = {
            'fk_person1_id': user1,
            'fk_person2_id': user2,
            'date_formed': matchStartDate.isoformat(),
            'date_ended': matchEndDate.isoformat()
    }

    matchID = dbConnection.insertData('"match"', {0: currentMatch})[0]
    currentMatch['id'] = matchID

    matches[matchID] = currentMatch

def populateSwipes ():
    for userNumber, (userID, userData) in enumerate(users.items()):
        swiped[userID] = list(users.keys())
        swiped[userID].remove(userID)
        for i in range(utils.randomNumber(0, config['max_user_swipes'])):
            # generate swiping user
            swipingUser = userID

            # generate swiped user
            swipedUser = selectSwipedUser(swipingUser)

            if swipedUser is not None:
                # generate result
                result = utils.randomPercentageConfig('right_swipe_ratio')

                currentSwipe = {
                    'fk_swiping_user_details_id': swipingUser,
                    'fk_swiped_user_details_id': swipedUser,
                    'result': result
                }

                swipeID = dbConnection.insertData('swipe', {0: currentSwipe})[0]
                currentSwipe['id'] = swipeID

                if swipingUser not in swipes.keys():
                    swipes[swipingUser] = {}

                swipes[swipingUser][swipedUser] = result

                if swipedUser in swipes.keys() and swipingUser in swipes[swipedUser].keys():
                    if swipes[swipedUser][swipingUser] and swipes[swipingUser][swipedUser]:
                        createMatch(swipingUser, swipedUser)

        for i in range(100):
            if utils.randomPercentageConfig('user_block_ratio'):
                blockedUser = selectBlockedUser(userID)
                if blockedUser is not None:
                    generateBlock(userID, blockedUser, max(datetime.datetime.fromisoformat(users[userID]['creation_date']), datetime.datetime.fromisoformat(users[blockedUser]['creation_date'])))

        if userNumber % 10 == 0 and userNumber > 0:
            print(f'{userNumber} / {len(users.items())}')
