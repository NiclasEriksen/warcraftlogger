import os


APP_PUB_KEY = os.getenv("APP_PUB_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")
WARCRAFT_LOGS_CLIENT_ID = os.getenv("WARCRAFT_LOGS_CLIENT_ID")
WARCRAFT_LOGS_SECRET = os.getenv("WARCRAFT_LOGS_SECRET")
APP_ID = os.getenv("APP_ID")
try:
    GUILD_ID = int(os.getenv("WARCRAFT_LOGS_GUILD_ID"))
except TypeError:
    GUILD_ID = -1

#SERVER_IDS = [442452004430675968, 1183366538414276689]
#GUILD_ID = 726684



CLASS_NAME = {
    0: "Unknown",
    1: "Paladin",
    2: "Druid",
    3: "Hunter",
    4: "Mage",
    7: "Priest",
    8: "Rogue",
    9: "Shaman",
    10: "Warlock",
    11: "Warrior",
}


WARCRAFT_LOGS_AUTH_URL = "https://www.warcraftlogs.com/oauth/token"
WARCRAFT_LOGS_API_URL = "https://www.warcraftlogs.com/api/v2/client"
