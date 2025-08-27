# backend/app/api/hr_routes.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/test")
def test_hr():
    return {"status": "HR route is working!"}

# backend/app/api/job_seeker_routes.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/test")
def test_jobseeker():
    return {"status": "Job Seeker route is working!"}
