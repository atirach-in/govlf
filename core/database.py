import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

user = os.getenv("MONGO_USER")
password = os.getenv("MONGO_PASS")
host = os.getenv("MONGO_HOST")
port = os.getenv("MONGO_PORT")
db_name = os.getenv("MONGO_DB")
auth_db = os.getenv("MONGO_AUTH_DB")

MONGO_URI = f"mongodb://{user}:{password}@{host}:{port}/{db_name}?authSource={auth_db}"
print(f"Connecting to MongoDB at {MONGO_URI}")
client = AsyncIOMotorClient(MONGO_URI)
db = client[db_name]