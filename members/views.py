from django.shortcuts import render, redirect
from .forms import SignUpForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import Group
from django.contrib import messages


# Create your views here.

def home(request):
    user = request.user
    if user.is_authenticated:
        if user.groups.filter(name='Student').exists():
            return redirect('student_dashboard')
        if user.groups.filter(name='Instructor').exists():
            return redirect('view_tests')
    else:
        return redirect('login')
    return render(request, 'home.html', {})


# Add if anonymous decorator
def register_user(request):
    form = SignUpForm()
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data['username']
            password = form.cleaned_data['password1']
            is_instructor = form.cleaned_data['is_instructor']  # Get the is_instructor value

            # Assign group based on is_instructor
            if is_instructor:  # '1' corresponds to "Yes"
                group, created = Group.objects.get_or_create(name='Instructor')
            else:
                group, created = Group.objects.get_or_create(name='Student')

            user = authenticate(username=username, password=password)
            user.groups.add(group)
            # log in user
            login(request, user)
            messages.success(request, ("Registration successful"))
            return redirect('home')
        else:
            messages.success(request, ("Whooopps there was a problem registering, please try again"))
            return redirect('register')
    else:
        return render(request, 'register.html', {'form': form})


def login_user(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, ("You have been logged in"))
            return redirect('home')
        else:
            messages.success(request, ("There was an error please try again"))
            return redirect('login')
    else:
        return render(request, "login.html", {})


def logout_user(request):
    logout(request)
    messages.success(request, ("You have been logged out... Thanks for stopping by"))
    return redirect('login')