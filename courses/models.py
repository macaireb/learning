from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import User
from django.shortcuts import redirect


# Create your models here.
class Course(models.Model):
    title = models.CharField(max_length=100)
    instructor = models.ManyToManyField(User, related_name="instructor_courses")
    description = models.TextField(blank=True, null=True)
    students = models.ManyToManyField(User, related_name='student_courses')

    def __str__(self):
        return self.title


class Test(models.Model):
    title = models.CharField(max_length=100)
    instructor = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, blank=True, null=False, on_delete=models.CASCADE)

    def __str__(self):
        if self.instructor.first_name and self.instructor.last_name:
            return f"{self.title} | {self.instructor.first_name} {self.instructor.last_name}"
        else:
            return f"{self.title} | {self.instructor.username}"

    def get_absolute_url(self):
        return redirect('home')
        #return reverse('choose_question', args=(self.pk,))


class Assignment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    student = models.ForeignKey(User, on_delete=models.CASCADE, blank=False, null=False)
    correct_answers = models.PositiveIntegerField(blank=True, null=True)
    incorrect_answers = models.PositiveIntegerField(blank=True, null=True)
    feedback = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=50, choices=[('pending', 'Pending'), ('completed', 'Completed'), ('graded', 'Graded')], default='pending')
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        abstract = True  # Abstract base class, no direct database table

    def __str__(self):
        return f"{self.student.username} | {self.get_assignment_type()}"

    def get_assignment_type(self):
        return self.__class__.__name__  # Returns the name of the subclass


class TestAssignment(Assignment):
    test = models.ForeignKey(Test, on_delete=models.CASCADE)

    def clean(self):
        # Validate that the sum of correct and incorrect doesn't exceed the total number of questions
        total_questions = self.test.questions.count()
        if self.correct_answers + self.incorrect_answers > total_questions:
            raise ValidationError("The total of correct and incorrect answers cannot exceed the number of questions.")

    def __str__(self):
        return f"{self.test.title} | {self.student.username}"


class Question(models.Model):
    # Common fields for all question types
    text = models.CharField(max_length=200)  # The question itself

    # Multiple Choice Options (These can be None for True/False or Fill-in-the-Blank)
    option_one = models.CharField(max_length=200)
    option_two = models.CharField(max_length=200, blank=True, null=True)
    option_three = models.CharField(max_length=200, blank=True, null=True)
    option_four = models.CharField(max_length=200, blank=True, null=True)
    option_five = models.CharField(max_length=200, blank=True, null=True)

    class Answers(models.IntegerChoices):
        one = 1
        two = 2
        three = 3
        four = 4
        five = 5

    # Field for specifying the correct answer based on the question type
    correct_answer = models.IntegerField(choices=Answers.choices, blank=True, null=True)

    # Field for storing user's answer
    # user_answer = models.CharField(max_length=200, blank=True, null=True)

    class QType(models.IntegerChoices):
        FIB = 1  # Fill in the blank
        TF = 2  # True/False
        MC = 3  # Multiple Choice

    # Question type (FIB, TF, or MC)
    type = models.IntegerField(choices=QType.choices)

    # Relationship to the exam this question belongs to
    exam = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='questions')

    def __str__(self):
        return f"Question: {self.text}"

    # Method to determine if a student's answer is correct
    def is_correct(self):
        return self.correct_answer == self.user_answer


class StudentAnswer(models.Model):
    assignment = models.ForeignKey(TestAssignment, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='student_answers')
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    answer = models.CharField(max_length=200, blank=True, null=True)  # The student's answer
    is_correct = models.BooleanField(default=False)  # Tracks correctness

    def __str__(self):
        return f"{self.student.username} | {self.question.text} | {self.answer}"

