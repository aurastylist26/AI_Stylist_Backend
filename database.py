from motor.motor_asyncio import AsyncIOMotorClient

# Notice the quotation marks at the very beginning and very end of the link!
MONGO_URL = "mongodb+srv://officialaurastylist26:aurastylist123@cluster26.bohww7c.mongodb.net/aura_saas?retryWrites=true&w=majority"

client = AsyncIOMotorClient(MONGO_URL)
db = client.aura_saas
users_collection = db.users