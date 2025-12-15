from django.http import HttpResponse
from django.shortcuts import render
from .models import *

""" NO LONGER USING THIS FILE...USING SEPARATE VIEW FILES FOR EACH PAGE"""

# def homePage(request):
#      return render(request, 'home-page.html')

# def checkinPage(request):
#     return render(request, 'check-in-page.html')

# def studentPage(request):
#      students = Students.objects.all()

#      return render(request, 'students-page.html')

#def examPage(request):
     #return render(request, 'exam-page.html')

# def tableReport(request):
#     students = Students.objects.all()
#     courses = Courses.objects.all()
#     users = Users.objects.all()
#     exams = Exams.objects.all()

#     return render(request, 'table-page.html', {
#         'students': students,
#         'courses': courses,
#         'users': users,
#         'exams': exams
#     })