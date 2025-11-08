# utils for reading csv files and picking random choices

import csv
import random
from config import config
from faker import Faker

def readCSV (filename):
    result = {}
    with open(filename) as file:
        reader = csv.DictReader(file)
        for i in reader:
            result[list(i.values())[0]] = i
    return result

def randomChoice (mainDict, sumColumn):
    total = 0
    helperDict = {}

    for k, v in mainDict.items():
        total += int(v[sumColumn])
        helperDict[k] = int(v[sumColumn])

    rand = random.randint(0, total)
    for k, v in helperDict.items():
        rand -= v
        if rand <= 0:
            return k

def randomFairChoice (mainDict):
    return list(mainDict.keys())[random.randint(0, len(mainDict.keys()) - 1)]

def randomNumber (min, max):
    return random.randint(min, max)

def randomPercentageConfig (keyName):
    return randomNumber(0, 100) < config[keyName]

def getFake (locale, thingName):
    fake = Faker(locale)
    function = getattr(fake, thingName)
    return function()
