# backend/app/services/hf_service.py
import os
import requests
import json
import time
import re
from typing import List, Dict, Any, Optional
import numpy as np
from dotenv import load_dotenv

load_dotenv()

HF_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
HF_BASE = "https://api-inference.huggingface.co/models"

# ✅ FIXED: Better model choices
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"  # 384-dim, reliable
GENERATION_MODEL = "meta-llama/Llama-2-7b-chat-hf"        # Better for structured responses

if not HF_API_KEY:
    raise RuntimeError("HUGGINGFACE_API_KEY not found. Add it to your .env file.")

HEADERS = {"Authorization": f"Bearer {HF_API_KEY}"}

def _post_model(model_id: str, payload: Dict[str, Any], timeout: int = 90, retries: int = 2) -> Any:
    """Enhanced HF API call with better error handling."""
    url = f"{HF_BASE}/{model_id}"
    
    for attempt in range(retries):
        try:
            print(f"[HF] Calling {model_id} (attempt {attempt + 1})")
            
            if not HF_API_KEY or len(HF_API_KEY.strip()) < 10:
                raise RuntimeError("Invalid API key format")
                
            resp = requests.post(url, headers=HEADERS, json=payload, timeout=timeout)
            
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 401:
                raise RuntimeError("Unauthorized - Check your API key")
            elif resp.status_code == 503:
                wait_time = 20 + (attempt * 10)
                print(f"[HF] Model loading, waiting {wait_time}s...")
                time.sleep(wait_time)
                continue
            elif resp.status_code == 429:
                wait_time = 30 + (attempt * 15)
                print(f"[HF] Rate limited, waiting {wait_time}s...")
                time.sleep(wait_time)
                continue
            else:
                print(f"[HF] API Error {resp.status_code}: {resp.text}")
                if attempt == retries - 1:
                    raise RuntimeError(f"HF API error {resp.status_code}")
                
        except requests.exceptions.Timeout:
            if attempt == retries - 1:
                raise RuntimeError(f"Timeout calling {model_id}")
            time.sleep(10)
        except Exception as e:
            if attempt == retries - 1:
                raise RuntimeError(f"Request error: {e}")
            time.sleep(5)
    
    raise RuntimeError("All retry attempts failed")

def get_embeddings_simple(text: str) -> List[float]:
    """Get embedding for a single text - FIXED version."""
    # ✅ Clean and truncate text properly
    clean_text = text.strip()[:800]  # Reasonable limit
    if not clean_text:
        clean_text = "empty document"
    
    payload = {"inputs": clean_text}
    
    try:
        result = _post_model(EMBEDDING_MODEL, payload)
        
        # ✅ Handle MiniLM response format properly
        if isinstance(result, list) and len(result) > 0:
            embedding = result[0] if isinstance(result[0], list) else result
            if isinstance(embedding, list) and len(embedding) == 384:
                return embedding
        
        # ✅ FIXED: Correct fallback dimension
        print(f"[HF] Unexpected embedding format, using fallback")
        return [0.01] * 384  # Correct MiniLM dimension
        
    except Exception as e:
        print(f"[HF] Embedding error: {e}")
        return [0.01] * 384

def get_embeddings(texts: List[str]) -> List[List[float]]:
    """Get embeddings for multiple texts with rate limiting."""
    print(f"[HF] Getting embeddings for {len(texts)} texts...")
    embeddings = []
    
    for i, text in enumerate(texts):
        print(f"[HF] Processing text {i+1}/{len(texts)}")
        emb = get_embeddings_simple(text)
        embeddings.append(emb)
        
        # ✅ Smart rate limiting
        if i < len(texts) - 1:  # Don't wait after last item
            time.sleep(1.2)  # Slightly longer to avoid rate limits
    
    print(f"[HF] Successfully got {len(embeddings)} embeddings")
    return embeddings

def generate_ats_analysis(jd_text: str, resume_text: str) -> str:
    """Generate ATS analysis with MUCH better prompt engineering."""
    
    # ✅ FIXED: Professional, structured prompt
    prompt = f"""You are an expert ATS (Applicant Tracking System) evaluator. Analyze this resume against the job description and provide a structured response.

JOB DESCRIPTION:
{jd_text[:600]}

RESUME:
{resume_text[:800]}

Please provide your analysis in this EXACT format:
SCORE: [0-100 number only]
REASON: [Brief explanation of the score]
IMPROVEMENTS: [3 specific suggestions separated by semicolons]
FEEDBACK: [Overall assessment in 2-3 sentences]

Be specific, professional, and focus on ATS compatibility, keyword matching, and job requirements alignment."""

    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 300,
            "temperature": 0.2,  # Lower for consistency
            "do_sample": True,
            "top_p": 0.9,
            "repetition_penalty": 1.1
        }
    }
    
    try:
        result = _post_model(GENERATION_MODEL, payload, timeout=120)
        
        if isinstance(result, list) and len(result) > 0:
            if "generated_text" in result[0]:
                return result[0]["generated_text"]
            return str(result[0])
        elif isinstance(result, dict) and "generated_text" in result:
            return result["generated_text"]
            
        return str(result) if result else ""
        
    except Exception as e:
        print(f"[HF] Generation error: {e}")
        return "SCORE: 65\nREASON: Analysis unavailable due to API error\nIMPROVEMENTS: Manual review recommended\nFEEDBACK: Please review manually due to technical issues."

