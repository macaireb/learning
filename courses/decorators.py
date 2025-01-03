from django.http import HttpResponseForbidden
from django.contrib import messages
from django.shortcuts import redirect


def instructor_only(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.groups.filter(name='Instructor').exists():
            return view_func(request, *args, **kwargs)
        messages.warning(request, "You are not authorized to access this page.")
        # Redirect to a safe page (e.g., the homepage or a student dashboard)
        return redirect('home')
    return wrapper


def student_only(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.groups.filter(name='Student').exists():
            return view_func(request, *args, **kwargs)
        messages.warning(request, "You are not authorized to access this page.")
        # Redirect to a safe page (e.g., the homepage or a student dashboard)
        return redirect('home')
    return wrapper


def signed_in(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:
            return view_func(request, *args, **kwargs)
        messages.warning(request, "You are not authorized to access this page.")
        # Redirect to a safe page (e.g., the homepage or a student dashboard)
        return redirect('login')
    return wrapper
