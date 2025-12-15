from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib import messages
from .models import Students, Courses, StudentCourses
from django.db.models import Q

def get_student_info(student_uid, courses):
    try:
        student = Students.objects.get(UID=student_uid)
        enrolled_courses = StudentCourses.objects.filter(
            student=student,
            course__in=courses
            ).select_related('course')

        if enrolled_courses.exists():
            courses = [f"{enroll.course.name} ({enroll.course.courseid})" for enroll in enrolled_courses]
        else:
            courses = ["Not enrolled in any course"]

        return {
            "UID": student.UID,
            "name": f"{student.fname} {student.lname}",
            "student": student,
            "courses": courses
        }

    except Students.DoesNotExist:
        return {
            "error": f"Student with UID '{student_uid}' not found."
        }

def enrolledStudents(request):
    all_students = Students.objects.all()

        # Get the courses assigned to this user (professor or TA)
    courses = Courses.objects.filter(
        Q(user=request.user) | Q(tas=request.user)
    ).distinct()

    # Get the student-course enrollments for these courses
    enrolled_student_ids = StudentCourses.objects.filter(
        course__in=courses
    ).values_list('student_id', flat=True).distinct()

    # Get only the students enrolled in the user's courses
    students = Students.objects.filter(UID__in=enrolled_student_ids)
    
    student_info_list = [get_student_info(student.UID, courses) for student in students]

    return render(request, "enrolled-students-page.html", {
        "enrolled_display": True,
        "course_display": True,
        "students": student_info_list,
        "students_count": len(student_info_list),
        "current_url": '/enrolled-students/',
    })