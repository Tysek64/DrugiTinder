import yaml

config = None

with open('config.yml') as file:
    config = yaml.load(file, Loader=yaml.CLoader)
