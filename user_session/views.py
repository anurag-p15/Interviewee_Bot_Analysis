from django.http import HttpResponse,JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import redirect, render
from pymongo import MongoClient
from django.contrib.auth.hashers import make_password,check_password
from .models import User
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth import authenticate, login as auth_login
from threading import Thread
import cv2
import time
from deepface import DeepFace
from django.views.decorators.http import require_POST
from django.contrib.auth import logout as django_logout


#User Session
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

    # Logout the user using Django's logout function
    django_logout(request)

    # Clear the analysis results
    video_analyzer.latest_analysis_results = []

    # Redirect to the login page
    return redirect('user_session:login')


def past_interviews(request):
    return render(request,'past_interviews.html')



#Camera views
class VideoAnalyzer:
    def __init__(self):
        self.recording = False
        self.video_capture = None
        self.analysis_duration = 20
        self.latest_analysis_results = []

    def start_analysis(self):
        self.recording = True
        Thread(target=self.analyze_video).start()

    def analyze_frame(self, frame):
        # Your frame analysis code here
        # ...
        faceCascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = faceCascade.detectMultiScale(gray, 1.1, 4)

        if isinstance(faces, tuple):
            print("No Face Detected")
            return {"status": "No Face Detected"}
        else:
            print("Face Detected")
            # Add text to the frame
            cv2.putText(frame, "Hello User!", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

            # Analyze emotions using DeepFace
            result = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
            print(result)
            return result 
        # Return the analysis result
        return result

    def analyze_video(self):
        self.video_capture = cv2.VideoCapture(0)

        start_time = time.time()

        while self.recording:
            ret, frame = self.video_capture.read()

            if ret:
                # Display the frame in a window
                cv2.imshow('Video Feed', frame)
                cv2.waitKey(1)  # Allow the window to refresh
                result = self.analyze_frame(frame)
                elapsed_time = time.time() - start_time
                if elapsed_time >= self.analysis_duration:
                    self.recording = False
                    # Update the latest analysis result
                    self.latest_analysis_results.append(result)
                    break
                # Store the result at 5-second intervals
                if elapsed_time % 5 == 0:
                    self.latest_analysis_results.append(result)
        self.video_capture.release()
        cv2.destroyAllWindows()

    def get_average_emotion(self):
        if not self.latest_analysis_results:
            return None

        # Calculate the average emotion scores
        average_emotion = {
            'angry': 0,
            'disgust': 0,
            'fear': 0,
            'happy': 0,
            'sad': 0,
            'surprise': 0,
            'neutral': 0
        }

        for result in self.latest_analysis_results:
            emotions = result[0]['emotion']
            for emotion in emotions:
                average_emotion[emotion] += emotions[emotion]

        num_results = len(self.latest_analysis_results)
        for emotion in average_emotion:
            average_emotion[emotion] /= num_results

        return average_emotion

# Initialize the VideoAnalyzer
video_analyzer = VideoAnalyzer()

# Views
@csrf_exempt
def check_login_status(request):
    user_data = request.session.get('user')
    if user_data:
        return JsonResponse({'status': 'logged_in'})
    else:
        return JsonResponse({'status': 'not_logged_in'})

@csrf_exempt
def start_analysis_view(request):
    user_data = request.session.get('user')
    print(user_data)
    if user_data:
        # Clear the analysis results before starting a new analysis
        video_analyzer.latest_analysis_results = []
        
        # Start the analysis
        result = video_analyzer.start_analysis()
        return HttpResponse()
    else:
        # Redirect to login page if user not logged in
        messages.error(request, 'Please login to access the dashboard.')
        return redirect('user_session:login')

@csrf_exempt
def check_analysis_result(request):
    # Wait until the analysis is complete
    while video_analyzer.recording:
        time.sleep(1)

    average_emotion = video_analyzer.get_average_emotion()

    if average_emotion:
        # Format the average emotion information as HTML
        html_result = "<h2>Average Emotion Result</h2>"
        for emotion, score in average_emotion.items():
            html_result += f"<p>{emotion.capitalize()}: {score}</p>"

        # Return HTML response
        return JsonResponse({"html_result": html_result}, safe=False)
    else:
        return JsonResponse({"html_result": "You have not logged in !! Login to Continue !!"}, safe=False)
    
@require_POST
def clear_analysis_results(request):
    # Clear the analysis results
    video_analyzer.latest_analysis_results = []
    return JsonResponse({'message': 'Analysis results cleared successfully'})