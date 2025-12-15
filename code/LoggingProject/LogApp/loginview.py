from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import check_password
from .models import Users
from .decorators import logged_in
from django.contrib.auth import login 

@logged_in
def loginPage(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            user = Users.objects.get(email=email)
            if not user.is_active:
                messages.error(request, 'Account not activated. Please check your email.')
                return render(request, 'login-page.html', {"enrolled_display": False, "course_display": False})
            if check_password(password, user.password):
                login(request, user)
                return redirect('/courses')

            else:
                messages.error(request, 'Incorrect password.')
        except Users.DoesNotExist:
            messages.error(request, 'User not found.')

    return render(request, 'login-page.html', {"enrolled_display": False, "course_display": False})