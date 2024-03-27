from django.http import HttpResponse
from django.shortcuts import render
from pymongo import MongoClient
from django.contrib.auth.hashers import make_password,check_password
from .models import User
from django.contrib.auth import authenticate, login as auth_login



def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('username')  # Assuming 'username' is actually 'email'
        password = request.POST.get('password')
        bio = request.POST.get('bio')

        hashed_password = make_password(password)

        try:
            # Check if email is unique
            if User.objects.filter(username=username).exists():
                error_message = 'Email already exists'
                return render(request, 'register.html', {'error': error_message})

            user = User(username=username, password=hashed_password, bio=bio)
            user.save()

            # Redirect to a success page or any other desired action
            return render(request, 'login.html')

        except:
            # Handle any exception occurred during database operations
            error_message = 'Same email id exists...Use Another One !!'
            return render(request, 'register.html', {'error': error_message})

    else:
        # Handle GET request for registration page
        return render(request, 'register.html')

def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Retrieve user from the database using username
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # User does not exist
            error_message = 'Invalid username or password'
            return render(request, 'login.html', {'error': error_message})

        # Check if the entered password matches the one stored in the database
        if check_password(password, user.password):
            # Passwords match, authenticate user and redirect to dashboard
          #  auth_login(request, user)
            message='Hello eRROR HERE !!'
            # No need to manually set last_login for MongoDB user model
            request.session['user_id'] = user.id
            return render(request, 'dashboard.html', {'user_data': user})
        else:
            # Passwords don't match
            error_message = 'Invalid username or password'
            return render(request, 'login.html', {'error': error_message})
    else:
        return render(request, 'login.html')
    
def dashboard(request):
    return render(request,'dashboard.html')

def past_interviews(request):
    return render(request,'past_interviews.html')