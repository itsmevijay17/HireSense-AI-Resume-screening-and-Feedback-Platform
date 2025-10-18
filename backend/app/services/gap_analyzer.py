import json
from .skills_extractor import SkillsExtractor

class SkillsGapAnalyzer:
    def __init__(self, use_ai=False, llm_client=None):
        self.extractor = SkillsExtractor(use_ai=use_ai, llm_client=llm_client)
        self.use_ai = use_ai
        self.llm_client = llm_client
        
        # Transferable skills mapping
        self.transferable_map = {
            "Python": ["Django", "Flask", "FastAPI", "Data Science", "Machine Learning"],
            "JavaScript": ["React", "Node.js", "Vue.js", "Angular", "TypeScript"],
            "Java": ["Spring Boot", "Hibernate", "Kotlin", "Android"],
            "SQL": ["PostgreSQL", "MySQL", "Oracle", "Database Design"],
            "AWS": ["Azure", "GCP", "Cloud Architecture", "DevOps"],
            "Docker": ["Kubernetes", "Container Orchestration", "Microservices"],
            "Git": ["GitHub Actions", "GitLab CI", "Version Control", "CI/CD"],
            "React": ["Next.js", "React Native", "Redux", "Frontend Architecture"],
            "Node.js": ["Express.js", "NestJS", "Backend Development"],
            "Leadership": ["Team Management", "Project Management", "Mentoring"],
            "Communication": ["Presentation", "Documentation", "Stakeholder Management"]
        }
        
        # Skill difficulty levels
        self.skill_difficulty = {
            "easy": ["Git", "HTML", "CSS", "Agile", "Scrum", "Jira", "GitHub", "GitLab"],
            "medium": ["JavaScript", "Python", "SQL", "REST API", "Docker", "MongoDB", "Node.js", "React", "PostgreSQL"],
            "hard": ["AWS", "Kubernetes", "Machine Learning", "System Design", "Microservices", "Spring Boot"]
        }
        
        # Learning time estimates (in weeks)
        self.learning_time = {
            "easy": 2,
            "medium": 6,
            "hard": 12
        }

    def analyze_gap(self, resume_text, jd_text, hybrid=True):
        """Enhanced gap analysis with transferable skills and learning paths"""
        
        # Extract skills from both sources
        jd_priorities = self.extractor.identify_priority_from_jd(jd_text)
        jd_skills = self.extractor.extract_skills(jd_text, jd_priorities)
        resume_skills = self.extractor.extract_skills(resume_text)
        
        # Normalize skill names for better matching
        resume_skill_names = {self._normalize_skill(s["skill"]): s for s in resume_skills}
        jd_skill_names = {self._normalize_skill(s["skill"]): s for s in jd_skills}
        
        matched_skills = []
        missing_skills = []
        transferable_skills = []
        
        # Analyze each JD skill
        for jd_skill_norm, jd_skill_obj in jd_skill_names.items():
            if jd_skill_norm in resume_skill_names:
                # Direct match
                matched_skills.append({
                    **jd_skill_obj,
                    "match_type": "exact"
                })
            else:
                # Check for transferable skills
                transferable = self._find_transferable_skills(
                    jd_skill_obj["skill"], 
                    list(resume_skill_names.values())
                )
                
                if transferable:
                    transferable_skills.append({
                        "skill": jd_skill_obj["skill"],
                        "category": jd_skill_obj.get("category", "Unknown"),
                        "priority": jd_skill_obj.get("priority", "medium"),
                        "related_skills": transferable,
                        "related_skill": transferable[0] if transferable else "",  # For singular reference
                        "confidence": "high" if len(transferable) > 1 else "medium"
                    })
                else:
                    # Add difficulty and learning time
                    difficulty = self._get_difficulty(jd_skill_obj["skill"])
                    missing_skills.append({
                        **jd_skill_obj,
                        "difficulty": difficulty,
                        "estimated_weeks": self.learning_time.get(difficulty, 8),
                        "priority_score": self._calculate_priority_score(jd_skill_obj)
                    })
        
        # Sort missing skills by priority score
        missing_skills.sort(key=lambda x: x.get("priority_score", 0), reverse=True)
        
        # Calculate metrics
        total_jd_skills = len(jd_skills)
        match_percentage = round((len(matched_skills) / total_jd_skills * 100), 2) if total_jd_skills else 0
        transferable_boost = round((len(transferable_skills) / total_jd_skills * 100), 2) if total_jd_skills else 0
        adjusted_match = min(100, match_percentage + (transferable_boost * 0.5))
        
        # Calculate ATS score (multiple factors)
        ats_score = self._calculate_ats_score(
            matched_skills, 
            missing_skills, 
            transferable_skills, 
            jd_priorities
        )
        
        result = {
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "transferable_skills": transferable_skills,
            "match_percentage": match_percentage,
            "adjusted_match_percentage": round(adjusted_match, 2),
            "ats_score": ats_score,
            "total_jd_skills": total_jd_skills,
            "skill_clusters": self._cluster_missing_skills(missing_skills),
            "learning_roadmap": self._generate_learning_roadmap(missing_skills)
        }
        
        # AI-powered gap analysis (if enabled)
        if self.use_ai and self.llm_client and hybrid:
            ai_gap = self.analyze_gap_ai(resume_text, jd_text, result)
            result["ai_insights"] = ai_gap
        
        return result

    def _normalize_skill(self, skill):
        """Normalize skill names for better matching"""
        # Handle common variations
        skill_lower = skill.lower().strip()
        normalizations = {
            "node.js": "nodejs",
            "node js": "nodejs",
            "react.js": "react",
            "vue.js": "vue",
            "c++": "cpp",
            "c#": "csharp",
            ".net": "dotnet",
            "ci/cd": "cicd"
        }
        return normalizations.get(skill_lower, skill_lower)

    def _find_transferable_skills(self, target_skill, resume_skills):
        """Find transferable skills from resume that relate to target skill"""
        transferable = []
        
        for base_skill, related_skills in self.transferable_map.items():
            if self._normalize_skill(target_skill) in [self._normalize_skill(s) for s in related_skills]:
                # Check if candidate has the base skill
                for resume_skill_obj in resume_skills:
                    resume_skill = resume_skill_obj.get("skill", "")
                    if self._normalize_skill(base_skill) == self._normalize_skill(resume_skill):
                        transferable.append(base_skill)
                        break
        
        return transferable

    def _get_difficulty(self, skill):
        """Determine learning difficulty of a skill"""
        skill_norm = self._normalize_skill(skill)
        
        for difficulty, skills in self.skill_difficulty.items():
            if any(self._normalize_skill(s) == skill_norm for s in skills):
                return difficulty
        
        # Default to medium if not found
        return "medium"

    def _calculate_priority_score(self, skill_obj):
        """Calculate priority score for missing skills"""
        score = 0
        
        # Priority level from JD - FIXED to include 'preferred'
        priority_weights = {
            "critical": 10, 
            "high": 7, 
            "important": 6,
            "medium": 5, 
            "preferred": 4,
            "low": 3,
            "nice-to-have": 2
        }
        score += priority_weights.get(skill_obj.get("priority", "medium"), 5)
        
        # Category weight
        category_weights = {
            "Programming Languages": 9,
            "Cloud & DevOps": 8,
            "Backend": 8,
            "Frontend": 7,
            "Databases": 7,
            "Data & ML": 8,
            "Tools": 6,
            "Soft Skills": 5,
            "Certifications": 9
        }
        score += category_weights.get(skill_obj.get("category", "Tools"), 5)
        
        return score

    def _calculate_ats_score(self, matched, missing, transferable, priorities):
        """Calculate comprehensive ATS score"""
        score = 0
        max_score = 100
        
        # Keyword matching (40 points)
        total_skills = len(matched) + len(missing) + len(transferable)
        if total_skills > 0:
            keyword_score = (len(matched) / total_skills) * 40
            score += keyword_score
        
        # Priority skills (30 points)
        critical_matched = sum(1 for s in matched if s.get("priority") == "critical")
        critical_total = sum(1 for s in (matched + missing + transferable) if s.get("priority") == "critical")
        if critical_total > 0:
            priority_score = (critical_matched / critical_total) * 30
            score += priority_score
        
        # Transferable skills bonus (15 points)
        if len(transferable) > 0:
            transferable_score = min(15, len(transferable) * 3)
            score += transferable_score
        
        # Experience indicators (15 points)
        score += 10  # Placeholder for resume quality metrics
        
        return round(min(score, max_score), 2)

    def _cluster_missing_skills(self, missing_skills):
        """Group missing skills by learning path/domain - IMPROVED to reduce 'Other' category"""
        clusters = {
            "Frontend Development": [],
            "Backend Development": [],
            "DevOps & Cloud": [],
            "Databases & Data": [],
            "Development Tools": [],
            "Soft Skills": []
        }
        
        cluster_keywords = {
            "Frontend Development": ["react", "vue", "angular", "html", "css", "javascript", "typescript", "frontend", "next.js", "redux", "bootstrap", "tailwind"],
            "Backend Development": ["python", "java", "node", "express", "api", "django", "spring", "backend", "flask", "fastapi", "nestjs", "kotlin"],
            "DevOps & Cloud": ["aws", "azure", "docker", "kubernetes", "ci/cd", "jenkins", "terraform", "cloud", "gcp", "ansible", "cicd"],
            "Databases & Data": ["mysql", "postgresql", "mongodb", "redis", "sql", "database", "nosql", "elasticsearch", "cassandra", "oracle"],
            "Development Tools": ["git", "github", "gitlab", "jira", "postman", "junit", "vs code", "intellij", "linux", "bash"],
            "Soft Skills": ["leadership", "communication", "agile", "scrum", "management", "teamwork", "collaboration"]
        }
        
        for skill in missing_skills:
            skill_name = skill["skill"].lower()
            category = skill.get("category", "").lower()
            clustered = False
            
            # First try keyword matching
            for cluster_name, keywords in cluster_keywords.items():
                if any(keyword in skill_name for keyword in keywords):
                    clusters[cluster_name].append(skill)
                    clustered = True
                    break
            
            # If not clustered by keyword, try category matching
            if not clustered:
                if "frontend" in category:
                    clusters["Frontend Development"].append(skill)
                elif "backend" in category:
                    clusters["Backend Development"].append(skill)
                elif "cloud" in category or "devops" in category:
                    clusters["DevOps & Cloud"].append(skill)
                elif "database" in category or "data" in category:
                    clusters["Databases & Data"].append(skill)
                elif "tool" in category:
                    clusters["Development Tools"].append(skill)
                elif "soft" in category or "skill" in category:
                    clusters["Soft Skills"].append(skill)
                else:
                    # Try to infer from skill name patterns
                    if any(term in skill_name for term in ["test", "debug", "lint"]):
                        clusters["Development Tools"].append(skill)
                    elif any(term in skill_name for term in ["design", "architecture", "pattern"]):
                        clusters["Backend Development"].append(skill)
                    else:
                        # Last resort - put in most relevant cluster based on difficulty
                        difficulty = skill.get("difficulty", "medium")
                        if difficulty == "hard":
                            clusters["DevOps & Cloud"].append(skill)
                        else:
                            clusters["Development Tools"].append(skill)
        
        # Remove empty clusters
        return {k: v for k, v in clusters.items() if v}

    def _generate_learning_roadmap(self, missing_skills):
        """Create a 30/60/90 day learning roadmap"""
        roadmap = {
            "quick_wins_30_days": [],
            "intermediate_60_days": [],
            "advanced_90_days": []
        }
        
        for skill in missing_skills:
            difficulty = skill.get("difficulty", "medium")
            priority = skill.get("priority_score", 5)
            
            # Quick wins: Easy skills OR high-priority skills
            if difficulty == "easy" or priority > 12:
                roadmap["quick_wins_30_days"].append(skill)
            # Intermediate: Medium difficulty OR medium-high priority
            elif difficulty == "medium" or priority > 8:
                roadmap["intermediate_60_days"].append(skill)
            # Advanced: Hard skills OR lower priority
            else:
                roadmap["advanced_90_days"].append(skill)
        
        return roadmap

    def analyze_gap_ai(self, resume_text, jd_text, base_analysis):
        """Enhanced AI analysis with structured insights - FIXED career_fit parsing"""
        prompt = f"""Analyze the skill gap between this resume and job description. Provide insights in JSON format.

Resume: {resume_text[:1200]}

Job Description: {jd_text[:1200]}

Current Analysis:
- Matched: {len(base_analysis['matched_skills'])} skills
- Missing: {len(base_analysis['missing_skills'])} skills
- Transferable: {len(base_analysis['transferable_skills'])} skills

Provide a JSON object with:
1. "overall_assessment": Brief 2-3 sentence summary
2. "strengths": Array of 3 candidate strengths (strings)
3. "improvement_areas": Array of 3 specific areas to improve (strings)
4. "career_fit": Integer from 1-10
5. "career_fit_explanation": Brief 1-sentence explanation
6. "unique_insights": Any non-obvious observations (string)

Return ONLY valid JSON, no markdown or extra text."""

        try:
            response = self.llm_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=600
            )
            
            content = response.choices[0].message.content.strip()
            
            # Clean response
            if content.startswith("```"):
                content = content.strip("`").strip()
                if content.startswith("json"):
                    content = content[4:].strip()
            
            ai_insights = json.loads(content) if content else {}
            
            # Ensure proper structure
            if not isinstance(ai_insights.get("strengths", []), list):
                ai_insights["strengths"] = []
            if not isinstance(ai_insights.get("improvement_areas", []), list):
                ai_insights["improvement_areas"] = []
            
            # Ensure career_fit is an integer
            if "career_fit" in ai_insights:
                try:
                    ai_insights["career_fit"] = int(ai_insights["career_fit"])
                except:
                    ai_insights["career_fit"] = 5
            
            return ai_insights
            
        except Exception as e:
            print(f"AI gap analysis failed: {e}")
            return {
                "overall_assessment": "AI analysis unavailable",
                "strengths": [],
                "improvement_areas": [],
                "career_fit": 5,
                "career_fit_explanation": "",
                "unique_insights": ""
            }

    def generate_personalized_learning_plan(self, missing_skills, resume_skills):
        resume_skill_names = [s.get("skill", "") for s in resume_skills]
        learning_plan = []
        for skill_obj in missing_skills[:10]:
            skill = skill_obj.get("skill", "")
            difficulty = skill_obj.get("difficulty", "medium")
            priority = skill_obj.get("priority", "medium")
            prereqs = self._get_prerequisites(skill)
            missing_prereqs = [p for p in prereqs if p not in resume_skill_names]
            related_existing = []
            for resume_skill in resume_skill_names:
                if self._are_skills_related(skill, resume_skill):
                    related_existing.append(resume_skill)
            base_time = {"easy": 2, "medium": 6, "hard": 12}.get(difficulty, 6)
            adjusted_time = int(base_time * 0.7) if related_existing else base_time
            learning_plan.append({
                "skill": skill,
                "priority": priority,
                "difficulty": difficulty,
                "prerequisites": prereqs,
                "missing_prerequisites": missing_prereqs,
                "related_skills_you_have": related_existing,
                "estimated_weeks": adjusted_time,
                "learning_advantage": "high" if related_existing else "medium",
                "recommended_order": self._calculate_learning_order(
                    skill, missing_prereqs, priority
                )
            })
        learning_plan.sort(key=lambda x: x["recommended_order"])
        return learning_plan

    def _get_prerequisites(self, skill):
        prereq_map = {
            "React": ["JavaScript", "HTML", "CSS"],
            "Angular": ["TypeScript", "JavaScript"],
            "Vue.js": ["JavaScript"],
            "Django": ["Python"],
            "Flask": ["Python"],
            "FastAPI": ["Python"],
            "Spring Boot": ["Java"],
            "Node.js": ["JavaScript"],
            "Express.js": ["Node.js", "JavaScript"],
            "Kubernetes": ["Docker"],
            "Docker": [],
            "AWS": [],
            "MongoDB": [],
            "PostgreSQL": ["SQL"],
            "Machine Learning": ["Python", "Mathematics"],
            "TensorFlow": ["Python", "Machine Learning"],
            "PyTorch": ["Python", "Machine Learning"]
        }
        return prereq_map.get(skill, [])

    def _are_skills_related(self, skill1, skill2):
        relationships = {
            "Python": ["Django", "Flask", "FastAPI", "Machine Learning", "Data Science"],
            "JavaScript": ["React", "Node.js", "Angular", "Vue.js", "TypeScript"],
            "Java": ["Spring Boot", "Kotlin", "Android"],
            "Docker": ["Kubernetes"],
            "HTML": ["CSS", "React", "Angular"],
            "SQL": ["PostgreSQL", "MySQL", "Database Design"]
        }
        skill1_lower = skill1.lower()
        skill2_lower = skill2.lower()
        for base, related in relationships.items():
            if skill1_lower == base.lower() and skill2 in related:
                return True
            if skill2_lower == base.lower() and skill1 in related:
                return True
        return False

    def _calculate_learning_order(self, skill, missing_prereqs, priority):
        score = 0
        priority_weights = {"critical": 0, "important": 5, "high": 5, "medium": 10, "low": 15}
        score += priority_weights.get(priority, 10)
        score += len(missing_prereqs) * 10
        return score

    def get_skill_market_data(self, skill):
        demand_scores = {
            "Python": 98, "JavaScript": 97, "React": 95, "AWS": 92,
            "Docker": 88, "Kubernetes": 85, "Node.js": 90,
            "TypeScript": 87, "Java": 90, "PostgreSQL": 85,
            "MongoDB": 82, "Machine Learning": 78, "Angular": 80,
            "Vue.js": 75, "Django": 72, "Flask": 70, "FastAPI": 68,
            "Spring Boot": 85, "Go": 75, "Rust": 65
        }
        salary_impact = {
            "AWS": 25, "Kubernetes": 22, "Machine Learning": 30,
            "React": 18, "Python": 20, "Docker": 15,
            "TypeScript": 12, "Node.js": 15, "Spring Boot": 18,
            "Angular": 16, "PostgreSQL": 12, "MongoDB": 10
        }
        growth_trends = {
            "Rust": "rapidly growing", "Go": "growing", "TypeScript": "growing",
            "React": "stable", "Python": "stable", "Kubernetes": "growing",
            "Machine Learning": "rapidly growing", "Vue.js": "stable",
            "Angular": "declining", "jQuery": "declining"
        }
        return {
            "skill": skill,
            "market_demand_score": demand_scores.get(skill, 60),
            "salary_impact_percent": salary_impact.get(skill, 10),
            "growth_trend": growth_trends.get(skill, "stable"),
            "recommendation": self._generate_skill_recommendation(
                demand_scores.get(skill, 60),
                salary_impact.get(skill, 10),
                growth_trends.get(skill, "stable")
            )
        }

    def _generate_skill_recommendation(self, demand, salary_impact, trend):
        if demand >= 90 and salary_impact >= 20:
            return "High priority - in-demand with strong salary impact"
        elif demand >= 80:
            return "Recommended - strong market demand"
        elif trend == "rapidly growing":
            return "Future-proof - rapidly growing demand"
        elif trend == "declining":
            return "Consider modern alternatives"
        else:
            return "Solid choice - stable market demand"