import re
import os
import pdfplumber

# Predefined taxonomy of skills categorized by domain
SKILLS_TAXONOMY = {
    'Languages': ['Python', 'JavaScript', 'TypeScript', 'Java', 'C\\+\\+', 'C\\#', 'Go', 'Rust', 'Ruby', 'PHP', 'Swift', 'Kotlin', 'HTML', 'CSS', 'SQL', 'Bash', 'R', 'Scala', 'C'],
    'Frontend': ['React', 'Angular', 'Vue', 'Next\\.js', 'Nuxt', 'Svelte', 'Bootstrap', 'Tailwind', 'jQuery', 'Sass', 'Less'],
    'Backend': ['Django', 'Flask', 'FastAPI', 'Express', 'Node\\.js', 'Spring Boot', 'Laravel', 'Rails', 'ASP\\.NET', 'NestJS', 'GraphQL'],
    'Database': ['SQLite', 'PostgreSQL', 'Postgres', 'MySQL', 'MongoDB', 'Redis', 'Oracle', 'Cassandra', 'MariaDB', 'Firebase', 'DynamoDB'],
    'Cloud & DevOps': ['Git', 'Docker', 'Kubernetes', 'AWS', 'Azure', 'GCP', 'Terraform', 'Jenkins', 'GitHub Actions', 'GitLab CI', 'Ansible'],
    'Data Science & ML': ['Pandas', 'NumPy', 'Scikit-learn', 'TensorFlow', 'PyTorch', 'Keras', 'OpenCV', 'NLTK', 'SpaCy', 'Matplotlib', 'Seaborn', 'Tableau', 'Power BI'],
    'Soft Skills & Methods': ['Agile', 'Scrum', 'Communication', 'Leadership', 'Teamwork', 'Problem Solving', 'Management', 'Project Management']
}

# Sections in resumes to scan
SECTION_KEYWORDS = {
    'Education': ['education', 'academic background', 'qualifications', 'degree', 'studies'],
    'Experience': ['experience', 'employment', 'work history', 'professional background', 'work experience', 'career history'],
    'Skills': ['skills', 'technical skills', 'technologies', 'expertise', 'core competencies'],
    'Projects': ['projects', 'personal projects', 'key projects', 'academic projects'],
    'Certifications': ['certifications', 'certificates', 'accreditations', 'courses', 'awards']
}

# Role categories and skills required for matching
ROLE_TEMPLATES = {
    'Python Backend Developer': ['Python', 'Django', 'Flask', 'FastAPI', 'SQL', 'PostgreSQL', 'SQLite', 'Docker', 'Git', 'REST'],
    'Frontend Developer': ['JavaScript', 'TypeScript', 'React', 'Angular', 'Vue', 'HTML', 'CSS', 'Tailwind', 'Bootstrap', 'Git'],
    'Full Stack Developer': ['Python', 'JavaScript', 'Django', 'React', 'Node.js', 'SQL', 'Git', 'HTML', 'CSS', 'Express'],
    'Data Scientist / ML Engineer': ['Python', 'Pandas', 'NumPy', 'Scikit-learn', 'TensorFlow', 'PyTorch', 'SQL', 'R', 'Matplotlib', 'Machine Learning'],
    'DevOps Engineer': ['AWS', 'Docker', 'Kubernetes', 'Terraform', 'Jenkins', 'Bash', 'Git', 'Linux', 'Ansible', 'CI/CD']
}

def extract_text_from_pdf(pdf_path):
    """Extracts text from a PDF file using pdfplumber."""
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                extracted_text = page.extract_text()
                if extracted_text:
                    text += extracted_text + "\n"
    except Exception as e:
        print(f"Error reading PDF {pdf_path}: {e}")
    return text

def extract_name(text):
    """Heuristic to extract name from the top lines of a resume."""
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    # Check the first few lines
    for line in lines[:5]:
        # Exclude line if it looks like contact info
        if '@' in line or any(char.isdigit() for char in line):
            continue
        
        # Exclude if it contains common resume words
        lower_line = line.lower()
        exclude_words = ['resume', 'cv', 'curriculum', 'vitae', 'portfolio', 'contact', 'address', 'page', 'email', 'phone', 'profile']
        if any(word in lower_line for word in exclude_words):
            continue
        
        # Check if the line has 2 to 4 capitalized words
        words = line.split()
        if 2 <= len(words) <= 4:
            if all(w[0].isupper() for w in words if w.isalpha()):
                return line
                
    # Fallback to first line that doesn't have an email or digit
    for line in lines[:5]:
        if '@' not in line and not any(char.isdigit() for char in line):
            return line
            
    return "Unknown Candidate"

def extract_email(text):
    """Extracts email addresses from text."""
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}'
    match = re.search(pattern, text)
    return match.group(0) if match else None

def extract_phone(text):
    """Extracts phone numbers from text."""
    # Matches common phone formats: +1 (123) 456-7890, 123-456-7890, +911234567890, etc.
    pattern = r'(?:\+?\d{1,3}[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}'
    match = re.search(pattern, text)
    if match:
        return match.group(0)
    
    # Fallback for standard 10 digit number without spacing
    pattern_fb = r'\b\d{10}\b'
    match_fb = re.search(pattern_fb, text)
    return match_fb.group(0) if match_fb else None

