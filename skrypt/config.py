import yaml
import os

config = None

with open("config.yml") as file:
    config = yaml.load(file, Loader=yaml.CLoader)

if os.environ.get("DB_HOST"):
    config["host"] = os.environ.get("DB_HOST")
if os.environ.get("DB_PORT"):
    config["port"] = os.environ.get("DB_PORT")
if os.environ.get("DB_USER"):
    config["username"] = os.environ.get("DB_USER")
if os.environ.get("DB_PASS"):
    config["password"] = os.environ.get("DB_PASS")
if os.environ.get("DB_NAME"):
    config["database_name"] = os.environ.get("DB_NAME")
