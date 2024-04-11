import threading
from django.http import HttpResponse,JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import redirect, render
from django.contrib.auth.hashers import make_password,check_password
from .models import User
from django.contrib import messages
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



#Camera views
class VideoAnalyzer:
    def __init__(self):
        self.recording = False
        self.video_capture = None
        self.latest_analysis_results = []
        self.resolution = (1300, 1300)
        self.audio_thread=None

    def set_resolution(self, resolution):
        self.resolution = resolution

    def load_questions_from_csv(self, csv_file):
        questions = []
        try:
            with open(csv_file, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    question_data = {
                        'Domain': row['Domain'],
                        'Question': row['Question']
                    }
                    questions.append(question_data)
        except Exception as e:
            print(f"Error loading questions from CSV: {e}")
        print("Loaded questions:", len(questions))
        return questions
    
    def filter_questions_by_domain(self, domain):
        filtered_questions = [question for question in self.questions if question['Domain'] == domain]
        return filtered_questions 
    
    def start_analysis(self, domain,num_questions_to_show):
        print("Starting analysis for domain:", domain)  # Debug statement
        self.recording = True
        self.questions = self.load_questions_from_csv('questions_dataset.csv')
        filtered_questions = self.filter_questions_by_domain(domain)
        threading.Thread(target=self.analyze_video, args=(filtered_questions, num_questions_to_show)).start()


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
            record_audio=recognizer.listen(source,timeout=60)
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
    
    
    def analyze_video(self,questions,num_questions_to_show): 
        if not questions:
            print("No questions available for analysis.")
            return
        
        self.video_capture = cv2.VideoCapture(0)
        self.video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
        self.video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
        counter=0
        question=random.choice(questions)
        self.audio_thread=Thread(target=self.analyze_audio)
        self.audio_thread.start()
        
        
        while self.recording:
            
            ret, frame = self.video_capture.read()

            if ret:
                font=cv2.FONT_HERSHEY_COMPLEX
                bottom_center=(frame.shape[1]//2,frame.shape[0]-10)
                bottom_left_corner=(10, frame.shape[0] - 10)
                font_scale = 1
                font_thickness = 2
                
                
                # hello_message = "Hello!"
                text_size = cv2.getTextSize(str(question), font, font_scale, font_thickness)[0]

                # Calculate the position for the rectangle background
                background_position = (bottom_center[0] - text_size[0] // 2 - 5, bottom_center[1] - text_size[1] + 5)
                background_size = (text_size[0] + 10, text_size[1] + 10)

                # Draw the white rectangle background

                # Define background color and text color
                background_color = (0, 119, 204)  # BGR color for #F77700 (orange)
                text_color = (0, 0, 0)  # Black

                 # Calculate text size
                text_size = cv2.getTextSize(str(question), font, font_scale, font_thickness)[0]

                # Calculate background rectangle position and size
                background_position = (bottom_left_corner[0], bottom_left_corner[1] - text_size[1] - 5)
                background_size = (1300, text_size[1] + 80)  # Add some padding

                # Draw filled rectangle as background
                cv2.rectangle(frame, background_position, (background_position[0] + background_size[0], background_position[1] + background_size[1]), background_color, -1)

                # Draw text on top of background rectangle
                cv2.putText(frame, question['Question'], (bottom_left_corner[0], bottom_left_corner[1] - 5), font, font_scale, text_color, font_thickness, cv2.LINE_AA)


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
                key = cv2.waitKey(5)

                if key == ord('q'):  # Quit if 'q' key is pressed
                    break
                elif key == ord('e'):  # End analysis if 'e' key is pressed
                    self.recording = False
                    break
                elif (counter >= num_questions_to_show):
                    self.recording = False
                    break
                elif (key == ord('n') and counter < num_questions_to_show):
                    counter += 1  # Next question if 'n' key is pressed
                    question = random.choice(questions)
                    if self.audio_thread and self.audio_thread.is_alive():
                        self.audio_thread.join()  # Wait for the previous audio analysis to finish
                    self.audio_thread = Thread(target=self.analyze_audio)
                    self.audio_thread.start()
                    continue
                
                result = self.analyze_frame(frame)
                
                # Store the result at 5-second intervals
                self.latest_analysis_results.append(result)

        self.video_capture.release()
        cv2.destroyAllWindows()
        self.print_results()
        
    def print_results(self):
        print("Interview Analysis Results:")
        for idx, result in enumerate(self.latest_analysis_results, start=1):
            print(f"Result {idx}: {result}")

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
@csrf_exempt
def start_analysis_view(request):
    user_data = request.session.get('user')
    if user_data:
        if request.method == 'POST':
            domain = request.POST.get('domain')  # Retrieve the domain from POST data
            num_questions = int(request.POST.get('numQuestions'))

            # Check if the selected domain is not null
            if domain != 'null' and num_questions > 0:
                # Set the resolution based on domain
                if domain == 'engineering':
                    video_analyzer.set_resolution((1920, 1080))
                elif domain == 'bba':
                    video_analyzer.set_resolution((1280, 720))
                elif domain == 'finance':
                    video_analyzer.set_resolution((640, 480))
                elif domain == 'management':
                    video_analyzer.set_resolution((800, 600))

                # Start the analysis with the provided domain
                video_analyzer.start_analysis(domain, num_questions)  # Pass the domain and num_questions_to_show

                return render(request, 'interview.html', {'message': 'Analysis started successfully'})
            else:
                # If domain is null or number of questions is 0, show an error message
                messages.error(request, 'Please select a domain and specify the number of questions.')
                return render('interview.html')  # Redirect to dashboard or wherever appropriate
        else:
            # If the request method is not POST, redirect to dashboard or wherever appropriate
            messages.error(request, 'Invalid request method.')
            return redirect('user_session:start_analysis')  # Redirect to dashboard or wherever appropriate
    else:
        # If user is not logged in, redirect to login page
        messages.error(request, 'Please login to access the analysis feature.')
        return redirect('user_session:login')
    
@csrf_exempt
def check_analysis_result(request):
    # Wait until the analysis is complete
    while video_analyzer.recording:
        time.sleep(1)

    # Fetch the latest analysis results
    analysis_results = video_analyzer.latest_analysis_results

    # Get average emotion and audio sentiment
    average_emotion = video_analyzer.get_average_emotion()
    audio_sentiment = video_analyzer.analyze_audio()

    if analysis_results:
        # Pass the analysis results to the template
        return render(request, 'result.html', {'analysis_results': analysis_results, 'average_emotion': average_emotion, 'audio_sentiment': audio_sentiment})
    else:
        return JsonResponse({"html_result": "You have not logged in !! Login to Continue !!"}, safe=False)

    
@require_POST
def clear_analysis_results(request):
    # Clear the analysis results
    video_analyzer.latest_analysis_results = []
    return JsonResponse({'message': 'Analysis results cleared successfully'})

