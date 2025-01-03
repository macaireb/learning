from django import forms
from .models import Course, Test, Question, StudentAnswer
from django.contrib.auth.models import User, Group
from django.forms import modelformset_factory


class GradeTestForm(forms.ModelForm):
    is_correct = forms.ChoiceField(
        label='Correct',
        choices=[
            (True, 'correct'),
            (False, 'incorrect')
        ],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input', 'type': 'checkbox', 'role': 'switch'})
    )

    class Meta:
        model = StudentAnswer
        fields = ['is_correct']


GradeTestFormSet = modelformset_factory(
    StudentAnswer,  # The model the formset is based on
    form=GradeTestForm,
    extra=0  # No extra blank forms; only display existing records
)


class TakeTestForm(forms.ModelForm):
    class Meta:
        model = StudentAnswer
        fields = ['answer']
        widgets = {
            'answer': forms.TextInput(),
        }

    def __init__(self, *args, **kwargs):
        question = kwargs.pop('question', None)  # Accept a question instance
        super().__init__(*args, **kwargs)
        if question and question.type == Question.QType.MC:  # If it's a multiple-choice question
            self.fields['answer'] = forms.ChoiceField(
                choices=[
                    (1, question.option_one),
                    (2, question.option_two),
                    (3, question.option_three),
                    (4, question.option_four),
                    (5, question.option_five),
                ],
                widget=forms.RadioSelect(attrs={'class': 'form-control'}),
            )
        elif question.type == Question.QType.TF:  # True/False
            self.fields['answer'] = forms.ChoiceField(
                choices=[(1, "True"), (0, "False")],
                widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
            )
        elif question.type == Question.QType.FIB:  # Fill in the Blank
            self.fields['answer'] = forms.CharField(
                widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your Answer'}),
                required=True,
            )


class CreateCourseForm(forms.ModelForm):
    title = forms.CharField(label='', widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Course Title'}), required=True)
    description = forms.CharField(label='', widget=forms.Textarea(
        attrs={'class': 'form-control', 'placeholder': 'Course Description'}), required=True)

    instructor = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
        required=False,
    )

    students = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
        required=False,
    )

    class Meta:
        model = Course
        fields = ['title', 'description', 'instructor', 'students']

    def __init__(self, *args, exclude_user=None, **kwargs):
        super().__init__(*args, **kwargs)

        # Get the 'Instructor' group
        instructor_group = Group.objects.get(name='Instructor')
        student_group = Group.objects.get(name='Student')

        # Filter users in the 'Instructor' group and exclude the provided user
        self.fields['instructor'].queryset = User.objects.filter(groups=instructor_group).exclude(id=exclude_user.id)
        self.fields['students'].queryset = User.objects.filter(groups=student_group)


class CreateTestForm(forms.ModelForm):
    title = forms.CharField(label='', widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Test Title'}), required=True)
    # Explicitly define ModelChoiceField
    course = forms.ModelChoiceField(
        label='',
        queryset=Course.objects.none(),  # Default, will override in __init__
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        required=True
    )

    class Meta:
        model = Test
        fields = ['title', 'course']

        exclude = ['instructor', ]

    def __init__(self, *args, **kwargs):
        # Pass 'user' from the view to filter courses by instructor
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['course'].queryset = Course.objects.filter(instructor=user)


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = [
            'text',
            'type',
            'option_one',
            'option_two',
            'option_three',
            'option_four',
            'option_five',
            'correct_answer',
            # 'exam',
            # 'assignment',
        ]

        exclude = ['exam',]
        widgets = {
            'text': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter the question'}),
            'type': forms.Select(attrs={'class': 'form-control'}),
            'option_one': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Option 1'}),
            'option_two': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Option 2'}),
            'option_three': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Option 3'}),
            'option_four': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Option 4'}),
            'option_five': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Option 5'}),
            'correct_answer': forms.Select(attrs={'class': 'form-control'}),
            # 'exam': forms.Select(attrs={'class': 'form-control'}),
            # 'assignment': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        question_type = cleaned_data.get('type')
        correct_answer = cleaned_data.get('correct_answer')

        # Validation based on question type
        if question_type == Question.QType.MC:
            # Ensure at least two options are provided for multiple-choice questions
            options = [
                cleaned_data.get('option_one'),
                cleaned_data.get('option_two'),
                cleaned_data.get('option_three'),
                cleaned_data.get('option_four'),
                cleaned_data.get('option_five'),
            ]
            if len([opt for opt in options if opt]) < 2:
                raise forms.ValidationError("Multiple-choice questions require at least two options.")
            if correct_answer not in range(1, 6):
                raise forms.ValidationError("Correct answer must be one of the provided options.")

        elif question_type == Question.QType.FIB:
            # For fill-in-the-blank, ensure no options are provided
            if any(cleaned_data.get(f'option_{i}') for i in range(1, 6)):
                raise forms.ValidationError("Fill-in-the-blank questions should not have options.")
            if not cleaned_data.get('correct_answer'):
                raise forms.ValidationError("A correct answer is required for fill-in-the-blank questions.")

        elif question_type == Question.QType.TF:
            # For true/false, ensure no options are provided and correct_answer is valid
            if any(cleaned_data.get(f'option_{i}') for i in range(1, 6)):
                raise forms.ValidationError("True/False questions should not have options.")
            if correct_answer not in [1, 2]:
                raise forms.ValidationError("Correct answer for True/False must be 1 (True) or 2 (False).")

        return cleaned_data

    def __init__(self, *args, exam=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['option_one'].label = ''
        self.fields['option_two'].label = ''
        self.fields['option_three'].label = ''
        self.fields['option_four'].label = ''
        self.fields['option_five'].label = ''
        if exam:
            self.instance.exam = exam