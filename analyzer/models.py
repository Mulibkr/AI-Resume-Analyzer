from django.db import models

class ResumeReport(models.Model):
    filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    candidate_name = models.CharField(max_length=255, blank=True, null=True)
    candidate_email = models.EmailField(blank=True, null=True)
    candidate_phone = models.CharField(max_length=50, blank=True, null=True)
    candidate_links = models.JSONField(default=list, blank=True)
    score = models.IntegerField(default=0)
    job_description = models.TextField(blank=True, null=True)
    jd_match_score = models.IntegerField(blank=True, null=True)
    skills_found = models.JSONField(default=list, blank=True)
    skills_missing = models.JSONField(default=list, blank=True)
    sections_present = models.JSONField(default=dict, blank=True) # e.g. {'Experience': True, 'Education': False}
    recommendations = models.JSONField(default=list, blank=True)
    strengths = models.JSONField(default=list, blank=True)
    weaknesses = models.JSONField(default=list, blank=True)
    suggested_roles = models.JSONField(default=list, blank=True)
    
    def __str__(self):
        return f"{self.candidate_name or 'Resume'} ({self.score}/100) - {self.uploaded_at.strftime('%Y-%m-%d %H:%M')}"
