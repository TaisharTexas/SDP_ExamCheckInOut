from django.test import TestCase, Client, RequestFactory
from django.urls import reverse
from django.utils.timezone import now
from .models import *
from .courseview import *
from django.contrib.messages import get_messages
from datetime import datetime
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.hashers import make_password
from LogApp.studentview import handle_name_conflict, process_student_row, enroll_student_in_course
from LogApp.enrolledstudentsview import get_student_info
from django.core import mail
from django.contrib.auth.hashers import make_password
from LogApp.registerview import activateEmail, registerPage
from .examtimewindows import exam_end_buffer, checkin_window 
from LogApp.examview import get_exams_split, get_exam
from unittest.mock import patch
from django.contrib.messages.storage.fallback import FallbackStorage
from django.http import Http404
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes


class CheckinPageTest(TestCase):
    def setUp(self):
        self.client = Client()

        self.test_user = Users.objects.create_user(
            email='test@example.com',
            password='testpassword',
            first_name='Test',
            last_name='User',
            role='professor'
        )

        self.client.force_login(self.test_user)

        # Create a course
        self.course = Courses.objects.create(
            id = 1,
            courseid="MATH101",
            name="Math 101",
            sectionid="A1",
            semester="Fall",
            year=2024,
            user=self.test_user
        )

        now = timezone.now() 
        # Create an exam linked to the course
        self.exam = Exams.objects.create(
            course=self.course, 
            sectionid="001", 
            examName="Midterm Exam", 
            examStart=now, 
            examEnd=now + timedelta(hours=3),
        )

        # Create a student
        self.student = Students.objects.create(
            UID="1111111",
            fname="John",
            lname="Doe",
            email="johndoe@example.com"
        )

        self.student_CheckedIn = Students.objects.create(
            UID="2222222", 
            fname = "Wayne",
            lname = "Ken",
            email="WayneKen@example.com"
        )

        self.student_course1 = StudentCourses.objects.create(
            student = self.student,
            course = self.course,
            section_id = "1234",
        )

        self.student_course2 = StudentCourses.objects.create(
            student = self.student_CheckedIn,
            course = self.course,
            section_id = "1234",
        )


        self.checkin = Checkins.objects.create(
            student = self.student_CheckedIn,
            examid = self.exam,
            checkin=timezone.make_aware(datetime(2025, 3, 15, 9, 0)),
            checkout=timezone.make_aware(datetime(2025, 3, 15, 12, 0)),
        )

        # Get the check-in URL
        self.checkin_url = reverse("checkinPage", kwargs={"exam_id": self.exam.examid})

    def test_checkin_valid_student(self):
        response = self.client.post(self.checkin_url, {"mode": "checkin", "student_id": self.student.UID})
        #print(f'Student ID: {self.student.UID}')
        self.assertEqual(Checkins.objects.count(), 2)
        self.assertTrue(Checkins.objects.filter(student=self.student, examid=self.exam, checkout__isnull=True).exists())

    def test_checkin_already_checked_in_student(self):
        # Test attempting to check in a student who is already checked in 
        response = self.client.post(self.checkin_url, {"mode": "checkin", "student_id": self.student.UID})
        response = self.client.post(self.checkin_url, {"mode": "checkin", "student_id": self.student.UID})
        self.assertContains(response, f"Student {self.student.fname} {self.student.lname} is already checked in!")

    def test_checkout_valid_student(self):
        # Test a valid student successfully checking out 
        response = self.client.post(self.checkin_url, {"mode": "checkin", "student_id": self.student.UID})
        response = self.client.post(self.checkin_url, {"mode": "checkout", "student_id": self.student.UID})
        self.assertContains(response, "checked out successfully!")
        self.assertEqual(Checkins.objects.count(), 2)
        checkin_log = Checkins.objects.filter(student=self.student, examid=self.exam).first()
        self.assertIsNotNone(checkin_log.checkin)
        self.assertIsNotNone(checkin_log.checkout)

    def test_checkout_without_checkin(self):
        # Test checking out a student who hasn't checked in 
        response = self.client.post(self.checkin_url, {"mode": "checkout", "student_id": self.student.UID})
        self.assertContains(response, f"Error: No check-in record found for {self.student.fname} {self.student.lname}!")

    def test_checkin_invalid_student(self):
        # Test attempting to check in with a non-existent student ID 
        self.assertEqual(Checkins.objects.count(), 1) # Already 1 in test DB
        response = self.client.post(self.checkin_url, {"student_id": "9999999", "mode": "checkin"})
        self.assertEqual(Checkins.objects.count(), 1) # Already 1 in test DB

    def test_checkin_missing_student_id(self):
        self.assertEqual(Checkins.objects.count(), 1) # Already 1 in test DB
        # Test attempting to check in without providing a student ID 
        response = self.client.post(self.checkin_url, {"mode": "checkin", "student_id": ""})
        self.assertEqual(Checkins.objects.count(), 1) # Already 1 in test DB

