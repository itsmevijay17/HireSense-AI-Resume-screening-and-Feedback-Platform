from datetime import datetime
from typing import Dict, Optional
import uuid

def resume_document(filename: str, parsed_data: Dict, bulk_upload_id: Optional[str] = None):
    if bulk_upload_id is None:
        bulk_upload_id = str(uuid.uuid4())   # fallback if not provided
    
    return {
        "bulk_upload_id": bulk_upload_id,    # ✅ group resumes by upload session
        "filename": filename,
        "parsed_data": parsed_data,
        "uploaded_at": datetime.utcnow(),
        "status": "parsed",                  # ✅ later can be "scored"
        "score": None                        # ✅ Hugging Face model will update this
    }
