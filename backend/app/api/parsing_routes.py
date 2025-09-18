from fastapi import APIRouter, UploadFile, File, HTTPException
from backend.app.services.parsing_service import ResumeParserService
from backend.app.database import resumes_collection
from backend.app.models.db_models import resume_document
import os
import tempfile
import shutil
from typing import List
from datetime import datetime
import uuid

router = APIRouter()
parser = ResumeParserService()


@router.post("/parse-resume")
async def parse_resume(file: UploadFile = File(...)):
    """
    Accept a single resume upload (PDF) and return structured data.
    Also stores parsed resume data in MongoDB.
    """
    try:
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only .pdf files are supported right now.")

        # Save to a temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            shutil.copyfileobj(file.file, tmp)
            temp_path = tmp.name

        # Parse resume
        result = parser.parse_single_resume(temp_path)

        # Clean up
        try:
            os.remove(temp_path)
        except Exception:
            pass

        # Create DB doc (single upload → new bulk_upload_id auto-generated)
        mongo_doc = resume_document(file.filename, result)
        resumes_collection.insert_one(mongo_doc)

        return {
            "filename": file.filename,
            "parsed_data": result
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/parse-bulk-resumes")
async def parse_bulk_resumes(files: List[UploadFile] = File(...)):
    """
    Accept multiple resumes (PDFs), parse them, and store in MongoDB.
    Groups all resumes under the same bulk_upload_id.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    bulk_upload_id = str(uuid.uuid4())
    results, mongo_docs = [], []

    for file in files:
        if not file.filename.lower().endswith(".pdf"):
            results.append({
                "filename": file.filename,
                "error": "Only .pdf files are supported."
            })
            continue

        try:
            # Save to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                shutil.copyfileobj(file.file, tmp)
                temp_path = tmp.name

            # Parse
            parsed_result = parser.parse_single_resume(temp_path)

            # Build schema doc
            mongo_doc = resume_document(file.filename, parsed_result, bulk_upload_id)
            mongo_docs.append(mongo_doc)

            results.append({
                "filename": file.filename,
                "parsed_data": parsed_result
            })

        except Exception as e:
            results.append({
                "filename": file.filename,
                "error": str(e)
            })

        finally:
            try:
                os.remove(temp_path)
            except Exception:
                pass

    if mongo_docs:
        resumes_collection.insert_many(mongo_docs)

    return {
        "bulk_upload_id": bulk_upload_id,
        "processed": len(files),
        "successful": len([r for r in results if "parsed_data" in r]),
        "failed": len([r for r in results if "error" in r]),
        "results": results
    }
