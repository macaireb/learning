from django.urls import path
from . import views

urlpatterns = [
  path('create_course/', views.create_course, name='create_course'),
  path('update_course/<int:pk>', views.update_course, name='update_course'),
  path('delete_course/<int:pk>/', views.delete_course, name='delete_course'),
  path('view_courses', views.view_courses, name='view_courses'),
  path('course_detail/<int:pk>', views.course_detail, name='course_detail'),
  path('student_course_detail/<int:course_pk>', views.student_course_detail, name='student_course_detail'),
  path('student_results/', views.student_results, name='student_results'),
  path('student_test_detail/<int:assignment_pk>', views.student_test_detail, name='student_test_detail'),
  path('take_test/<int:assignment_pk>', views.take_test, name='take_test'),
  path('create_test/', views.create_test, name='create_test'),
  path('delete_test/<int:pk>', views.delete_test, name='delete_test'),
  path('view_tests/', views.view_tests, name='view_tests'),
  path('update_test/<int:pk>', views.update_test, name='update_test'),
  path('test_detail/<int:pk>', views.test_detail, name='test_detail'),
  path('grade_test/<int:pk>', views.grade_test, name='grade_test'),
  path('create_question/<int:pk>', views.create_question, name='create_question'),
  path('delete_question/<int:pk>', views.delete_question, name='delete_question'),
  path('view_assignments/', views.view_assignments, name='view_assignments'),
  path('assign_test/<int:test_pk>/<int:student_pk>/', views.assign_test, name='assign_test'),
  path('enroll_student/<int:course_pk>/<int:student_pk>/', views.enroll_student, name='enroll_student'),
  path('unenroll_student/<int:course_pk>/<int:student_pk>/', views.unenroll_student, name='unenroll_student'),
  path('assign_instructor/<int:course_pk>/<int:instructor_pk>/', views.assign_instructor, name='assign_instructor'),
  path('unassign_instructor/<int:course_pk>/<int:instructor_pk>/', views.unassign_instructor, name='unassign_instructor'),
  path('student_dashboard/', views.student_dashboard, name='student_dashboard'),
]