from django.http import HttpResponse
from django.shortcuts import render
# from .models import *

def homePage(request):
     return render(request, 'home-page.html', {"enrolled_display":False,"course_display":False})