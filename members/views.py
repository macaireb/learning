from django.shortcuts import render, redirect
from .forms import SignUpForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import Group, User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Conversation, Message
import json


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


@login_required
def send_message(request):
    if request.method == 'POST':
        data = json.loads(request.body)  # Parse the JSON payload
        recipient = data.get('recipient')  # Get the recipient's username
        content = data.get('content')

        try:
            # Get the recipient user
            print(f"Trying to get recipient with user id: {recipient}")
            recipient = User.objects.get(id=recipient)
        except User.DoesNotExist:
            return JsonResponse({'error': 'Recipient does not exist.'}, status=404)

        # Check if a conversation already exists
        conversation = Conversation.objects.filter(
            participants=request.user
        ).filter(
            participants=recipient
        ).first()

        if not conversation:
            # Create a new conversation if it doesn't exist
            conversation = Conversation.objects.create()
            conversation.participants.add(request.user, recipient)

        # Create the message
        message = Message.objects.create(
            conversation=conversation,
            sender=request.user,
            content=content
        )

        return JsonResponse({
            'message': 'Message sent successfully!',
            'conversation_id': conversation.id,
            'message_id': message.id,
            'timestamp': message.timestamp.isoformat(),
            'current_user': request.user.username,
            'recipient': recipient
        })
    else:
        recipients = User.objects.exclude(id=request.user.id)
        return render(request, 'send_message.html', {'recipients': recipients})

@login_required
def get_messages(request, conversation_id):
    # Fetch messages for the given conversation
    messages = Message.objects.filter(conversation_id=conversation_id).order_by('timestamp')

    # Return a JSON response with message data
    message_list = [
        {"sender": message.sender.username, "content": message.content, "timestamp": message.timestamp}
        for message in messages
    ]
    return JsonResponse({
        "messages": message_list,
        "current_user": request.user.username
    })

@login_required
def get_conversations(request):
    user = request.user
    conversations = Conversation.objects.filter(participants=user)

    data = []
    for conversation in conversations:
        # Get the other participant by excluding the logged-in user
        other_participant = conversation.participants.exclude(id=user.id).first()
        data.append({
            'id': conversation.id,
            'recipient': other_participant.username if other_participant else 'Unknown',  # Handle potential None
            'recipient_id': other_participant.id if other_participant else 'Unknown',
        })

    return JsonResponse({'conversations': data})
