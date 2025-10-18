from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from backend.app.services.parsing_service import ResumeParserService
from backend.app.models.db_models import resume_document
from backend.app.database import db, resumes_collection

import os
import tempfile
import shutil
from typing import List
import uuid

router = APIRouter()
parser = ResumeParserService()


@router.post("/upload-resumes")
async def upload_resumes(
    resumes: List[UploadFile] = File(...),
    bulk_upload_id: str = Form(None)
):
    """
    Upload multiple resumes for a single HR session.
    Each session is grouped by bulk_upload_id.
    """
    if not bulk_upload_id:
        bulk_upload_id = str(uuid.uuid4())  # create new session if not provided

    results = []
    os.makedirs("temp_files", exist_ok=True)

    for file in resumes:
        file_path = f"temp_files/{file.filename}"

        # Save temporarily
        with open(file_path, "wb") as f:
            f.write(await file.read())

        # Parse
        parsed = parser.parse_single_resume(file_path)

        # Wrap into DB schema
        doc = resume_document(file.filename, parsed, bulk_upload_id)
        inserted = resumes_collection.insert_one(doc)
        doc["_id"] = str(inserted.inserted_id)  # include MongoDB _id for frontend

        results.append(doc)

        # Clean temp file
        try:
            os.remove(file_path)
        except Exception:
            pass

    return {
        "bulk_upload_id": bulk_upload_id,
        "uploaded": len(results),
        "resumes": [{"filename": r["filename"], "_id": r["_id"]} for r in results]
    }


@router.post("/parse-resume")
async def parse_resume(file: UploadFile = File(...)):
    """
    Accept a single resume upload (PDF) and return structured data.
    Also stores parsed resume data in MongoDB.
    """
    try:
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only .pdf files are supported.")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            shutil.copyfileobj(file.file, tmp)
            temp_path = tmp.name

        result = parser.parse_single_resume(temp_path)

        try:
            os.remove(temp_path)
        except Exception:
            pass

        mongo_doc = resume_document(file.filename, result)
        inserted = resumes_collection.insert_one(mongo_doc)
        mongo_doc["_id"] = str(inserted.inserted_id)

        return {
            "filename": file.filename,
            "parsed_data": result,
            "_id": mongo_doc["_id"]
        }

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

    os.makedirs("temp_files", exist_ok=True)

    for file in files:
        if not file.filename.lower().endswith(".pdf"):
            results.append({
                "filename": file.filename,
                "error": "Only .pdf files are supported."
            })
            continue

        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                shutil.copyfileobj(file.file, tmp)
                temp_path = tmp.name

            parsed_result = parser.parse_single_resume(temp_path)

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
        inserted = resumes_collection.insert_many(mongo_docs)
        # attach _id to results
        for i, doc_id in enumerate(inserted.inserted_ids):
            if i < len(results) and "parsed_data" in results[i]:
                results[i]["_id"] = str(doc_id)

    return {
        "bulk_upload_id": bulk_upload_id,
        "processed": len(files),
        "successful": len([r for r in results if "parsed_data" in r]),
        "failed": len([r for r in results if "error" in r]),
        "results": results
    }


@router.get("/resumes")
async def get_resumes(bulk_upload_id: str):
    """
    Fetch all resume IDs and filenames for a given bulk_upload_id.
    Returns a list of objects with 'id' and 'filename'.
    """
    docs = list(resumes_collection.find({"bulk_upload_id": bulk_upload_id}, {"_id": 1, "filename": 1}))
    return [{"id": str(doc["_id"]), "filename": doc["filename"]} for doc in docs]
