from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
import os
import tempfile

from analyzer.models import ResumeReport
from analyzer.parser import extract_text_from_pdf, analyze_resume

def home(request):
    """View to handle resume uploading and job description matching."""
    if request.method == 'POST':
        resume_file = request.FILES.get('resume')
        job_description = request.POST.get('job_description', '').strip()
        
        if not resume_file:
            messages.error(request, "Please select a resume file to upload.")
            return redirect('home')
            
        filename = resume_file.name
        ext = os.path.splitext(filename)[1].lower()
        
        if ext not in ['.pdf', '.txt']:
            messages.error(request, "Unsupported file format. Only PDF and TXT files are accepted.")
            return redirect('home')
            
        resume_text = ""
        
        try:
            if ext == '.pdf':
                # Save to a temporary file safely (especially for Windows file sharing locks)
                fd, temp_path = tempfile.mkstemp(suffix='.pdf')
                try:
                    with os.fdopen(fd, 'wb') as temp_file:
                        for chunk in resume_file.chunks():
                            temp_file.write(chunk)
                    # Parse PDF
                    resume_text = extract_text_from_pdf(temp_path)
                finally:
                    # Clean up temporary file
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
            else:
                # Parse TXT file
                resume_text = resume_file.read().decode('utf-8', errors='ignore')
                
        except Exception as e:
            messages.error(request, f"Error reading resume file: {str(e)}")
            return redirect('home')
            
        if not resume_text.strip():
            messages.error(request, "Failed to extract text from the resume. Ensure it is not empty or password protected.")
            return redirect('home')
            
        # Analyze the resume text
        analysis = analyze_resume(resume_text, job_description if job_description else None)
        
        # Save to database
        report = ResumeReport.objects.create(
            filename=filename,
            candidate_name=analysis['candidate_name'],
            candidate_email=analysis['candidate_email'],
            candidate_phone=analysis['candidate_phone'],
            candidate_links=analysis['candidate_links'],
            score=analysis['score'],
            job_description=job_description if job_description else None,
            jd_match_score=analysis['jd_match_score'],
            skills_found=analysis['skills_found'],
            skills_missing=analysis['skills_missing'],
            sections_present=analysis['sections_present'],
            recommendations=analysis['recommendations'],
            strengths=analysis['strengths'],
            weaknesses=analysis['weaknesses'],
            suggested_roles=analysis['suggested_roles']
        )
        
        return redirect('result', report_id=report.id)
        
    return render(request, 'home.html')

def result(request, report_id):
    """View to display detailed analysis result of a resume."""
    report = get_object_or_404(ResumeReport, id=report_id)
    
    # Calculate key summary stats for templates
    sections_count = sum(1 for present in report.sections_present.values() if present)
    total_sections = len(report.sections_present)
    
    # Determine level for display styles (e.g. colors)
    score_color = 'success'
    if report.score < 40:
        score_color = 'danger'
    elif report.score < 70:
        score_color = 'warning'
        
    jd_score_color = 'success'
    if report.jd_match_score is not None:
        if report.jd_match_score < 40:
            jd_score_color = 'danger'
        elif report.jd_match_score < 70:
            jd_score_color = 'warning'

    # Calculate gauge dashoffsets (circumference is 2 * pi * 75 = 471.2)
    score_dashoffset = ((100 - report.score) / 100.0) * 471.2
    jd_dashoffset = 471.2
    if report.jd_match_score is not None:
        jd_dashoffset = ((100 - report.jd_match_score) / 100.0) * 471.2

    context = {
        'report': report,
        'sections_count': sections_count,
        'total_sections': total_sections,
        'score_color': score_color,
        'jd_score_color': jd_score_color,
        'score_dashoffset': score_dashoffset,
        'jd_dashoffset': jd_dashoffset,
    }
    return render(request, 'result.html', context)


def history(request):
    """View to display all past resume analysis reports with search and filter functionality."""
    q = request.GET.get('q', '').strip()
    reports = ResumeReport.objects.all().order_by('-uploaded_at')
    
    if q:
        # Search by candidate name, filename, email or skills
        reports = reports.filter(
            Q(candidate_name__icontains=q) |
            Q(filename__icontains=q) |
            Q(candidate_email__icontains=q) |
            Q(skills_found__icontains=q)
        )
        
    context = {
        'reports': reports,
        'q': q
    }
    return render(request, 'history.html', context)

def delete_report(request, report_id):
    """Endpoint to delete an analysis report."""
    if request.method == 'POST':
        report = get_object_or_404(ResumeReport, id=report_id)
        report.delete()
        messages.success(request, f"Successfully deleted analysis report for {report.candidate_name or report.filename}.")
    return redirect('history')
