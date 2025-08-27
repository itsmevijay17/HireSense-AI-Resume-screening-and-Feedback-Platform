from datetime import datetime
from typing import Dict, Any, Optional
from bson import ObjectId
from backend.app.database import resumes_coll, jds_coll

def _now():
    return datetime.utcnow()

def _oid(s: str) -> ObjectId:
    return ObjectId(s)

async def save_parsed_resume(structured: Dict[str, Any], source: str = "job_seeker") -> str:
    doc = {
        **structured,
        "source": source,
        "created_at": _now(),
        "updated_at": _now(),
        # make sure optional fields exist
        "skills": structured.get("skills", {}),
        "evaluations": structured.get("evaluations", []),
    }
    res = await resumes_coll.insert_one(doc)
    return str(res.inserted_id)

async def create_job_description(raw_text: str,
                                 title: Optional[str] = None,
                                 company: Optional[str] = None,
                                 location: Optional[str] = None,
                                 extracted_skills: Optional[list[str]] = None) -> str:
    doc = {
        "title": title,
        "company": company,
        "location": location,
        "raw_text": raw_text,
        "extracted_skills": extracted_skills or [],
        "created_by": None,
        "created_at": _now(),
        "updated_at": _now(),
    }
    res = await jds_coll.insert_one(doc)
    return str(res.inserted_id)
