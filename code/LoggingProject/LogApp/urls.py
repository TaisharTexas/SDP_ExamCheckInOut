from django.urls import path
from .courseview import coursePage, addCourse, deleteCourse, editCourse
from .examview import examPage, generate_exam_report, addExam, deleteExam, view_exam_report
from .checkinview import checkinPage
from .studentview import studentPage, import_students
from .homeview import homePage
from .tableview import tableReport
from .enrolledstudentsview import enrolledStudents
from .coursetasview import CourseTAs, removeTA
from .activationview import activate
from .loginview import loginPage
from .registerview import registerPage
from .studentview import remove_student, add_student, remove_all_students, edit_student, resolve_import_conflicts
from .logoutview import logoutUser
from .assignTAview import assign_ta_to_course
from .profileview import profilePage
from .profileview import profilePage
# from .examreportview import view_exam_report
from django.contrib.auth import views as auth_views

urlpatterns = [
    #activation 
    path('activate/<uidb64>/<token>/', activate, name='activate'),

    #register page
    path('logout/', logoutUser, name = 'logout'),
    path('register/', registerPage, name="registerPage"),

    # Home Page
    path('accounts/login/', loginPage, name="loginPage"),
    path('', loginPage, name="loginPage"),

    # Courses
    path('courses/', coursePage, name="coursePage"),
    path('courses/add/', addCourse, name='addCourse'),
    path('courses/delete/<int:course_id>/', deleteCourse, name="deleteCourse"),
    path("courses/edit/", editCourse, name="editCourse"),

    # urls.py
    path("assign-ta/", assign_ta_to_course, name="assignTA"),

    #Profile
    path('profile/', profilePage, name='profilePage'),


    # Exams (linked to specific courses)
    path('exams/<int:course_id>/', examPage, name="examPage"),
    path("report/<int:exam_id>/", generate_exam_report, name="generate_exam_report"),
    path('exams/add/<int:course_id>/', addExam, name='addExam'),
    path('exams/delete/<int:exam_id>/', deleteExam, name='deleteExam'),
    path("exam/report/view/<int:exam_id>/", view_exam_report, name="view_exam_report"),

    # Students (linked to specific courses)
    path('enrolled-students/', enrolledStudents, name="enrolled-students"),
    path('students/<int:course_id>/', studentPage, name="studentPage"),
    path('students/import/<int:course_id>/', import_students, name="import_students"),
    path('students/remove/<int:course_id>/<str:student_id>/', remove_student, name='remove_student'),
    path('students/remove/<int:course_id>/', remove_all_students, name='remove_all_students'), #!
    path('students/add/<int:course_id>/', add_student, name='add_student'),
    path('students/edit/<int:course_id>/<str:student_id>/', edit_student, name='edit_student'),
    path('resolve-conflicts/', resolve_import_conflicts, name='resolve_conflicts'),    
    
    # Course TAs (linked to specific courses)
    path('course-tas/<int:course_id>/', CourseTAs, name="course-tas"),
    path('course-tas/remove/<int:course_id>/<int:ta_user_id>/', removeTA, name='removeTA'),

    # Check-in
    path('check-in/<int:exam_id>/', checkinPage, name="checkinPage"),

    # Reports
    path('table/', tableReport, name="tableReport"),

    # Password reset (forgot password) flow:
    path(
        'password-reset/',
        auth_views.PasswordResetView.as_view(
            template_name='password_reset_form.html',
            email_template_name='password_reset_email.html',
            subject_template_name='password_reset_subject.txt',
            success_url='/password-reset/done/'
        ),
        name='password_reset'
    ),
    path(
        'password-reset/done/',
        auth_views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'),
        name='password_reset_done'
    ),
    path(
        'reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='password_reset_confirm.html',
            success_url='/password-reset/complete/'
        ),
        name='password_reset_confirm'
    ),
    path(
        'password-reset/complete/',
        auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'),
        name='password_reset_complete'
    ),
]