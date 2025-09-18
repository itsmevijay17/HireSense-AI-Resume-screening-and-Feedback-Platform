from pymongo import MongoClient

# Replace with your actual Atlas connection string
MONGO_URI = "mongodb+srv://vijayrv1719:H6WaPYBSACOixe9Q@cluster0-resumeproj.haqrozr.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0-Resumeproj"

client = MongoClient(MONGO_URI)
db = client["Cluster0-Resumeproj"]   # use your DB name
resumes_collection = db["resumes"]
