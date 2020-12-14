"""Load constants from config file."""


import os
import sys
from pathlib import Path
import yaml


###########################################
# Load config.yaml                        #
###########################################
PATH = os.path.dirname(os.path.abspath(__file__))
config_file = PATH + "/config.yaml"
my_file = Path(config_file)
if my_file.is_file():
    with open(config_file) as fp:
        config = yaml.safe_load(fp)
else:
    print("config.yaml file does not exists. Please make one  from config.sample.yaml file")
    sys.exit()


BOTNAME = config["BOT_USERNAME"]
BOT_VERSION = config["BOT_VERSION"]
TELEGRAM_BOT_TOKEN = config["BOT_TOKEN"]
ADMINS = config["ADMINS"]
GROUPS = config["GROUPS"]
MESSAGE_TYPES = config["MESSAGE_TYPES"]
SQLITE3_DB = config["SQLITE3_DB"]

# webhook
PUB_IP = config["PUB_IP"]
CERT = config["CERT"]
PRIV_KEY = config["PRIV_KEY"]
