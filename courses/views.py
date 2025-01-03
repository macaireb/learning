from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User, Group
from .forms import CreateCourseForm, CreateTestForm, QuestionForm, TakeTestForm, GradeTestForm, GradeTestFormSet
from .models import Course, Test, Question, TestAssignment, StudentAnswer
from .decorators import instructor_only, signed_in, student_only


# Create your views here.
@student_only
def student_test_detail(request, assignment_pk):
    student = request.user
    assignment = TestAssignment.objects.filter(student=student, id=assignment_pk, status__iexact='completed').first()
    answers = StudentAnswer.objects.filter(assignment=assignment, student=student)
    print(assignment)
    print(answers)
    return render(request, 'student_test_detail.html', {
        'answers': answers
    })
@student_only
def student_results(request):
    student = request.user
    test_assignments = TestAssignment.objects.filter(student=student, status__iexact='completed')
    if test_assignments:
        return render(request, 'student_results.html', {
            'test_assignments': test_assignments
        })
    else:
        messages.success(request, "You don't have any completed test assignments")
        return redirect('student_dashboard')

@student_only
def take_test(request, assignment_pk):
    test_assignment = TestAssignment.objects.get(pk=assignment_pk)
    student = request.user

    # Step 1: Get all questions for the TestAssignment
    questions = Question.objects.filter(exam=test_assignment.test)

    # Step 2: Get all UserAnswer objects for the TestAssignment and Student
    student_answers = StudentAnswer.objects.filter(
        assignment=test_assignment,
        student=student
    )

    # Step 3: Compare answered questions and filter unanswered ones
    answered_question_ids = student_answers.values_list('question_id', flat=True)
    unanswered_questions = questions.exclude(id__in=answered_question_ids)

    if not unanswered_questions.exists():
        test_assignment.status = 'completed'
        test_assignment.save()
        messages.success(request, f"{test_assignment.test.title} completed")
        return redirect('student_results')  # Redirect when all questions are answered

    print(f"{unanswered_questions.first()}")
    question = unanswered_questions.first()  # Get the next unanswered question
    test_assignment.status = 'pending'
    test_assignment.save()
    if request.method == 'POST':
        form = TakeTestForm(request.POST, question=question)
        if form.is_valid():
            student_answer = form.cleaned_data['answer']
            # Create a UserAnswer record
            print(f"Student entered {student_answer}")
            StudentAnswer.objects.create(
                question=question,
                assignment=test_assignment,
                student=student,
                answer=student_answer
            )
            return redirect('take_test', assignment_pk=assignment_pk)
    else:
        form = TakeTestForm(question=question)
    return render(request, 'take_test.html', {'form': form, 'question': question,
                                              'test': test_assignment.test})


@student_only
def student_course_detail(request, course_pk):
    student = request.user
    if student.groups.filter(name='Student').exists():
        course = Course.objects.filter(id=course_pk).first()  # Or use get(id=course_pk)
        if course:
            # Filter assignments for the specific student and course
            assignments = TestAssignment.objects.filter(student=student, course=course)
            return render(request, 'student_course_detail.html',
                      {'course': course, 'assignments': assignments})
        else:
            assignments = None  # Handle case where course doesn't exist
            return render(request, 'student_course_detail.html',
                          {})
    else:
        messages.error(request, "The selected user is not a student.")
        return redirect('home')


@student_only
def student_dashboard(request):
    student = request.user

    if student.groups.filter(name='Student').exists():
        # Query courses where the student is enrolled
        courses = Course.objects.filter(students=student)
        assignments = TestAssignment.objects.filter(student=student)
        return render(request, 'student_dashboard.html',
                      {'courses': courses, 'assignments': assignments})
    else:
        messages.error(request, "The selected user is not a student.")
        return redirect('home')
@instructor_only
def assign_instructor(request, course_pk, instructor_pk):
    # Get the course and instructor objects
    course = get_object_or_404(Course, id=course_pk)
    instructor = get_object_or_404(User, id=instructor_pk)

    # Add the student to the course
    if instructor.groups.filter(name='Instructor').exists():
        course.instructor.add(instructor)
        messages.success(request, f"{instructor.get_full_name() or instructor.username} has been enrolled in {course.title}.")
    else:
        messages.error(request, "The selected user is not an instructor.")

    # Redirect back to the course management page or another appropriate page
    return redirect('course_detail', pk=course_pk)

@instructor_only
def unassign_instructor(request, course_pk, instructor_pk):
    # Get the course and student objects
    course = get_object_or_404(Course, id=course_pk)
    instructor = get_object_or_404(User, id=instructor_pk)

    # Add the student to the course
    if instructor.groups.filter(name='Instructor').exists():
        if course.instructor.count() > 1:
            course.instructor.remove(instructor)
            messages.success(request, f"{instructor.get_full_name() or instructor.username} has been unassigned from {course.title}.")
        else:
            messages.error(request, f"{instructor.get_full_name() or instructor.username} is the only instructor for {course.title}, can't unassign")
    else:
        messages.error(request, "The selected user is not an instructor.")

    # Redirect back to the course management page or another appropriate page
    return redirect('course_detail', pk=course_pk)


