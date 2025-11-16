from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

uri = "mongodb+srv://NasirAhmad:Sagheer123@tta-login-cluster.3ocooiw.mongodb.net/?appName=TTA-Login-Cluster"

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

db = client.UserDB
collection = db["userData"]