class CourseViewTest(TestCase):
    def setUp(self):
        self.client = Client()

        self.test_user = Users.objects.create_user(
            email='test@example.com',
            password='testpassword',
            first_name='Test',
            last_name='User',
            role='professor'
        )

        self.client.force_login(self.test_user)

        course1 = Courses.objects.create(
            courseid="1111", 
            name="Math 101",
            sectionid="A1", 
            semester="Fall",  
            year=datetime.now().year,
            user=self.test_user,
        )

        course2 = Courses.objects.create(
            courseid="2222",  
            name="Calculus I",
            sectionid="B2", 
            semester="Spring", 
            year=2024,
            user=self.test_user
        )

        student1 = Students.objects.create(
            email = "student1Email@gmail.com",
            UID = "10000",
            fname = "Dave",
            lname = "Wu"
        )

        student2 = Students.objects.create(
            email = "student2Email@gmail.com",
            UID = "10001",
            fname = "Pam",
            lname = "Jim"
        )

        StudentCourses.objects.create(
            student= student1,
            course = course1,
            section_id= course1.sectionid 
        )

        StudentCourses.objects.create(
            student= student2,
            course = course2,
            section_id= course2.sectionid  
        )

        self.course_data_add = {
            "course_id": "3333", 
            "course_name": "Computer Science 1", 
            "section_id": "B3",
            "semester": "Fall", 
            "year": 2024
        }

        self.course_url_add = reverse('addCourse')

    def test_getCourses(self):
        courses = GetCourses()
        self.assertEqual(len(courses), 2)
        self.assertEqual(courses[0].id, 1) 
        self.assertEqual(courses[1].id, 2) 

    def test_createCourse(self):
        createCourse(self.test_user, 'TestCourseID', 'TestCourseName', '100', 'Fall', 2024)
        courses  = GetCourses()
        self.assertEqual(len(courses), 3)
        self.assertEqual(courses[2].courseid, "TestCourseID") 
        self.assertEqual(courses[2].name, "TestCourseName") 
        self.assertEqual(courses[2].sectionid, "100") 

    def test_coursePage_loads(self):
        course_url = reverse("coursePage")
        response = self.client.get(course_url)
        self.assertEqual(response.status_code, 200)

    def test_addCourse_success(self):
        response = self.client.post(self.course_url_add, self.course_data_add)
        self.assertEqual(Courses.objects.count(), 3) # Account for the 2 already in Test Database
        self.assertEqual(Courses.objects.last().courseid, "3333")
        self.assertEqual(Courses.objects.last().name, "Computer Science 1")

    def test_addCourse_missingFields(self):
        course_data_add = {
            "section_id": "",
            "course_id": "",
            "course_name": ""
        }
        response = self.client.post(self.course_url_add, course_data_add)
        self.assertEqual(Courses.objects.count(), 2)
        self.assertRedirects(response, reverse('coursePage'))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "All fields are required.")
        
    def test_addCourse_section_alnum(self):
        self.course_data_add["section_id"] = "123-!@"
        response = self.client.post(self.course_url_add, self.course_data_add)
        self.assertRedirects(response, reverse('coursePage'))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "Section ID must be alphanumeric.")

    def test_addCourse_courseID_alnum(self):
        self.course_data_add["course_id"] = "1@#@"
        response = self.client.post(self.course_url_add, self.course_data_add)
        self.assertRedirects(response, reverse('coursePage'))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "Course ID must be alphanumeric.")

    
    def test_addCourse_year_invalid(self):
        self.course_data_add["year"] = "ten"
        response = self.client.post(self.course_url_add, self.course_data_add)
        self.assertRedirects(response, reverse('coursePage'))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "Year must be a valid number.")

    def test_addCourse_duplicate_check(self):
        Courses.objects.create(
            courseid="78", 
            name="Math 101",
            sectionid="A1", 
            semester="Fall",  
            year=datetime.now().year,
            user=self.test_user,
        )
        data = {
            "course_id": "78",
            "course_name": "Math 101",
            "course_code": "1111",
            "section_id": "A1",
            "semester": "Fall",
            "year": datetime.now().year,
        }
        response = self.client.post(self.course_url_add, data)
        self.assertRedirects(response, reverse('coursePage'))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "This course already exists.")




    def test_deleteCourse_success(self):
        course_url_delete = reverse('deleteCourse', kwargs = {'course_id': '2'})
        self.assertEqual(Courses.objects.count(), 2)
        response = self.client.post(course_url_delete)
        self.assertEqual(Courses.objects.count(), 1)
        self.assertEqual(Courses.objects.first().id, 1)

    def test_deleteCourse_notExist(self):
        course_url_delete = reverse('deleteCourse', kwargs = {'course_id': '3'})
        response = self.client.post(course_url_delete)
        self.assertRedirects(response, reverse('coursePage'))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "Course not found.")

    def test_editCourse_success(self):
        course_url_edit = reverse('editCourse')
        data = {
            "course_id": "2",
            "course_name": "Computer Science 1",
            "course_code": "2222",
            "section_id": "B3",
            "semester": "Fall",
            "year": 2026,
        }
        response = self.client.post(course_url_edit, data)
        self.assertEqual(Courses.objects.count(), 2)
        self.assertEqual(Courses.objects.last().id, 2)
        self.assertEqual(Courses.objects.last().sectionid, "B3")
        self.assertEqual(Courses.objects.last().name, "Computer Science 1")

    def test_editCourse_NotFilledOut(self):
        course_url_edit = reverse('editCourse')
        data = {
            "course_id": "",
            "course_name": "",
            "course_code": "",
            "section_id": "",
            "semester": "",
            "year": 2026,
        }
        self.assertEqual(Courses.objects.count(), 2)
        response = self.client.post(course_url_edit, data, follow = True)
        self.assertEqual(Courses.objects.count(), 2)
        self.assertContains(response, "All fields are required.")

    def test_editCourse_Course_Code_NotNNum(self):
        course_url_edit = reverse('editCourse')
        data = {
            "course_id": "2",
            "course_name": "Computer Science 1",
            "course_code": "ABC!",
            "section_id": "B3",
            "semester": "Fall",
            "year": 2026,
        }
        self.assertEqual(Courses.objects.count(), 2)
        response = self.client.post(course_url_edit, data, follow = True)
        self.assertEqual(Courses.objects.count(), 2)
        messages = list(get_messages(response.wsgi_request))
        self.assertIn("Course ID must be alphanumeric.", [m.message for m in messages])

    def test_editCourse_Section_NotNum(self):
        course_url_edit = reverse('editCourse')
        data = {
            "course_id": "2",
            "course_name": "Computer Science 1",
            "course_code": "2222",
            "section_id": "B3!",
            "semester": "Fall",
            "year": 2026,
        }
        self.assertEqual(Courses.objects.count(), 2)
        response = self.client.post(course_url_edit, data, follow = True)
        self.assertEqual(Courses.objects.count(), 2)
        messages = list(get_messages(response.wsgi_request))
        self.assertIn("Section ID must be alphanumeric.", [m.message for m in messages])

    def test_editCourse_Year_Invalid(self):
        course_url_edit = reverse('editCourse')
        data = {
            "course_id": "2",
            "course_name": "Computer Science 1",
            "course_code": "2222",
            "section_id": "B3",
            "semester": "Fall",
            "year": "Ten",
        }
        self.assertEqual(Courses.objects.count(), 2)
        response = self.client.post(course_url_edit, data, follow = True)
        self.assertEqual(Courses.objects.count(), 2)
        messages = list(get_messages(response.wsgi_request))
        self.assertIn("Year must be a valid number.", [m.message for m in messages])

    def test_editCourse_Duplicate_Check(self):
        course_url_edit = reverse('editCourse')
        data = {
            "course_id": "2",
            "course_name": "Math 101",
            "course_code": "1111",
            "section_id": "A1",
            "semester": "Fall",
            "year": datetime.now().year,
        }

        self.assertEqual(Courses.objects.count(), 2)
        response = self.client.post(course_url_edit, data, follow = True)
        self.assertEqual(Courses.objects.count(), 2)
        messages = list(get_messages(response.wsgi_request))
        self.assertIn("Another course with this exact information already exists.", [m.message for m in messages])

    def test_editCourse_unexpected_exception(self):
        with patch('LogApp.models.Courses.save', side_effect=Exception("Unexpected DB error")):
            response = self.client.post(reverse("editCourse"), {
                "course_id": '1',
                "course_name": "Updated Course",
                "course_code": "CS102",
                "section_id": "B1",
                "semester": "Spring",
                "year": 2025,
            }, follow=True)

        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Error updating course: Unexpected DB error" in m.message for m in messages))


    def test_addCourse_unexpected_exception(self):
        with patch('LogApp.models.Courses.save', side_effect=Exception("Cannot Add Course")):
            response = self.client.post(reverse("addCourse"), {
                "course_id": '5',
                "course_name": "New Course",
                "course_code": "CS102",
                "section_id": "B1",
                "semester": "Spring",
                "year": 2025,
            }, follow=True)

        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Error: Cannot Add Course" in m.message for m in messages))

    def test_deleteCourse_unexpected_exception(self):
        course_url_delete = reverse('deleteCourse', kwargs = {'course_id': '2'})
        with patch('LogApp.models.Courses.delete', side_effect=Exception("Cannot Delete Course")):
            response = self.client.post(course_url_delete)
    
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Error deleting course: Cannot Delete Course" in m.message for m in messages))
            
        

    def test_editCourse_notFound(self):
        course_url_edit = reverse('editCourse')
        data = {
            "course_id": "3",
            "course_name": "Computer Science 1",
            "course_code": "2222",
            "section_id": "B3",
            "semester": "Fall",
            "year": 2026,
        }
        response = self.client.post(course_url_edit, data)
        self.assertRedirects(response, reverse('coursePage'))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "Course not found.")
        


