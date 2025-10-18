import json
from typing import List, Dict, Any, Optional

class ActionItemGenerator:
    def __init__(self, use_ai=False, llm_client=None):
        self.use_ai = use_ai
        self.llm_client = llm_client
        
        # Minimal fallback resources (only used if AI fails)
        self.fallback_resources = {
            "React": {"difficulty": "medium", "learning_time": "4-6 weeks"},
            "Angular": {"difficulty": "hard", "learning_time": "6-8 weeks"},
            "Node.js": {"difficulty": "medium", "learning_time": "4-5 weeks"},
            "Python": {"difficulty": "medium", "learning_time": "6-8 weeks"},
            "Django": {"difficulty": "medium", "learning_time": "4-6 weeks"},
            "AWS": {"difficulty": "hard", "learning_time": "8-12 weeks"},
            "Docker": {"difficulty": "medium", "learning_time": "2-3 weeks"},
            "PostgreSQL": {"difficulty": "medium", "learning_time": "3-4 weeks"},
            "Machine Learning": {"difficulty": "hard", "learning_time": "12-16 weeks"},
            "default": {"difficulty": "medium", "learning_time": "4-6 weeks"}
        }
        
        # Skill dependencies (what to learn first)
        self.skill_prerequisites = {
            "React": ["JavaScript", "HTML", "CSS"],
            "Angular": ["TypeScript", "JavaScript"],
            "Node.js": ["JavaScript"],
            "Django": ["Python"],
            "Spring Boot": ["Java"],
            "Kubernetes": ["Docker"],
            "Machine Learning": ["Python"]
        }

    def generate_priority_actions(
        self, 
        gap_analysis: Dict[str, Any], 
        resume_text: Optional[str] = None, 
        jd_text: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        AI-first action generation with intelligent fallback.
        """
        # Try AI-powered generation first (preferred)
        if self.use_ai and self.llm_client and resume_text and jd_text:
            print("[ActionGenerator] Using AI-powered action generation...")
            ai_actions = self._generate_comprehensive_ai_actions(gap_analysis, resume_text, jd_text)
            
            if ai_actions and len(ai_actions) >= 5:
                print(f"[ActionGenerator] Successfully generated {len(ai_actions)} AI actions")
                return self._ensure_proper_formatting(ai_actions)
            else:
                print("[ActionGenerator] AI generated insufficient actions, using hybrid approach...")
        
        # Fallback: Rule-based with AI enrichment
        print("[ActionGenerator] Using rule-based action generation...")
        rule_based = self._generate_rule_based_actions(gap_analysis, resume_text, jd_text)
        return self._ensure_proper_formatting(rule_based)

    def _generate_comprehensive_ai_actions(
        self, 
        gap_analysis: Dict[str, Any], 
        resume_text: str, 
        jd_text: str
    ) -> List[Dict[str, Any]]:
        """
        Comprehensive AI-powered action generation with detailed learning paths.
        """
        missing_skills = gap_analysis.get('missing_skills', [])[:10]
        matched_skills = gap_analysis.get('matched_skills', [])[:10]
        transferable_skills = gap_analysis.get('transferable_skills', [])[:5]
        match_pct = gap_analysis.get('match_percentage', 0)
        
        # Build context
        missing_skills_str = ", ".join([s['skill'] for s in missing_skills])
        matched_skills_str = ", ".join([s['skill'] for s in matched_skills])
        transferable_str = ", ".join([
            f"{s.get('skill', '')} (from {s.get('related_skill', s.get('related_skills', ['experience'])[0] if s.get('related_skills') else 'experience')})" 
            for s in transferable_skills
        ])
        
        critical_skills = [s['skill'] for s in missing_skills if s.get('priority') == 'critical'][:3]
        
        prompt = f"""You are an expert career coach. Generate 8-10 detailed, actionable recommendations for this candidate.

**CANDIDATE PROFILE:**
Current Skills: {matched_skills_str}
Match Rate: {match_pct}%
Resume Snippet: {resume_text[:800]}

**TARGET ROLE:**
Job Description: {jd_text[:800]}

**GAP ANALYSIS:**
Critical Missing Skills: {', '.join(critical_skills) if critical_skills else 'None'}
All Missing Skills: {missing_skills_str}
Transferable Skills: {transferable_str}

**INSTRUCTIONS:**
Generate specific, personalized actions in these categories:

1. **Quick Wins (2-3 actions)**: Resume rewording, highlighting transferable skills
   - Be specific about what to change
   - Reference actual skills they have

2. **Skill Development (3-4 actions)**: For critical missing skills
   - Recommend SPECIFIC courses with platform names (Udemy, Coursera, YouTube)
   - Include instructor names if known
   - Suggest hands-on practice projects
   - Estimate learning time realistically

3. **Portfolio Projects (1-2 actions)**: Practical demonstrations
   - Suggest specific project ideas that combine multiple missing skills
   - Include deployment suggestions

4. **Career Strategy (1-2 actions)**: Networking, certifications, or application timing

**CRITICAL REQUIREMENTS:**
- Every action must be specific and actionable (not generic advice)
- Include real course names and platforms where possible
- Provide realistic timelines
- Tailor advice to candidate's existing skills

Return ONLY a valid JSON array (no markdown, no extra text):
[
  {{
    "action": "Specific action to take",
    "description": "Detailed explanation with specific resources (2-3 sentences)",
    "impact": "critical|high|medium|low",
    "difficulty": "easy|medium|hard",
    "category": "Quick Win|Skill Development|Portfolio Project|Career Strategy|Resume Optimization",
    "timeline": "realistic time estimate",
    "specific_resources": ["Specific course/resource names with platform"],
    "practice_suggestion": "Concrete practice project or activity"
  }}
]"""

        try:
            response = self.llm_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a career coach providing specific, actionable advice. Always return valid JSON arrays with detailed recommendations."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.4,  # Slightly higher for creativity in recommendations
                max_tokens=2000
            )
            
            content = response.choices[0].message.content.strip()
            print(f"[ActionGenerator] AI Response length: {len(content)} chars")
            
            # Clean response
            if content.startswith("```"):
                content = content.strip("`").strip()
                if content.startswith("json"):
                    content = content[4:].strip()
            
            # Extract JSON if wrapped in text
            if "[" in content and "]" in content:
                start = content.find("[")
                end = content.rfind("]") + 1
                content = content[start:end]
            
            if not content or content == "[]":
                print("[ActionGenerator] AI returned empty response")
                return []
            
            actions = json.loads(content)
            
            # Validate and enrich actions
            validated_actions = []
            for action in actions:
                if "action" in action and action["action"]:
                    # Calculate estimated_hours from timeline
                    timeline = action.get("timeline", "4 weeks")
                    hours = self._estimate_hours_from_timeline(timeline)
                    
                    validated_actions.append({
                        "action": action.get("action", ""),
                        "description": action.get("description", ""),
                        "impact": action.get("impact", "medium"),
                        "effort": action.get("difficulty", "medium"),
                        "difficulty": action.get("difficulty", "medium"),
                        "category": action.get("category", "Skill Development"),
                        "timeline": timeline,
                        "estimated_hours": hours,
                        "resources": self._format_resources(action.get("specific_resources", [])),
                        "practice": action.get("practice_suggestion", ""),
                        "ai_generated": True
                    })
            
            print(f"[ActionGenerator] Validated {len(validated_actions)} actions")
            return validated_actions
            
        except json.JSONDecodeError as e:
            print(f"[ActionGenerator] JSON parsing error: {e}")
            print(f"[ActionGenerator] Problematic content: {content[:200]}...")
            return []
        except Exception as e:
            print(f"[ActionGenerator] AI generation failed: {e}")
            return []

    def _generate_rule_based_actions(
        self, 
        gap_analysis: Dict[str, Any], 
        resume_text: Optional[str],
        jd_text: Optional[str]
    ) -> List[Dict[str, Any]]:
        """
        Rule-based fallback with optional AI enrichment for specific details.
        """
        actions = []
        missing_skills = gap_analysis.get("missing_skills", [])
        matched_skills = gap_analysis.get("matched_skills", [])
        transferable_skills = gap_analysis.get("transferable_skills", [])
        
        user_skills = [s["skill"] for s in matched_skills]
        
        # Categorize by priority
        critical_skills = [s for s in missing_skills if s.get("priority") == "critical"]
        important_skills = [s for s in missing_skills if s.get("priority") in ["important", "high"]]
        
        # 1. Transferable Skills - Quick Wins
        for skill in transferable_skills[:2]:
            related_skill = skill.get("related_skill", skill.get("related_skills", ["your experience"])[0] if skill.get("related_skills") else "your experience")
            
            # Try to get AI-generated specific advice for this skill
            if self.use_ai and self.llm_client:
                specific_advice = self._get_ai_skill_advice(skill['skill'], related_skill, "transferable")
                if specific_advice:
                    actions.append(specific_advice)
                    continue
            
            # Fallback
            actions.append({
                "action": f"Reword resume to emphasize {skill['skill']} through {related_skill} experience",
                "description": f"You have {related_skill} which translates to {skill['skill']}. Add bullet points showing this connection.",
                "impact": "high",
                "effort": "low",
                "difficulty": "easy",
                "category": "Quick Win",
                "timeline": "2-3 hours",
                "estimated_hours": 2,
                "resources": []
            })
        
        # 2. Critical Skills with AI-generated learning paths
        for skill_obj in critical_skills[:3]:
            skill = skill_obj["skill"]
            
            # Try AI-generated learning path
            if self.use_ai and self.llm_client:
                learning_action = self._get_ai_learning_path(skill, user_skills, "critical")
                if learning_action:
                    actions.append(learning_action)
                    continue
            
            # Fallback to basic recommendation
            resource = self.fallback_resources.get(skill, self.fallback_resources["default"])
            actions.append({
                "action": f"Master {skill} - critical requirement",
                "description": f"This is a must-have skill. Invest time in comprehensive learning.",
                "impact": "critical",
                "effort": resource["difficulty"],
                "difficulty": resource["difficulty"],
                "category": "Skill Development",
                "timeline": resource["learning_time"],
                "estimated_hours": self._estimate_hours_from_timeline(resource["learning_time"]),
                "resources": [],
                "skill": skill
            })
        
        # 3. Resume Optimization
        if len(matched_skills) > 0:
            top_skills = ", ".join([s['skill'] for s in matched_skills[:5]])
            actions.insert(0, {
                "action": f"Feature these matching skills prominently: {top_skills}",
                "description": "Move these to a dedicated skills section near the top for better ATS scoring",
                "impact": "high",
                "effort": "low",
                "difficulty": "easy",
                "category": "Resume Optimization",
                "timeline": "1-2 hours",
                "estimated_hours": 1,
                "resources": []
            })
        
        # 4. Portfolio Project
        if len(critical_skills) >= 2:
            project_skills = [s["skill"] for s in critical_skills[:3]]
            
            # Try AI-generated project idea
            if self.use_ai and self.llm_client:
                project_action = self._get_ai_project_idea(project_skills)
                if project_action:
                    actions.append(project_action)
                else:
                    actions.append(self._fallback_project_action(project_skills))
            else:
                actions.append(self._fallback_project_action(project_skills))
        
        return self._prioritize_actions(actions)

    def _get_ai_skill_advice(self, skill: str, related_skill: str, context: str) -> Optional[Dict[str, Any]]:
        """Get AI-generated specific advice for a single skill."""
        prompt = f"""Give specific advice for improving a resume to highlight {skill} when the candidate has {related_skill}.

Return ONLY a JSON object:
{{
  "action": "Specific action to take",
  "description": "Detailed 2-sentence explanation",
  "timeline": "time estimate"
}}

No extra text, just the JSON object."""

        try:
            response = self.llm_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=200
            )
            
            content = response.choices[0].message.content.strip()
            if content.startswith("```"):
                content = content.strip("`").strip()
                if content.startswith("json"):
                    content = content[4:].strip()
            
            advice = json.loads(content)
            
            return {
                "action": advice.get("action", ""),
                "description": advice.get("description", ""),
                "impact": "high",
                "effort": "low",
                "difficulty": "easy",
                "category": "Quick Win",
                "timeline": advice.get("timeline", "2-3 hours"),
                "estimated_hours": 2,
                "resources": [],
                "ai_generated": True
            }
        except:
            return None

    def _get_ai_learning_path(self, skill: str, existing_skills: List[str], priority: str) -> Optional[Dict[str, Any]]:
        """Get AI-generated learning path with specific resources for a skill."""
        prereqs = self.skill_prerequisites.get(skill, [])
        missing_prereqs = [p for p in prereqs if p not in existing_skills]
        
        prompt = f"""Recommend the best way to learn {skill} for someone who knows: {', '.join(existing_skills[:5])}.
{"Prerequisites needed: " + ', '.join(missing_prereqs) if missing_prereqs else "They have the prerequisites."}

Return ONLY a JSON object:
{{
  "action": "Learning action",
  "description": "2-3 sentence plan with specific course recommendations",
  "timeline": "realistic time estimate",
  "specific_resources": ["Course Name (Platform - Instructor if known)", "..."],
  "practice": "Specific project to build"
}}

No markdown, just JSON."""

        try:
            response = self.llm_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
                max_tokens=300
            )
            
            content = response.choices[0].message.content.strip()
            if content.startswith("```"):
                content = content.strip("`").strip()
                if content.startswith("json"):
                    content = content[4:].strip()
            
            path = json.loads(content)
            timeline = path.get("timeline", "6 weeks")
            
            return {
                "action": path.get("action", f"Learn {skill}"),
                "description": path.get("description", ""),
                "impact": "critical" if priority == "critical" else "high",
                "effort": "medium",
                "difficulty": "medium",
                "category": "Skill Development",
                "timeline": timeline,
                "estimated_hours": self._estimate_hours_from_timeline(timeline),
                "resources": self._format_resources(path.get("specific_resources", [])),
                "practice": path.get("practice", ""),
                "skill": skill,
                "ai_generated": True
            }
        except:
            return None

    def _get_ai_project_idea(self, skills: List[str]) -> Optional[Dict[str, Any]]:
        """Get AI-generated project idea combining multiple skills."""
        prompt = f"""Suggest a specific portfolio project that demonstrates: {', '.join(skills)}.

Return ONLY a JSON object:
{{
  "action": "Build [specific project name]",
  "description": "2-3 sentences: what to build, why it demonstrates these skills, where to deploy",
  "timeline": "time estimate",
  "practice": "Step-by-step approach"
}}

Be specific with project name and features. No markdown."""

        try:
            response = self.llm_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=250
            )
            
            content = response.choices[0].message.content.strip()
            if content.startswith("```"):
                content = content.strip("`").strip()
                if content.startswith("json"):
                    content = content[4:].strip()
            
            project = json.loads(content)
            
            return {
                "action": project.get("action", f"Build project with {', '.join(skills)}"),
                "description": project.get("description", ""),
                "impact": "critical",
                "effort": "high",
                "difficulty": "hard",
                "category": "Portfolio Project",
                "timeline": project.get("timeline", "3-4 weeks"),
                "estimated_hours": 60,
                "resources": [{"type": "guide", "name": "GitHub for hosting"}],
                "practice": project.get("practice", ""),
                "ai_generated": True
            }
        except:
            return None

    def _fallback_project_action(self, skills: List[str]) -> Dict[str, Any]:
        """Fallback project recommendation."""
        return {
            "action": f"Build a portfolio project using: {', '.join(skills)}",
            "description": "Create a full-stack application showcasing these skills, deploy it, and add to your resume",
            "impact": "critical",
            "effort": "high",
            "difficulty": "hard",
            "category": "Portfolio Project",
            "timeline": "3-4 weeks",
            "estimated_hours": 60,
            "resources": []
        }

    def _format_resources(self, resources: List) -> List[Dict[str, str]]:
        """Format resources into structured format."""
        formatted = []
        for resource in resources:
            if isinstance(resource, str):
                formatted.append({"type": "course", "name": resource})
            elif isinstance(resource, dict):
                formatted.append(resource)
        return formatted

    def _estimate_hours_from_timeline(self, timeline: str) -> int:
        """Convert timeline string to estimated hours."""
        timeline_lower = timeline.lower()
        
        if "hour" in timeline_lower:
            return int(''.join(filter(str.isdigit, timeline.split()[0])) or "2")
        elif "day" in timeline_lower:
            days = int(''.join(filter(str.isdigit, timeline.split()[0])) or "3")
            return days * 3
        elif "week" in timeline_lower:
            weeks = int(''.join(filter(str.isdigit, timeline.split()[0])) or "4")
            return weeks * 10
        elif "month" in timeline_lower:
            months = int(''.join(filter(str.isdigit, timeline.split()[0])) or "2")
            return months * 40
        else:
            return 40

    def _ensure_proper_formatting(self, actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Ensure all actions have proper fields."""
        for action in actions:
            # Ensure effort field
            if not action.get("effort") or action.get("effort") == "N/A":
                action["effort"] = action.get("difficulty", "medium")
            
            # Ensure timeline
            if not action.get("timeline") or action.get("timeline") == "N/A":
                hours = action.get("estimated_hours", 0)
                if hours > 0:
                    if hours <= 10:
                        action["timeline"] = "1-2 weeks"
                    elif hours <= 40:
                        action["timeline"] = "1 month"
                    else:
                        action["timeline"] = f"{hours//40} months"
                else:
                    action["timeline"] = "2-4 weeks"
            
            # Ensure estimated_hours
            if not action.get("estimated_hours") or action.get("estimated_hours") == 0:
                action["estimated_hours"] = self._estimate_hours_from_timeline(action.get("timeline", "4 weeks"))
        
        return actions

    def _prioritize_actions(self, actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort actions by impact and difficulty."""
        priority_map = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        difficulty_map = {"easy": 1, "medium": 2, "hard": 3}
        
        def priority_score(action):
            impact_score = priority_map.get(action.get("impact", "medium"), 2)
            difficulty_score = difficulty_map.get(action.get("difficulty", "medium"), 2)
            return (impact_score * 10) - difficulty_score
        
        return sorted(actions, key=priority_score, reverse=True)

    def generate_learning_roadmap(
        self, 
        gap_analysis: Dict[str, Any], 
        timeline_weeks: int = 12
    ) -> Dict[str, Any]:
        """Generate structured learning roadmap."""
        missing_skills = gap_analysis.get("missing_skills", [])
        critical = [s for s in missing_skills if s.get("priority") == "critical"]
        important = [s for s in missing_skills if s.get("priority") in ["important", "high"]]
        
        return {
            "phase_1_30_days": {
                "focus": "Quick wins and foundations",
                "skills": [{"skill": s["skill"], "difficulty": s.get("difficulty", "medium")} for s in critical[:2]],
                "goals": ["Complete foundational courses", "Build 1-2 small projects", "Update resume"],
                "estimated_hours": 80
            },
            "phase_2_60_days": {
                "focus": "Intermediate mastery",
                "skills": [{"skill": s["skill"], "difficulty": s.get("difficulty", "medium")} for s in (critical[2:4] + important[:2])],
                "goals": ["Build portfolio project", "Contribute to open source", "Network in communities"],
                "estimated_hours": 100
            },
            "phase_3_90_days": {
                "focus": "Advanced skills and job readiness",
                "skills": [{"skill": s["skill"], "difficulty": s.get("difficulty", "medium")} for s in important[2:5]],
                "goals": ["Complete certification", "Polish portfolio", "Start applying"],
                "estimated_hours": 80
            }
        }