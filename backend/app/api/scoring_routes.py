from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import StreamingResponse
from typing import List, Optional
from backend.app.database import resumes_collection
from backend.app.services.huggingface_service import HuggingFaceScoringService
from bson import ObjectId
import csv
import io
import pdfplumber

router = APIRouter()
hf_service = HuggingFaceScoringService()

@router.post("/score-resumes")
async def score_resumes(
    jd_file: UploadFile = File(...),
    resume_ids: Optional[List[str]] = Query(default=None),
    download: bool = Query(default=False, description="Set true to download CSV")
):
    try:
        # ✅ Read file as bytes
        file_bytes = await jd_file.read()

        # ✅ Extract text from PDF
        jd_text = ""
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                jd_text += page.extract_text() or ""

        if not jd_text.strip():
            raise HTTPException(status_code=400, detail="Unable to extract text from Job Description PDF.")

        # ✅ Convert resume_ids to ObjectId
        if resume_ids:
            try:
                object_ids = [ObjectId(rid) for rid in resume_ids]
            except Exception:
                raise HTTPException(status_code=400, detail="Invalid resume_id format")
            query = {"_id": {"$in": object_ids}}
        else:
            query = {}

        resumes = list(resumes_collection.find(query))

        if not resumes:
            raise HTTPException(status_code=404, detail="No resumes found in database.")

        results = []
        for resume in resumes:
            parsed_data = resume.get("parsed_data", {})
            evaluation = hf_service.evaluate_resume(jd_text, parsed_data)

            result = {
                "resume_id": str(resume["_id"]),
                "filename": resume.get("filename"),
                "ats_score": evaluation["ats_score"],
                "feedback": evaluation["feedback"],
                "improvements": evaluation["improvements"],
                "reason": evaluation["reason"],
                "cover_letter": evaluation["cover_letter"]
            }
            results.append(result)

        # Sort by ATS score
        results = sorted(results, key=lambda x: x["ats_score"], reverse=True)

        # ✅ If HR wants CSV
        if download:
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
            output.seek(0)

            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=resume_scores.csv"}
            )

        return {"jd": jd_text, "results": results}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server Error: {str(e)}")