class ExamPageTest(TestCase):
    def setUp(self):
        self.client = Client()

        self.test_user = Users.objects.create_user(
            email='test@example.com',
            password='testpassword',
            first_name='Test',
            last_name='User',
            role='professor'
        )

        self.client.force_login(self.test_user)

        self.student = Students.objects.create(
            UID="S101",
            fname="John",
            lname="Doe",
            email="john.doe@example.com"
        )

        self.course = Courses.objects.create(
            id="1111",
            courseid="CS101",
            name="Computer Science",
            sectionid="A1",
            user = self.test_user,
        )
        
        self.exam1 = Exams.objects.create(
            examid = 1,
            course=self.course,
            examName="First Exam",
            sectionid="A1",
            examStart=timezone.make_aware(datetime(2025, 3, 15, 9, 0)),
            examEnd=timezone.make_aware(datetime(2025, 3, 15, 12, 0))
        )
        
        self.exam2 = Exams.objects.create(
            examid = 2,
            course=self.course,
            examName="Mid Exam",
            sectionid="A1",
            examStart=timezone.make_aware(datetime(2025, 4, 15, 9, 0)),
            examEnd=timezone.make_aware(datetime(2025, 4, 15, 12, 0))
        )


        self.checkin1 = Checkins.objects.create(
            student=self.student,
            examid=self.exam1,
            checkin=timezone.make_aware(datetime(2025, 3, 15, 8, 45)),
            checkout=timezone.make_aware(datetime(2025, 3, 15, 12, 0)),
            isLate=False
        )

        self.checkin2 = Checkins.objects.create(
            student=self.student,
            examid=self.exam1,
            checkin=timezone.make_aware(datetime(2025, 3, 15, 9, 10)),
            checkout=timezone.make_aware(datetime(2025, 3, 15, 12, 0)),
            isLate=True
        )


        self.exam_data_add = {
            "exam_name": "Final Exam",
            "exam_start": timezone.make_aware(datetime(2025, 5, 10, 9, 0)),
            "exam_end": timezone.make_aware(datetime(2025, 5, 10, 12, 0))
        }


        self.exam_url_add = reverse(
            'addExam', 
            kwargs={'course_id': self.course.id})
        
        self.exam_url_delete = reverse(
            'deleteExam', 
            kwargs={'exam_id': self.exam2.examid})


    def test_ExamPage_loads(self):
        exam_url = reverse('examPage', kwargs={'course_id': self.course.id})
        response = self.client.get(exam_url)
        self.assertEqual(response.status_code, 200)
        

    def test_addExam_success(self):
        response = self.client.post(self.exam_url_add, self.exam_data_add)
        self.assertEqual(Exams.objects.count(), 3) # There are 2 exams already in test DB
        self.assertEqual(Exams.objects.last().examName, self.exam_data_add["exam_name"])
        self.assertEqual(Exams.objects.last().examStart, self.exam_data_add["exam_start"])

    def test_addExam_missingFields(self):
        self.exam_data_add = {
            "exam_name": "",
            #"section_id": "",
            "exam_start": "",
            "exam_end": ""
        }
        self.assertEqual(Exams.objects.count(), 2)
        response = self.client.post(self.exam_url_add, self.exam_data_add)
        self.assertEqual(Exams.objects.count(), 2)
    
    def test_addExam_Wrong_times(self):
        self.exam_data_add = {
            "exam_name": "Final Exam",
            "exam_start": timezone.make_aware(datetime(2025, 5, 10, 12, 0)), 
            "exam_end": timezone.make_aware(datetime(2025, 5, 10, 9, 0)),
        }
        self.assertEqual(Exams.objects.count(), 2)
        response = self.client.post(self.exam_url_add, self.exam_data_add)
        self.assertEqual(Exams.objects.count(), 2)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "Start time must be before end time.")


    def test_addExam_exception(self):
        self.exam_data_add = {
            "exam_name": "Final Exam",
            "exam_start": timezone.make_aware(datetime(2025, 5, 10, 9, 0)),
            "exam_end": timezone.make_aware(datetime(2025, 5, 10, 12, 0))
        }
        self.assertEqual(Exams.objects.count(), 2)
        with patch('LogApp.models.Exams.save', side_effect=Exception("Cannot Add Exam")):
            response = self.client.post(self.exam_url_add, self.exam_data_add)
        self.assertEqual(Exams.objects.count(), 2)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "Error creating exam: Cannot Add Exam")

    def test_deleteExam_success(self):
        # Test deleting Exam2
        self.assertEqual(Exams.objects.count(), 2)
        response = self.client.post(self.exam_url_delete)
        self.assertEqual(Exams.objects.count(), 1)
        self.assertEqual(Exams.objects.first().sectionid, self.exam1.sectionid)
        self.assertEqual(Exams.objects.first().examStart, self.exam1.examStart)

    def test_deleteExam_notFound(self):
        self.assertEqual(Exams.objects.count(), 2)
        exam_url_delete_NF = reverse(
            'deleteExam', 
            kwargs={'exam_id': 3214})
        with patch('LogApp.examview.get_exam', side_effect=Exams.DoesNotExist): 
            response = self.client.post(exam_url_delete_NF, follow=True)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "Exam not found.")
        self.assertEqual(Exams.objects.count(), 2)


    def test_examReport(self):
        exam_url_report = reverse(
            "generate_exam_report",
            kwargs = {'exam_id': self.exam1.examid})
        response = self.client.post(exam_url_report)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Content-Disposition', response.headers)
        

