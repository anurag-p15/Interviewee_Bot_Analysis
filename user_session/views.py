import datetime
import threading
from django.http import HttpResponse,JsonResponse
from django.urls import reverse
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
import webbrowser
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from django.shortcuts import render
from .models import InterviewResult
from datetime import datetime


#Camera views
class VideoAnalyzer:
    def __init__(self):
        self.recording = False
        self.video_capture = None
        self.latest_analysis_results = []
        self.questions = []
        self.user_answers = []
        self.expected_answers = []
        self.resolution = (1300, 1300)
        self.audio_thread=None
        self.web_page_opened=False

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
                        'Question': row['Question'],
                        'Expected Answer': row['Expected Answer']
                    }
                    questions.append(question_data)
        except Exception as e:
            print(f"Error loading questions from CSV: {e}")
        print("Loaded questions:", len(questions))
        return questions
    
    def filter_questions_by_domain(self, domain):
        filtered_questions = [question for question in self.questions if question['Domain'] == domain]
        return filtered_questions 
    
    
    def start_analysis(self, domain, num_questions_to_show, username):
        print("Starting analysis for domain:", domain)  # Debug statement
        self.recording = True
        self.questions = []
        self.user_answers = []
        self.expected_answers = []
        self.questions = self.load_questions_from_csv('questions_dataset.csv')
        filtered_questions = self.filter_questions_by_domain(domain)
        threading.Thread(target=self.analyze_video, args=(filtered_questions, domain,num_questions_to_show, username)).start()



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
        
        


    def analyze_audio(self,timeout=30):
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
        self.user_answers.append(text)
        return sentence
    
    
    def analyze_video(self,questions,domain,num_questions_to_show,username): 
        if not questions:
            print("No questions available for analysis.")
            return
        
        self.web_page_opened = False
        self.questions.clear()
        self.user_answers.clear()
        self.expected_answers.clear()
        self.latest_analysis_results.clear()
    
        self.video_capture = cv2.VideoCapture(0)
        self.video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
        self.video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
        counter=0
        question=random.choice(questions)
        question_text = question['Question']
        self.questions.append(question['Question'])
        print(self.questions)
        expected_answer = self.get_expected_answer(question_text)  # Pass question text as argument
        self.expected_answers.append(expected_answer)
        self.audio_thread=Thread(target=self.analyze_audio)
        self.audio_thread.start()
        
        
        # Initialize a list to store user answers
        user_answers = []
        
        while self.recording:
            
            ret, frame = self.video_capture.read()
            
            # self.questions.append(question['Question'])

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
                button_margin = 10
                button_width = 150

                # Draw the white rectangle background

                # Define background color and text color
                background_color = (0, 119, 204)  # BGR color for #F77700 (orange)
                text_color = (0, 0, 0)  # Black

                 # Calculate text size
                text_size = cv2.getTextSize(str(question), font, font_scale, font_thickness)[0]
                while text_size[0] > frame.shape[1] - 2 * button_width - 4 * button_margin:
                    font_scale -= 0.1
                    text_size = cv2.getTextSize(question_text, font, font_scale, font_thickness)[0]

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

                if key == ord('q'):  # Quit if 'q' key is pressedr
                    break
                elif key == ord('e'):  # End analysis if 'e' key is pressed
                    self.recording = False
                    break
                elif (counter > num_questions_to_show):
                    self.recording = False
                    break
                elif (key == ord('n') and counter < num_questions_to_show):
                    counter += 1
                    if (counter > num_questions_to_show):
                        self.recording = False
                    question = random.choice(questions)
                    question_text = question['Question']
                    self.questions.append(question_text)
                    expected_answer = self.get_expected_answer(question_text)  # Pass question text as argument
                    self.expected_answers.append(expected_answer)
                    user_answer = self.analyze_audio()
                    if user_answer is not None:
                        user_answers.append(user_answer)
                # Start a new audio analysis thread for the next question
                    self.audio_thread = Thread(target=self.analyze_audio)
                    self.audio_thread.start()
                
                # Analyze frame and append results to latest_analysis_results
                analysis_result = self.analyze_frame(frame)
                if analysis_result is not None:
                    self.latest_analysis_results.append(analysis_result)
                    
        self.video_capture.release()
        cv2.destroyAllWindows()
        self.print_results(domain,username)
        
        
        
    def get_expected_answer(self, question_text):
        expected_answer = None
        try:
            with open('questions_dataset.csv', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    csv_question_text = row['Question'].strip().lower()  # Strip whitespace and convert to lowercase
                    #print("Question from CSV:", csv_question_text)  # Debug print
                    #print("Question passed as argument:", question_text.strip().lower())  # Debug print
                    if csv_question_text == question_text.strip().lower():
                        expected_answer = row['Expected Answer']
                        break
        except Exception as e:
            print(f"Error fetching expected answer from CSV: {e}")
        return expected_answer


        
        
    def print_results(self,domain, username):
        results = []
        #username
        #domain
        #num questions
        #time
        #video vala ka result
        for idx, (question, user_answer, expected_answer) in enumerate(zip(self.questions, self.user_answers, self.expected_answers), start=1):
            result = {
                "index": idx,
                "question": question,
                "user_answer": user_answer,
                "expected_answer": expected_answer
            }
            results.append(result)
        
        # After collecting all results, attempt to open the web browser
        if not self.web_page_opened:
            try:
                result_pie_url = f"http://localhost:8000/user_session/result_pie/{username}/{domain}/"
                webbrowser.open(result_pie_url)
                self.web_page_opened = True
            except Exception as e:
                print(f"Failed to redirect to result_pie view: {e}")

        return results



    def get_average_emotion(self):
        if not self.latest_analysis_results:
            return None

    # Initialize average emotion dictionary with initial values
        average_emotion = {
        'angry': 0,
        'disgust': 0,
        'fear': 0,
        'happy': 0,
        'sad': 0,
        'surprise': 0,
        'neutral': 0
        }

        num_results = len(self.latest_analysis_results)

        for result in self.latest_analysis_results:
            try:
                if 'emotion' in result[0]:  # Check if 'emotion' key exists in the result
                    emotions = result[0]['emotion']
                    for emotion in emotions:
                        average_emotion[emotion] += emotions[emotion]
            except KeyError:
                print("Face not detected")

    # Calculate average emotion scores
        if num_results > 0:
            for emotion in average_emotion:
                average_emotion[emotion] /= num_results

        return average_emotion


# Initialize the VideoAnalyzer
video_analyzer = VideoAnalyzer()


def calculate_cosine_similarity(text1, text2):
    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform([text1, text2])
    similarity = cosine_similarity(vectors)
    return similarity[0][1]


#User Session
def register(request):
    if request.method == 'POST':
        name=request.POST.get('name')
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

            user = User(username=username, password=hashed_password, bio=bio,name=name)
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
            request.session['username'] = username  # Store the username in the session
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
    if user_data:
        # Fetch past interview data for the logged-in user
        past_interviews = InterviewResult.objects.filter(username=user_data['username'])
        # Pass the past interviews data to the template context
        context = {
            'past_interviews': past_interviews
        }
        return render(request, 'past_interviews.html', context)
    else:
        # Redirect to login page if user not logged in
        messages.error(request, 'Please login to access the dashboard.')
        return redirect('user_session:login')


def view_past_attempt_results(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        domain = request.POST.get('domain')
        completion_time_str = request.POST.get('completion_time')
        num_questions=request.POST.get('num_questions')
        # No need to parse completion_time_str since it's already in ISO8601 format
        
        try:
            interview_results = InterviewResult.objects.filter(username=username, domain=domain,num_questions=num_questions)
            
            # Iterate over each interview result
            for interview_result in interview_results:
                emotion_data = interview_result.emotion_data
                bar_chart_data = interview_result.bar_chart_data
                date = completion_time_str  # Assign the ISO8601 date string directly
                return render(request, 'past_attempts.html', {
                    'interview_result': interview_result,
                    'emotion_data': emotion_data,
                    'bar_chart_data': bar_chart_data,
                    'date': date  # Pass completion_time_str to the template
                })      
        except InterviewResult.DoesNotExist:
            # Handle case where interview result does not exist
            pass
    # Handle other HTTP methods or form submission failure
    return render(request, 'error_page.html', {'message': 'Failed to fetch interview details'})


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
    try:
        user_data = request.session.get('user')
        if user_data:
            username = user_data.get('username')
            if request.method == 'POST':
                domain = request.POST.get('domain')  # Retrieve the domain from POST data
                num_questions = request.POST.get('numQuestions')

                # Check if both domain and num_questions are provided
                if domain and num_questions:
                    num_questions = int(num_questions)

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
                        video_analyzer.start_analysis(domain, num_questions, username)

                        return render(request, 'interview.html', {'message': 'Analysis started successfully'})
                    else:
                        # If domain is null or number of questions is 0, show an error message
                        return render(request, 'interview.html', {'error_message': 'Please select a proper domain and specify the number of questions.'})
                else:
                    # If either domain or number of questions is not provided, show an error message
                    return render(request, 'interview.html', {'error_message': 'Please select both a domain and specify the number of questions.'})
            else:
                # If the request method is not POST, redirect to dashboard or wherever appropriate
                return render(request, 'interview.html', {'error_message': 'Invalid request method.'})
        else:
            # If user is not logged in, redirect to login page
            return redirect('user_session:login')
    except Exception as e:
        # Log or handle the exception appropriately
        return render(request, 'interview.html', {'error_message': 'An error occurred: {}'.format(str(e))})
        
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

def result_pie_view(request,username,domain):
    # Extract the username from the request if the user is authenticated
    analysis_results = video_analyzer.print_results(domain,username)
    average_emotion = video_analyzer.get_average_emotion()
    emotion_data = {
        'labels': list(average_emotion.keys()),
        'data': list(average_emotion.values())
    }
    
    similarity_scores = []
    for user_answer, expected_answer in zip(video_analyzer.user_answers, video_analyzer.expected_answers):
        similarity = calculate_cosine_similarity(user_answer, expected_answer)
        similarity_scores.append(similarity)
    
    bar_chart_data = {
        'labels': [f"Question {i+1}" for i in range(len(similarity_scores))],
        'data': similarity_scores
    }
    
    # Save the data to MongoDB
    interview_result = InterviewResult(
        username=username,  # Save the username here
        domain=domain, # Replace with the actual domain
        num_questions=len(video_analyzer.questions),
        analysis_results=analysis_results,
        emotion_data=emotion_data,
        bar_chart_data=bar_chart_data
    )
    print("Username before saving:", username)  # Debug print
    interview_result.save()
    
    return render(request, 'resultpie.html', {
        'analysis_results': analysis_results,
        'emotion_data': emotion_data,
        'bar_chart_data': bar_chart_data
    })

    
@require_POST
def clear_analysis_results(request):
    # Clear the analysis results
    video_analyzer.latest_analysis_results = []
    return JsonResponse({'message': 'Analysis results cleared successfully'})

