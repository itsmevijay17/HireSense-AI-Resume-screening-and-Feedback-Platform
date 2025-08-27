# backend/app/api/parsing_routes.py
from fastapi import APIRouter, UploadFile, File, HTTPException
from backend.app.services.parsing_service import ResumeParserService
import os
import tempfile
import shutil
from pymongo import MongoClient
from datetime import datetime

router = APIRouter()
parser = ResumeParserService()

# MongoDB connection (Update URI if needed)
client = MongoClient("mongodb://localhost:27017/")
db = client["ats_db"]   # database
resumes_collection = db["resumes"]   # collection


@router.post("/parse-resume")
async def parse_resume(file: UploadFile = File(...)):
    """
    Accept a single resume upload (PDF) and return extracted text.
    Saves to a system temp file (works on Windows/macOS/Linux), then parses.
    Also stores parsed resume data in MongoDB.
    """
    try:
        # Basic validation (PDF only for now)
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only .pdf files are supported right now.")

        # Create a temp file path in the OS temp directory
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            shutil.copyfileobj(file.file, tmp)
            temp_path = tmp.name

        # Parse using your service (expects a file path)
        result = parser.parse_single_resume(temp_path)

        # Clean up temp file
        try:
            os.remove(temp_path)
        except Exception:
            pass

        # Insert parsed data into MongoDB
        mongo_doc = {
            "filename": file.filename,
            "parsed_data": result,
            "uploaded_at": datetime.utcnow()
        }
        resumes_collection.insert_one(mongo_doc)

        return {
            "filename": file.filename,
            "parsed_data": result  # {file_name, content, error}
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
