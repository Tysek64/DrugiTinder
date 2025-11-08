# create conversations linked to matches and messages in them

import utils
import dbConnection
import datetime
from createUsers import users
from createMatches import matches
from faker import Faker
from config import config
from messageGenerator import generateMessage

print('Populating conversations...')

def addMessages (conversation):
    messagesNumber = utils.randomNumber(0, config['max_conversation_length'])

    match = matches[conversation['fk_match_id']]
    person1 = match['fk_person1_id']
    person2 = match['fk_person2_id']

    startTime = datetime.datetime.fromisoformat(match['date_formed'])
    endTime = datetime.datetime.fromisoformat(match['date_ended'])

    ids = {}

    for i in range(messagesNumber):
        messageSendTime = startTime + i * ((endTime - startTime) / messagesNumber)
        message = {
			'send_time': messageSendTime.isoformat(),
			'contents': generateMessage(),
			'reaction': utils.randomNumber(0, 5),
            'fk_sender_id': utils.randomFairChoice({person1: None, person2: None}),
			'fk_conversation_id': conversation['id']
        }

        messageID = dbConnection.insertData('message', {0: message})[0]

        if len(ids.keys()) > 0 and utils.randomPercentageConfig('reply_ratio'):
            dbConnection.updateData('message', {messageID: utils.randomFairChoice(ids)}, 'id', 'fk_replying_to_message_id')

        ids[messageID] = None

def populateConversations ():
    for matchNumber, (matchID, match) in enumerate(matches.items()):

        currentConversation = {
			'fk_match_id': matchID,
			'chat_theme': 'dark' if utils.randomNumber(0, 10) == 0 else 'light',
			'chat_reaction': utils.randomNumber(-1, 5),
        }

        conversationID = dbConnection.insertData('conversation', {0: currentConversation})[0]
        currentConversation['id'] = conversationID

        addMessages(currentConversation)

        if matchNumber % 10 == 0 and matchNumber > 0:
            print(f'{matchNumber} / {len(matches.items())}')
