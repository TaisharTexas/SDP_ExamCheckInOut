from django.shortcuts import render, redirect
from .models import *

def tableReport(request):
    students = Students.objects.all()
    courses = Courses.objects.all()
    users = Users.objects.all()
    exams = Exams.objects.all()

    return render(request, 'table-page.html', {
        'students': students,
        'courses': courses,
        'users': users,
        'exams': exams
    })