class GetExamsSplitTest(TestCase):
    def setUp(self):
        
        self.Professor = Users.objects.create_user(
            email='test@example.com',
            password='testpassword',
            first_name='Test',
            last_name='User',
            role='professor'
        )
        
        self.course1 = Courses.objects.create(
            id=1,
            courseid="CS101",
            name="Computer Science",
            sectionid="Section1",
            semester="Fall",
            year=2025,
            user = self.Professor,
        )

        now = timezone.now()

        self.exam_before_buffer = Exams.objects.create(
            examid = 2,
            course=self.course1,
            examName="First Exam",
            sectionid= self.course1.sectionid,
            examStart=now - timedelta(days=2),
            examEnd=now - timedelta(days=1, minutes=30)
        )

        self.exam_within_buffer = Exams.objects.create(
            examid = 3,
            course=self.course1,
            examName="2nd Exam",
            sectionid= self.course1.sectionid,
            examStart=now + timedelta(minutes=10),
            examEnd=now + timedelta(hours=1),
        )     

        self.exam_ongoing_buffer = Exams.objects.create(
            examid = 4,
            course=self.course1,
            examName="2nd Exam",
            sectionid= self.course1.sectionid,
            examStart=now - timedelta(minutes=15),
            examEnd=now + timedelta(minutes=45)
        )
    
    def test_get_exams_split_logic(self):
        future_exams, _ = get_exams_split(self.course1)

        self.assertEqual(len(future_exams), 2)

        now = timezone.now()

        for exam in future_exams:
            self.assertTrue(hasattr(exam, 'can_checkin'))
            self.assertTrue(hasattr(exam, 'has_started'))
            self.assertTrue(hasattr(exam, 'has_ended'))

            checkin_start = exam.examStart - checkin_window
            self.assertEqual(exam.can_checkin, checkin_start <= now <= exam.examEnd + exam_end_buffer)
            self.assertEqual(exam.has_started, exam.examStart <= now)
            self.assertEqual(exam.has_ended, exam.examEnd <= now)

