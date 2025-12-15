import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib import messages
from .models import Students, Courses, StudentCourses
import re
from django.views.decorators.csrf import csrf_exempt

# View to add a new student
def add_student(request, course_id):
    course = get_object_or_404(Courses, pk=course_id)

    if request.method == "POST":
        student_id = request.POST.get("student_id", "").strip()
        student_fname = request.POST.get("student_fname", "").strip()
        student_lname = request.POST.get("student_lname", "").strip()
        confirm_choice = request.POST.get("confirm_name_choice")

        # Validate student ID: must be exactly 7 digits
        if not re.fullmatch(r"\d{7}", student_id):
            messages.error(request, "Student ID must be exactly 7 digits.")
            return redirect("studentPage", course_id=course.id)

        try:
            conflict_response = handle_name_conflict(request, student_id, student_fname, student_lname, course)
            if conflict_response:
                return conflict_response
            existing_student = Students.objects.filter(UID=student_id).first()
            # check if student ID exists in DB and if the name in the DB matches the given name (if theres a mismatch, ask user to confirm which one to use)
            if existing_student:    
                if confirm_choice == "use_new":
                    existing_student.fname = student_fname
                    existing_student.lname = student_lname
                    existing_student.save()
                elif confirm_choice == "keep_existing":
                    student_fname = existing_student.fname
                    student_lname = existing_student.lname

                student = existing_student
            else:
                # Student does not exist, create new
                student = Students.objects.create(
                    UID=student_id,
                    fname=student_fname,
                    lname=student_lname,
                    email=f"{student_id}@example.com"
                )
            # Check if this student ID is already enrolled in this specific course section
            existing_enrollment = StudentCourses.objects.filter(
                course=course,
                section_id=course.sectionid,
                student__UID=student_id
            ).select_related("student").first()

            if existing_enrollment:
                messages.info(request, f"Student {student.fname} {student.lname} is already enrolled.")
            else:
                StudentCourses.objects.get_or_create(
                    student=student,
                    course=course,
                    section_id=course.sectionid
                )
                messages.success(request, f"Student {student.fname} {student.lname} enrolled successfully!")
            
        except Exception as e:
            messages.error(request, f"Error adding student: {e}")

    return redirect("studentPage", course_id=course.id)

def remove_student(request, course_id, student_id):
    course = get_object_or_404(Courses, pk=course_id)
    student = get_object_or_404(Students, UID=student_id)

    # Delete the student-course relation
    try:
        student_course = StudentCourses.objects.get(student=student, course=course)
        student_course.delete()
        messages.success(request, f"Student {student.fname} {student.lname} removed successfully.")
    except StudentCourses.DoesNotExist:
        messages.error(request, f"Student {student.fname} {student.lname} is not enrolled in this course.")

    return redirect("studentPage", course_id=course.id)

def edit_student(request, course_id, student_id):
    course = get_object_or_404(Courses, pk=course_id)
    student = get_object_or_404(Students, UID=student_id)
    
    if request.method == 'POST':
        
        student.fname = request.POST.get('student_first_name', '').strip()
        student.lname = request.POST.get('student_last_name', '').strip()
        student.save()
        messages.success(request, 'Student updated successfully.')
        return redirect("studentPage", course_id=course.id)
    
    return redirect("studentPage", course_id=course.id)

def handle_name_conflict(request, student_id, student_fname, student_lname, course):
    existing_student = Students.objects.filter(UID=student_id).first()

    if existing_student:
        if (existing_student.fname != student_fname or existing_student.lname != student_lname):
            # Only trigger conflict if user hasn’t already confirmed their choice
            if not request.POST.get("confirm_name_choice"):
                # Fetch all current students for the course to populate the page as usual
                student_courses = StudentCourses.objects.filter(course=course).select_related("student")
                students = [sc.student for sc in student_courses]

                return render(request, "students-page.html", {
                    "incoming_name_conflict": {
                        "student_id": student_id,
                        "incoming_fname": student_fname,
                        "incoming_lname": student_lname,
                        "db_fname": existing_student.fname,
                        "db_lname": existing_student.lname
                    },
                    "course": course,
                    "students": students,
                    "students_count": len(students),
                    "enrolled_display": False,
                    "course_display": True,
                    "students_url": f"/students/{course.id}/",
                    "exams_url": f"/exams/{course.id}/",
                    "current_url": f"/students/{course.id}/",
                })

    return None

def remove_all_students(request, course_id):
    course = get_object_or_404(Courses, pk=course_id)

    # Delete the student-course relation
    try:
        student_courses = StudentCourses.objects.filter(course=course)
        
        count = len(student_courses)
        
        if count > 0:
            # Delete all the relationships
            student_courses.delete()
            messages.success(request, f"All {count} students removed successfully from {course.name}.")
        else:
            messages.info(request, f"No students were enrolled in {course.name}.")
    except Exception as e:
        messages.error(request, f"Error: {str(e)}")

    return redirect("studentPage", course_id=course.id)

# Helper function to get the course
def get_course(course_id):
    return get_object_or_404(Courses, pk=course_id)

# Helper function to process the CSV file
def process_csv_file(csv_file):
    decoded_file = csv_file.read().decode("utf-8").splitlines()
    return csv.reader(decoded_file)

