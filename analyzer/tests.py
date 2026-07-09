from django.test import TestCase
from analyzer.models import ResumeReport
from analyzer.parser import extract_email, extract_phone, extract_name, extract_links, analyze_resume

class ParserHelperTestCase(TestCase):
    def setUp(self):
        self.sample_resume = """
        John Doe
        Software Engineer
        Email: john.doe@example.com | Phone: +1 123-456-7890
        GitHub: https://github.com/johndoe
        LinkedIn: linkedin.com/in/johndoe
        
        EXPERIENCE
        Senior developer building Python backend applications with Django and PostgreSQL.
        
        EDUCATION
        B.S. in Computer Science
        
        SKILLS
        Python, Django, PostgreSQL, Docker, Git, JavaScript, HTML, CSS, Problem Solving
        """
        
        self.sample_jd = """
        Looking for a Python Developer experienced in Django, PostgreSQL, and Git.
        """

    def test_extract_email(self):
        self.assertEqual(extract_email(self.sample_resume), "john.doe@example.com")
        self.assertIsNone(extract_email("No email here"))

    def test_extract_phone(self):
        # Allow variations in formatting
        phone = extract_phone(self.sample_resume)
        self.assertIn("123-456-7890", phone)
        self.assertIsNone(extract_phone("No phone number"))

    def test_extract_name(self):
        self.assertEqual(extract_name(self.sample_resume), "John Doe")

    def test_extract_links(self):
        links = extract_links(self.sample_resume)
        self.assertTrue(any("github.com/johndoe" in l.lower() for l in links))
        self.assertTrue(any("linkedin.com/in/johndoe" in l.lower() for l in links))

    def test_analyze_resume_basics(self):
        results = analyze_resume(self.sample_resume)
        self.assertEqual(results['candidate_name'], "John Doe")
        self.assertEqual(results['candidate_email'], "john.doe@example.com")
        self.assertTrue("Python" in results['skills_found'])
        self.assertTrue("Django" in results['skills_found'])
        self.assertTrue(results['sections_present']['Experience'])
        self.assertTrue(results['sections_present']['Education'])
        self.assertTrue(results['score'] > 50) # High score expected for structured data

    def test_analyze_resume_with_jd(self):
        results = analyze_resume(self.sample_resume, self.sample_jd)
        self.assertIsNotNone(results['jd_match_score'])
        # Since standard skills from JD are python, django, postgresql, git and resume has them, score should be high
        self.assertTrue(results['jd_match_score'] >= 80)
        self.assertEqual(len(results['skills_missing']), 0)

class DatabaseModelTestCase(TestCase):
    def test_resume_report_creation(self):
        report = ResumeReport.objects.create(
            filename="resume.pdf",
            candidate_name="John Doe",
            candidate_email="john@example.com",
            candidate_phone="1234567890",
            score=85,
            skills_found=["Python", "Django"],
            sections_present={"Experience": True, "Education": True}
        )
        self.assertEqual(report.filename, "resume.pdf")
        self.assertEqual(report.score, 85)
        self.assertEqual(report.skills_found, ["Python", "Django"])
        self.assertTrue("John Doe" in str(report))
