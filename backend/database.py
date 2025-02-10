from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = "mongodb://localhost:27017"
client = AsyncIOMotorClient(MONGO_URL)
db = client["game_db"]  # Створюємо базу даних
characters_collection = db["characters"]
food_collection = db["food"]