@instructor_only
def enroll_student(request, course_pk, student_pk):
    # Get the course and student objects
    course = get_object_or_404(Course, id=course_pk)
    student = get_object_or_404(User, id=student_pk)

    # Add the student to the course
    if student.groups.filter(name='Student').exists():
        course.students.add(student)
        messages.success(request, f"{student.get_full_name() or student.username} has been enrolled in {course.title}.")
    else:
        messages.error(request, "The selected user is not a student.")

    # Redirect back to the course management page or another appropriate page
    return redirect('course_detail', pk=course_pk)


@instructor_only
def unenroll_student(request, course_pk, student_pk):
    # Get the course and student objects
    course = get_object_or_404(Course, id=course_pk)
    student = get_object_or_404(User, id=student_pk)

    # Add the student to the course
    if student.groups.filter(name='Student').exists():
        course.students.remove(student)
        messages.success(request, f"{student.get_full_name() or student.username} has been unenrolled from {course.title}.")
    else:
        messages.error(request, "The selected user is not a student.")

    # Redirect back to the course management page or another appropriate page
    return redirect('course_detail', pk=course_pk)

@instructor_only
def create_course(request):
    create_course_form = CreateCourseForm(request.POST or None, exclude_user=request.user)
    if create_course_form.is_valid():
        new_course = Course(
            # instructor=request.user,
            title=create_course_form.cleaned_data['title'],
            description=create_course_form.cleaned_data['description'])
        new_course.save()
        # Add the current user and other selected instructors
        new_course.instructor.add(request.user)  # Automatically saved
        new_course.instructor.add(*create_course_form.cleaned_data['instructor'])  # Add multiple instructors
        new_course.students.add(*create_course_form.cleaned_data['students'])
        messages.success(request, "New course created")
        return redirect('home')
    return render(request, 'create_course.html', {'form': create_course_form})

@instructor_only
def delete_course(request, pk):
    course = Course.objects.filter(id=pk).first()
    title = course.title
    course.delete()
    messages.success(request, f"Successfully deleted course {title}")
    return redirect('view_courses')


@instructor_only
def update_course(request, pk):
    course = Course.objects.filter(id=pk).first()
    if course:
        create_course_form = CreateCourseForm(request.POST or None, instance=course, exclude_user=request.user)
        if create_course_form.is_valid() and request.POST:
            course.instructor.clear()
            course.students.clear()
            course.title = create_course_form.cleaned_data['title']
            course.description = create_course_form.cleaned_data['description']
            course.instructor.add(request.user)  # Automatically saved
            course.instructor.add(*create_course_form.cleaned_data['instructor']) # Add multiple instructors
            course.students.add(*create_course_form.cleaned_data['students'])
            messages.success(request, "Course successfully updated")
            return redirect('course_detail', pk=course.id)
        else:
            return render(request, 'update_course.html', {'form': create_course_form,
                                                          'course': course})

@signed_in
def view_courses(request):
    courses = Course.objects.all()
    if courses:
        return render(request, 'view_courses.html', {'courses': courses})
    else:
        return render(request, 'view_courses.html', {})

@signed_in
def course_detail(request, pk):
    course = Course.objects.filter(id=pk).first()
    courses = Course.objects.all()
    # Filter users who belong to the 'student' group
    student_group = Group.objects.get(name='Student')
    all_students = User.objects.filter(groups=student_group)
    unenrolled_students = all_students.exclude(id__in=course.students.all())
    instructor_group = Group.objects.get(name='Instructor')
    all_instructors = User.objects.filter(groups=instructor_group)
    unassigned_instructors = all_instructors.exclude(id__in=course.instructor.all())
    multiple_instructors = course.instructor.count() > 1
    tests = Test.objects.filter(course=course)
    multiple_courses = courses.count() > 1
    if course:
        return render(request, 'course_detail.html',
                      {'course': course, 'unenrolled_students': unenrolled_students,
                       'unassigned_instructors': unassigned_instructors,
        'multiple_instructors': multiple_instructors, 'tests': tests,
                       'multiple_courses': multiple_courses})
    else:
        messages.success(request, "Error looking up that course")
        return redirect('view_courses')

@instructor_only
def create_test(request):
    create_test_form = CreateTestForm(request.POST or None, user=request.user)
    if create_test_form.is_valid():
        new_test = Test(
            instructor=request.user,
            title=create_test_form.cleaned_data['title'],
            course=create_test_form.cleaned_data['course']
        )
        new_test.save()
        messages.success(request, "New test created")
        return redirect('view_tests')
    return render(request, 'create_test.html', {'form': create_test_form})

