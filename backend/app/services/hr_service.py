import io
import csv
from typing import List, Dict, Any, Optional
from bson import ObjectId
import numpy as np
from datetime import datetime
from backend.app.database import resumes_collection
from backend.app.services.hf_service import evaluate_with_embeddings_and_generation, get_embeddings

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
    def __init__(self, hf_detailed: bool = True, top_k_details: Optional[int] = None):
        self.hf_detailed = hf_detailed
        self.top_k = top_k_details

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
            return []

    def score_batch(self, jd_text: str, resume_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Score resumes against job description - ENHANCED version."""
        if not jd_text or not jd_text.strip():
            raise ValueError("Job description cannot be empty")
            
        docs = self.fetch_resumes(resume_ids)
        if not docs:
            print("[HR] No resumes found to score")
            return []

        print(f"[HR] Starting batch scoring for {len(docs)} resumes")
        
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
        
        try:
            # Get embeddings for similarity scoring
            print("[HR] Computing embeddings...")
            all_texts = [jd_text] + resume_texts
            embed_resp = get_embeddings(all_texts)
            
            if len(embed_resp) < len(all_texts):
                raise RuntimeError("Incomplete embedding response")

            jd_emb = embed_resp[0]
            resume_embs = embed_resp[1:]

            # Create initial results with similarity scores
            for doc, r_emb, r_text in zip(docs, resume_embs, resume_texts):
                sim = _cosine(jd_emb, r_emb)
                ats_score = round(max(0, min(100, sim * 100)), 2)  # Clamp to [0,100]

                # Extract candidate name safely
                candidate_name = "Unknown"
                try:
                    name = doc.get("parsed_data", {}).get("personal_info", {}).get("name")
                    if name and name.strip():
                        candidate_name = name.strip()
                except:
                    pass

                results.append({
                    "resume_id": str(doc["_id"]),
                    "filename": doc.get("filename", "unknown.pdf"),
                    "candidate_name": candidate_name,
                    "raw_text": r_text,
                    "ats_score": ats_score,
                    "reason": f"Initial similarity: {ats_score}% based on semantic matching",
                    "improvements": ["Add relevant keywords", "Align skills with job requirements"],
                    "feedback": f"Resume shows {ats_score}% semantic similarity with job requirements.",
                    "processed_at": datetime.utcnow().isoformat(),
                })

        except Exception as e:
            print(f"[HR] Embedding processing failed: {e}")
            # Fallback to basic results
            for doc, r_text in zip(docs, resume_texts):
                results.append({
                    "resume_id": str(doc["_id"]),
                    "filename": doc.get("filename", "unknown.pdf"),
                    "candidate_name": "Unknown",
                    "raw_text": r_text,
                    "ats_score": 50.0,
                    "reason": "Could not compute similarity - manual review needed",
                    "improvements": ["Manual review required"],
                    "feedback": "Technical error occurred during analysis",
                    "processed_at": datetime.utcnow().isoformat(),
                })

        # Sort by score and assign ranks
        results.sort(key=lambda r: r["ats_score"], reverse=True)
        for idx, r in enumerate(results, start=1):
            r["rank"] = idx

        # Enhanced analysis for top candidates (if requested)
        if self.hf_detailed and results:
            top_candidates = results[:self.top_k] if self.top_k else results
            print(f"[HR] Running detailed analysis for top {len(top_candidates)} candidates...")
            
            for r in top_candidates:
                try:
                    print(f"[HR] Analyzing {r['filename']}...")
                    detailed = evaluate_with_embeddings_and_generation(jd_text, r["raw_text"])
                    
                    # Update with detailed analysis
                    r.update({
                        "ats_score": round(float(detailed.get("ats_score", r["ats_score"])), 2),
                        "reason": detailed.get("reason", r["reason"]),
                        "improvements": detailed.get("improvements", r["improvements"]),
                        "feedback": detailed.get("feedback", r["feedback"]),
                        "raw_generation": detailed.get("raw_generation", ""),
                        "analysis_type": "detailed_llm"
                    })
                    
                except Exception as e:
                    print(f"[HR] Detailed analysis failed for {r['filename']}: {e}")
                    r["analysis_type"] = "similarity_only"
                    r["reason"] = f"Detailed analysis error: {str(e)}"

            # Re-sort after detailed scoring
            results.sort(key=lambda r: r["ats_score"], reverse=True)
            for idx, r in enumerate(results, start=1):
                r["rank"] = idx

        print(f"[HR] Completed scoring {len(results)} resumes")
        return results

    def make_csv_bytes(self, results: List[Dict[str, Any]]) -> bytes:
        """Enhanced CSV export with better formatting."""
        if not results:
            # Return empty CSV with headers
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["message", "No results to export"])
            return output.getvalue().encode("utf-8")

        output = io.StringIO()
        
        # Enhanced field names
        fieldnames = [
            "rank", "candidate_name", "filename", "ats_score", 
            "reason", "improvements", "feedback", "resume_id",
            "analysis_type", "processed_at"
        ]
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for r in results:
            # Clean and format data for CSV
            improvements_str = "; ".join(r.get("improvements", []))
            if len(improvements_str) > 200:  # Truncate very long improvements
                improvements_str = improvements_str[:197] + "..."
                
            reason_clean = str(r.get("reason", "")).replace("\n", " ").replace("\r", " ")
            feedback_clean = str(r.get("feedback", "")).replace("\n", " ").replace("\r", " ")

            writer.writerow({
                "rank": r.get("rank", ""),
                "candidate_name": r.get("candidate_name", "Unknown"),
                "filename": r.get("filename", ""),
                "ats_score": r.get("ats_score", 0),
                "reason": reason_clean[:300],  # Limit length
                "improvements": improvements_str,
                "feedback": feedback_clean[:300],  # Limit length
                "resume_id": r.get("resume_id", ""),
                "analysis_type": r.get("analysis_type", "similarity"),
                "processed_at": r.get("processed_at", "")
            })

        csv_content = output.getvalue()
        print(f"[HR] Generated CSV with {len(results)} records")
        return csv_content.encode("utf-8")