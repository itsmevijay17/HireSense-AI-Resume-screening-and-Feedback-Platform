import os
import json
import re
from typing import Dict, List, Set, Optional

class SkillsExtractor:
    def __init__(self, use_ai=False, llm_client=None):
        self.use_ai = use_ai
        self.llm_client = llm_client
        
        # Comprehensive skill database organized by career paths
        self.skill_categories = {
            "Programming Languages": [
                "Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "Go", 
                "Rust", "Ruby", "PHP", "Swift", "Kotlin", "Scala", "R"
            ],
            "Frontend": [
                "React", "Angular", "Vue.js", "Svelte", "Next.js", "HTML", "CSS", 
                "SASS", "Tailwind CSS", "Bootstrap", "jQuery", "Redux", "Material-UI"
            ],
            "Backend": [
                "Node.js", "Express.js", "Django", "Flask", "FastAPI", "Spring Boot",
                "ASP.NET", "Ruby on Rails", "Laravel", "NestJS"
            ],
            "Databases": [
                "MongoDB", "PostgreSQL", "MySQL", "Redis", "Elasticsearch", 
                "DynamoDB", "Cassandra", "Oracle", "SQL Server", "SQLite"
            ],
            "Cloud & DevOps": [
                "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Terraform", 
                "Jenkins", "GitLab CI", "GitHub Actions", "Ansible", "Chef", "CI/CD"
            ],
            "Data & ML": [
                "TensorFlow", "PyTorch", "Scikit-learn", "Pandas", "NumPy", 
                "Keras", "OpenCV", "NLTK", "SpaCy", "Hadoop", "Spark", "Machine Learning"
            ],
            "Tools": [
                "Git", "GitHub", "GitLab", "Jira", "Postman", "VS Code", "IntelliJ", 
                "Figma", "Slack", "Confluence", "Linux", "Bash", "JUnit"
            ],
            "Soft Skills": [
                "Leadership", "Communication", "Teamwork", "Problem-solving",
                "Time management", "Adaptability", "Critical thinking", "Collaboration"
            ],
            "Certifications": [
                "AWS Certified", "Google Cloud Certified", "Azure Certified",
                "PMP", "Scrum Master", "CISSP"
            ]
        }
        
        # Skill synonyms and variations
        self.skill_synonyms = {
            "AWS": ["Amazon Web Services", "AWS Cloud"],
            "Node.js": ["NodeJS", "Node"],
            "React": ["ReactJS", "React.js"],
            "Angular": ["AngularJS"],
            "Vue.js": ["Vue", "VueJS"],
            "MongoDB": ["Mongo"],
            "PostgreSQL": ["Postgres", "PSQL"],
            "JavaScript": ["JS"],
            "TypeScript": ["TS"],
            "Kubernetes": ["K8s"],
            "Machine Learning": ["ML"],
            "Artificial Intelligence": ["AI"],
            "CI/CD": ["Continuous Integration", "Continuous Deployment"]
        }
        
        # Skill relationships for transferable skills analysis
        self.skill_relationships = {
            "Python": ["Django", "Flask", "FastAPI", "Pandas", "NumPy"],
            "JavaScript": ["React", "Angular", "Vue.js", "Node.js", "Express.js"],
            "Java": ["Spring Boot", "Hibernate"],
            "AWS": ["Docker", "Kubernetes", "Terraform"],
            "React": ["Next.js", "Redux", "Material-UI"],
            "SQL": ["PostgreSQL", "MySQL", "Oracle"]
        }
        
        # Learning difficulty levels
        self.skill_difficulty = {
            "easy": ["HTML", "CSS", "Git", "Jira", "Slack"],
            "medium": ["JavaScript", "Python", "React", "MongoDB", "Docker", "Node.js"],
            "hard": ["Kubernetes", "AWS", "Machine Learning", "Microservices", "System Design"]
        }

    def extract_skills(self, text: str, priority_levels: Optional[Dict] = None, 
                       hybrid: bool = True) -> List[Dict]:
        """Extract skills with enhanced categorization and context."""
        found_skills = []
        text_lower = text.lower()
        
        for category, skills_list in self.skill_categories.items():
            for skill in skills_list:
                if self._find_skill_in_text(text, skill):
                    prominence = self._calculate_prominence(text_lower, skill)
                    found_skills.append({
                        "skill": skill,
                        "category": category,
                        "priority": priority_levels.get(skill, "medium") if priority_levels else "medium",
                        "prominence": prominence,
                        "difficulty": self._get_difficulty(skill),
                        "related_skills": self.skill_relationships.get(skill, [])
                    })
        
        ai_skills = []
        if self.use_ai and self.llm_client:
            ai_skills = self.extract_skills_ai(text)
        
        if hybrid and ai_skills:
            all_skills = {s["skill"].lower(): s for s in found_skills}
            for s in ai_skills:
                skill_lower = s["skill"].lower()
                if skill_lower not in all_skills:
                    # Find proper category name
                    s["category"] = self._categorize_skill(s["skill"])
                    s["difficulty"] = self._get_difficulty(s["skill"])
                    s["related_skills"] = self.skill_relationships.get(s["skill"], [])
                    all_skills[skill_lower] = s
            return list(all_skills.values())
        elif self.use_ai and ai_skills:
            return ai_skills
        else:
            return found_skills

    def _categorize_skill(self, skill: str) -> str:
        """Find the proper category for a skill."""
        skill_lower = skill.lower()
        for category, skills_list in self.skill_categories.items():
            if any(skill_lower == s.lower() for s in skills_list):
                return category
        return "Tools"  # Default category

    def extract_skills_ai(self, text: str) -> List[Dict]:
        """AI-powered skill extraction with robust JSON handling."""
        prompt = f"""Extract ALL technical and soft skills from this text. Be thorough and specific.

Text: {text[:2500]}

Return ONLY a JSON array of objects with this structure:
[
  {{"skill": "Python", "category": "Programming Languages", "experience_level": "expert"}},
  {{"skill": "React", "category": "Frontend", "experience_level": "intermediate"}}
]

Categories: Programming Languages, Frontend, Backend, Databases, Cloud & DevOps, Data & ML, Tools, Soft Skills, Certifications

Experience levels: beginner, intermediate, expert

Return ONLY the JSON array, no explanations."""
        
        try:
            response = self.llm_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a skill extraction expert. Return only valid JSON arrays."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=800
            )
            
            content = response.choices[0].message.content.strip()
            print("[SkillsExtractor] LLM raw output:", content)
            
            # Remove code block markers and whitespace
            content = re.sub(r'```json\s*', '', content)
            content = re.sub(r'```\s*', '', content).strip()
            
            # Remove trailing commas before closing brackets
            content = re.sub(r',\s*([\]}])', r'\1', content)
            
            # Ensure it starts with [ and ends with ]
            if "[" in content and not content.startswith("["):
                content = content[content.find("["):]
            if "]" in content and not content.endswith("]"):
                content = content[:content.rfind("]")+1]
            
            if not content or content == "[]":
                print("[SkillsExtractor] AI returned empty response")
                return []
            
            try:
                skills = json.loads(content)
            except Exception as e:
                print(f"[SkillsExtractor] JSON parse error after cleaning: {e}")
                return []
            
            validated_skills = []
            for s in skills:
                if "skill" in s and s["skill"]:
                    validated_skills.append({
                        "skill": s["skill"],
                        "category": s.get("category", "Tools"),
                        "experience_level": s.get("experience_level", "intermediate"),
                        "prominence": 1
                    })
            
            print(f"[SkillsExtractor] AI extracted {len(validated_skills)} skills")
            return validated_skills
            
        except Exception as e:
            print(f"[SkillsExtractor] AI extraction failed: {e}")
            return []

    def identify_priority_from_jd(self, jd_text: str) -> Dict[str, str]:
        """Enhanced priority identification from job description."""
        priorities = {}
        
        critical_patterns = [
            r"required|must have|essential|mandatory|critical",
            r"minimum \d+ years",
            r"strong proficiency in"
        ]
        
        preferred_patterns = [
            r"preferred|desired|nice to have|bonus|plus",
            r"familiarity with|exposure to"
        ]
        
        lines = jd_text.split('\n')
        current_priority = "medium"
        
        for line in lines:
            line_lower = line.lower()
            
            if any(re.search(pattern, line_lower) for pattern in critical_patterns):
                current_priority = "critical"
            elif any(re.search(pattern, line_lower) for pattern in preferred_patterns):
                current_priority = "preferred"
            elif "qualifications" in line_lower or "requirements" in line_lower:
                current_priority = "critical"
            
            for category, skills_list in self.skill_categories.items():
                for skill in skills_list:
                    if self._find_skill_in_text(line, skill):
                        if skill in priorities:
                            if priorities[skill] == "preferred" and current_priority == "critical":
                                priorities[skill] = "critical"
                        else:
                            priorities[skill] = current_priority
        
        return priorities

    def identify_transferable_skills(self, resume_skills: List[str], 
                                    missing_skills: List[str]) -> List[Dict]:
        """Identify skills that can help learn missing skills faster."""
        transferable = []
        resume_skill_names = [s.lower() if isinstance(s, str) else s.get("skill", "").lower() 
                             for s in resume_skills]
        
        for missing in missing_skills:
            missing_name = missing if isinstance(missing, str) else missing.get("skill", "")
            
            for resume_skill in resume_skills:
                resume_skill_name = resume_skill if isinstance(resume_skill, str) else resume_skill.get("skill", "")
                related = self.skill_relationships.get(resume_skill_name, [])
                
                if missing_name in related:
                    transferable.append({
                        "missing_skill": missing_name,
                        "transferable_from": resume_skill_name,
                        "reason": f"Experience with {resume_skill_name} will help learn {missing_name}",
                        "learning_advantage": "high"
                    })
                    break
        
        return transferable

    def _find_skill_in_text(self, text: str, skill: str) -> bool:
        """Enhanced skill finding with synonyms and case-insensitive matching."""
        text_lower = text.lower()
        
        if re.search(r'\b' + re.escape(skill.lower()) + r'\b', text_lower):
            return True
        
        for synonym in self.skill_synonyms.get(skill, []):
            if re.search(r'\b' + re.escape(synonym.lower()) + r'\b', text_lower):
                return True
        
        return False

    def _calculate_prominence(self, text_lower: str, skill: str) -> int:
        """Calculate how prominently a skill is mentioned."""
        count = len(re.findall(r'\b' + re.escape(skill.lower()) + r'\b', text_lower))
        
        for synonym in self.skill_synonyms.get(skill, []):
            count += len(re.findall(r'\b' + re.escape(synonym.lower()) + r'\b', text_lower))
        
        return min(count, 5)

    def _get_difficulty(self, skill: str) -> str:
        """Get learning difficulty for a skill."""
        for level, skills in self.skill_difficulty.items():
            if skill in skills:
                return level
        
        for category, skills in self.skill_categories.items():
            if skill in skills:
                if category in ["Programming Languages", "Cloud & DevOps", "Data & ML"]:
                    return "hard"
                elif category in ["Frontend", "Backend", "Databases"]:
                    return "medium"
                else:
                    return "easy"
        
        return "medium"
    
    def extract_experience_level(self, text: str, skill: str) -> str:
        """
        Determine experience level for a skill based on context clues.
        Returns: "beginner", "intermediate", "expert"
        """
        text_lower = text.lower()
        skill_lower = skill.lower()
        expert_patterns = [
            f"expert in {skill_lower}",
            f"{skill_lower} expert",
            f"advanced {skill_lower}",
            f"mastery of {skill_lower}",
            f"specialized in {skill_lower}",
            r"[0-9]+ years.*" + skill_lower
        ]
        for pattern in expert_patterns:
            if re.search(pattern, text_lower):
                return "expert"
        intermediate_patterns = [
            f"proficient in {skill_lower}",
            f"experienced with {skill_lower}",
            f"working knowledge of {skill_lower}",
            f"strong {skill_lower}"
        ]
        for pattern in intermediate_patterns:
            if re.search(pattern, text_lower):
                return "intermediate"
        return "beginner"

    def suggest_keyword_improvements(self, resume_text, jd_text):
        """
        Analyze resume for ATS keyword optimization.
        Returns suggestions for improving keyword density and placement.
        """
        resume_lower = resume_text.lower()
        jd_lower = jd_text.lower()
        suggestions = {
            "missing_keywords": [],
            "weak_keywords": [],
            "good_keywords": [],
            "placement_tips": []
        }
        jd_keywords = self._extract_important_keywords(jd_text)
        for keyword in jd_keywords:
            keyword_lower = keyword.lower()
            count_in_resume = resume_lower.count(keyword_lower)
            if count_in_resume == 0:
                suggestions["missing_keywords"].append({
                    "keyword": keyword,
                    "recommendation": f"Add '{keyword}' to your resume if you have experience"
                })
            elif count_in_resume == 1:
                suggestions["weak_keywords"].append({
                    "keyword": keyword,
                    "recommendation": f"'{keyword}' appears only once - mention it 2-3 times in different contexts"
                })
            else:
                suggestions["good_keywords"].append(keyword)
        if suggestions["missing_keywords"]:
            suggestions["placement_tips"].append(
                "Create a 'Technical Skills' section and list all relevant skills prominently"
            )
        if suggestions["weak_keywords"]:
            suggestions["placement_tips"].append(
                "Mention key skills in your summary, experience descriptions, and skills section"
            )
        if "skills" not in resume_lower and "technical skills" not in resume_lower:
            suggestions["placement_tips"].append(
                "Add a dedicated 'Skills' or 'Technical Skills' section for better ATS parsing"
            )
        return suggestions

    def _extract_important_keywords(self, jd_text):
        """Extract important technical keywords from JD"""
        keywords = []
        for category, skills_list in self.skill_categories.items():
            for skill in skills_list:
                if self._find_skill_in_text(jd_text, skill):
                    keywords.append(skill)
        return keywords

    def get_skill_statistics(self, skills: List[Dict]) -> Dict:
        """Calculate statistics about extracted skills."""
        stats = {
            "total_skills": len(skills),
            "by_category": {},
            "by_difficulty": {"easy": 0, "medium": 0, "hard": 0},
            "high_prominence": []
        }
        
        for skill in skills:
            category = skill.get("category", "unknown")
            stats["by_category"][category] = stats["by_category"].get(category, 0) + 1
            
            difficulty = skill.get("difficulty", "medium")
            stats["by_difficulty"][difficulty] = stats["by_difficulty"].get(difficulty, 0) + 1
            
            if skill.get("prominence", 0) >= 3:
                stats["high_prominence"].append(skill["skill"])
        
        return stats