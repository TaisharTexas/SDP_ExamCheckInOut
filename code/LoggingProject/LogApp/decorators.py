from django.http import HttpResponse
from django.shortcuts import redirect

def logged_in(view_func):
    def wrapper_func(request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('/courses')
        else:
            return view_func(request, *args, **kwargs)
        
    return wrapper_func

#Not functioning currently, just based on the video tutorial