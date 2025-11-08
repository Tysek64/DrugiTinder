# create reports and bans

import utils
import dbConnection
import datetime
from createUsers import users
from createAdmins import admins
from faker import Faker
from config import config

print('Populating reports...')
reasons = utils.readCSV('reportReasons.csv')
bans = {}

def checkIfBanned (userID, checkDate):
    for ban in bans[userID]:
        if checkDate >= ban[0] and checkDate <= ban[1]:
            return True
    return False

def getLowestNotBannedDate (userID, checkDate):
    result = datetime.date.today()
    for ban in bans[userID]:
        if checkDate >= ban[0] and checkDate <= ban[1]:
            result = min(result, ban[0])
    return result

def generateBan (report):
    startDate = min(datetime.date.today(), datetime.date.fromisoformat(report['report_date']) + datetime.timedelta(days=utils.randomNumber(0, config['max_report_ban_difference'])))
    duration = utils.randomNumber(config['min_ban_length'], config['max_ban_length'])
    endDate = startDate + datetime.timedelta(days=duration)

    ban = {
		'fk_user_id': report['fk_reported_user_id'],
		'fk_report_id': report['id'],
		'start_date': startDate.isoformat(),
		'period_days': duration,
		'is_active': endDate >= datetime.date.today(),
    }

    dbConnection.insertData('ban', {0: ban})
    if ban['fk_user_id'] not in bans.keys():
        bans[ban['fk_user_id']] = [(startDate, endDate)]
    else:
        bans[ban['fk_user_id']].append((startDate, endDate))

def updateAdminStats (adminStats):
    dbConnection.updateData('administrator', adminStats, 'fk_account_id', 'reports_handled')

def populateReports ():
    adminReportStats = {}

    for i in range(int(config['users_number'] * config['user_report_ratio'] / 100)):
        # generate reporting user
        reportingUser = utils.randomFairChoice(users)

        # generate reported user
        reportedUser = reportingUser
        while reportedUser == reportingUser:
            reportedUser = utils.randomFairChoice(users)

        # generate reason
        reason = utils.randomChoice(reasons, 'freq')

        # generate report date
        minDate = max(datetime.datetime.fromisoformat(users[reportingUser]['creation_date']), datetime.datetime.fromisoformat(users[reportedUser]['creation_date']))
        reportDate = Faker().date_time_between(minDate, datetime.datetime.now())

        currentReport = {
            'reason': reason,
            'report_date': datetime.date(reportDate.year, reportDate.month, reportDate.day).isoformat(),
            'fk_reporting_user_id': reportingUser,
            'fk_reported_user_id': reportedUser,
            'fk_administrator_id': utils.randomFairChoice(admins)
        }

        reportID = dbConnection.insertData('"report"', {0: currentReport})[0]
        currentReport['id'] = reportID

        # generate ban!!!
        if utils.randomPercentageConfig('report_ban_ratio'):
            generatedBan = generateBan(currentReport)

            adminReportStats[currentReport['fk_administrator_id']] = 1 + adminReportStats.get(currentReport['fk_administrator_id'], 0)

        if i % 100 == 0 and i > 0:
            print(f'{i} / {int(config['users_number'] * config['user_report_ratio'] / 100)}')

    updateAdminStats(adminReportStats)
