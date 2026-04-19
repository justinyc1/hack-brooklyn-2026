from pymongo import MongoClient
from config import settings

client = MongoClient(settings.mongodb_uri)
db = client[settings.database_name]