class StudentPageTest(TestCase):
    def setUp(self):
        self.client = Client()

        self.factory = RequestFactory()

        self.test_user = Users.objects.create_user(
            email='test@example.com',
            password='testpassword',
            first_name='Test',
            last_name='User',
            role='professor'
        )

        self.client.force_login(self.test_user)

        self.course1 = Courses.objects.create(
            id=1,
            courseid="CS101",
            name="Computer Science",
            sectionid="Section1",
            semester="Fall",
            year=2025,
            user = self.test_user,
        )

        self.student1 = Students.objects.create(
            UID="1111111",
            fname="John",
            lname="Doe",
            email="john.doe@example.com"
        )

        self.student2 = Students.objects.create(
            UID="2222222",
            fname="Ken",
            lname="Yi",
            email="Ken.Yi@example.com"
        )

        self.student3 = Students.objects.create(
            UID="3333333",
            fname="Bard",
            lname="Jax",
            email="Bard.Jax@example.com"
        )

        self.student4 = Students.objects.create(
            UID="4444444",
            fname="Zoe",
            lname="",
            email="Zoe.@example.com"
        )

        self.student5 = Students.objects.create(
            UID="5555555",
            fname="Vlad",
            lname="",
            email="Vlad.@example.com"
        )


        self.studentCourse1 = StudentCourses.objects.create(
            student= self.student1,
            course = self.course1,
            section_id= self.course1.sectionid 
        )

        self.studentCourse2 = StudentCourses.objects.create(
            student= self.student2,
            course = self.course1,
            section_id= self.course1.sectionid 
        )

    def post_add_student(self, confirm_choice):
        url = reverse("add_student", kwargs={"course_id": self.course1.id})
        return self.client.post(url, {
            "student_id": self.student3.UID,  
            "student_fname": "fname",  
            "student_lname": "lname",  
            "confirm_name_choice": confirm_choice,
        })
    
    def test_keep_existing_name(self):
        response = self.post_add_student("keep_existing")
        self.student3.refresh_from_db()
        self.assertEqual(self.student3.fname, "Bard") 
        self.assertEqual(self.student3.lname, "Jax") 
    
    def test_use_new_name(self):
        response = self.post_add_student("use_new")
        self.student3.refresh_from_db()
        self.assertEqual(self.student3.fname, "fname")
        self.assertEqual(self.student3.lname, "lname")
    

    def test_studentPage_loads(self):
        student_url = reverse(
            "studentPage",
            kwargs = {'course_id': self.course1.id})
        response = self.client.post(student_url)
        self.assertEqual(response.status_code, 200)

    def test_addStudent_success(self):
        student_url = reverse(
            "add_student",
            kwargs = {'course_id': self.course1.id}
        )
        student_data = {
            "student_id": self.student3.UID,
            "student_fname": self.student3.fname,
            "student_lname": self.student3.lname,
        }
        self.assertEqual(StudentCourses.objects.count(), 2)
        response = self.client.post(student_url, student_data)
        self.assertEqual(StudentCourses.objects.last().student, self.student3)
        self.assertEqual(StudentCourses.objects.count(), 3)
        

    def test_addStudent_(self):
        student_url = reverse(
            "add_student",
            kwargs = {'course_id': self.course1.id}
        )
        student_data = {
            "student_id": 1234321,
            "student_fname": 'Blue',
            "student_lname": 'Green',
        }
        self.assertEqual(StudentCourses.objects.count(), 2)
        response = self.client.post(student_url, student_data)
        self.assertEqual(StudentCourses.objects.last().student.lname, 'Green')
        self.assertEqual(StudentCourses.objects.count(), 3)


    def test_addStudent_1_digit_ID(self):
        student_url = reverse(
            "add_student",
            kwargs = {'course_id': self.course1.id}
        )
        student_data = {
            "student_id": 1,
            "student_fname": self.student3.fname,
            "student_lname": self.student3.lname,
        }
        self.assertEqual(StudentCourses.objects.count(), 2)
        response = self.client.post(student_url, student_data, follow=True)
        self.assertContains(response, "Student ID must be exactly 7 digits.")
        self.assertEqual(StudentCourses.objects.count(), 2)
    
    
    
    def test_removeStudent_success(self):
        student_url = reverse(
            "remove_student",
            kwargs = {"course_id": self.course1.id, "student_id": self.student2.UID})
        postData = {
            "course_id": self.course1.id,
            "student_id": self.student2.UID
        }
        response = self.client.post(student_url, postData)
        self.assertEqual(StudentCourses.objects.count(), 1)
        self.assertEqual(StudentCourses.objects.last().student, self.student1)

    def test_removeStudent_student_not_found(self):
        self.assertEqual(StudentCourses.objects.count(), 2)
        student_url = reverse(
            "remove_student",
            kwargs = {"course_id": self.course1.id, "student_id": self.student3.UID})
        postData = {
            "course_id": self.course1.id,
            "student_id": self.student3.UID
        }
        response = self.client.post(student_url, postData, follow = True)
        self.assertEqual(StudentCourses.objects.count(), 2)
        self.assertContains(response, f"Student {self.student3.fname} {self.student3.lname} is not enrolled in this course.")


    def test_handle_name_conflict_render(self):
        request = self.factory.post("/", data={})
        response = handle_name_conflict(
            request=request,
            student_id=self.student1.UID,
            student_fname="FName", 
            student_lname="LName", 
            course=self.course1
        )
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Conflict Detected", response.content)

        
    def testEditStudent_success(self):
        student_url = reverse(
            "edit_student",
            kwargs = {"course_id": self.course1.id, "student_id": self.student1.UID})
        postData = {
            "student_first_name": "ChangedFName",
            "student_last_name": "ChangedFName",
        }
        response = self.client.post(student_url, postData)
        self.assertEqual(StudentCourses.objects.count(), 2)
        updated_student = Students.objects.get(UID=self.student1.UID)
        self.assertEqual(updated_student.fname, "ChangedFName")
        self.assertEqual(updated_student.lname, "ChangedFName")


    def testEditStudent_redirct(self):
        student_url = reverse(
            "edit_student",
            kwargs = {"course_id": self.course1.id, "student_id": self.student1.UID})
        postData = {
            "student_first_name": "ChangedFName",
            "student_last_name": "ChangedFName",
        }
        response = self.client.post(student_url, postData)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("studentPage", kwargs={"course_id": self.course1.id}))

    def testRemoveAllStudent_success(self):
        self.assertEqual(StudentCourses.objects.count(), 2)
        student_url = reverse(
            "remove_all_students",
            kwargs = {"course_id": self.course1.id})
        response = self.client.post(student_url)
        self.assertEqual(StudentCourses.objects.count(), 0)
        
    def test_resolve_import_conflicts_creates_new_student(self):
        url = reverse("resolve_conflicts") 

        new_student_uid = "6666666"
        post_data = {
            "course_id": self.course1.id,
            f"conflict_{new_student_uid}": "use_new",
            f"fname_{new_student_uid}": "Lana",
            f"lname_{new_student_uid}": "Rhodes"
        }

        response = self.client.post(url, data=post_data)

        self.assertRedirects(response, reverse("studentPage", args=[self.course1.id]))
        student = Students.objects.get(UID=new_student_uid)
        self.assertEqual(student.fname, "Lana")
        self.assertEqual(student.lname, "Rhodes")
        self.assertTrue(
            StudentCourses.objects.filter(student=student, course=self.course1).exists()
        )
    
    def test_resolve_import_conflicts_updates(self):
        url = reverse("resolve_conflicts")
        post_data = {
            "course_id": self.course1.id,
            f"conflict_{self.student3.UID}": "use_new",
            f"fname_{self.student3.UID}": "UpdatedFirst",
            f"lname_{self.student3.UID}": "UpdatedLast"
        }

        response = self.client.post(url, data=post_data)

        updated_student = Students.objects.get(UID=self.student3.UID)
        self.assertEqual(updated_student.fname, "UpdatedFirst")
        self.assertEqual(updated_student.lname, "UpdatedLast")
        self.assertTrue(
            StudentCourses.objects.filter(student=updated_student, course=self.course1).exists()
        )

    def test_valid_row_creates_student(self):
        row = ["1234567", "Doe, John"]
        student, conflict = process_student_row(row)

        self.assertIsNotNone(student)
        self.assertIsNone(conflict)
        self.assertEqual(student.UID, "1234567")
        self.assertEqual(student.fname, "John")
        self.assertEqual(student.lname, "Doe")

    def test_existing_student_matching_name(self):
        Students.objects.create(UID="1234567", fname="Jane", lname="Doe", email="1234567@example.com")
        row = ["1234567", "Doe, Jane"]
        student, conflict = process_student_row(row)

        self.assertIsNotNone(student)
        self.assertIsNone(conflict)

    def test_existing_student_name_conflict(self):
        Students.objects.create(UID="1234567", fname="John", lname="Smith", email="1234567@example.com")
        row = ["1234567", "Doe, Jane"]
        student, conflict = process_student_row(row)

        self.assertIsNone(student)
        self.assertIsNotNone(conflict)
        self.assertEqual(conflict["student_id"], "1234567")
        self.assertEqual(conflict["db_fname"], "John")
        self.assertEqual(conflict["incoming_fname"], "Jane")

    def test_invalid_name_format(self):
        row = ["1234567", "JaneDoe"]
        student, error = process_student_row(row)

        self.assertIsNone(student)
        self.assertTrue("Invalid name format" in error)

    def test_invalid_student_id(self):
        row = ["123", "Doe, Jane"]
        student, error = process_student_row(row)

        self.assertIsNone(student)
        self.assertTrue("Invalid student ID" in error)

    def test_missing_fields(self):
        row = ["1234567"]
        student, error = process_student_row(row)

        self.assertIsNone(student)
        self.assertTrue("Missing or invalid" in error)

    def test_enroll_student_in_course(self):
        error = enroll_student_in_course(self.student3, self.course1)

        self.assertIsNone(error)
        self.assertTrue(StudentCourses.objects.filter(student=self.student3, course=self.course1).exists())
        


