from django.http import HttpResponse
from django.shortcuts import redirect, render
from pymongo import MongoClient
from django.contrib.auth.hashers import make_password,check_password
from .models import User
from django.contrib import messages
from django.contrib.auth import logout
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

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            error_message = 'Invalid username or password'
            return render(request, 'login.html', {'error': error_message})

        if check_password(password, user.password):
            # Store the entire user object in the session
            request.session['user'] = {
                'name': user.name,
                'username': user.username,
                'bio': user.bio  # Add more fields as needed
            }
            # Redirect to dashboard on successful login
            return redirect('user_session:dashboard')
        else:
            error_message = 'Invalid username or password'
            return render(request, 'login.html', {'error': error_message})
    else:
        return render(request, 'login.html')

def dashboard(request):
    user_data = request.session.get('user')
    print(user_data)
    if user_data:
        # Pass user_data to the template
        return render(request, 'dashboard.html', {'user_data': user_data})
    else:
        # Redirect to login page if user not logged in
        messages.error(request, 'Please login to access the dashboard.')
        return redirect('user_session:login')


def logout_view(request):
    # Clear all session-stored variables
    request.session.flush()
    # Alternatively, if you want to clear specific session variables, you can use:
    # for key in list(request.session.keys()):
    #     del request.session[key]

    # Logout the user (optional, if you're using Django authentication system)
    logout(request)
    
    # Redirect to the login page
    return redirect('user_session:login')


def past_interviews(request):
    return render(request,'past_interviews.html')