from fastapi import APIRouter, UploadFile, File, Query, HTTPException
from fastapi.responses import StreamingResponse
from backend.app.services.hr_service import HRService
import fitz  # PyMuPDF

router = APIRouter()

@router.post("/score-resumes")
async def score_resumes(
    jd_file: UploadFile = File(...),
    resume_ids: list[str] = Query(...),
    download: bool = Query(False)
):
    try:
        # Extract JD text
        doc = fitz.open(stream=await jd_file.read(), filetype="pdf")
        job_description = "".join([page.get_text() for page in doc])

        service = HRService(hf_detailed=True, top_k_details=5)
        results = service.score_batch(job_description, resume_ids)

        if download:
            csv_bytes = service.make_csv_bytes(results)
            return StreamingResponse(
                iter([csv_bytes]),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=resume_scores.csv"},
            )

        return {"results": results}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
