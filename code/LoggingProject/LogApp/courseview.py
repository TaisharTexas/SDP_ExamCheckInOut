from django.shortcuts import render, redirect
from django.http import HttpResponseNotAllowed
from .models import Courses
from django.contrib import messages
from datetime import datetime
from django.db.models import Q  
# Retrieves all courses from the database
def GetCourses():
    return list(Courses.objects.all())

# Creates and saves a new course in the database
def createCourse(user, course_id, name, section_id, semester, year):
    return Courses.objects.create(user = user,courseid=course_id, name=name, sectionid=section_id, semester = semester, year = year)


# Renders the course page with a list of all available courses
def coursePage(request):
    

   
    if request.user.is_authenticated:
        print(f"User is logged in as: {request.user.email}")
    else:
        print("No user is logged in")
    courses = Courses.objects.filter(
        Q(user=request.user) | Q(tas=request.user)
    ).distinct().order_by("name")

    return render(request, "course-page.html", {
        "enrolled_display":True,
        "course_display":False, 
        "courses": courses
    })

# Handles POST form submission to add a new course
def addCourse(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    # --- Cleaned Input ---
    section_id = request.POST.get("section_id", "").strip()
    course_id = request.POST.get("course_id", "").strip()
    name = request.POST.get("course_name", "").strip()
    semester = request.POST.get("semester", "").strip()
    year = request.POST.get("year", "").strip()

    # --- Basic Validation ---
    if not all([course_id, name, section_id, semester, year]):
        messages.error(request, "All fields are required.")
        return redirect("coursePage")

    if not course_id.isalnum():
        messages.error(request, "Course ID must be alphanumeric.")
        return redirect("coursePage")

    if not section_id.replace("-", "").isalnum():
        messages.error(request, "Section ID must be alphanumeric.")
        return redirect("coursePage")

    try:
        year = int(year)
    except ValueError:
        messages.error(request, "Year must be a valid number.")
        return redirect("coursePage")

    # --- Duplicate Check ---
    if Courses.objects.filter(
        courseid=course_id,
        sectionid=section_id,
        name=name,
        semester=semester,
        year=year
    ).exists():
        messages.error(request, "This course already exists.")
        return redirect("coursePage")

    # --- Create ---
    try:
        createCourse(request.user, course_id, name, section_id, semester, year)
        messages.success(request, f"Course '{name}' added successfully.")
    except Exception as e:
        messages.error(request, f"Error: {str(e)}")

    return redirect("coursePage")

# Deletes Course
def deleteCourse(request, course_id):
    if request.method == "POST":
        try:
            course = Courses.objects.get(id=course_id, user=request.user)
            course.delete()
            messages.success(request, f"Course '{course.name}' deleted successfully.")
        except Courses.DoesNotExist:
            messages.error(request, "Course not found.")
        except Exception as e:
            messages.error(request, f"Error deleting course: {str(e)}")
        return redirect("coursePage")

    return HttpResponseNotAllowed(["POST"])

def editCourse(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    course_id = request.POST.get("course_id", "").strip()
    new_name = request.POST.get("course_name", "").strip()
    new_course_id = request.POST.get("course_code", "").strip()
    new_section = request.POST.get("section_id", "").strip()
    new_semester = request.POST.get("semester", "").strip()
    new_year = request.POST.get("year", "").strip()

    # --- Basic Validation ---
    if not all([course_id, new_name, new_course_id, new_section, new_semester, new_year]):
        messages.error(request, "All fields are required.")
        return redirect("coursePage")

    if not new_course_id.isalnum():
        messages.error(request, "Course ID must be alphanumeric.")
        return redirect("coursePage")

    if not new_section.replace("-", "").isalnum():
        messages.error(request, "Section ID must be alphanumeric.")
        return redirect("coursePage")

    try:
        new_year = int(new_year)
    except ValueError:
        messages.error(request, "Year must be a valid number.")
        return redirect("coursePage")

    try:
        course = Courses.objects.get(id=course_id, user=request.user)

        # --- Duplicate Check ---
        if Courses.objects.exclude(id=course_id).filter(
            name=new_name,
            courseid=new_course_id,
            sectionid=new_section,
            semester=new_semester,
            year=new_year
        ).exists():
            messages.error(request, "Another course with this exact information already exists.")
            return redirect("coursePage")

        # --- Update Fields ---
        course.name = new_name
        course.courseid = new_course_id
        course.sectionid = new_section
        course.semester = new_semester
        course.year = new_year
        course.save()

        messages.success(request, f"Course '{new_name}' updated successfully.")

    except Courses.DoesNotExist:
        messages.error(request, "Course not found.")
    except Exception as e:
        messages.error(request, f"Error updating course: {str(e)}")

    return redirect("coursePage")








