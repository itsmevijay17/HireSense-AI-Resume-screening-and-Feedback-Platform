from fpdf import FPDF
import json
from datetime import datetime
import re

class PDFReportGenerator:
    def __init__(self, use_ai=False, llm_client=None):
        self.use_ai = use_ai
        self.llm_client = llm_client
        
        # Color scheme
        self.colors = {
            "primary": (41, 128, 185),
            "success": (39, 174, 96),
            "warning": (243, 156, 18),
            "danger": (231, 76, 60),
            "dark": (44, 62, 80),
            "light": (236, 240, 241),
            "white": (255, 255, 255),
            "purple": (155, 89, 182),
            "teal": (26, 188, 156)
        }

    def _clean_text(self, text):
        """Remove characters that can't be encoded in latin1"""
        if not text:
            return ""
        
        text = str(text)
        replacements = {
            '"': '"', '"': '"', ''': "'", ''': "'", '—': '-', '–': '-',
            '…': '...', '•': '*', '™': '(TM)', '®': '(R)', '©': '(C)',
            '°': ' degrees', '±': '+/-', '×': 'x', '÷': '/', '→': '->'
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        try:
            text.encode('latin1')
            return text
        except UnicodeEncodeError:
            return text.encode('latin1', errors='replace').decode('latin1')

    def _truncate_text(self, text, max_length):
        """Safely truncate text"""
        text = self._clean_text(text)
        if len(text) > max_length:
            return text[:max_length-3] + "..."
        return text

    def _extract_job_title(self, jd_text):
        """Extract job title from JD using AI or patterns"""
        if self.use_ai and self.llm_client:
            try:
                prompt = f"Extract ONLY the job title from this job description. Return just the title, nothing else.\n\n{jd_text[:500]}"
                response = self.llm_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=20
                )
                title = response.choices[0].message.content.strip()
                return title if title and len(title) < 50 else "Software Engineer"
            except:
                pass
        
        # Fallback to pattern matching
        patterns = [
            r"(?:position|role|job title):\s*(.+?)(?:\n|$)",
            r"(?:hiring for|seeking|looking for)\s+(?:a\s+)?(.+?)(?:\n|to|with)",
            r"^(.+?)\s*(?:position|role|job)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, jd_text[:300], re.IGNORECASE)
            if match:
                return match.group(1).strip()[:50]
        
        return "Target Position"

    def generate(self, candidate_name, gap_analysis, actions, resume_text=None, 
                 jd_text=None, learning_roadmap=None, job_title=None):
        """Generate comprehensive, AI-personalized PDF report"""
        try:
            # Clean inputs
            candidate_name = self._clean_text(candidate_name)
            
            # Extract job title dynamically
            if not job_title and jd_text:
                job_title = self._extract_job_title(jd_text)
            job_title = self._clean_text(job_title or "Target Position")
            
            # Initialize PDF
            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=15)
            
            # Generate personalized insights FIRST (for use throughout)
            personalized_insights = self._generate_personalized_insights(
                resume_text, jd_text, gap_analysis, actions
            )
            
            # Generate pages with personalization
            self._add_cover_page(pdf, candidate_name, job_title, gap_analysis)
            self._add_executive_summary(pdf, gap_analysis, resume_text, jd_text, 
                                       personalized_insights)
            self._add_skills_analysis(pdf, gap_analysis, personalized_insights)
            self._add_transferable_skills(pdf, gap_analysis, personalized_insights)
            self._add_action_plan(pdf, actions, gap_analysis, learning_roadmap, 
                                 personalized_insights)
            self._add_market_insights(pdf, gap_analysis, personalized_insights)
            self._add_learning_resources(pdf, actions, personalized_insights)
            self._add_next_steps(pdf, gap_analysis, personalized_insights)
            
            return pdf.output(dest='S').encode('latin1', errors='replace')
            
        except Exception as e:
            print(f"[PDFReportGenerator] Error: {e}")
            import traceback
            traceback.print_exc()
            raise

    def _generate_personalized_insights(self, resume_text, jd_text, gap_analysis, actions):
        """Generate comprehensive personalized insights using AI"""
        if not self.use_ai or not self.llm_client or not resume_text or not jd_text:
            return self._generate_fallback_insights(gap_analysis, actions)
        
        try:
            matched = [s["skill"] for s in gap_analysis.get("matched_skills", [])][:10]
            missing = [s["skill"] for s in gap_analysis.get("missing_skills", [])][:10]
            match_pct = gap_analysis.get("match_percentage", 0)
            
            prompt = f"""You are a career coach analyzing a candidate's fit for a role. Provide personalized, encouraging, and actionable insights.

**Candidate's Resume Highlights:**
{resume_text[:1000]}

**Job Description:**
{jd_text[:1000]}

**Current Match:** {match_pct}%
**Matched Skills:** {', '.join(matched)}
**Missing Skills:** {', '.join(missing)}

Generate a JSON response with these keys:

1. "executive_summary": Personalized 3-4 sentence assessment. Mention specific strengths from their resume and how they relate to the role. Be encouraging but honest about gaps.

2. "unique_strengths": Array of 3 specific strengths based on their actual experience (not generic). Format: ["strength description", ...]

3. "strategic_improvements": Array of 3 specific, actionable improvements tied to their background. Format: ["action + why it matters for THIS role", ...]

4. "career_fit_score": Integer 1-10

5. "career_fit_reasoning": 2 sentences explaining the score based on their specific background

6. "quick_wins": Array of 2-3 things they can do THIS WEEK to improve their candidacy

7. "standout_advice": One unique, non-obvious piece of advice specific to their profile and target role

8. "salary_impact": Estimate which missing skills have highest ROI. Format: "Learning [skill] could increase offers by X%"

9. "timeline_to_ready": Realistic estimate: "With focused effort, you could be interview-ready in X weeks"

Be specific, personal, and reference actual details from their resume. Avoid generic advice.

Return ONLY valid JSON."""

            response = self.llm_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
                max_tokens=1200
            )
            
            content = response.choices[0].message.content.strip()
            
            # Clean response
            if content.startswith("```"):
                content = content.strip("`").strip()
                if content.startswith("json"):
                    content = content[4:].strip()
            
            insights = json.loads(content) if content else {}
            
            # Validate structure
            required_keys = ["executive_summary", "unique_strengths", "strategic_improvements", 
                           "career_fit_score", "quick_wins"]
            for key in required_keys:
                if key not in insights:
                    insights[key] = [] if key.endswith("s") or key == "quick_wins" else ""
            
            return insights
            
        except Exception as e:
            print(f"AI personalization failed: {e}")
            return self._generate_fallback_insights(gap_analysis, actions)

    def _generate_fallback_insights(self, gap_analysis, actions):
        """Generate basic insights without AI"""
        match_pct = gap_analysis.get("match_percentage", 0)
        matched_count = len(gap_analysis.get("matched_skills", []))
        
        return {
            "executive_summary": f"You match {matched_count} key skills ({match_pct}% overall). Focus on building critical missing skills to strengthen your candidacy.",
            "unique_strengths": [
                f"Strong foundation with {matched_count} matched technical skills",
                "Demonstrated relevant experience in core technologies",
                "Transferable skills that can accelerate learning"
            ],
            "strategic_improvements": [a.get("action", "")[:80] for a in actions[:3]],
            "career_fit_score": min(10, int(match_pct / 10) + 3),
            "career_fit_reasoning": "Based on current skill match and learning potential",
            "quick_wins": ["Update resume keywords", "Highlight transferable skills", "Start learning critical missing skills"],
            "standout_advice": "Focus on building a portfolio project that showcases missing skills",
            "salary_impact": "Learning in-demand skills can increase offer potential by 15-25%",
            "timeline_to_ready": "4-8 weeks with focused effort"
        }

    def _add_cover_page(self, pdf, candidate_name, job_title, gap_analysis):
        """Professional cover page with visual appeal"""
        pdf.add_page()
        
        # Gradient-like header (two-tone)
        pdf.set_fill_color(*self.colors["primary"])
        pdf.rect(0, 0, 210, 60, 'F')
        pdf.set_fill_color(30, 100, 150)
        pdf.rect(0, 60, 210, 30, 'F')
        
        # Title
        pdf.set_text_color(*self.colors["white"])
        pdf.set_font("Arial", 'B', 32)
        pdf.ln(20)
        pdf.cell(0, 15, "Skill Gap Analysis", ln=True, align='C')
        pdf.set_font("Arial", '', 16)
        pdf.cell(0, 8, "AI-Powered Career Insights", ln=True, align='C')
        
        # Candidate info
        pdf.ln(10)
        pdf.set_font("Arial", 'B', 20)
        pdf.cell(0, 10, self._truncate_text(candidate_name, 50), ln=True, align='C')
        pdf.set_font("Arial", '', 14)
        pdf.cell(0, 8, self._truncate_text(f"Applying for: {job_title}", 60), ln=True, align='C')
        
        # Reset color
        pdf.set_text_color(*self.colors["dark"])
        
        # Key metrics with visual boxes
        pdf.ln(25)
        match_pct = gap_analysis.get("match_percentage", 0)
        ats_score = gap_analysis.get("ats_score", 0)
        adjusted_match = gap_analysis.get("adjusted_match_percentage", match_pct)
        
        metrics = [
            ("Skills Match", f"{match_pct:.0f}%", self.colors["primary"]),
            ("ATS Score", f"{ats_score:.0f}/100", self.colors["success"] if ats_score >= 70 else self.colors["warning"]),
            ("With Transferable", f"{adjusted_match:.0f}%", self.colors["teal"])
        ]
        
        box_width = 55
        start_x = 22
        
        for idx, (label, value, color) in enumerate(metrics):
            x = start_x + (idx * (box_width + 8))
            self._draw_enhanced_metric_box(pdf, x, 125, box_width, 35, label, value, color)
        
        # Highlights bar
        pdf.ln(55)
        pdf.set_font("Arial", 'B', 11)
        pdf.set_text_color(*self.colors["dark"])
        
        matched = len(gap_analysis.get("matched_skills", []))
        missing = len(gap_analysis.get("missing_skills", []))
        transferable = len(gap_analysis.get("transferable_skills", []))
        
        pdf.cell(0, 6, f"{matched} Matched Skills  |  {missing} Skills to Develop  |  {transferable} Transferable Skills", 
                ln=True, align='C')
        
        # Footer
        pdf.ln(15)
        pdf.set_font("Arial", '', 9)
        pdf.set_text_color(100, 100, 100)
        day = datetime.now().day
        date_str = datetime.now().strftime(f'%B {day}, %Y')
        pdf.cell(0, 5, f"Generated: {date_str}", ln=True, align='C')
        pdf.cell(0, 5, "Powered by AI-Driven Career Intelligence", ln=True, align='C')

    def _draw_enhanced_metric_box(self, pdf, x, y, width, height, label, value, color):
        """Draw enhanced metric box with shadow effect"""
        # Shadow
        pdf.set_fill_color(200, 200, 200)
        pdf.rect(x+2, y+2, width, height, 'F')
        
        # Main box
        pdf.set_fill_color(255, 255, 255)
        pdf.set_draw_color(*color)
        pdf.set_line_width(1.5)
        pdf.rect(x, y, width, height, 'FD')
        
        # Label
        pdf.set_xy(x, y + 8)
        pdf.set_font("Arial", 'B', 9)
        pdf.set_text_color(*self.colors["dark"])
        pdf.cell(width, 5, self._clean_text(label), align='C')
        
        # Value
        pdf.set_xy(x, y + 16)
        pdf.set_font("Arial", 'B', 18)
        pdf.set_text_color(*color)
        pdf.cell(width, 10, self._clean_text(value), align='C')

    def _add_executive_summary(self, pdf, gap_analysis, resume_text, jd_text, insights):
        """AI-personalized executive summary"""
        pdf.add_page()
        self._add_section_header(pdf, "Executive Summary")
        
        # AI-generated personalized summary
        summary = insights.get("executive_summary", "Analysis complete.")
        pdf.set_font("Arial", '', 11)
        pdf.multi_cell(0, 6, self._clean_text(summary))
        
        pdf.ln(8)
        
        # Career Fit Score with visual bar
        self._add_subsection_header(pdf, "Career Readiness Assessment")
        
        career_fit = insights.get("career_fit_score", 5)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(40, 8, f"Fit Score: {career_fit}/10", ln=False)
        
        # Visual score bar
        bar_x = pdf.get_x() + 5
        bar_y = pdf.get_y() + 2
        bar_width = 100
        bar_height = 6
        
        # Background
        pdf.set_fill_color(*self.colors["light"])
        pdf.rect(bar_x, bar_y, bar_width, bar_height, 'F')
        
        # Filled portion
        fill_width = (career_fit / 10) * bar_width
        color = self.colors["success"] if career_fit >= 7 else (self.colors["warning"] if career_fit >= 5 else self.colors["danger"])
        pdf.set_fill_color(*color)
        pdf.rect(bar_x, bar_y, fill_width, bar_height, 'F')
        
        pdf.ln(10)
        
        # Reasoning
        reasoning = insights.get("career_fit_reasoning", "")
        if reasoning:
            pdf.set_font("Arial", '', 10)
            pdf.multi_cell(0, 5, self._clean_text(f"  {reasoning}"))
        
        pdf.ln(5)
        
        # Your Unique Strengths
        strengths = insights.get("unique_strengths", [])
        if strengths:
            self._add_subsection_header(pdf, "Your Unique Strengths")
            pdf.set_font("Arial", '', 10)
            for strength in strengths[:3]:
                pdf.set_font("Arial", 'B', 10)
                pdf.cell(5, 6, "*", ln=False)
                pdf.set_font("Arial", '', 10)
                pdf.multi_cell(0, 6, self._clean_text(strength))
        
        pdf.ln(5)
        
        # Quick Wins
        quick_wins = insights.get("quick_wins", [])
        if quick_wins:
            self._add_subsection_header(pdf, "Quick Wins (This Week!)")
            pdf.set_font("Arial", '', 10)
            for win in quick_wins[:3]:
                pdf.set_font("Arial", 'B', 10)
                pdf.set_text_color(*self.colors["success"])
                pdf.cell(5, 6, ">", ln=False)
                pdf.set_text_color(*self.colors["dark"])
                pdf.set_font("Arial", '', 10)
                pdf.multi_cell(0, 6, self._clean_text(win))

    def _add_skills_analysis(self, pdf, gap_analysis, insights):
        """Skills breakdown with personalized context"""
        pdf.add_page()
        self._add_section_header(pdf, "Detailed Skills Analysis")
        
        # Add context
        strategic_improvements = insights.get("strategic_improvements", [])
        if strategic_improvements:
            pdf.set_font("Arial", 'I', 10)
            pdf.multi_cell(0, 5, self._clean_text(f"Focus Area: {strategic_improvements[0][:100]}"))
            pdf.ln(3)
        
        # Matched Skills
        matched_count = len(gap_analysis.get("matched_skills", []))
        self._add_subsection_header(pdf, f"Your Matched Skills ({matched_count})")
        
        if matched_count == 0:
            pdf.set_font("Arial", 'I', 10)
            pdf.cell(0, 6, "Focus on building foundational skills first.", ln=True)
        else:
            pdf.set_font("Arial", '', 9)
            pdf.set_text_color(*self.colors["success"])
            pdf.multi_cell(0, 5, "These are your strengths - highlight them prominently in your resume!")
            pdf.set_text_color(*self.colors["dark"])
            pdf.ln(2)
            self._add_skills_table(pdf, gap_analysis.get("matched_skills", [])[:12], self.colors["success"])
        
        pdf.ln(8)
        
        # Missing Skills with priority context
        missing_count = len(gap_analysis.get("missing_skills", []))
        self._add_subsection_header(pdf, f"Skills Gap ({missing_count})")
        
        critical_missing = [s for s in gap_analysis.get("missing_skills", []) if s.get("priority") == "critical"]
        
        if critical_missing:
            pdf.set_font("Arial", 'B', 9)
            pdf.set_text_color(*self.colors["danger"])
            pdf.cell(0, 5, f"PRIORITY: {len(critical_missing)} critical skills need immediate attention", ln=True)
            pdf.set_text_color(*self.colors["dark"])
            pdf.ln(2)
        
        self._add_skills_table(pdf, gap_analysis.get("missing_skills", [])[:15], self.colors["danger"])

    def _add_skills_table(self, pdf, skills, color):
        """Enhanced skills table"""
        if not skills:
            pdf.set_font("Arial", 'I', 10)
            pdf.cell(0, 6, "None identified", ln=True)
            return
        
        # Table header
        pdf.set_fill_color(*self.colors["light"])
        pdf.set_font("Arial", 'B', 9)
        pdf.cell(65, 7, "Skill", 1, 0, 'L', True)
        pdf.cell(40, 7, "Category", 1, 0, 'C', True)
        pdf.cell(30, 7, "Priority", 1, 0, 'C', True)
        pdf.cell(35, 7, "Learn Time", 1, 1, 'C', True)
        
        # Table rows
        pdf.set_font("Arial", '', 8)
        for skill in skills[:15]:
            skill_name = self._truncate_text(skill.get("skill", ""), 23)
            category = self._truncate_text(skill.get("category", ""), 16)
            priority = self._clean_text(skill.get("priority", "medium"))
            
            # Estimate learning time
            difficulty = skill.get("difficulty", "medium")
            time_map = {"easy": "1-2 weeks", "medium": "4-6 weeks", "hard": "8-12 weeks"}
            learn_time = time_map.get(difficulty, "4-6 weeks")
            
            pdf.cell(65, 6, skill_name, 1, 0, 'L')
            pdf.cell(40, 6, category, 1, 0, 'C')
            
            # Priority with color coding
            if priority == "critical":
                pdf.set_text_color(*self.colors["danger"])
            elif priority == "important" or priority == "high":
                pdf.set_text_color(*self.colors["warning"])
            else:
                pdf.set_text_color(*self.colors["dark"])
            
            pdf.cell(30, 6, priority.capitalize(), 1, 0, 'C')
            pdf.set_text_color(*self.colors["dark"])
            
            pdf.cell(35, 6, learn_time, 1, 1, 'C')

    def _add_transferable_skills(self, pdf, gap_analysis, insights):
        """Transferable skills with actionable advice"""
        pdf.add_page()
        self._add_section_header(pdf, "Leverage Your Transferable Skills")
        
        transferable = gap_analysis.get("transferable_skills", [])
        
        if not transferable:
            pdf.set_font("Arial", '', 10)
            pdf.multi_cell(0, 6, "No direct transferable skills identified. Focus on building foundational skills first.")
            return
        
        pdf.set_font("Arial", '', 10)
        pdf.multi_cell(0, 6, "You already have skills that make learning these easier! Highlight these connections in your resume:")
        pdf.ln(5)
        
        for idx, skill in enumerate(transferable[:6], 1):
            target_skill = skill.get("skill", "")
            related = skill.get("related_skills", [])
            
            if isinstance(related, list) and related:
                related_text = ", ".join(related[:3])
            else:
                related_text = skill.get("related_skill", "your experience")
            
            # Skill name
            pdf.set_font("Arial", 'B', 11)
            pdf.set_text_color(*self.colors["teal"])
            pdf.cell(0, 7, f"{idx}. {self._clean_text(target_skill)}", ln=True)
            
            # Connection
            pdf.set_font("Arial", '', 10)
            pdf.set_text_color(*self.colors["dark"])
            pdf.multi_cell(0, 5, f"   Build on your {related_text} experience")
            
            # Action tip
            pdf.set_font("Arial", 'I', 9)
            pdf.multi_cell(0, 5, f"   Tip: Mention '{related_text}' and show willingness to expand into {target_skill}")
            pdf.ln(3)
        
        # Standout advice if available
        standout = insights.get("standout_advice", "")
        if standout:
            pdf.ln(5)
            self._add_subsection_header(pdf, "Pro Tip")
            pdf.set_fill_color(255, 252, 230)
            pdf.set_font("Arial", 'I', 10)
            pdf.multi_cell(0, 6, self._clean_text(f"  {standout}"), fill=True)

    def _add_action_plan(self, pdf, actions, gap_analysis, learning_roadmap, insights):
        """Priority actions with complete, non-truncated descriptions"""
        pdf.add_page()
        self._add_section_header(pdf, "Your Personalized Action Plan")
        
        # Strategic context
        improvements = insights.get("strategic_improvements", [])
        if improvements:
            pdf.set_font("Arial", '', 10)
            pdf.multi_cell(0, 6, self._clean_text(f"Strategy: {improvements[0][:120]}"))
            pdf.ln(5)
        
        # Actions
        for idx, action in enumerate(actions[:8], 1):
            # Action title
            pdf.set_font("Arial", 'B', 11)
            impact = action.get("impact", "medium")
            color = self._get_impact_color(impact)
            pdf.set_text_color(*color)
            pdf.cell(10, 7, f"{idx}.")
            pdf.set_text_color(*self.colors["dark"])
            
            action_text = self._clean_text(action.get("action", ""))
            # COMPLETE text - no truncation
            pdf.multi_cell(0, 7, action_text)
            
            # Description if available
            description = action.get("description", "")
            if description:
                pdf.set_font("Arial", '', 9)
                # COMPLETE description - no truncation
                pdf.multi_cell(0, 5, f"   {self._clean_text(description)}")
            
            # Meta info
            pdf.set_font("Arial", '', 8)
            impact_text = self._clean_text(action.get('impact', 'medium')).capitalize()
            effort = self._clean_text(action.get('effort', action.get('difficulty', 'medium'))).capitalize()
            timeline = self._clean_text(action.get('timeline', 'TBD'))
            category = self._clean_text(action.get('category', 'General'))
            
            pdf.set_text_color(100, 100, 100)
            pdf.cell(0, 5, f"   {category} | Impact: {impact_text} | Effort: {effort} | Timeline: {timeline}", ln=True)
            pdf.set_text_color(*self.colors["dark"])
            
            # Resources if available
            resources = action.get("resources", [])
            if resources:
                pdf.set_font("Arial", 'I', 8)
                for resource in resources[:2]:
                    if isinstance(resource, dict):
                        resource_text = resource.get("name", "Resource")
                    else:
                        resource_text = str(resource)
                    pdf.cell(0, 4, f"   > {self._clean_text(resource_text[:70])}", ln=True)
            
            pdf.ln(3)
        
        # Learning Roadmap
        pdf.ln(5)
        self._add_subsection_header(pdf, "30/60/90 Day Learning Roadmap")
        
        roadmap = learning_roadmap if learning_roadmap else gap_analysis.get("learning_roadmap", {})
        
        phases = [
            ("Quick Wins (0-30 Days)", roadmap.get("quick_wins_30_days", roadmap.get("phase_1_30_days", {}).get("skills", []))),
            ("Build Momentum (30-60 Days)", roadmap.get("intermediate_60_days", roadmap.get("phase_2_60_days", {}).get("skills", []))),
            ("Master Advanced Skills (60-90 Days)", roadmap.get("advanced_90_days", roadmap.get("phase_3_90_days", {}).get("skills", [])))
        ]
        
        pdf.set_font("Arial", '', 9)
        for period, skills in phases:
            if skills:
                pdf.set_font("Arial", 'B', 10)
                pdf.cell(0, 6, self._clean_text(period), ln=True)
                pdf.set_font("Arial", '', 9)
                
                if isinstance(skills[0], dict):
                    skill_list = ", ".join([s.get("skill", str(s)) for s in skills[:6]])
                else:
                    skill_list = ", ".join([str(s) for s in skills[:6]])
                
                pdf.multi_cell(0, 5, f"  {self._clean_text(skill_list)}")
                pdf.ln(2)
        
        # Timeline to ready
        timeline = insights.get("timeline_to_ready", "")
        if timeline:
            pdf.ln(5)
            pdf.set_font("Arial", 'B', 10)
            pdf.set_text_color(*self.colors["success"])
            pdf.cell(0, 6, f"Estimated Time to Interview-Ready: {timeline}", ln=True)
            pdf.set_text_color(*self.colors["dark"])

    def _add_market_insights(self, pdf, gap_analysis, insights):
        """Market insights and salary impact"""
        pdf.add_page()
        self._add_section_header(pdf, "Market Insights & ROI")
        
        # Salary impact
        salary_impact = insights.get("salary_impact", "")
        if salary_impact:
            self._add_subsection_header(pdf, "Salary Impact Potential")
            pdf.set_font("Arial", '', 10)
            pdf.set_fill_color(230, 255, 230)
            pdf.multi_cell(0, 6, self._clean_text(f"  {salary_impact}"), fill=True)
            pdf.ln(5)
        
        # High-value skills
        missing_skills = gap_analysis.get("missing_skills", [])
        critical_skills = [s["skill"] for s in missing_skills if s.get("priority") == "critical"][:5]
        
        if critical_skills:
            self._add_subsection_header(pdf, "High-ROI Skills to Prioritize")
            pdf.set_font("Arial", '', 10)
            pdf.multi_cell(0, 6, "These skills are in high demand and critical for this role:")
            pdf.ln(2)
            
            for skill in critical_skills:
                pdf.set_font("Arial", 'B', 10)
                pdf.cell(5, 6, "*", ln=False)
                pdf.set_font("Arial", '', 10)
                pdf.cell(0, 6, self._clean_text(skill), ln=True)
        
        pdf.ln(5)
        
        # Skill clusters insight
        clusters = gap_analysis.get("skill_clusters", {})
        if clusters:
            self._add_subsection_header(pdf, "Recommended Learning Paths")
            pdf.set_font("Arial", '', 9)
            
            for cluster_name, cluster_skills in list(clusters.items())[:4]:
                if cluster_skills:
                    pdf.set_font("Arial", 'B', 9)
                    pdf.cell(0, 6, f"{cluster_name} ({len(cluster_skills)} skills)", ln=True)
                    pdf.set_font("Arial", '', 9)
                    skill_names = ", ".join([s.get("skill", "") for s in cluster_skills[:4]])
                    pdf.multi_cell(0, 5, f"  {self._clean_text(skill_names)}")
                    pdf.ln(1)

    def _add_learning_resources(self, pdf, actions, insights):
        """Curated learning resources with complete information"""
        pdf.add_page()
        self._add_section_header(pdf, "Curated Learning Resources")
        
        pdf.set_font("Arial", '', 10)
        pdf.multi_cell(0, 6, "Based on your skill gaps, here are recommended resources to accelerate your learning:")
        pdf.ln(5)
        
        # Collect resources from actions
        skill_resources = {}
        for action in actions:
            if action.get("resources"):
                skill = action.get("action", "")[:40]
                # Extract skill name from action
                for word in skill.split():
                    if word[0].isupper() and len(word) > 3:
                        skill_name = word
                        break
                else:
                    skill_name = "General"
                
                if skill_name not in skill_resources:
                    skill_resources[skill_name] = action["resources"]
        
        count = 0
        for skill, resources in list(skill_resources.items())[:8]:
            if count >= 8:
                break
            
            pdf.set_font("Arial", 'B', 10)
            pdf.set_text_color(*self.colors["primary"])
            pdf.cell(0, 6, self._clean_text(skill), ln=True)
            pdf.set_text_color(*self.colors["dark"])
            
            pdf.set_font("Arial", '', 9)
            for resource in resources[:3]:
                if isinstance(resource, dict):
                    resource_name = resource.get('name', 'Resource')
                    resource_url = resource.get('url', '')
                else:
                    resource_name = str(resource)
                    resource_url = ""
                
                pdf.cell(5, 5, ">", ln=False)
                pdf.multi_cell(0, 5, f" {self._clean_text(resource_name[:70])}")
                
                if resource_url:
                    pdf.set_font("Arial", 'I', 8)
                    pdf.set_text_color(0, 0, 255)
                    pdf.cell(0, 4, f"   {resource_url[:60]}", ln=True)
                    pdf.set_text_color(*self.colors["dark"])
                    pdf.set_font("Arial", '', 9)
            
            pdf.ln(3)
            count += 1

    def _add_next_steps(self, pdf, gap_analysis, insights):
        """Clear next steps and call to action"""
        pdf.add_page()
        self._add_section_header(pdf, "Your Next Steps")
        
        match_pct = gap_analysis.get("match_percentage", 0)
        
        # Personalized recommendation
        if match_pct >= 70:
            recommendation = "You're ready to apply! Focus on resume optimization and interview prep."
            color = self.colors["success"]
        elif match_pct >= 50:
            recommendation = "You're close! Invest 4-6 weeks building critical skills, then apply with confidence."
            color = self.colors["warning"]
        else:
            recommendation = "Build foundational skills first (8-12 weeks), then re-evaluate your readiness."
            color = self.colors["danger"]
        
        pdf.set_fill_color(*color)
        pdf.set_text_color(*self.colors["white"])
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(0, 10, self._clean_text(recommendation), ln=True, align='C', fill=True)
        pdf.set_text_color(*self.colors["dark"])
        
        pdf.ln(10)
        
        # Action checklist
        self._add_subsection_header(pdf, "Action Checklist")
        
        checklist = [
            "[ ] Review this report and identify your top 3 priority actions",
            "[ ] Update your resume to highlight matched skills prominently",
            "[ ] Reframe transferable skills to align with job requirements",
            "[ ] Enroll in 1-2 courses for critical missing skills",
            "[ ] Build a portfolio project showcasing target skills",
            "[ ] Practice explaining your learning journey in interviews",
            "[ ] Set up weekly progress tracking (use this report as baseline)",
            "[ ] Re-analyze your profile after 30 days to measure improvement"
        ]
        
        pdf.set_font("Arial", '', 10)
        for item in checklist:
            pdf.multi_cell(0, 6, self._clean_text(item))
        
        pdf.ln(8)
        
        # Motivational close
        self._add_subsection_header(pdf, "Remember")
        
        pdf.set_font("Arial", 'I', 10)
        pdf.set_fill_color(255, 250, 230)
        pdf.multi_cell(0, 6, self._clean_text(
            "Every expert was once a beginner. The skills you're building today "
            "are the foundation of your future success. Stay consistent, track your "
            "progress, and don't hesitate to showcase your learning journey - "
            "employers value growth mindset as much as current skills."
        ), fill=True)
        
        pdf.ln(5)
        
        # Contact/feedback section
        pdf.set_font("Arial", '', 9)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 5, "Questions about this report? Re-run the analysis after 30 days to track your progress.", ln=True, align='C')
        pdf.cell(0, 5, "Good luck on your career journey!", ln=True, align='C')

    def _add_section_header(self, pdf, title):
        """Styled section header"""
        pdf.set_fill_color(*self.colors["primary"])
        pdf.set_text_color(*self.colors["white"])
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, self._clean_text(title), 0, 1, 'L', True)
        pdf.set_text_color(*self.colors["dark"])
        pdf.ln(3)

    def _add_subsection_header(self, pdf, title):
        """Styled subsection header"""
        pdf.set_font("Arial", 'B', 11)
        pdf.set_text_color(*self.colors["dark"])
        pdf.cell(0, 7, self._clean_text(title), ln=True)

    def _get_impact_color(self, impact):
        """Get color based on impact level"""
        impact_lower = str(impact).lower()
        if impact_lower in ["high", "critical"]:
            return self.colors["success"]
        elif impact_lower == "medium":
            return self.colors["warning"]
        else:
            return self.colors["dark"]