class ImportStudentsTest(TestCase):
    def setUp(self):

        self.Professor = Users.objects.create_user(
            email='Professor@example.com',
            password='testpassword',
            first_name='Pro',
            last_name='fessor',
            role='professor'
        )

        self.course1 = Courses.objects.create(
            id=1,
            courseid="CS101",
            name="Computer Science",
            sectionid="Section1",
            semester="Fall",
            year=2025,
            user = self.Professor,
        )

        self.student1 = Students.objects.create(
            UID="1234567",
            fname="John",
            lname="Doe",
            email="john.doe@example.com"
        )

        self.student2 = Students.objects.create(
            UID="2345678",
            fname="Jane",
            lname="Smith",
            email="john.doe@example.com"
        )

        self.import_url = reverse('import_students', kwargs={'course_id': self.course1.id})

    def test_import_valid_csv(self):
        csv_content = b"UID,Full Name\n3456789,\"Smith, John\"\n"

        csv_file = SimpleUploadedFile("students.csv", csv_content, content_type="text/csv")

        response = self.client.post(self.import_url, {'csv_file': csv_file}, follow=True)

        self.assertRedirects(response, reverse('studentPage', kwargs={'course_id': self.course1.id}))
        messages = list(get_messages(response.wsgi_request))
        self.assertIn("Students imported and enrolled successfully!", str(messages[0]))


    def test_import_not_csv_file(self):
        bad_file = SimpleUploadedFile("students.txt", b"1234567,\"Smith, John\"", content_type="text/plain")

        response = self.client.post(self.import_url, {'csv_file': bad_file}, follow=True)

        self.assertRedirects(response, reverse('studentPage', kwargs={'course_id': self.course1.id}))
        messages = list(get_messages(response.wsgi_request))
        self.assertIn("Invalid file type. Please upload a CSV file.", str(messages[0]))
    






