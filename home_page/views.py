from django.shortcuts import render

# Create your views here.

def home(request):
    return render(request,'home.html')

def domain(request):
    return render(request,'domain.html')

