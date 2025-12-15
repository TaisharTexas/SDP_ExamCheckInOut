# SDP25 Swift Check-in App

FOR DOCKER: https://www.youtube.com/watch?v=0eoFwpqBWSQ&list=PLE2ylUlNTZkWjX2IzkhgIkjmHq-MZ3dKs&index=80&t=1213s
- docker build -t sdp_exam .
(sdp_exam is the name...can change to be something else)

SEE EXISTING DOCKER CONTAINERS:
docker ps -A

EXPORT TO .tar FILE:
docker export 779c3899bc0b > sdp_exam.tar

turn on venv with: source venv/bin/activate

A Django-based exam check-in system for professors and TAs to manage courses, students, exams, and on-site check-ins.

## Features

- **User management**: sign-up (with email verification), login, password reset, profile editing  
- **Roles**: Professor vs. TA  
- **Course & Exam CRUD**: create, view, edit, delete courses and exams  
- **Student import & management** (CSV), “Your Students” view for professors  
- **Check-in workflow** with AJAX and real-time feedback  
- **Tailwind CSS** for modern, responsive UI  

---

## Prerequisites

- Python 3.10+  
- Node.js & npm (for Tailwind)  
- MySQL (or another Django-supported database)  
- (Optional) SSH access for remote DB tunneling  

## Testing Instructions

    To run all test cases:
    cd LoggingProject
    python manage.py test


## Install tailwind (how i set up tailwind in case it isn't all included)
    (assumed npm and node are installed)
    python manage.py tailwind install
    python manage.py tailwind start

## To run app:
    python manage.py tailwind start
    ssh -L 3307:127.0.0.1:3306 passthrough@98.84.13.90
    SwiftCheckin4SDP!
    python manage.py runserver