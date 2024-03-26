from django.http import HttpResponse
from django.shortcuts import render
from pymongo import MongoClient
from django.contrib.auth.hashers import make_password
from .models import User


def register(request):
    if request.method == 'POST':
        # Assuming you have form fields named 'name', 'username', 'email', 'password', 'password_repeat', and 'bio'
        name = request.POST.get('name')
        username = request.POST.get('username')
        email = request.POST.get('username')  # Assuming 'username' is actually 'email'
        password = request.POST.get('password')
        password_repeat = request.POST.get('password_repeat')
        bio = request.POST.get('bio')
         # Hash the password
        hashed_password = make_password(password)
        
        # Check if email is unique
        if User.objects.filter(username=username).exists():
            error_message = 'Email already exists'
            return render(request, 'register.html', {'error': error_message})
    
        
        # Create a new user object
        user = User(name=name, username=username, password=hashed_password,bio=bio)
        # Save the user to the database
        user.save()

        # Redirect to a success page or any other desired action
        return render(request, 'login.html')

    
    else:
        # Handle GET request for registration page
        return render(request, 'register.html')

def login(request):
    return render(request,'login.html')



def dashboard(request):
    return render(request,'dashboard.html')

def past_interviews(request):
    return render(request,'past_interviews.html')