class CourseTATest(TestCase):
    def setUp(self):
        self.client = Client()

        self.TA1 = Users.objects.create_user(
            email='TA1@example.com',
            password='testpassword',
            first_name='TA1_F',
            last_name='TA1_L',
            role='TA'
        )

        self.TA2 = Users.objects.create_user(
            email='TA2@example.com',
            password='testpassword',
            first_name='TA2_F',
            last_name='TA2_L',
            role='TA'
        )

        self.Professor = Users.objects.create_user(
            email='Professor@example.com',
            password='testpassword',
            first_name='Pro',
            last_name='fessor',
            role='professor'
        )

        self.course1 = Courses.objects.create(
            id=1,
            courseid="CS101",
            name="Computer Science",
            sectionid="Section1",
            semester="Fall",
            year=2025,
            user = self.Professor,
        )

        self.course1.tas.set([self.TA1, self.TA2])

    def test_displays_tas(self):
        url = reverse('course-tas', kwargs={'course_id': self.course1.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.TA1.first_name)
        self.assertContains(response, self.TA2.first_name)

    def test_Remove_tas(self):
        self.assertEqual(Users.objects.count(), 3)
        url = reverse('removeTA', kwargs={
            'course_id': self.course1.id, 
            'ta_user_id': self.TA1.userId})
        response = self.client.post(url)
        self.assertNotIn(self.TA1, self.course1.tas.all())


class AssignTAToCourseTests(TestCase):
    def setUp(self):
        self.client = Client()

        self.Professor = Users.objects.create_user(
            email='Professor@example.com',
            password='testpassword',
            first_name='Pro',
            last_name='fessor',
            role='professor'
        )

        self.NotTA = Users.objects.create_user(
            email='notta@example.com',
            password='testpassword',
            first_name='not',
            last_name='ta',
            role='professor'
        )
        
        self.course1 = Courses.objects.create(
            id=1,
            courseid="CS101",
            name="Computer Science",
            sectionid="Section1",
            semester="Fall",
            year=2025,
            user = self.Professor,
        )

        self.TA = Users.objects.create_user(
            email='ta@example.com',
            password='testpassword',
            first_name='T',
            last_name='A',
            role='TA'
        )

        self.url = reverse("assignTA")

    def test_valid_ta_assignment(self):
        self.client.force_login(self.Professor)
        self.assertEqual(self.course1.user, self.Professor)

        response = self.client.post(self.url, {
            "course_id": self.course1.id,
            "ta_email": self.TA.email
            
        })
        self.assertRedirects(response, reverse("course-tas", kwargs={"course_id": self.course1.id}))
        self.course1.refresh_from_db()
        var = self.course1.tas.all()

        self.assertIn(self.TA, self.course1.tas.all()) 
    
    def test_email_not_found(self):
        self.client.force_login(self.Professor)

        response = self.client.post(self.url, {
            "course_id": self.course1.id,
            "ta_email": "notfound@example.com"
        }, follow=True)

        self.assertContains(response, "No registered user found with that email.")


    def test_user_not_a_ta(self):
        self.client.force_login(self.Professor)

        response = self.client.post(self.url, {
            "course_id": self.course1.id,
            "ta_email": self.NotTA.email
        }, follow=True)

        self.assertContains(response, "does not have the role")

    def test_ta_already_assigned(self):
        self.course1.tas.add(self.TA)
        self.client.force_login(self.Professor)

        response = self.client.post(self.url, {
            "course_id": self.course1.id,
            "ta_email": self.TA.email
        }, follow=True)

        self.assertContains(response, "is already registered as a TA")
    
    def test_method_not_allowed(self):
        self.client.force_login(self.Professor)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)


class ActivateEmailTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get('/register')

        setattr(self.request, 'session', {})
        messages = FallbackStorage(self.request)
        setattr(self.request, '_messages', messages)

        self.user = Users.objects.create(
            first_name='Jane',
            last_name='Doe',
            email='janedoe@example.com',
            password=make_password('TestPassword123'),
            is_active=False
        )

    def test_activate_email_sends_email(self):
        activateEmail(self.request, self.user, self.user.email)

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Activate your account', mail.outbox[0].subject)
        self.assertIn('activate/', mail.outbox[0].body)
        self.assertIn(self.user.email, mail.outbox[0].to)


