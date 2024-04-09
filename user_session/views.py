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
import csv
import time
import random
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import speech_recognition as sr
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
    user_data = request.session.get('user')
    print(user_data)
    if user_data:
        return render(request,'past_interviews.html')
    else:
        # Redirect to login page if user not logged in
        messages.error(request, 'Please login to access the dashboard.')
        return redirect('user_session:login')

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
    audio_sentiment=video_analyzer.analyze_audio()

    if average_emotion:
        # Format the average emotion information as HTML
        html_result = "<h2>Average Emotion Result</h2>"
        for emotion, score in average_emotion.items():
            html_result += f"<p>{emotion.capitalize()}: {score}</p>"

        html_result += "<h2>Audio Sentiment Result</h2>"
        for sentiment, value in audio_sentiment.items():
            html_result += f"<p>{sentiment.capitalize()}: {value}</p>"

        # Return HTML response
        return JsonResponse({"html_result": html_result}, safe=False)
    else:
        return JsonResponse({"html_result": "You have not logged in !! Login to Continue !!"}, safe=False)
    
@require_POST
def clear_analysis_results(request):
    # Clear the analysis results
    video_analyzer.latest_analysis_results = []
    return JsonResponse({'message': 'Analysis results cleared successfully'})

#Camera views
class VideoAnalyzer:
    def __init__(self):
        self.recording = False
        self.video_capture = None
        self.analysis_duration = 20
        self.latest_analysis_results = []
        self.questions = self.load_questions_from_csv('questions_dataset.csv')
        self.resolution = (1300,1300)  # Default resolution

    def set_resolution(self, resolution):
        self.resolution = resolution

        
    def load_questions_from_csv(self,csv_file):
        questions=[]
        with open(csv_file,newline='',encoding='utf-8') as csvfile:
            reader=csv.DictReader(csvfile)
            for row in reader:
                questions.append(row['Question'])
        return questions
    
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

            # Analyze emotions using DeepFace
            result = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
            print(result)
            # Return the analysis result
            return result 
        



    def analyze_audio(self):
        recognizer = sr.Recognizer()
        text=""
        
        with sr.Microphone() as source:
            print("Clearing Background noise...")
            recognizer.adjust_for_ambient_noise(source,duration=1)
            print("Waiting for user's message...")
            record_audio=recognizer.listen(source)
            print("Done recording..")
            
        try:
            print("Printing the message...")
            text=recognizer.recognize_google(record_audio,language='en-US')
            print("Your Message: {}".format(text))
        except Exception as ex:
            print(ex)
            
            
        sentence=[str(text)]
        
        analyzer=SentimentIntensityAnalyzer()
        audio_sentiment=analyzer.polarity_scores(text)
        print("Vader Sentiment Scores: ",audio_sentiment)
        return audio_sentiment
    
    
    def analyze_video(self): 
        self.video_capture = cv2.VideoCapture(0)
        self.video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
        self.video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])

        question=random.choice(self.questions)
        audio_thread=Thread(target=self.analyze_audio)
        audio_thread.start()

        while self.recording:
            ret, frame = self.video_capture.read()

            if ret:
                font=cv2.FONT_HERSHEY_COMPLEX
                bottom_center=(frame.shape[1]//2,frame.shape[0]-10)
                bottom_left_corner=(10, frame.shape[0] - 10)
                font_scale = 1
                font_thickness = 2
                # hello_message = "Hello!"
                text_size = cv2.getTextSize(question, font, font_scale, font_thickness)[0]

                # Calculate the position for the rectangle background
                background_position = (bottom_center[0] - text_size[0] // 2 - 5, bottom_center[1] - text_size[1] + 5)
                background_size = (text_size[0] + 10, text_size[1] + 10)

                # Draw the white rectangle background

                # Define background color and text color
                background_color = (0, 119, 204)  # BGR color for #F77700 (orange)
                text_color = (0, 0, 0)  # Black

                # Calculate text size
                text_size = cv2.getTextSize(question, font, font_scale, font_thickness)[0]

                # Calculate background rectangle position and size
                background_position = (bottom_left_corner[0], bottom_left_corner[1] - text_size[1] - 5)
                background_size = (1300, text_size[1] + 80)  # Add some padding

                # Draw filled rectangle as background
                cv2.rectangle(frame, background_position, (background_position[0] + background_size[0], background_position[1] + background_size[1]), background_color, -1)

                # Draw text on top of background rectangle
                cv2.putText(frame, question, (bottom_left_corner[0], bottom_left_corner[1] - 5), font, font_scale, text_color, font_thickness, cv2.LINE_AA)


                button_margin = 10
                button_height = 30
                button_width = 150
                button_color = (255, 255, 255)
                button_text_color = (0, 0, 0)

                next_button_top_left = (frame.shape[1] - button_width - button_margin, button_margin)
                next_button_bottom_right = (frame.shape[1] - button_margin, button_margin + button_height)
                cv2.rectangle(frame, next_button_top_left, next_button_bottom_right, button_color, -1)
                cv2.putText(frame, 'Next Question', (next_button_top_left[0] + 10, next_button_top_left[1] + 25), font, 0.5, button_text_color, 1, cv2.LINE_AA)

                end_button_top_left = (frame.shape[1] - button_width - button_margin, button_margin + button_height + button_margin)
                end_button_bottom_right = (frame.shape[1] - button_margin, button_margin + button_height + button_margin + button_height)
                cv2.rectangle(frame, end_button_top_left, end_button_bottom_right, button_color, -1)
                cv2.putText(frame, 'End', (end_button_top_left[0] + 40, end_button_top_left[1] + 25), font, 0.5, button_text_color, 1, cv2.LINE_AA)
               
               
                # Display the frame in a window
                cv2.imshow('Video Feed', frame)
                key = cv2.waitKey(50)

                if key == ord('q'):  # Quit if 'q' key is pressed
                    break

                elif key == ord('n'):  # Next question if 'n' key is pressed
                    question = random.choice(self.questions)

                elif key == ord('e'):  # End analysis if 'e' key is pressed
                    self.recording = False
                    # Update the latest analysis result
                    self.latest_analysis_results.append(result)
                    break
                result = self.analyze_frame(frame)
            audio_thread.join()
                # Store the result at 5-second intervals
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

