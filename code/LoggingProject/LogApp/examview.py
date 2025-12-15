from datetime import timedelta
from django.utils import timezone
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse, HttpResponseNotAllowed
from django.contrib import messages
from django.utils.dateparse import parse_datetime
from .models import Checkins, Exams, Courses, StudentCourses
from .examtimewindows import exam_end_buffer, checkin_window
import csv


# --------------------------------------------
# Helper Functions
# --------------------------------------------

# Retrieve a course by course ID or return 404
def get_course(course_id):
    return get_object_or_404(Courses, pk=course_id)

# Retrieve an exam by its primary key or return 404
def get_exam(exam_id):
    return get_object_or_404(Exams, pk=exam_id)

# Split exams into future and past based on current date
def get_exams_split(course):
    now = timezone.now()
    exams = Exams.objects.filter(course=course) 

    time_buffer = now - exam_end_buffer

    future = exams.filter(examEnd__gte=time_buffer).order_by('examStart')
    for exam in future:
        checkin_window_start = exam.examStart - checkin_window #CAN CHECK IN x MINS BEFORE
        exam.can_checkin = checkin_window_start <= now <= exam.examEnd + exam_end_buffer
        exam.has_started = exam.examStart <= now
        exam.has_ended = exam.examEnd <= now
    

    
    past = exams.filter(examEnd__lt=time_buffer).order_by('-examEnd')
    return future, past

# Generate CSV HTTP response from check-in data
def generate_exam_csv(exam, checkins, download=True):
    response = HttpResponse(content_type="text/csv")
    disposition = "attachment" if download else "inline"
    response["Content-Disposition"] = f'{disposition}; filename="exam_report_{exam.pk}.csv"'

    writer = csv.writer(response)
    writer.writerow(["First Name", "Last Name","Student ID", "Exam Name", "Check-In Time", "Check-Out Time", "Is Late"])
    
    for checkin in checkins:
        writer.writerow([
            checkin.student.fname,
            checkin.student.lname,
            checkin.student.UID,
            exam.examName,
            checkin.checkin.strftime("%Y-%m-%d %H:%M:%S"),
            checkin.checkout.strftime("%Y-%m-%d %H:%M:%S") if checkin.checkout else "N/A",
            "Yes" if checkin.isLate else "No"
        ])

    return response

def view_exam_report(request, exam_id):
    exam = get_exam(exam_id)
    checkins = Checkins.objects.filter(examid=exam)
    return render(request, "exam-report.html", {
        "exam": exam,
        "checkins": checkins
    })

# --------------------------------------------
# Views
# --------------------------------------------

# Displays all exams for a given course (separates past and future)
def examPage(request, course_id):
    course = get_course(course_id)
    future_exams, past_exams = get_exams_split(course)
    # student_courses = StudentCourses.objects.filter(course=course).select_related("student")
    # students = [sc.student for sc in student_courses]  # Extract student objects

    return render(request, "exam-page.html", {
        "enrolled_display":False,
        "course_display":True,
        "course_tas_url": f"/course-tas/{course.id}/",
        "course": course,
        "future_exams": future_exams,
        "past_exams": past_exams,
        "students_url": f"/students/{course.id}/",
        "exams_url": f"/exams/{course.id}/",
        "current_url": f"/exams/{course.id}/"
    })

# Generates a downloadable CSV report for a specific exam
def generate_exam_report(request, exam_id):
    exam = get_exam(exam_id)
    checkins = Checkins.objects.filter(examid=exam)
    download = "download" in request.GET
    return generate_exam_csv(exam, checkins, download)

# Handles POST request to add a new exam
def addExam(request, course_id):
    if request.method == "POST":
        course = get_course(course_id)
        name = request.POST.get("exam_name", "").strip()
        start = parse_datetime(request.POST.get("exam_start", "").strip())
        end = parse_datetime(request.POST.get("exam_end", "").strip())

        # Validation
        if not name or not start or not end:
            messages.error(request, "All fields are required.")
        elif start >= end:
            messages.error(request, "Start time must be before end time.")
        else:
            try:
                Exams.objects.create(
                    course=course,
                    examName=name,
                    examStart=start,
                    examEnd=end
                )
                messages.success(request, f"Exam '{name}' added.")
            except Exception as e:
                messages.error(request, f"Error creating exam: {str(e)}")

        return redirect("examPage", course_id=course_id)

    return HttpResponseNotAllowed(["POST"])

# Handles POST request to delete an exam by ID
def deleteExam(request, exam_id):
    if request.method == "POST":
        try:
            exam = get_exam(exam_id)
            course_id = exam.course.id
            exam.delete()
            messages.success(request, "Exam deleted.")
            return redirect("examPage", course_id=course_id)
        except Exams.DoesNotExist:
            messages.error(request, "Exam not found.")
            return redirect("coursePage") 
    return HttpResponseNotAllowed(["POST"])










