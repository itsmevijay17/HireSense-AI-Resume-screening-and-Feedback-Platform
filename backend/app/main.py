# backend/app/main.py
from fastapi import FastAPI
from backend.app.api import hr_routes, job_seeker_routes, parsing_routes

app = FastAPI(title="Resume ATS API")

# Include routes
app.include_router(hr_routes.router, prefix="/hr", tags=["HR Module"])
app.include_router(job_seeker_routes.router, prefix="/jobseeker", tags=["Job Seeker Module"])
app.include_router(parsing_routes.router, prefix="/parser", tags=["Parsing Service"])

@app.get("/")
def root():
    return {"message": "Resume ATS API is running 🚀"}