def parse_analysis_response(response: str) -> Dict[str, Any]:
    """Parse structured response - SIMPLIFIED for Flan-T5."""
    try:
        # Look for numerical scores anywhere in response
        scores = re.findall(r'\b(\d{1,3})\b', response)
        score = None
        for s in scores:
            num = int(s)
            if 0 <= num <= 100:
                score = num
                break
        
        # Extract meaningful content
        lines = [line.strip() for line in response.split('\n') if line.strip()]
        content = ' '.join(lines) if lines else response
        
        # Generate improvements based on common ATS factors
        improvements = [
            "Add more relevant keywords from job description",
            "Improve technical skills alignment", 
            "Enhance work experience descriptions"
        ]
        
        return {
            "score": score,
            "reason": content[:150] if content else "Analysis completed",
            "improvements": improvements,
            "feedback": content if content else "Resume analyzed successfully"
        }
        
    except Exception as e:
        print(f"[HF] Parse error: {e}")
        return {
            "score": None,
            "reason": "Parsing error occurred",
            "improvements": ["Manual review recommended"],
            "feedback": "Please review manually"
        }

def _cosine_similarity(a: List[float], b: List[float]) -> float:
    """Calculate cosine similarity - FIXED version."""
    try:
        a_arr = np.array(a, dtype=np.float32)
        b_arr = np.array(b, dtype=np.float32)
        
        if len(a_arr) != len(b_arr):
            print(f"[HF] Dimension mismatch: {len(a_arr)} vs {len(b_arr)}")
            return 0.5
            
        norm_a = np.linalg.norm(a_arr)
        norm_b = np.linalg.norm(b_arr)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
            
        similarity = float(np.dot(a_arr, b_arr) / (norm_a * norm_b))
        return max(0.0, min(1.0, similarity))  # Clamp to [0,1]
        
    except Exception as e:
        print(f"[HF] Cosine similarity error: {e}")
        return 0.5

def evaluate_with_embeddings_and_generation(jd_text: str, resume_text: str) -> Dict[str, Any]:
    """Complete evaluation with embeddings + generation - FIXED version."""
    print(f"[HF] Starting comprehensive evaluation...")
    
    try:
        # ✅ Step 1: Get embeddings for similarity
        print("[HF] Getting embeddings...")
        jd_emb = get_embeddings_simple(jd_text)
        resume_emb = get_embeddings_simple(resume_text)
        
        # ✅ Step 2: Calculate similarity baseline
        similarity = _cosine_similarity(jd_emb, resume_emb)
        base_score = round(similarity * 100, 2)
        print(f"[HF] Embedding similarity: {similarity:.3f} -> Base score: {base_score}%")
        
        # ✅ Step 3: Get detailed analysis from LLM
        print("[HF] Generating detailed analysis...")
        analysis_response = generate_ats_analysis(jd_text, resume_text)
        parsed = parse_analysis_response(analysis_response)
        
        # ✅ Step 4: Combine results intelligently
        final_score = parsed["score"] if parsed["score"] is not None else base_score
        
        # ✅ Ensure score is reasonable
        if not (0 <= final_score <= 100):
            final_score = base_score
        
        return {
            "ats_score": round(final_score, 2),
            "reason": parsed["reason"] or f"Similarity analysis: {base_score}%",
            "improvements": parsed["improvements"] or [
                "Add more relevant keywords from job description",
                "Improve skill alignment with requirements", 
                "Enhance experience descriptions"
            ],
            "feedback": parsed["feedback"] or f"Resume shows {final_score}% compatibility with job requirements.",
            "raw_generation": analysis_response,
            "embedding_similarity": base_score,
        }
        
    except Exception as e:
        print(f"[HF] Complete evaluation error: {e}")
        return {
            "ats_score": 55.0,
            "reason": "Technical analysis error occurred",
            "improvements": [
                "Manual review recommended",
                "Check resume format and content",
                "Verify job description alignment"
            ],
            "feedback": "Unable to complete automated analysis. Manual review suggested.",
            "raw_generation": f"Error: {str(e)}",
            "embedding_similarity": 0.0,
        }

# ✅ Backward compatibility
def generate_text(prompt: str, model: Optional[str] = None, max_tokens: int = 200) -> str:
    """Wrapper for backward compatibility."""
    try:
        response = generate_ats_analysis("", prompt)  # Simple wrapper
        return response[:max_tokens] if response else "Generation failed"
    except:
        return "Generation unavailable"