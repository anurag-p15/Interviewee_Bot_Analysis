# video_analyzer/views.py
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render

def start_interview(request):
    return render(request, 'interview.html')