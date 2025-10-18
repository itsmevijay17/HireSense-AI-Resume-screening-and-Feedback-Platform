# backend/app/api/hr_routes.py - FIXED VERSION
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import StreamingResponse
from backend.app.services.hr_service import HRService, score_resumes_with_llm, get_resume_statistics
from backend.app.database import resumes_collection
from typing import Optional, List
import fitz  # PyMuPDF
import io
from datetime import datetime

router = APIRouter()

@router.post("/score-resumes")
async def score_resumes(
    jd_file: Optional[UploadFile] = File(None),
    jd_text: Optional[str] = Form(None),
    bulk_upload_id: Optional[str] = Form(None),
    use_llm: bool = Form(True),
    download: bool = Form(False)
):
    """
    Score all resumes from a bulk_upload_id against a job description.
    FIXED: Now properly passes resume documents to HRService instead of IDs.
    """
    try:
        # --- Extract Job Description ---
        job_description = ""
        if jd_text:
            job_description = jd_text.strip()
        elif jd_file:
            if jd_file.content_type == "text/plain":
                job_description = (await jd_file.read()).decode("utf-8").strip()
            elif jd_file.content_type == "application/pdf":
                doc = fitz.open(stream=await jd_file.read(), filetype="pdf")
                job_description = "".join([page.get_text() for page in doc])
                doc.close()
        if not job_description:
            raise HTTPException(status_code=400, detail="Job description is required.")

        # --- Fetch resumes using bulk_upload_id ---
        if not bulk_upload_id:
            raise HTTPException(status_code=400, detail="bulk_upload_id is required to fetch resumes.")
        
        resumes_to_score = list(resumes_collection.find({"bulk_upload_id": bulk_upload_id}))
        print(f"[HR_ROUTES] Found {len(resumes_to_score)} resumes for bulk_upload_id: {bulk_upload_id}")

        if not resumes_to_score:
            raise HTTPException(status_code=404, detail="No resumes found for this bulk_upload_id.")

        # --- Score resumes - FIXED: Pass resume documents directly ---
        service = HRService(use_llm=use_llm)
        # Convert ObjectIds to strings for compatibility
        for resume in resumes_to_score:
            resume["_id"] = str(resume["_id"])
        
        # Use the new method that accepts resume documents
        results = service.score_batch_from_documents(job_description, resumes_to_score)

        if download:
            csv_bytes = service.make_csv_bytes(results)
            filename = f"resume_scores_{bulk_upload_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            return StreamingResponse(
                io.BytesIO(csv_bytes),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )

        statistics = get_resume_statistics(results)

        return {
            "success": True,
            "message": f"Successfully analyzed {len(results)} resumes from session {bulk_upload_id} using {'LLM' if use_llm else 'keyword matching'}",
            "bulk_upload_id": bulk_upload_id,
            "results": results,
            "statistics": statistics,
            "analysis_type": "llm_analysis" if use_llm else "keyword_matching",
            "job_description_preview": job_description[:200] + "..." if len(job_description) > 200 else job_description
        }

    except Exception as e:
        print(f"[HR_ROUTES] Error in score_resumes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@router.post("/score-resumes-by-session")
async def score_resumes_by_session(
    jd_text: Optional[str] = Form(None),
    jd_file: Optional[UploadFile] = File(None),
    bulk_upload_id: str = Form(...),  # REQUIRED - which session to score
    use_llm: bool = Form(True)
):
    """
    NEW ENDPOINT: Score ONLY resumes from a specific upload session.
    This is the main endpoint the HR module should use.
    """
    try:
        # Get job description
        job_description = ""
        if jd_text:
            job_description = jd_text.strip()
        elif jd_file:
            if jd_file.content_type == "text/plain":
                content = await jd_file.read()
                job_description = content.decode("utf-8").strip()
            elif jd_file.content_type == "application/pdf":
                doc = fitz.open(stream=await jd_file.read(), filetype="pdf")
                job_description = "".join([page.get_text() for page in doc])
                doc.close()
        
        if not job_description:
            raise HTTPException(status_code=400, detail="Job description required")

        # Get ONLY resumes from this session
        session_resumes = list(resumes_collection.find({"bulk_upload_id": bulk_upload_id}))
        
        if not session_resumes:
            raise HTTPException(
                status_code=404, 
                detail=f"No resumes found for session {bulk_upload_id}"
            )

        print(f"[HR_ROUTES] Scoring {len(session_resumes)} resumes from session {bulk_upload_id}")

        # Convert ObjectIds to strings
        for resume in session_resumes:
            resume["_id"] = str(resume["_id"])

        # Score using HRService with documents
        service = HRService(use_llm=use_llm)
        results = service.score_batch_from_documents_chunked(job_description, session_resumes, batch_size=2)  # Adjust batch_size as needed

        # Add statistics
        statistics = get_resume_statistics(results)
        
        return {
            "success": True,
            "message": f"Successfully analyzed {len(results)} resumes from session {bulk_upload_id}",
            "bulk_upload_id": bulk_upload_id,
            "results": results,
            "statistics": statistics,
            "analysis_type": "llm_analysis" if use_llm else "keyword_matching"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[HR_ROUTES] Error in score_resumes_by_session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.post("/score-resumes-llm")
async def score_resumes_llm_endpoint(
    jd_text: Optional[str] = Form(None),
    jd_file: Optional[UploadFile] = File(None)
):
    """
    Score ALL resumes in database against a job description using LLM.
    LEGACY ENDPOINT - scores all resumes, not session-specific.
    """
    try:
        # --- Extract Job Description ---
        job_description = ""
        if jd_text:
            job_description = jd_text.strip()
        elif jd_file:
            if jd_file.content_type == "text/plain":
                job_description = (await jd_file.read()).decode("utf-8").strip()
            elif jd_file.content_type == "application/pdf":
                doc = fitz.open(stream=await jd_file.read(), filetype="pdf")
                job_description = "".join([page.get_text() for page in doc])
                doc.close()
            else:
                raise HTTPException(status_code=400, detail="Job description file must be .txt or .pdf format")
        else:
            raise HTTPException(status_code=400, detail="Please provide either jd_text or jd_file")

        if not job_description or len(job_description) < 50:
            raise HTTPException(status_code=400, detail="Job description is too short or empty.")

        # --- Score all resumes using LLM ---
        result = score_resumes_with_llm(job_description)
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["message"])

        result["statistics"] = get_resume_statistics(result["results"])
        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@router.post("/export-csv")
async def export_csv(
    jd_text: Optional[str] = Form(None),
    jd_file: Optional[UploadFile] = File(None),
    bulk_upload_id: Optional[str] = Form(None),
    use_llm: bool = Form(True)
):
    """
    Export resume analysis results as CSV file.
    FIXED: Now handles session-based export properly.
    """
    try:
        # --- Extract Job Description ---
        job_description = ""
        if jd_text:
            job_description = jd_text.strip()
        elif jd_file:
            if jd_file.content_type == "text/plain":
                job_description = (await jd_file.read()).decode("utf-8").strip()
            elif jd_file.content_type == "application/pdf":
                doc = fitz.open(stream=await jd_file.read(), filetype="pdf")
                job_description = "".join([page.get_text() for page in doc])
                doc.close()
        if not job_description:
            raise HTTPException(status_code=400, detail="Job description is required.")

        # --- Fetch resumes using bulk_upload_id ---
        if not bulk_upload_id:
            raise HTTPException(status_code=400, detail="bulk_upload_id is required to fetch resumes.")
        
        resumes_to_score = list(resumes_collection.find({"bulk_upload_id": bulk_upload_id}))

        if not resumes_to_score:
            raise HTTPException(status_code=404, detail="No resumes found for this bulk_upload_id.")

        # Convert ObjectIds to strings
        for resume in resumes_to_score:
            resume["_id"] = str(resume["_id"])

        # --- Score resumes ---
        service = HRService(use_llm=use_llm)
        results = service.score_batch_from_documents(job_description, resumes_to_score)

        if not results:
            raise HTTPException(status_code=404, detail="No resumes found to analyze.")

        csv_bytes = service.make_csv_bytes(results)
        filename = f"resume_analysis_{bulk_upload_id}_{'llm' if use_llm else 'keyword'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        return StreamingResponse(
            io.BytesIO(csv_bytes),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating CSV: {str(e)}")

@router.get("/resume-statistics")
async def get_latest_statistics():
    """Get statistics info."""
    try:
        return {
            "message": "Statistics are generated when you run resume scoring.",
            "available_endpoints": {
                "score_resumes": "Score resumes by bulk_upload_id",
                "score-resumes-by-session": "NEW: Score resumes by session (recommended)",
                "score_resumes-llm": "Score all resumes with LLM (legacy)",
                "export_csv": "Export results to CSV"
            },
            "note": "Use /score-resumes-by-session for session-based analysis."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting statistics info: {str(e)}")