class ProfilePageTests(TestCase):
    def setUp(self):
        self.client = Client()
        
        self.user = Users.objects.create_user(
            email='test@example.com',
            password='OldPassword123!',
            first_name='Test',
            last_name='User',
            role='professor'
        )

        self.url = reverse('profilePage')
        self.client.force_login(self.user)

    def test_get_profile_page_renders_correctly(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'profile-page.html')

    def test_post_update_profile_success(self):
        response = self.client.post(self.url, {
            'first_name': 'Updated',
            'last_name': 'User',
            'email': 'test@example.com',
            'update_profile': '1',
        })
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')

        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Profile updated successfully" in str(m) for m in messages))
        self.assertRedirects(response, self.url)

    def test_post_change_password_success(self):
        response = self.client.post(self.url, {
            'old_password': 'OldPassword123!',
            'new_password1': 'NewPassword456!',
            'new_password2': 'NewPassword456!',
            'change_password': '1',
        })
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'success': 'Password updated successfully.'})

        # Ensure the user can log in with the new password
        self.client.logout()
        login_success = self.client.login(email='test@example.com', password='NewPassword456!')
        self.assertTrue(login_success)
    
    def test_post_change_password_mismatch(self):
        response = self.client.post(self.url, {
            'old_password': 'OldPassword123!',
            'new_password1': 'NewPassword456!',
            'new_password2': 'Mismatch!',
            'change_password': '1',
        })
        self.assertEqual(response.status_code, 400)

    def test_post_change_password_invalid(self):
        response = self.client.post(self.url, {
            'old_password': 'WrongOldPassword!',
            'new_password1': 'NewPassword456!',
            'new_password2': 'NewPassword456!',
            'change_password': '1',
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'old_password', response.content)


class enrolledStudentsViewTest(TestCase):
    def setUp(self):

        self.Professor = Users.objects.create_user(
            email='Professor@example.com',
            password='testpassword',
            first_name='Pro',
            last_name='fessor',
            role='professor'
        )

        self.TA = Users.objects.create_user(
            email='tar@example.com',
            password='testpassword',
            first_name='T',
            last_name='A',
            role='TA'
        )

        self.student1 = Students.objects.create(
            UID="1111111",
            fname="John",
            lname="Doe",
            email="johndoe@example.com"
        )

        self.student2 = Students.objects.create(
            UID="2222222",
            fname="D",
            lname="W",
            email="dw@example.com"
        )

        self.course1 = Courses.objects.create(
            id = 1,
            courseid="MATH101",
            name="Math 101",
            sectionid="A1",
            semester="Fall",
            year=2024,
            user=self.Professor
        )

        self.studentCourse1 = StudentCourses.objects.create(
            student= self.student1,
            course = self.course1,
            section_id= self.course1.sectionid 
        )

        self.course1.tas.add(self.TA)

    def test_enrolled_students_professor(self):
        self.client.force_login(self.Professor)
        response = self.client.get(reverse('enrolled-students'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "John Doe")
        self.assertContains(response, "Math 101")
        self.assertContains(response, "MATH101")

    def test_enrolled_students_TA(self):
        self.client.force_login(self.TA)
        response = self.client.get(reverse('enrolled-students'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "John Doe")
        self.assertContains(response, "Math 101")
        self.assertContains(response, "MATH101")

    def test_get_student_info_valid(self):
        result = get_student_info("1111111", [self.course1])
        self.assertEqual(result["UID"], "1111111")
        self.assertEqual(result["name"], "John Doe")
        self.assertIn("Math 101 (MATH101)", result["courses"])

    def test_get_student_info_invalid(self):
        result = get_student_info("999999", [self.course1])
        self.assertIn("error", result)
        self.assertEqual(result["error"], "Student with UID '999999' not found.")

    def test_get_student_info_valid_noCourses(self):
        result = get_student_info("2222222", [self.course1])
        self.assertEqual(result["UID"], "2222222")
        self.assertEqual(result["name"], "D W")
        self.assertIn("Not enrolled in any course", result["courses"])

class ActivationViewTest(TestCase):
    def setUp(self):
        self.user = Users.objects.create(
            first_name='Test',
            last_name='User',
            email='test@example.com',
            password='hashed_password123',  # Should be hashed in production
            role='TA',
            is_active=False
        )

        self.uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        self.token = default_token_generator.make_token(self.user)
        self.invalid_token = 'invalid-token'
        self.invalid_uid = urlsafe_base64_encode(force_bytes(999999))

    def test_activate_with_valid_token(self):
        response = self.client.get(reverse('activate', args=[self.uidb64, self.token]))
        self.user.refresh_from_db()

        self.assertTrue(self.user.is_active)
        self.assertRedirects(response, '/')  # or your login URL
        messages = list(response.wsgi_request._messages)
        self.assertTrue(any("Account activated successfully!" in str(m) for m in messages))

    def test_activate_with_invalid_token(self):
        response = self.client.get(reverse('activate', args=[self.uidb64, self.invalid_token]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Activation link is invalid!')
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)

    def test_activate_with_invalid_uid(self):
        response = self.client.get(reverse('activate', args=[self.invalid_uid, self.token]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Activation link is invalid!')


class LoginPageTest(TestCase):
    def setUp(self):
        self.login_url = reverse('loginPage')

        self.active_user = Users.objects.create(
            first_name='Active',
            last_name='User',
            email='active@example.com',
            password=make_password('correct_password'),
            role='TA',
            is_active=True
        )

        self.inactive_user = Users.objects.create(
            first_name='Inactive',
            last_name='User',
            email='inactive@example.com',
            password=make_password('correct_password'),
            role='TA',
            is_active=False
        )
    
    def test_login_successful(self):
        self.client.login(email='active@example.com', password='correct_password')
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)

    """
    def test_login_inactive_user(self):
        response = self.client.post(self.login_url, {
            'email': 'inactive@example.com',
            'password': 'correct_password'
        }, follow = True)
        print(response.content)

        self.assertContains(response, 'Account not activated. Please check your email.')
    """
        
class TableReportTest(TestCase):
    def setUp(self):
        self.Professor = Users.objects.create_user(
            email='Professor@example.com',
            password='testpassword',
            first_name='Pro',
            last_name='fessor',
            role='professor'
        )

        self.student1 = Students.objects.create(
            email = "student1Email@gmail.com",
            UID = "10000",
            fname = "Dave",
            lname = "Wu"
        )

        self.course1 = Courses.objects.create(
            courseid="1111", 
            name="Math 101",
            sectionid="A1", 
            semester="Fall",  
            year=datetime.now().year,
            user=self.Professor,
        )

        self.exam1 = Exams.objects.create(
            examid = 1,
            course=self.course1,
            examName="First Exam",
            sectionid="A1",
            examStart=timezone.make_aware(datetime(2025, 3, 15, 9, 0)),
            examEnd=timezone.make_aware(datetime(2025, 3, 15, 12, 0))
        )

        self.url = reverse('tableReport')

    def test_table_report_view(self):
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('students', response.context)
        self.assertIn('courses', response.context)
        self.assertIn('users', response.context)
        self.assertIn('exams', response.context)
        
        self.assertEqual(response.context['students'].count(), 1)
        self.assertEqual(response.context['courses'].count(), 1)
        self.assertEqual(response.context['users'].count(), 1)
        self.assertEqual(response.context['exams'].count(), 1)
        
        
class RegisterPageTest(TestCase):
    def setUp(self):
        self.url = reverse('registerPage')

    def test_register_page_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)

    def test_register_user_success(self):
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
            'role': 'professor',  
            'password1': 'password123!@#',
            'password2': 'password123!@#',
        }
        response = self.client.post(self.url, data)
        user = Users.objects.get(email='john.doe@example.com')
        self.assertEqual(user.first_name, 'John')
        self.assertEqual(user.last_name, 'Doe')
        self.assertFalse(user.is_active)

        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any(str(msg) == 'Dear user, please go to your email john.doe@example.com, check your inbox AND your junk folder. Click on the activation link to complete registration' for msg in messages))


    def test_register_user_no_role(self):
        Users.objects.create_user(
            first_name='Jane',
            last_name='Doe',
            email='jane.doe@example.com',
            password='password123'
        )
        
        data = {
            'first_name': 'John',
            'last_name': 'Smith',
            'email': 'jane.doe@example.com',  
            'password1': 'password123',
            'password2': 'password123',
        }
        
        response = self.client.post(self.url, data)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "This field is required.")
        self.assertEqual(Users.objects.filter(email='jane.doe@example.com').count(), 1)
        self.assertEqual(response.status_code, 200)
