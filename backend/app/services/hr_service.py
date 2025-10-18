import io
import csv
from typing import List, Dict, Any, Optional
from bson import ObjectId
from datetime import datetime
from backend.app.database import resumes_collection
from backend.app.services.LLM_Service import analyze_multiple_resumes
import numpy as np
import traceback
import re

def _to_objectids(ids: List[str]) -> List[ObjectId]:
    """Convert string IDs to ObjectId with validation."""
    try:
        return [ObjectId(i) for i in ids if ObjectId.is_valid(i)]
    except Exception as e:
        print(f"[HR] Invalid ObjectId conversion: {e}")
        return []

def _cosine(a: List[float], b: List[float]) -> float:
    """Cosine similarity with better error handling."""
    try:
        a, b = np.array(a, dtype=np.float32), np.array(b, dtype=np.float32)
        norm_product = (np.linalg.norm(a) * np.linalg.norm(b))
        if norm_product == 0:
            return 0.0
        return float(np.dot(a, b) / norm_product)
    except Exception as e:
        print(f"[HR] Cosine similarity error: {e}")
        return 0.0

class HRService:
    def __init__(self, hf_detailed: bool = True, top_k_details: int = 5, use_llm: bool = True):
        self.hf_detailed = hf_detailed
        self.top_k_details = top_k_details
        self.use_llm = use_llm

    def fetch_resumes(self, resume_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Fetch resumes from MongoDB with better error handling."""
        try:
            if resume_ids:
                object_ids = _to_objectids(resume_ids)
                if not object_ids:
                    print("[HR] No valid resume IDs provided")
                    return []
                docs = list(resumes_collection.find({"_id": {"$in": object_ids}}))
            else:
                docs = list(resumes_collection.find({}))
            
            print(f"[HR] Fetched {len(docs)} resumes from database")
            return docs
        except Exception as e:
            print(f"[HR] Database fetch error: {e}")
            traceback.print_exc()
            return []

    def score_batch_from_documents(self, jd_text: str, resume_documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Score resumes from provided document list (not from database).
        This method accepts resume documents directly instead of fetching from DB.
        """
        if not jd_text or not jd_text.strip():
            raise ValueError("Job description cannot be empty")
            
        if not resume_documents:
            print("[HR] No resume documents provided")
            return []

        print(f"[HR] Starting scoring for {len(resume_documents)} provided documents")
        
        try:
            if self.use_llm:
                return self._score_documents_llm(jd_text, resume_documents)
            else:
                return self._score_documents_keyword(jd_text, resume_documents)
                
        except Exception as e:
            print(f"[HR] Error in score_batch_from_documents: {e}")
            traceback.print_exc()
            # Fallback to keyword matching
            return self._score_documents_keyword(jd_text, resume_documents)

    def score_batch_from_documents_chunked(self, jd_text: str, resume_documents: List[Dict[str, Any]], batch_size: int = 2) -> List[Dict[str, Any]]:
        """
        Score resumes in batches to avoid LLM token limits.
        """
        all_results = []
        for i in range(0, len(resume_documents), batch_size):
            batch = resume_documents[i:i+batch_size]
            if self.use_llm:
                batch_results = self._score_documents_llm(jd_text, batch)
            else:
                batch_results = self._score_documents_keyword(jd_text, batch)
            all_results.extend(batch_results)
        return all_results

    def _score_documents_llm(self, jd_text: str, docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Score provided documents using LLM."""
        # Limit to 2 for testing (remove this in production)
        
        print(f"[HR] Using LLM to score {len(docs)} documents")
        
        try:
            from backend.app.services.LLM_Service import analyze_multiple_resumes
            
            # Convert string IDs back to proper format for LLM service
            processed_docs = []
            for doc in docs:
                # Handle both string and ObjectId formats
                doc_copy = doc.copy()
                if isinstance(doc_copy.get("_id"), str):
                    # Keep as string for LLM service compatibility
                    pass
                processed_docs.append(doc_copy)
            
            llm_results = analyze_multiple_resumes(processed_docs, jd_text)
            
            # Convert to expected format
            results = []
            for llm_result in llm_results:
                analysis = llm_result.get("analysis", {})
                
                # Find corresponding document
                doc = None
                resume_id = llm_result.get("resume_id", "")
                for d in processed_docs:
                    if str(d["_id"]) == resume_id:
                        doc = d
                        break
                
                # Extract candidate info
                candidate_name = "Unknown"
                email = "Not found"
                if doc:
                    personal_info = doc.get("parsed_data", {}).get("personal_info", {})
                    candidate_name = personal_info.get("name", "Unknown")
                    email = personal_info.get("email", "Not found")
                
                # Handle improvements properly - no nested arrays
                improvements = analysis.get("improvements", [])
                if isinstance(improvements, list):
                    improvements_final = improvements
                else:
                    improvements_final = [str(improvements)]
                
                results.append({
                    "resume_id": resume_id,
                    "filename": llm_result.get("filename", "unknown.pdf"),
                    "candidate_name": candidate_name,
                    "email": email,
                    "ats_score": analysis.get("ats_score", 0),
                    "reason": analysis.get("reason", analysis.get("reasoning", "")),
                    "improvements": improvements_final,
                    "feedback": analysis.get("feedback", ""),
                    "processed_at": datetime.utcnow().isoformat(),
                    "rank": llm_result.get("rank", 0),
                    "analysis_type": "llm_analysis",
                    "raw_text": doc.get("parsed_data", {}).get("raw_text", "") if doc else ""
                })
            
            print(f"[HR] Completed LLM scoring of documents: {len(results)} results")
            return results
            
        except Exception as e:
            print(f"[HR] LLM document scoring failed: {e}")
            traceback.print_exc()
            # Fallback to keyword matching
            return self._score_documents_keyword(jd_text, docs)

    def _score_documents_keyword(self, jd_text: str, docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Fallback keyword scoring for provided documents."""
        print(f"[HR] Using keyword matching to score {len(docs)} documents")
        
        # Extract resume texts
        resume_texts = []
        for doc in docs:
            raw_text = doc.get("parsed_data", {}).get("raw_text", "")
            if not raw_text:
                # Fallback to structured data
                structured = doc.get("parsed_data", {})
                name = structured.get("personal_info", {}).get("name", "")
                skills = " ".join(structured.get("skills", []))
                raw_text = f"{name} {skills}".strip()
            resume_texts.append(raw_text or "Empty resume")

        results = []
        jd_keywords = set(jd_text.lower().split())
        
        for doc, r_text in zip(docs, resume_texts):
            resume_words = set(r_text.lower().split())
            match_count = len(jd_keywords.intersection(resume_words))
            score = min(100, match_count * 2)

            # Extract candidate info
            personal_info = doc.get("parsed_data", {}).get("personal_info", {})
            candidate_name = personal_info.get("name", "Unknown")
            email = personal_info.get("email", "Not found")

            results.append({
                "resume_id": str(doc["_id"]),
                "filename": doc.get("filename", "unknown.pdf"),
                "candidate_name": candidate_name,
                "email": email,
                "raw_text": r_text,
                "ats_score": score,
                "reason": "Scored by keyword matching (fallback method)",
                "improvements": ["Add more relevant keywords from job description"],
                "feedback": "Consider tailoring your resume to the job description.",
                "processed_at": datetime.utcnow().isoformat(),
                "rank": 0,
                "analysis_type": "basic_keyword",
            })

        # Sort and rank
        results.sort(key=lambda r: r["ats_score"], reverse=True)
        for idx, r in enumerate(results, start=1):
            r["rank"] = idx

        print(f"[HR] Completed keyword scoring of documents: {len(results)} results")
        return results

    def score_batch_llm(self, jd_text: str, resume_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Score resumes using LLM analysis."""
        if not jd_text or not jd_text.strip():
            raise ValueError("Job description cannot be empty")
            
        docs = self.fetch_resumes(resume_ids)
        if not docs:
            print("[HR] No resumes found to score")
            return []
        docs = docs[:2]

        print(f"[HR] Starting LLM batch scoring for {len(docs)} resumes")
        
        try:
            # Use LLM service for analysis
            llm_results = analyze_multiple_resumes(docs, jd_text)
            
            # Convert to expected format
            results = []
            for llm_result in llm_results:
                analysis = llm_result.get("analysis", {})
                
                # Find the corresponding document for additional info
                doc = None
                for d in docs:
                    if str(d["_id"]) == llm_result.get("resume_id"):
                        doc = d
                        break
                
                # Extract candidate info
                candidate_name = "Unknown"
                email = "Not found"
                if doc:
                    personal_info = doc.get("parsed_data", {}).get("personal_info", {})
                    candidate_name = personal_info.get("name", "Unknown")
                    email = personal_info.get("email", "Not found")
                
                results.append({
                    "resume_id": llm_result.get("resume_id"),
                    "filename": llm_result.get("filename"),
                    "candidate_name": candidate_name,
                    "email": email,
                    "ats_score": analysis.get("ats_score", 0),
                    "reason": analysis.get("reason", analysis.get("reasoning", "")),
                    "improvements": [analysis.get("improvements", "")],
                    "feedback": analysis.get("feedback", ""),
                    "processed_at": datetime.utcnow().isoformat(),
                    "rank": llm_result.get("rank", 0),
                    "analysis_type": "llm_analysis",
                    "raw_text": doc.get("parsed_data", {}).get("raw_text", "") if doc else ""
                })
            
            print(f"[HR] Completed LLM scoring {len(results)} resumes")
            return results
            
        except Exception as e:
            print(f"[HR] LLM scoring failed: {e}, falling back to keyword matching")
            return self.score_batch_keyword(jd_text, resume_ids)

    def score_batch_keyword(self, jd_text: str, resume_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Fallback keyword matching scoring method."""
        if not jd_text or not jd_text.strip():
            raise ValueError("Job description cannot be empty")
            
        docs = self.fetch_resumes(resume_ids)
        if not docs:
            print("[HR] No resumes found to score")
            return []

        print(f"[HR] Starting keyword batch scoring for {len(docs)} resumes")
        
        # Extract resume texts with fallbacks
        resume_texts = []
        for doc in docs:
            raw_text = doc.get("parsed_data", {}).get("raw_text", "")
            if not raw_text:
                # Try structured data fallback
                structured = doc.get("parsed_data", {})
                name = structured.get("personal_info", {}).get("name", "")
                skills = " ".join(structured.get("skills", []))
                raw_text = f"{name} {skills}".strip()
            resume_texts.append(raw_text or "Empty resume")

        results = []
        
        # Simple keyword matching for scoring
        jd_keywords = set(jd_text.lower().split())
        for doc, r_text in zip(docs, resume_texts):
            resume_words = set(r_text.lower().split())
            match_count = len(jd_keywords.intersection(resume_words))
            score = min(100, match_count * 2)

            # Extract candidate info
            personal_info = doc.get("parsed_data", {}).get("personal_info", {})
            candidate_name = personal_info.get("name", "Unknown")
            email = personal_info.get("email", "Not found")

            results.append({
                "resume_id": str(doc["_id"]),
                "filename": doc.get("filename", "unknown.pdf"),
                "candidate_name": candidate_name,
                "email": email,
                "raw_text": r_text,
                "ats_score": score,
                "reason": "Scored by keyword match (fallback method)",
                "improvements": ["Add more relevant keywords from job description"],
                "feedback": "Consider tailoring your resume to the job description.",
                "processed_at": datetime.utcnow().isoformat(),
                "rank": 0,
                "analysis_type": "basic_keyword",
            })

        # Sort by score and assign ranks
        results.sort(key=lambda r: r["ats_score"], reverse=True)
        for idx, r in enumerate(results, start=1):
            r["rank"] = idx

        print(f"[HR] Completed keyword scoring {len(results)} resumes")
        return results

    def score_batch(self, jd_text: str, resume_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Main scoring method - tries LLM first, falls back to keyword matching."""
        if self.use_llm:
            return self.score_batch_llm(jd_text, resume_ids)
        else:
            return self.score_batch_keyword(jd_text, resume_ids)

    def make_csv_bytes(self, results: List[Dict[str, Any]]) -> bytes:
        """Enhanced CSV export with email, reason, and rank columns."""
        if not results:
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["message", "No results to export"])
            return output.getvalue().encode("utf-8")

        output = io.StringIO()
        
        # UPDATED FIELDNAMES - Clear order with your 3 required columns
        fieldnames = [
            "rank",                # Column 1: Rank among all resumes
            "candidate_name",      # Column 2: Name
            "email",              # Column 3: Email (NEW)
            "filename",           # Column 4: Resume filename
            "ats_score",          # Column 5: Score
            "reason",             # Column 6: Reason for score
            "feedback",           # Column 7: Feedback
            "improvements",       # Column 8: Improvements
            "resume_id",          # Column 9: ID
            "analysis_type",      # Column 10: Analysis type
            "processed_at"        # Column 11: Timestamp
        ]
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for r in results:
            # Get email - first try from result dict, then extract from raw_text
            email = r.get("email", "Not found")
            if email == "Not found":
                raw_text = r.get("raw_text", "")
                if raw_text:
                    email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", raw_text)
                    if email_match:
                        email = email_match.group(0)
            
            # Handle improvements list properly
            improvements_list = r.get("improvements", [])
            if isinstance(improvements_list, list):
                improvements_str = "; ".join(str(imp) for imp in improvements_list)
            else:
                improvements_str = str(improvements_list)
                
            reason_clean = str(r.get("reason", "")).replace("\n", " ").replace("\r", " ")
            feedback_clean = str(r.get("feedback", "")).replace("\n", " ").replace("\r", " ")

            writer.writerow({
                "rank": r.get("rank", ""),
                "candidate_name": r.get("candidate_name", "Unknown"),
                "email": email,
                "filename": r.get("filename", ""),
                "ats_score": r.get("ats_score", 0),
                "reason": reason_clean[:500],
                "feedback": feedback_clean[:500],
                "improvements": improvements_str[:300],
                "resume_id": r.get("resume_id", ""),
                "analysis_type": r.get("analysis_type", "basic_keyword"),
                "processed_at": r.get("processed_at", "")
            })

        csv_content = output.getvalue()
        print(f"[HR] Generated CSV with {len(results)} records")
        return csv_content.encode("utf-8")


# Legacy functions for backward compatibility with new LLM integration

def score_resumes_with_llm(jd_text: str) -> Dict[str, Any]:
    """
    Score all resumes in database against a job description using LLM.
    Compatible with the new LLM service structure.
    """
    try:
        service = HRService(use_llm=True)
        results = service.score_batch(jd_text)
        
        return {
            "success": True,
            "message": f"Successfully analyzed {len(results)} resumes",
            "results": results,
            "total_resumes": len(results),
            "job_description": jd_text[:200] + "..." if len(jd_text) > 200 else jd_text
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error scoring resumes: {str(e)}",
            "results": [],
            "total_resumes": 0
        }

def export_results_to_csv(results: List[Dict[str, Any]]) -> str:
    """Export analysis results to CSV format."""
    service = HRService()
    csv_bytes = service.make_csv_bytes(results)
    return csv_bytes.decode("utf-8")

def get_resume_statistics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate statistics from resume analysis results."""
    if not results:
        return {
            "total_resumes": 0,
            "average_score": 0,
            "highest_score": 0,
            "lowest_score": 0,
            "score_distribution": {}
        }
    
    scores = [result["ats_score"] for result in results]
    
    # Score distribution ranges
    score_ranges = {
        "Excellent (80-100)": len([s for s in scores if s >= 80]),
        "Good (60-79)": len([s for s in scores if 60 <= s < 80]),
        "Average (40-59)": len([s for s in scores if 40 <= s < 60]),
        "Below Average (20-39)": len([s for s in scores if 20 <= s < 40]),
        "Poor (0-19)": len([s for s in scores if s < 20])
    }
    
    return {
        "total_resumes": len(results),
        "average_score": round(sum(scores) / len(scores), 2),
        "highest_score": max(scores),
        "lowest_score": min(scores),
        "score_distribution": score_ranges
    }