@instructor_only
def delete_test(request, pk):
    test = Test.objects.filter(id=pk).first()
    title = test.title
    test.delete()
    messages.success(request, f"Successfully deleted test - {title}")
    return redirect('view_tests')

@instructor_only
def view_tests(request):
    if request.user.is_authenticated:
        tests = Test.objects.filter(instructor=request.user)
        if tests:
            return render(request, 'view_tests.html', {'tests': tests})
        else:
            messages.success(request, "You haven't created any tests, please do so first")
            return redirect('create_test')
    else:
        messages.success(request, "Must be signed in to view this page")
        return redirect('login')

@instructor_only
def update_test(request, pk):
    test = Test.objects.filter(id=pk).first()
    if test:
        create_test_form = CreateTestForm(request.POST or None, instance=test, user=request.user)
        if create_test_form.is_valid() and request.POST:
            test.title=create_test_form.cleaned_data['title']
            test.course=create_test_form.cleaned_data['course']
            test.save()
            messages.success(request, "Course Updated")
            return redirect('view_tests')
        return render(request, 'create_test.html', {'form': create_test_form})

@instructor_only
def test_detail(request, pk):
    test = Test.objects.filter(id=pk).first()
    questions = Question.objects.filter(exam=test)
    assignments = TestAssignment.objects.filter(test=test)
    assigned_students = assignments.values_list('student', flat=True)

    # Get all users in the 'Student' group
    student_group = Group.objects.get(name='Student')
    all_students = User.objects.filter(groups=student_group)

    # Exclude the assigned students from all students
    unassigned_students = all_students.exclude(id__in=assigned_students)

    if test:
        return render(request, 'test_detail.html', {'test':test, 'questions': questions,
                                                    'assignments':assignments,
                                                    'unassigned_students': unassigned_students})
    else:
        messages.success(request, "Error looking up that test")
        return redirect('view_tests')


@instructor_only
def unasign_test(request, assignment_pk, student_pk):
    # Need to add app wide logging so when a student is removed from an assignment the score can be saved
    # Get the assignment and student objects
    assignment = get_object_or_404(TestAssignment, id=assignment_pk)
    student = get_object_or_404(User, id=student_pk)

    # Delete The assignment
    if student.groups.filter(name='Student').exists():
        # don't delete assignment if its been graded or completed
        if assignment.status == 'pending' or 'Pending':
            del(assignment)

@instructor_only
def assign_test(request, test_pk, student_pk):
    # Get the test and student objects
    test = get_object_or_404(Test, id=test_pk)
    student = get_object_or_404(User, id=student_pk)

    # Add the student and test to the assignment
    if student.groups.filter(name='Student').exists():
        assignment = TestAssignment(
            test=test,
            course=test.course,
            student=student
        )
        assignment.save()
        messages.success(request, f"{student.get_full_name() or student.username} assigned {test.title} test")
        return redirect('test_detail', pk=test_pk)
    else:
        messages.error(request, f"{student.get_full_name() or student.username} is not a student")
        return redirect('test_detail', pk=test_pk)


@instructor_only
def grade_test(request, pk):
    assignment = TestAssignment.objects.filter(id=pk).first()
    answers = StudentAnswer.objects.filter(assignment=assignment)
    # Initialize the formset
    formset = GradeTestFormSet(queryset=answers)

    if request.method == 'POST':
        formset = GradeTestFormSet(request.POST, queryset=answers)
        if formset.is_valid():
            # Save all changes
            formset.save()
            assignment.status = 'Graded'
            assignment.save()
            messages.success(request, f"{assignment.test.title} successfully graded")
            return redirect('test_detail', pk=assignment.test.id)
        else:
            print(formset.errors)
    return render(request, 'grade_test.html', {'formset': formset, 'assignment': assignment})


@instructor_only
def create_question(request, pk):
    test = Test.objects.filter(id=pk).first()
    if request.method == 'POST' and test:
        form = QuestionForm(request.POST, exam=test)
        if form.is_valid():
            form.save()
            # After saving clear form and allow user to re-enter another question
            form = QuestionForm(exam=test)
            messages.success(request, f"Question successfully added to {test.title}")
            return render(request, 'create_question.html', {'form': form, 'test': test})
    else:
        form = QuestionForm(exam=test)
    return render(request, 'create_question.html', {'form': form, 'test': test})

@instructor_only
def delete_question(request, pk):
    question = Question.objects.filter(id=pk).first()
    if question:
        test_pk = question.exam.pk
        question.delete()
        messages.success(request, f"Question successfully deleted")
        return redirect('test_detail', pk=test_pk)

@instructor_only
def view_assignments(request):
    instructor = request.user
    assignments = TestAssignment.objects.filter(test__instructor=instructor)
    return render(request, 'view_assignments.html', {'assignments': assignments})