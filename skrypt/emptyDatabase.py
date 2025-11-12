# clear data from all tables before populating database

import dbConnection

dbConnection.clearTable('country')
dbConnection.clearTable('city')

dbConnection.clearTable('sex')
dbConnection.clearTable('interest')
dbConnection.clearTable('subscription_plan')

dbConnection.clearTable('"user"')

dbConnection.clearTable('user_details')
dbConnection.clearTable('user_interest')
dbConnection.clearTable('image')

dbConnection.clearTable('billing_address')
dbConnection.clearTable('payment_data')
dbConnection.clearTable('subscription')

dbConnection.clearTable('search_preference')
dbConnection.clearTable('search_preference_sex')
dbConnection.clearTable('search_preference_interest')

dbConnection.clearTable('administrator')

dbConnection.clearTable('"report"')
dbConnection.clearTable('ban')

dbConnection.clearTable('swipe')
dbConnection.clearTable('"match"')
dbConnection.clearTable('block')

dbConnection.clearTable('conversation')
dbConnection.clearTable('message')
