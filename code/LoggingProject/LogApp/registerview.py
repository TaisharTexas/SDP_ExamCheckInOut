from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.hashers import make_password
from .models import *
from .forms import createUserForm
from .models import Users

def activateEmail(request, user, to_email):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    activation_link = f"http://127.0.0.1:8000/activate/{uid}/{token}/"
    subject = 'Activate your account'
    message = f'Hi {user.first_name}, please click the following link to activate your account:\n{activation_link}'
    send_mail(
        subject,
        message,
        'LogAppSDP@email.com',  # FROM email address
        [to_email],        # TO email address list
        fail_silently=False,
    )
    messages.success(request, 'Dear user, please go to your email ' + str(to_email) + ', check your inbox AND your junk folder. Click on the activation link to complete registration')
    
    

def registerPage(request):
    form = createUserForm()

    if request.method == 'POST':
        form = createUserForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            if Users.objects.filter(email=email).exists():
                messages.error(request, 'Email is already registered.')
            else:
                user = form.save(commit=False)  # UserCreationForm will hash for you
                user.is_active = False
                user.save()
                activateEmail(request, user, email)
                #messages.success(request, 'Account created successfully!')
                return redirect('/')
        else:
            # Add the form validation errors as messages
            for field in form.errors:
                for error in form.errors[field]:
                    messages.error(request, error) 
    context = {'form':form}
    return render(request, 'register.html',context)