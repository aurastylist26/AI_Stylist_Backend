from motor.motor_asyncio import AsyncIOMotorClient

# We are bypassing the environment variables completely for this test!
# PASTE YOUR EXACT MONGODB LINK INSIDE THESE QUOTES:
MONGO_URL = "mongodb+srv://officialaurastylist26:aurastylist123@cluster26.bohww7c.mongodb.net/aura_saas?retryWrites=true&w=majority"

client = AsyncIOMotorClient(mongodb+srv://officialaurastylist26:aurastylist123@cluster26.bohww7c.mongodb.net/aura_saas?retryWrites=true&w=majority)
db = client.aura_saas
users_collection = db.users