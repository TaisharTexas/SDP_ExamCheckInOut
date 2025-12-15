from django.shortcuts import render, get_object_or_404, redirect
from .models import Courses, Users

def removeTA(request, course_id, ta_user_id):
    if request.method == "POST":
        # Get the TA and course based on the provided user ID and course ID
        ta = get_object_or_404(Users, userId=ta_user_id)
        course = get_object_or_404(Courses, id=course_id)

        # Remove the TA from the course's TAs
        course.tas.remove(ta)

        # Redirect back to the course's TAs page
        return redirect('course-tas', course_id=course.id)

def CourseTAs(request, course_id):
    # Get the specific course
    course = get_object_or_404(Courses, id=course_id)

    # All TAs in the system
    all_tas = Users.objects.filter(role="TA")  # Adjust role field name if needed

    # TAs assigned to this course
    assigned_tas = course.tas.all()

    # TA dict for assigned TAs
    ta_dict = {
        ta.userId: {
            'ta': ta,
            'courses': [course.name]
        }
        for ta in assigned_tas
    }

    # Unassigned TAs: all_tas minus assigned_tas
    unassigned_tas = all_tas.exclude(userId__in=[ta.userId for ta in assigned_tas])

    context = {
        'tas': list(ta_dict.values()),
        'course': course,
        'all_tas': unassigned_tas,
        "enrolled_display": False,
        "course_display": True,
        "students_url": f"/students/{course.id}/",
        "exams_url": f"/exams/{course.id}/",
        "current_url": f"/course-tas/{course.id}/",
        "course_tas_url": f"/course-tas/{course.id}/",
    }

    return render(request, 'course-tas-page.html', context)
