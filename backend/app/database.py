import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()  # loads .env in dev

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("MONGO_DB", "resume_ats")

client = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]

# handy collection handles
resumes_coll = db["resumes"]
jds_coll = db["job_descriptions"]
