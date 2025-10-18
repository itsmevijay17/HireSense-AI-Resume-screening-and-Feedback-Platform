from pymongo import MongoClient

# Replace with your actual Atlas connection string
MONGO_URI = "your mongo url here"

client = MongoClient(MONGO_URI)
db = client["use your DB name"]   # use your DB name
resumes_collection = db["ur collection name"]
