from django.shortcuts import get_object_or_404, render
from django.utils.timezone import now
from django.utils import timezone
from .models import Students, Checkins, Exams, StudentCourses, Courses
from .examtimewindows import checkin_window, exam_end_buffer
from datetime import datetime, timedelta
import re

# Retrieve a student by UID, return error message if not found
def get_student(student_id):
    try:
        return Students.objects.get(UID=student_id), None
    except Students.DoesNotExist:
        return None, f"Error: No student found with ID {student_id}."

# Extract UH ID from raw input
def extract_uhid(raw_input):
    if re.fullmatch(r"\d{7}", raw_input):
        return raw_input
    match = re.search(r"%00(\d{7})\?", raw_input)
    if match:
        return match.group(1)
    match = re.search(r"\b(\d{7})\b", raw_input)
    if match:   
        return match.group(1)
    return None

# Handle the check-in logic for a student
def handle_checkin(student, exam):
    course = exam.course  # This will give you the course related to the exam
    
    # Get the course ID
    course_id = course.id

    # Check if the student is enrolled in the correct course, section, semester, and year
    enrollment_exists = StudentCourses.objects.filter(
        student=student,
        course__id=course_id,  # Filter based on the course's id
        
    ).exists()

    if not enrollment_exists:
        return f"Error: Student {student.fname} {student.lname} is not enrolled in the course {course.name}.", "error-message"
    
    existing = Checkins.objects.filter(student=student, examid=exam, checkout__isnull=True).first()
    if existing:
        return f"Student {student.fname} {student.lname} is already checked in!", "error-message"
    
    exam.has_ended = exam.examEnd <= timezone.now()

    if exam.has_ended:
        return f"Error: Exam has already ended.", "error-message"
    

    # Create a new check-in record
    Checkins.objects.create(student=student, examid=exam, checkin=now())
    return f"Student {student.fname} {student.lname} checked in successfully!", "success-message"

# Handle the check-out logic for a student
def handle_checkout(student, exam):
    # Check if the student has a current check-in for the exam
    existing = Checkins.objects.filter(student=student, examid=exam, checkout__isnull=True).first()
    if existing:
        # Update the checkout timestamp
        existing.checkout = now()
        existing.save()
        return f"Student {student.fname} {student.lname} checked out successfully!", "success-message"
    return f"Error: No check-in record found for {student.fname} {student.lname}!", "error-message"

# Main view for check-in/check-out page
def checkinPage(request, exam_id):
    # Get the exam and its related course
    exam = get_object_or_404(Exams, pk=exam_id)
    course = exam.course
    now = timezone.now()

    checkin_window_start = exam.examStart - timedelta(minutes=30) #CAN CHECK IN 30 MINS BEFORE
    checkin_window_end = exam.examEnd + timedelta(minutes=30)  # 30 minutes after end
    exam.can_checkin = checkin_window_start <= now <= checkin_window_end
    exam.has_started = exam.examStart <= now
    exam.has_ended = exam.examEnd <= now

    # Default response values
    message, message_class = "", ""
    current_mode = request.POST.get("mode", "checkin")

    if request.method == "POST":
        raw_input = request.POST.get("student_id")
        student_id = extract_uhid(raw_input)
        if student_id:
            print(student_id)
        else:
            print("no return\n")
        mode = request.POST.get("mode")
        print("\nRAW INPUT: " + raw_input + "\n")

        if not student_id:
            message = "Error: Student ID is required."
            message_class = "error-message"
        else:
            student, error = get_student(student_id)
            if error:
                message = error
                message_class = "error-message"
            else:
                if mode == "checkin":
                    message, message_class = handle_checkin(student, exam)
                elif mode == "checkout":
                    message, message_class = handle_checkout(student, exam)

    # Renders the page
    return render(request, "check-in-page.html", {
        "enrolled_display":True,
        "course_display":True,
        "exam": exam,
        "course": course,
        "message": message,
        "message_class": message_class,
        "mode": current_mode,
        "timestamp": datetime.now().timestamp(),
        "students_url": f"/students/{course.id}/",
        "exams_url": f"/exams/{course.id}/"
    })
