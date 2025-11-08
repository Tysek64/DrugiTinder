print('Reading config file...')
from config import config

import dbConnection
print('Connecting to database...')
dbConnection.openConnection(config['database_name'], config['username'])

print('Erasing all data...')
import emptyDatabase

import createCountries
createCountries.populateGeoData()

import createHardcoded
createHardcoded.populateHardcodedData()

import createUsers
createUsers.populateUsers()

import createAdmins
createAdmins.populateAdmins()

import createReports
createReports.populateReports()

import createMatches
createMatches.populateSwipes()

import createConversations
createConversations.populateConversations()

print('Committing changes and closing connection...')
dbConnection.closeConnection()
