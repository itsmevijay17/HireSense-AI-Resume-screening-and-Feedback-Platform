from fastapi import FastAPI
from backend.app.api import hr_routes, job_seeker_routes, parsing_routes, scoring_routes
from backend.app.database import client  

app = FastAPI(title="Resume ATS API")

# Include routes
app.include_router(hr_routes.router, prefix="/hr", tags=["HR Module"])
app.include_router(job_seeker_routes.router, prefix="/jobseeker", tags=["Job Seeker Module"])
app.include_router(parsing_routes.router, prefix="/parser", tags=["Parsing Service"])
app.include_router(scoring_routes.router, prefix="/scoring", tags=["Resume Scoring"])

@app.get("/")
def root():
    return {"message": "Resume ATS API is running 🚀"}

@app.on_event("startup")
def startup_db_client():
    try:
        client.admin.command("ping")
        print("✅ Successfully connected to MongoDB!")
    except Exception as e:
        print("❌ MongoDB connection error:", e)

@app.on_event("shutdown")
def shutdown_db_client():
    client.close()
    print("🔌 MongoDB connection closed.")
