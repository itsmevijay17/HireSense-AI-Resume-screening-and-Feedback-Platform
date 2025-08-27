from fastapi import APIRouter

router = APIRouter()

@router.get("/test")
def test_jobseeker():
    return {"status": "Job Seeker route is working!"}