# Helper function to process each row in the CSV
import re

# Helper function to process each row in the CSV
def process_student_row(row):
    try:
        # Ensure row is not empty
        if not row or len(row) < 2:  # Make sure there are at least two columns (ID and Name)
            raise ValueError("Missing or invalid student ID or name")
        
        # Student ID
        student_id = row[0].strip()
        
        # Student Name: Check if it's in 'lastname, firstname' format
        full_name = row[1].strip()
        if ',' in full_name:
            # Split by the comma (',') to separate last and first name
            student_lname, student_fname = [name.strip() for name in full_name.split(',', 1)]
        else:
            raise ValueError(f"Invalid name format in row: {row}, expected 'lastname, firstname'")

        # Validate the student ID format (must be exactly 7 digits)
        if not re.fullmatch(r"\d{7}", student_id):
            raise ValueError(f"Invalid student ID: {student_id}")

        # Check if the student already exists
        existing_student = Students.objects.filter(UID=student_id).first()
        if existing_student:
            if existing_student.fname != student_fname or existing_student.lname != student_lname:
                # Don't error, return a conflict
                return None, {
                    "student_id": student_id,
                    "db_fname": existing_student.fname,
                    "db_lname": existing_student.lname,
                    "incoming_fname": student_fname,
                    "incoming_lname": student_lname
                }
            return existing_student, None
        else:
            student = Students.objects.create(
                UID=student_id,
                fname=student_fname,
                lname=student_lname,
                email=f"{student_id}@example.com"
            )
            return student, None

    except Exception as e:
        return None, str(e)



# Helper function to enroll the student in the course
def enroll_student_in_course(student, course):
    try:
        StudentCourses.objects.get_or_create(
            student=student,
            course=course,
            section_id=course.sectionid
        )
    except Exception as e:
        return str(e)
    return None

# Main view to show students enrolled in the course
def studentPage(request, course_id):
    course = get_course(course_id)
    student_courses = StudentCourses.objects.filter(course=course).select_related("student")
    students = [sc.student for sc in student_courses]  # Extract student objects

    
    return render(request, "students-page.html", {
        "enrolled_display":False,
        "course_display":True, 
        "course": course, 
        "students": students,
        "students_count": len(students),
        "students_url": f"/students/{course.id}/",
        "exams_url": f"/exams/{course.id}/",
        "current_url": f"/students/{course.id}/",
        "course_tas_url": f"/course-tas/{course.id}/",
    })

# Main function to import students
def import_students(request, course_id):
    if request.method == "POST" and request.FILES.get("csv_file"):
        course = get_course(course_id)
        csv_file = request.FILES["csv_file"]

        # Ensure it's a CSV file
        if not csv_file.name.endswith(".csv"):
            messages.error(request, "Invalid file type. Please upload a CSV file.")
            return redirect("studentPage", course_id=course.id)

        reader = process_csv_file(csv_file)
        next(reader, None)  # Skip header row if exists

        conflicts = []
        successes = 0

        for row in reader:
            # Skip empty or whitespace-only rows
            if not row or all(not cell.strip() for cell in row):
                continue
            
            student, result = process_student_row(row)
            if student:
                # Enroll student in course if not already enrolled
                enrollment_error = enroll_student_in_course(student, course)
                if enrollment_error:
                    messages.error(request, f"Error enrolling student {student.UID}: {enrollment_error}")
                else:
                    successes += 1
            elif isinstance(result, dict):
                # name conflict
                result["course_id"] = course.id
                conflicts.append(result)
            else:
                messages.error(request, f"Error processing row {row}: {result}")

        if conflicts:
            return render(request, "resolve_conflicts.html", {
                "conflicts": conflicts,
                "course": course
            })
        messages.success(request, "Students imported and enrolled successfully!")
        return redirect("studentPage", course_id=course.id)

    return HttpResponse("Invalid request", status=400)

@csrf_exempt
def resolve_import_conflicts(request):
    if request.method == "POST":
        course_id = request.POST.get("course_id")
        course = get_object_or_404(Courses, pk=course_id)

        for key in request.POST:
            if key.startswith("conflict_"):
                student_id = key.replace("conflict_", "")
                action = request.POST.get(key)
                fname = request.POST.get(f"fname_{student_id}").strip()
                lname = request.POST.get(f"lname_{student_id}").strip()

                student = Students.objects.filter(UID=student_id).first()
                if not student:
                    # Create if not found (shouldn’t happen unless DB changed)
                    student = Students.objects.create(
                        UID=student_id,
                        fname=fname,
                        lname=lname,
                        email=f"{student_id}@example.com"
                    )
                elif action == "use_new":
                    student.fname = fname
                    student.lname = lname
                    student.save()

                try:
                    StudentCourses.objects.get_or_create(
                        student=student,
                        course=course,
                        section_id=course.sectionid
                    )
                except Exception as e:
                    messages.error(request, f"Could not enroll {student.UID}: {str(e)}")

        messages.success(request, "All conflicts resolved and students enrolled successfully!")
        return redirect("studentPage", course_id=course.id)

    return HttpResponse("Invalid request", status=400)