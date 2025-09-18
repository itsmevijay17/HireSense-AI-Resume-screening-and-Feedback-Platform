import os
import re
import pdfplumber
from typing import List, Dict, Optional


class ResumeParserService:
    def __init__(self):
        # Optional folder for HR local testing
        self.project_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../../")
        )
        self.resumes_folder = os.path.join(self.project_root, "resumes")

        if not os.path.exists(self.resumes_folder):
            os.makedirs(self.resumes_folder)
            print(f"[INFO] Created resumes folder at: {self.resumes_folder}")

    # -------------------------
    # Raw PDF Text Extraction
    # -------------------------
    def extract_text_from_pdf(self, file_path: str) -> Dict:
        """
        Extracts text from a single PDF file.
        """
        text = ""
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() or ""

            return {
                "file_name": os.path.basename(file_path),
                "content": text.strip(),
                "error": None
            }

        except Exception as e:
            return {
                "file_name": os.path.basename(file_path),
                "content": None,
                "error": str(e)
            }

    # -------------------------
    # Resume Structuring
    # -------------------------
    def structure_resume(self, parsed_data: Dict) -> Dict:
        """
        Convert raw extracted resume text into structured JSON schema.
        """
        if not parsed_data.get("content"):
            return {**parsed_data, "structured": None}

        raw_text = parsed_data["content"]

        # ---- Extract Personal Info ----
        email = re.search(r"[\w\.-]+@[\w\.-]+", raw_text)
        phone = re.search(r"\+?\d[\d\-\s]{8,}\d", raw_text)
        linkedin = re.search(r"(https?:\/\/)?(www\.)?linkedin\.com\/[A-Za-z0-9\-_/]+", raw_text)
        github = re.search(r"(https?:\/\/)?(www\.)?github\.com\/[A-Za-z0-9\-_/]+", raw_text)

        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        name = lines[0] if lines else None

        structured = {
            "file_name": parsed_data["file_name"],
            "personal_info": {
                "name": name,
                "phone": phone.group(0) if phone else None,
                "email": email.group(0) if email else None,
                "linkedin": linkedin.group(0) if linkedin else None,
                "github": github.group(0) if github else None,
                "location": None
            },
            "summary": None,
            "education": [],
            "experience": [],
            "projects": [],
            "skills": [],
            "certifications": [],
            "achievements": [],
            "raw_text": raw_text,
            "error": parsed_data.get("error")
        }

        sections = self.split_sections(raw_text)

        if "summary" in sections:
            structured["summary"] = sections["summary"]

        if "education" in sections:
            structured["education"].append({"details": sections["education"]})

        if "experience" in sections:
            structured["experience"].append({"details": sections["experience"]})

        if "projects" in sections:
            structured["projects"].append({"details": sections["projects"]})

        if "skills" in sections:
            structured["skills"] = self._extract_skills(sections["skills"])

        if "certifications" in sections:
            structured["certifications"].append(sections["certifications"])

        if "achievements" in sections:
            structured["achievements"].append(sections["achievements"])

        return structured

    def split_sections(self, text: str) -> Dict[str, str]:
        """
        Splits resume text into sections using common headers.
        """
        headers = [
            "summary", "education", "experience", "projects",
            "skills", "achievements", "certifications"
        ]
        sections = {}
        lowered = text.lower()

        for i, header in enumerate(headers):
            idx = lowered.find(header)
            if idx != -1:
                next_idx = len(text)
                for h in headers[i + 1:]:
                    nxt = lowered.find(h, idx + 1)
                    if nxt != -1:
                        next_idx = min(next_idx, nxt)
                sections[header] = text[idx:next_idx].strip()

        return sections

    def _extract_skills(self, skills_text: str) -> List[str]:
        """
        Extract skills from the Skills section.
        """
        skills = re.split(r",|\n|•|-", skills_text)
        return [s.strip() for s in skills if s.strip()]

    # -------------------------
    # API Helpers
    # -------------------------
    def parse_single_resume(self, file_path: str) -> Dict:
        """
        Parse a single resume given its file path.
        """
        if not os.path.exists(file_path):
            return {"file_name": os.path.basename(file_path), "content": None, "error": "File not found"}

        parsed = self.extract_text_from_pdf(file_path)
        return self.structure_resume(parsed)

    def parse_multiple_resumes(self, folder_path: Optional[str] = None) -> List[Dict]:
        """
        Parse multiple resumes from a folder (HR local testing).
        """
        folder = folder_path or self.resumes_folder
        parsed_resumes = []
        supported_extensions = [".pdf"]

        if not os.path.exists(folder):
            print(f"[ERROR] Resumes folder not found: {folder}")
            return []

        files = [
            f for f in os.listdir(folder)
            if os.path.isfile(os.path.join(folder, f))
            and f.lower().endswith(tuple(supported_extensions))
        ]

        if not files:
            print(f"[WARN] No PDF resumes found in {folder}")
            return []

        print(f"[INFO] Found {len(files)} resumes in {folder}\n")

        for idx, file_name in enumerate(files, start=1):
            file_path = os.path.join(folder, file_name)
            result = self.parse_single_resume(file_path)
            parsed_resumes.append(result)

            preview = (result["raw_text"][:200] + "...") if result.get("raw_text") else "[EMPTY FILE]"
            print(f"{idx}. {file_name} → {preview}")

        return parsed_resumes
