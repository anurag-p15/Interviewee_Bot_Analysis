# video_analyzer/views.py
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import json
from threading import Thread
import cv2
import time
from deepface import DeepFace

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
def start_interview(request):
    return render(request, 'interview.html')

@csrf_exempt
def start_analysis_view(request):
    result = video_analyzer.start_analysis()
    return HttpResponse()

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
        return JsonResponse({"html_result": "No analysis result available yet."}, safe=False)
