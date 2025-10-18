from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import StreamingResponse, JSONResponse
from typing import Optional
import fitz  # PyMuPDF
import os
from io import BytesIO
import traceback

# Import your services
from backend.app.services.skills_extractor import SkillsExtractor
from backend.app.services.gap_analyzer import SkillsGapAnalyzer
from backend.app.services.action_generator import ActionItemGenerator
from backend.app.services.pdf_reporter import PDFReportGenerator
from backend.app.services.LLM_Service import initialize_groq_client

# Initialize Groq LLM client
llm_client = None
try:
    initialize_groq_client()
    from backend.app.services.LLM_Service import client as llm_client
    print("✅ Groq LLM client initialized successfully")
except Exception as e:
    print(f"⚠️ LLM initialization failed: {e}")

router = APIRouter(tags=["Job Seeker"])

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def extract_resume_text(resume: UploadFile) -> str:
    """
    Extract text from uploaded resume (PDF or TXT).
    Supports PDF and plain text files.
    """
    try:
        filename = resume.filename.lower()
        
        if filename.endswith(".pdf"):
            # Extract from PDF
            pdf_bytes = resume.file.read()
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            resume_text = ""
            for page in doc:
                resume_text += page.get_text()
            doc.close()
            return resume_text.strip()
        
        elif filename.endswith((".txt", ".doc", ".docx")):
            # Extract from text file
            try:
                return resume.file.read().decode("utf-8").strip()
            except UnicodeDecodeError:
                return resume.file.read().decode("latin1", errors="ignore").strip()
        
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file format: {filename}. Please upload PDF or TXT."
            )
    
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to extract resume text: {str(e)}"
        )
    finally:
        resume.file.seek(0)  # Reset file pointer

def validate_inputs(resume_text: str, job_description: str):
    """
    Validate that resume and JD contain sufficient content.
    """
    if not resume_text or len(resume_text.strip()) < 50:
        raise HTTPException(
            status_code=400,
            detail="Resume is too short or empty. Please provide a valid resume."
        )
    
    if not job_description or len(job_description.strip()) < 50:
        raise HTTPException(
            status_code=400,
            detail="Job description is too short or empty. Please provide a valid JD."
        )

# ============================================================================
# API ENDPOINTS
# ============================================================================

@router.post("/analyze-gap")
async def analyze_gap(
    resume: UploadFile = File(..., description="Resume file (PDF or TXT)"),
    job_description: str = Form(..., description="Job description text"),
    use_ai: bool = Form(True, description="Enable AI-powered analysis"),
    include_roadmap: bool = Form(False, description="Include learning roadmap")
):
    """
    Analyze skill gap between resume and job description.
    
    Returns:
    - skills_analysis: Matched, missing, and transferable skills
    - priority_actions: Actionable recommendations
    - learning_roadmap: Optional 30/60/90 day plan
    """
    try:
        # Extract and validate inputs
        resume.file.seek(0)
        resume_text = extract_resume_text(resume)
        validate_inputs(resume_text, job_description)
        
        # Perform gap analysis
        analyzer = SkillsGapAnalyzer(use_ai=use_ai, llm_client=llm_client)
        gap = analyzer.analyze_gap(resume_text, job_description, hybrid=use_ai)
        
        # Generate priority actions
        action_gen = ActionItemGenerator(use_ai=use_ai, llm_client=llm_client)
        actions = action_gen.generate_priority_actions(
            gap, 
            resume_text=resume_text, 
            jd_text=job_description
        )
        
        # Build response
        response_data = {
            "status": "success",
            "skills_analysis": gap,
            "priority_actions": actions,
            "summary": {
                "total_jd_skills": len(gap.get("matched_skills", [])) + len(gap.get("missing_skills", [])),
                "matched_count": len(gap.get("matched_skills", [])),
                "missing_count": len(gap.get("missing_skills", [])),
                "transferable_count": len(gap.get("transferable_skills", [])),
                "match_percentage": gap.get("match_percentage", 0),
                "ats_score": gap.get("ats_score", 0)
            }
        }
        
        # Optional: Add learning roadmap
        if include_roadmap and hasattr(action_gen, 'generate_learning_roadmap'):
            roadmap = action_gen.generate_learning_roadmap(gap, timeline_weeks=12)
            response_data["learning_roadmap"] = roadmap
        
        return JSONResponse(content=response_data)
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Gap analysis error: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Gap analysis failed: {str(e)}"
        )

