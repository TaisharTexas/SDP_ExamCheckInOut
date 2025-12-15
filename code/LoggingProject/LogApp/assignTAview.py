from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect
from django.http import HttpResponseNotAllowed
from .models import Courses
from django.contrib import messages
from datetime import datetime
from django.db.models import Q  
User = get_user_model()

def assign_ta_to_course(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    course_id = request.POST.get("course_id")
    ta_email = request.POST.get("ta_email").strip().lower()

    try:
        course = Courses.objects.get(id=course_id, user=request.user)
        ta_user = User.objects.get(email=ta_email)

        if ta_user.role != "TA":
            messages.error(request, f"User {ta_email} does not have the role 'TA.'")
            return redirect("course-tas", course_id=course.id)
        
        if course.tas.filter(userId=ta_user.userId).exists():
            messages.error(request, f"User {ta_email} is already registered as a TA for this course.")
            return redirect("course-tas", course_id=course.id)

        course.tas.add(ta_user)
        course.save()

        messages.success(request, f"TA {ta_email} assigned to course {course.name}.")
    except User.DoesNotExist:
        messages.error(request, "No registered user found with that email.")
    except Exception as e:
        messages.error(request, f"Error: {str(e)}")

    return redirect("course-tas", course_id=course.id)
