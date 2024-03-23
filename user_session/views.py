from django.shortcuts import render

# Create your views here.

def login(request):
    return render(request,'login.html')

def register(request):
    return render(request,'register.html')

def dashboard(request):
    return render(request,'dashboard.html')

def past_interviews(request):
    return render(request,'past_interviews.html')