@router.post("/get-suggestions")
async def get_suggestions(
    resume: UploadFile = File(..., description="Resume file (PDF or TXT)"),
    job_description: str = Form(..., description="Job description text"),
    use_ai: bool = Form(True, description="Enable AI-powered suggestions")
):
    """
    Get section-by-section resume improvement suggestions.
    
    Returns detailed suggestions for:
    - Summary/Objective
    - Work Experience
    - Skills Section
    - Education
    - Formatting/ATS optimization
    """
    try:
        resume.file.seek(0)
        resume_text = extract_resume_text(resume)
        validate_inputs(resume_text, job_description)
        
        # Get gap analysis first
        analyzer = SkillsGapAnalyzer(use_ai=use_ai, llm_client=llm_client)
        gap = analyzer.analyze_gap(resume_text, job_description, hybrid=use_ai)
        
        # Generate suggestions
        action_gen = ActionItemGenerator(use_ai=use_ai, llm_client=llm_client)
        actions = action_gen.generate_priority_actions(
            gap,
            resume_text=resume_text,
            jd_text=job_description
        )
        
        # Organize suggestions by category
        suggestions_by_category = {}
        for action in actions:
            category = action.get("category", "General")
            if category not in suggestions_by_category:
                suggestions_by_category[category] = []
            suggestions_by_category[category].append(action)
        
        return JSONResponse(content={
            "status": "success",
            "suggestions": suggestions_by_category,
            "gap_summary": {
                "match_percentage": gap.get("match_percentage", 0),
                "missing_critical_skills": [
                    s["skill"] for s in gap.get("missing_skills", [])
                    if s.get("priority") == "critical"
                ][:5]
            }
        })
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Suggestions error: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Suggestion generation failed: {str(e)}"
        )

@router.post("/export-report")
async def export_report(
    resume: UploadFile = File(..., description="Resume file (PDF or TXT)"),
    job_description: str = Form(..., description="Job description text"),
    candidate_name: str = Form(..., description="Candidate's full name"),
    job_title: str = Form("Target Position", description="Job title applying for"),
    use_ai: bool = Form(True, description="Enable AI-powered analysis"),
    include_roadmap: bool = Form(True, description="Include learning roadmap in PDF")
):
    """
    Generate and download comprehensive PDF skill gap report.
    
    Includes:
    - Executive summary
    - Skills gap analysis
    - Priority action items with resources
    - Optional: 30/60/90 day learning roadmap
    """
    try:
        # Extract and validate
        resume.file.seek(0)
        resume_text = extract_resume_text(resume)
        validate_inputs(resume_text, job_description)
        
        if not candidate_name or len(candidate_name.strip()) < 2:
            raise HTTPException(
                status_code=400,
                detail="Please provide a valid candidate name"
            )
        
        if not job_title or len(job_title.strip()) < 2:
            job_title = "Target Position"
        
        # Perform analysis
        print(f"[PDF Export] Starting analysis for {candidate_name}")
        analyzer = SkillsGapAnalyzer(use_ai=use_ai, llm_client=llm_client)
        gap = analyzer.analyze_gap(resume_text, job_description, hybrid=use_ai)
        print(f"[PDF Export] Gap analysis complete")
        
        # Generate actions
        action_gen = ActionItemGenerator(use_ai=use_ai, llm_client=llm_client)
        actions = action_gen.generate_priority_actions(
            gap,
            resume_text=resume_text,
            jd_text=job_description
        )
        print(f"[PDF Export] Generated {len(actions)} actions")
        
        # Generate roadmap if requested
        roadmap = None
        if include_roadmap:
            roadmap = gap.get("learning_roadmap")
            print(f"[PDF Export] Using learning roadmap from gap analysis")
        
        # Generate PDF
        print(f"[PDF Export] Generating PDF...")
        pdf_gen = PDFReportGenerator(use_ai=use_ai, llm_client=llm_client)
        pdf_bytes = pdf_gen.generate(
            candidate_name=candidate_name,
            job_title=job_title,
            gap_analysis=gap,
            actions=actions,
            resume_text=resume_text,
            jd_text=job_description,
            learning_roadmap=roadmap
        )
        print(f"[PDF Export] PDF generated successfully: {len(pdf_bytes)} bytes")
        
        # Return as downloadable file
        filename = f"{candidate_name.replace(' ', '_')}_gap_report.pdf"
        
        return StreamingResponse(
            BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Length": str(len(pdf_bytes))
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        print("=" * 60)
        print("PDF GENERATION ERROR:")
        print(traceback.format_exc())
        print("=" * 60)
        raise HTTPException(
            status_code=500,
            detail=f"PDF report generation failed: {str(e)}"
        )

@router.post("/quick-score")
async def quick_score(
    resume: UploadFile = File(..., description="Resume file (PDF or TXT)"),
    job_description: str = Form(..., description="Job description text")
):
    """
    Quick ATS score and match percentage (no AI, fast rule-based).
    Useful for initial screening before full analysis.
    """
    try:
        resume.file.seek(0)
        resume_text = extract_resume_text(resume)
        validate_inputs(resume_text, job_description)
        
        # Fast rule-based analysis only
        analyzer = SkillsGapAnalyzer(use_ai=False, llm_client=None)
        gap = analyzer.analyze_gap(resume_text, job_description, hybrid=False)
        
        return JSONResponse(content={
            "status": "success",
            "ats_score": gap.get("ats_score", 0),
            "match_percentage": gap.get("match_percentage", 0),
            "matched_skills_count": len(gap.get("matched_skills", [])),
            "missing_skills_count": len(gap.get("missing_skills", [])),
            "top_missing_skills": [
                s["skill"] for s in gap.get("missing_skills", [])
            ][:5]
        })
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Quick score error: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Quick score failed: {str(e)}"
        )