def extract_links(text):
    """Extracts LinkedIn, GitHub, and portfolio links from text."""
    links = []
    # Search for github link
    github_match = re.search(r'(?:https?://)?(?:www\.)?github\.com/[a-zA-Z0-9_-]+', text, re.IGNORECASE)
    if github_match:
        links.append(github_match.group(0))
        
    # Search for linkedin link
    linkedin_match = re.search(r'(?:https?://)?(?:www\.)?linkedin\.com/in/[a-zA-Z0-9_-]+', text, re.IGNORECASE)
    if linkedin_match:
        links.append(linkedin_match.group(0))
        
    # Search for other general portfolio websites (excluding email domains)
    portfolio_matches = re.findall(r'(?:https?://)?(?:www\.)?[a-zA-Z0-9-]+\.(?:com|org|net|me|io|dev)(?:/[a-zA-Z0-9_-]+)*', text, re.IGNORECASE)
    for pm in portfolio_matches:
        if 'github.com' not in pm.lower() and 'linkedin.com' not in pm.lower() and pm not in links:
            # Clean match to verify it's not part of an email address
            if not re.search(rf'[\w\.-]+@{re.escape(pm)}', text):
                links.append(pm)
                
    return links[:4] # Limit to top 4 links

def analyze_resume(resume_text, job_desc_text=None):
    """
    Main resume parsing and scoring logic.
    Analyzes skills, contact details, sections, and calculates rating scores.
    """
    results = {}
    
    # 1. Basic Info Extraction
    results['candidate_name'] = extract_name(resume_text)
    results['candidate_email'] = extract_email(resume_text)
    results['candidate_phone'] = extract_phone(resume_text)
    results['candidate_links'] = extract_links(resume_text)
    
    # 2. Section Checking
    sections_status = {}
    resume_lower = resume_text.lower()
    for section, keywords in SECTION_KEYWORDS.items():
        found = False
        for keyword in keywords:
            # Check for section title with word boundary or new lines
            pattern = rf'(?:\b|{os.linesep}){keyword}(?:\b|{os.linesep})'
            if re.search(pattern, resume_lower):
                found = True
                break
        sections_status[section] = found
    results['sections_present'] = sections_status
    
    # 3. Skills Analysis
    extracted_skills = []
    for category, skills in SKILLS_TAXONOMY.items():
        for skill in skills:
            # Handle special characters like C++, C#, .NET
            clean_skill = skill.replace('.', '\\.')
            # Use custom bounds to match skills correctly (e.g. avoid matching "Go" in "Good")
            pattern = rf'(?<![a-zA-Z0-9]){clean_skill}(?![a-zA-Z0-9])'
            if re.search(pattern, resume_text, re.IGNORECASE):
                # Clean visual name (remove escape characters)
                visual_name = skill.replace('\\', '')
                if visual_name not in extracted_skills:
                    extracted_skills.append(visual_name)
                    
    results['skills_found'] = extracted_skills
    
    # 4. Job Description Matching (if provided)
    missing_skills = []
    jd_match_score = None
    if job_desc_text:
        # Find skills mentioned in the Job Description
        jd_skills = []
        for category, skills in SKILLS_TAXONOMY.items():
            for skill in skills:
                clean_skill = skill.replace('.', '\\.')
                pattern = rf'(?<![a-zA-Z0-9]){clean_skill}(?![a-zA-Z0-9])'
                if re.search(pattern, job_desc_text, re.IGNORECASE):
                    visual_name = skill.replace('\\', '')
                    if visual_name not in jd_skills:
                        jd_skills.append(visual_name)
        
        # If JD has some skills, compute intersection
        if jd_skills:
            matched_jd_skills = [s for s in jd_skills if s in extracted_skills]
            missing_skills = [s for s in jd_skills if s not in extracted_skills]
            jd_match_score = int((len(matched_jd_skills) / len(jd_skills)) * 100)
        else:
            # If no categorized skills in JD, calculate token overlap index
            jd_words = set(re.findall(r'\b\w+\b', job_desc_text.lower()))
            resume_words = set(re.findall(r'\b\w+\b', resume_text.lower()))
            overlap = jd_words.intersection(resume_words)
            jd_match_score = int((len(overlap) / max(len(jd_words), 1)) * 100)
            
    results['skills_missing'] = missing_skills
    results['jd_match_score'] = jd_match_score
    
    # 5. Career Path Recommendation
    suggested_roles = []
    for role, req_skills in ROLE_TEMPLATES.items():
        match_count = sum(1 for s in req_skills if s in extracted_skills)
        match_pct = int((match_count / len(req_skills)) * 100)
        if match_pct >= 20: # Suggest if at least some skills align
            suggested_roles.append({
                'role': role,
                'match_percentage': match_pct,
                'aligned_skills': [s for s in req_skills if s in extracted_skills]
            })
            
    # Sort roles by match percentage
    suggested_roles = sorted(suggested_roles, key=lambda x: x['match_percentage'], reverse=True)[:3]
    results['suggested_roles'] = suggested_roles
    
    # 6. Scoring System (Out of 100)
    score = 0
    strengths = []
    weaknesses = []
    recommendations = []
    
    # A. Contact Details (Max 15 points)
    contact_pts = 0
    if results['candidate_name'] != "Unknown Candidate":
        contact_pts += 5
    else:
        weaknesses.append("Name could not be clearly parsed from the top section of the resume.")
        recommendations.append("Ensure your full name is written clearly in a large font at the very top of your resume.")
        
    if results['candidate_email']:
        contact_pts += 5
    else:
        weaknesses.append("Email address was not found in the resume.")
        recommendations.append("Add a professional email address so recruiters can contact you.")
        
    if results['candidate_phone']:
        contact_pts += 5
    else:
        weaknesses.append("Phone number was not found.")
        recommendations.append("Provide a phone number with country/area code in the header.")
        
    # Check for social links
    if results['candidate_links']:
        contact_pts = min(contact_pts + 5, 15) # Add bonus if we have email/phone and a link
        strengths.append("Found professional link(s) (GitHub, LinkedIn, or portfolio).")
    else:
        weaknesses.append("No GitHub or LinkedIn profile links were identified.")
        recommendations.append("Include your LinkedIn profile and GitHub (for developers) to showcase your work.")
        
    score += contact_pts
    
    # B. Core Sections Presence (Max 25 points)
    section_pts = 0
    for section, present in sections_status.items():
        if present:
            section_pts += 5
        else:
            weaknesses.append(f"Missing a distinct '{section}' section header.")
            recommendations.append(f"Add a dedicated, clearly labeled '{section}' section to satisfy ATS parsing engines.")
            
    if section_pts == 25:
        strengths.append("All primary resume sections (Experience, Education, Skills, Projects, Certifications) are present.")
    elif section_pts >= 15:
        strengths.append("Most key sections are clearly defined.")
    score += section_pts
    
    # C. Skill Variety (Max 30 points)
    skill_pts = 0
    num_skills = len(extracted_skills)
    if num_skills >= 12:
        skill_pts = 30
        strengths.append(f"Excellent variety of skills identified ({num_skills} technical/soft skills).")
    elif num_skills >= 6:
        skill_pts = 20
        strengths.append(f"Good range of skills listed ({num_skills} skills found).")
    elif num_skills >= 1:
        skill_pts = 10
        weaknesses.append(f"Only a few technical skills detected ({num_skills} found).")
        recommendations.append("Expand the skills section to include more related technologies, databases, or libraries.")
    else:
        skill_pts = 0
        weaknesses.append("No technical skills were parsed from the resume.")
        recommendations.append("Create a dedicated 'Skills' section listing your technical tools and programming languages.")
    score += skill_pts
    
    # D. Content Density & Heuristics (Max 10 points)
    formatting_pts = 10
    word_count = len(resume_text.split())
    if word_count < 100:
        formatting_pts -= 5
        weaknesses.append("The resume text is extremely short (under 100 words).")
        recommendations.append("Elaborate on your experience and project descriptions to explain your responsibilities and achievements.")
    elif word_count > 1500:
        formatting_pts -= 3
        weaknesses.append("The resume word count is very high (over 1500 words).")
        recommendations.append("Condense your resume description. Try to keep it within 1-2 pages for maximum readability.")
    else:
        strengths.append("Resume length and content density are within standard limits.")
        
    # Check capitalization density (e.g. ALL CAPS could trigger parser issues)
    caps_ratio = sum(1 for c in resume_text if c.isupper()) / max(len(resume_text), 1)
    if caps_ratio > 0.25:
        formatting_pts -= 2
        weaknesses.append("High density of uppercase letters detected. This might disrupt layout parses.")
        recommendations.append("Avoid writing entire sentences in block capitals; save uppercase letters for headers and proper nouns.")
        
    score += formatting_pts
    
    # E. Job Description Match Bonus/Distribution (Max 20 points)
    # If a Job Description is matched, we map the final 20 points to the JD match score.
    # If not, we allocate it based on general formatting quality and strengths score.
    if job_desc_text:
        match_contrib = int((jd_match_score / 100) * 20)
        score += match_contrib
        if jd_match_score >= 70:
            strengths.append(f"Strong match with job description keywords ({jd_match_score}% match).")
        elif jd_match_score >= 40:
            strengths.append(f"Moderate relevance to job description ({jd_match_score}% match).")
        else:
            weaknesses.append(f"Low keyword overlap with target job description ({jd_match_score}% match).")
            recommendations.append("Customize your resume for this role by incorporating relevant keywords from the job description.")
    else:
        # Default distribution based on general structure
        if len(strengths) >= 3:
            score += 20
        elif len(strengths) >= 1:
            score += 12
        else:
            score += 5
            
    # Clamp score between 0 and 100
    results['score'] = max(0, min(score, 100))
    results['strengths'] = strengths
    results['weaknesses'] = weaknesses
    results['recommendations'] = recommendations if recommendations else ["Your resume format is solid! Consider adding projects to show practical knowledge."]
    
    return results
