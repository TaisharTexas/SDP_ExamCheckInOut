"""
URL configuration for LoggingProject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Home & Authentication
    path('', include("LogApp.urls")),
    #path('signin/', include("LogApp.urls")),

    # Include all LogApp URLs for better organization
    path('register/', include("LogApp.urls")),
    path('courses/', include("LogApp.urls")),
    path('check-in/', include("LogApp.urls")),
    path('students/', include("LogApp.urls")),
    path('enrolled-students/', include("LogApp.urls")),
    path('course-tas/', include("LogApp.urls")),
    path('table/', include("LogApp.urls")),
    path('profile/', include("LogApp.urls")),
    #path('login/', include("LogApp.urls")),

    # Tailwind css auto reload
    # path('tailwind-testing/', include("LogApp.urls")),
    path("__reload__/", include("django_browser_reload.urls")),
]
