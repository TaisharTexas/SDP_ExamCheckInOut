from django.db import models
from datetime import datetime
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
"""
When model is made/modified: python manage.py makemigrations
then run to update DB: python manage.py migrate

to manually add entries to the DB for testing: python manage.py shell
"""

# Create your models here.
def get_default_user():
    return Users.objects.first()  # Assign the first user as the default
class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)  # hashes the password
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class Users(AbstractBaseUser):
    userId = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255) 
    role = models.CharField(max_length=10, choices=[('professor', 'Professor'), ('TA', 'TA')])
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name','role']

    def get_full_name(self):
        return self.first_name+" "+self.last_name

    def get_short_name(self):
        return self.name
    
class Students(models.Model):
    email = models.EmailField(max_length=100) 
    UID = models.CharField(max_length=7, primary_key=True)
    fname = models.CharField(max_length=70)
    lname = models.CharField(max_length=70)
    cardnum = models.CharField(max_length=10, unique=True, null=True, blank=True)

class Courses(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE,default=get_default_user)
    tas = models.ManyToManyField(Users, related_name="ta_courses", blank=True)  # TAs
    id = models.AutoField(primary_key=True)  # No default needed
    courseid = models.CharField(max_length=10)
    name = models.CharField(max_length=100)
    sectionid = models.CharField(max_length=50, default="A1")
    semester = models.CharField(max_length=10, default="Fall")
    year = models.IntegerField(default=datetime.now().year)    

    class Meta:
        unique_together = [
            ("name", "courseid", "sectionid", "semester", "year")
        ]

class StudentCourses(models.Model):
    id = models.AutoField(primary_key=True)  
    student = models.ForeignKey(Students, on_delete=models.CASCADE)
    course = models.ForeignKey(Courses, on_delete=models.CASCADE)
    section_id = models.CharField(max_length=10)
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("student", "course", "section_id")  # Prevent duplicate enrollments

class Exams(models.Model):
    examid = models.AutoField(primary_key=True) 
    course = models.ForeignKey(Courses, on_delete=models.CASCADE)
    sectionid = models.CharField(max_length=10) 
    examName = models.CharField(max_length=100)
    examStart = models.DateTimeField()
    examEnd = models.DateTimeField()

class Checkins(models.Model):
    id = models.AutoField(primary_key=True)
    student = models.ForeignKey(Students, on_delete=models.CASCADE)
    examid = models.ForeignKey(Exams, on_delete=models.CASCADE)
    checkin = models.DateTimeField()
    checkout = models.DateTimeField(null=True, blank=True)
    isLate = models.BooleanField(default=False)

class TACourses(models.Model):
    professor = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='professor')
    ta = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='ta')
    course = models.ForeignKey(Courses, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('ta', 'course')  # A TA can only be assigned to a course once