@router.get("/health")
async def health_check():
    """
    Check if the Job Seeker module is running and LLM is available.
    """
    return {
        "status": "healthy",
        "llm_available": llm_client is not None,
        "services": {
            "gap_analyzer": "active",
            "action_generator": "active",
            "pdf_reporter": "active"
        }
    }

@router.post("/batch-analyze")
async def batch_analyze(
    resumes: list[UploadFile] = File(..., description="Multiple resume files"),
    job_description: str = Form(..., description="Job description text"),
    use_ai: bool = Form(False, description="Enable AI (slower for batch)"),
    top_n: int = Form(10, description="Return top N candidates")
):
    """
    Batch analyze multiple resumes against one job description.
    Returns ranked candidates by match score.
    """
    try:
        if len(resumes) > 50:
            raise HTTPException(
                status_code=400,
                detail="Maximum 50 resumes allowed per batch request"
            )
        
        validate_inputs("sample text for validation", job_description)
        
        results = []
        analyzer = SkillsGapAnalyzer(use_ai=use_ai, llm_client=llm_client)
        
        for idx, resume in enumerate(resumes):
            try:
                resume.file.seek(0)
                resume_text = extract_resume_text(resume)
                
                if len(resume_text.strip()) < 50:
                    results.append({
                        "filename": resume.filename,
                        "status": "skipped",
                        "reason": "Resume too short or empty"
                    })
                    continue
                
                gap = analyzer.analyze_gap(resume_text, job_description, hybrid=False)
                
                results.append({
                    "filename": resume.filename,
                    "status": "success",
                    "match_percentage": gap.get("match_percentage", 0),
                    "ats_score": gap.get("ats_score", 0),
                    "matched_skills_count": len(gap.get("matched_skills", [])),
                    "missing_skills_count": len(gap.get("missing_skills", [])),
                    "top_matched_skills": [
                        s["skill"] for s in gap.get("matched_skills", [])
                    ][:5],
                    "critical_missing_skills": [
                        s["skill"] for s in gap.get("missing_skills", [])
                        if s.get("priority") == "critical"
                    ][:3]
                })
            
            except Exception as e:
                results.append({
                    "filename": resume.filename,
                    "status": "error",
                    "reason": str(e)
                })
        
        successful_results = [r for r in results if r["status"] == "success"]
        successful_results.sort(key=lambda x: x["match_percentage"], reverse=True)
        top_candidates = successful_results[:top_n]
        
        return JSONResponse(content={
            "status": "success",
            "total_resumes_analyzed": len(resumes),
            "successful_analyses": len(successful_results),
            "failed_analyses": len([r for r in results if r["status"] != "success"]),
            "top_candidates": top_candidates,
            "all_results": results
        })
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Batch analysis error: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Batch analysis failed: {str(e)}"
        )

@router.post("/analyze-gap-enhanced")
async def analyze_gap_enhanced(
    resume: UploadFile = File(...),
    job_description: str = Form(...)
):
    resume_text = extract_resume_text(resume)
    analyzer = SkillsGapAnalyzer(use_ai=True, llm_client=llm_client)
    gap_analysis = analyzer.analyze_gap(resume_text, job_description, hybrid=True)

    # Add enhancements
    gap_analysis["learning_plan"] = analyzer.generate_personalized_learning_plan(
        gap_analysis["missing_skills"], gap_analysis["matched_skills"]
    )
    gap_analysis["market_insights"] = [
        analyzer.get_skill_market_data(skill_obj["skill"])
        for skill_obj in gap_analysis["missing_skills"][:5]
    ]
    extractor = SkillsExtractor()
    gap_analysis["keyword_optimization"] = extractor.suggest_keyword_improvements(
        resume_text, job_description
    )

    return {
        "status": "success",
        "gap_analysis": gap_analysis,
        "learning_plan": gap_analysis["learning_plan"],
        "market_insights": gap_analysis["market_insights"],
        "keyword_optimization": gap_analysis["keyword_optimization"]
    }