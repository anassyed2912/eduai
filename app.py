import streamlit as st
from dotenv import load_dotenv
import os
import google.generativeai as genai
from googletrans import Translator, LANGUAGES
import yt_dlp
import logging
import speech_recognition as sr
from gtts import gTTS
import moviepy.editor as mp
from moviepy.editor import AudioFileClip
import pyrebase
import requests
import time
import random

# Load environment variables
load_dotenv()

# Set constants from environment variables
PICTORY_API_BASE_URL = os.getenv("PICTORY_API_BASE_URL")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
PICTORY_USER_ID = os.getenv("PICTORY_USER_ID")
save_path = "output/video.mp4"

# Function to get job ID from Pictory API
def get_jobid(token, summary):
    url = f"{PICTORY_API_BASE_URL}/video/storyboard"
    payload = {
        "audio": {
            "aiVoiceOver": {
                "speaker": "Jackson",
                "speed": "100",
                "amplifyLevel": "0"
            },
            "autoBackgroundMusic": True,
            "backGroundMusicVolume": 0.5
        },
        "videoName": "output",
        "language": "en",
        "scenes": [
            {
                "text": summary,
                "voiceOver": True,
                "splitTextOnNewLine": True,
                "splitTextOnPeriod": True
            }
        ]
    }
    headers = {
        "accept": "application/json",
        "Authorization": token,
        "content-type": "application/json",
        "X-Pictory-User-Id": PICTORY_USER_ID
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        job_id = response.json().get("jobId")
        return job_id
    except requests.exceptions.RequestException as e:
        logging.error(f"Error getting job ID: {e}")
        return None

# Function to get video download URL from Pictory API
def get_video_download_url(job_id, access_token):
    url = f'{PICTORY_API_BASE_URL}/jobs/{job_id}'
    headers = {
        "accept": "application/json",
        "Authorization": access_token,
        "X-Pictory-User-Id": PICTORY_USER_ID
    }
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        video_url = data.get('data', {}).get('preview')
        if video_url:
            return video_url
        else:
            logging.error("'preview' key not found in the response data")
            return None
    except requests.exceptions.HTTPError as err:
        logging.error(f"HTTP Error occurred: {err}")
        return None

# Function to get Pictory access token
def get_pictory_access_token():
    token_url = f"{PICTORY_API_BASE_URL}/oauth2/token"
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
    try:
        response = requests.post(token_url, json=data, headers=headers)
        response.raise_for_status()
        token_data = response.json()
        access_token = token_data.get("access_token")
        if access_token:
            return access_token
        else:
            logging.error("Failed to obtain access token.")
            return None
    except requests.exceptions.HTTPError as err:
        logging.error(f"HTTP Error occurred: {err}")
        return None

# Function to generate video with Pictory
def generate_video_with_pictory(summary, target_language): 
    try:
        token = get_pictory_access_token()
        if token:
            job_id = get_jobid(token, summary)
            if job_id:
                # Wait for job completion with periodic checks
                for _ in range(30):  # Poll every 10 seconds for up to 5 minutes
                    time.sleep(10)
                    video_url = get_video_download_url(job_id, token)
                    if video_url:
                        return video_url
            else:
                logging.error("Failed to get job ID")
    except requests.exceptions.RequestException as e:
        logging.error(f"Request Error: {e}")
        return None

# Function to generate video from summary
def generate_video(summary, target_language):
    try:
        tts = gTTS(summary, lang=target_language)
        audio_path = 'output.mp3'
        tts.save(audio_path)

        images = ['output/image.png']
        durations = [AudioFileClip(audio_path).duration]
        clips = [mp.ImageClip(img).set_duration(duration) for img, duration in zip(images, durations)]

        video = mp.concatenate_videoclips(clips, method="compose")
        audio = mp.AudioFileClip(audio_path)
        video = video.set_audio(audio)
        video_path = 'output.mp4'
        video.write_videofile(video_path, codec="libx264", fps=24, audio_codec="aac")
        return video_path
    except Exception as e:
        logging.error(f"Error generating video: {e}")
        return None

# Function to download audio from YouTube
def download_audio(youtube_url, output_path):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'wav', 'preferredquality': '192'}],
        'outtmpl': output_path.rsplit('.', 1)[0],
        'ffmpeg_location': '/opt/homebrew/bin/ffmpeg',
        'nocheckcertificate': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])
    except Exception as e:
        logging.error(f"Error downloading audio: {e}")
        raise

# Function to transcribe audio
def transcribe_audio(audio_file):
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_file) as source:
        audio_data = recognizer.record(source)
    try:
        transcription = recognizer.recognize_sphinx(audio_data)
        return transcription
    except sr.UnknownValueError:
        return "Speech recognition could not understand audio"
    except sr.RequestError as e:
        return f"Speech recognition error: {e}"

# Main function to handle YouTube URL
def main(youtube_url):
    audio_file = 'audio.wav'
    try:
        download_audio(youtube_url, audio_file)
        if os.path.exists(audio_file) or os.path.exists(audio_file + '.wav'):
            if os.path.exists(audio_file + '.wav'):
                os.rename(audio_file + '.wav', audio_file)
            transcription = transcribe_audio(audio_file)
            os.remove(audio_file)
            return transcription
    except Exception as e:
        logging.error(f"Error during download or transcription: {e}")
        return None

# Firebase configuration for pyrebase
firebase_config = {
    "apiKey": os.getenv("FIREBASE_API_KEY"),
    "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN"),
    "databaseURL": os.getenv("FIREBASE_DATABASE_URL"),
    "projectId": os.getenv("FIREBASE_PROJECT_ID"),
    "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET"),
    "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
    "appId": os.getenv("FIREBASE_APP_ID"),
}

# Initialize pyrebase
firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()

# Configure Generative AI
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Initialize Google Translate client
translator = Translator()

# Function to generate varied questions and answers from summary
def generate_questions_and_answers(summary, num_questions=10):
    sentences = summary.split('.')
    questions_and_answers = []
    question_types = [
        "Explain the significance of the following point: {sentence}",
        "What might be the consequences of this point: {sentence}?",
        "What details support this point: {sentence}?",
        "What are the broader implications of this point: {sentence}?",
        "Can you provide an example related to this point: {sentence}?",
        "What is your opinion about this point: {sentence}?"
    ]

    for i in range(min(num_questions, len(sentences))):
        sentence = sentences[i].strip()
        if sentence:
            question_template = random.choice(question_types)
            question = question_template.format(sentence=sentence)
            # Generate a more elaborate answer
            if "significance" in question:
                answer = f"This point is important because it highlights the value and usefulness of learning how to {sentence.lower()}."
            elif "consequences" in question:
                answer = f"If you understand this point, you will be able to {sentence.lower()} more effectively, which can lead to better communication and understanding in Finnish."
            elif "details support" in question:
                answer = f"The main details that support this point are the practical applications and examples given on how to {sentence.lower()} in different contexts."
            elif "broader implications" in question:
                answer = f"The broader implications of this point include improved cultural awareness and the ability to engage more deeply with Finnish speakers."
            elif "example" in question:
                answer = f"An example related to this point would be a situation where you need to {sentence.lower()} while traveling in Finland."
            elif "opinion" in question:
                answer = f"My opinion about this point is that learning to {sentence.lower()} is crucial for anyone looking to effectively communicate in Finnish and understand the nuances of the language."

            questions_and_answers.append({"question": question, "answer": answer})

    return questions_and_answers

# Set up the Streamlit app
st.set_page_config(page_title="YouTube Video Summarizer", page_icon=":movie_camera:", layout="wide")
st.title("YouTube Video Summarizer")                

st.sidebar.title("Language Selection")
target_language = st.sidebar.selectbox("Select the target language", options=list(LANGUAGES.keys()), format_func=lambda lang: LANGUAGES[lang].capitalize())

# Sign Up form
st.sidebar.title("Sign Up")
email = st.sidebar.text_input("Email")
password = st.sidebar.text_input("Password", type="password")
confirm_password = st.sidebar.text_input("Confirm Password", type="password")
sign_up = st.sidebar.button("Sign Up")

if sign_up:
    if password == confirm_password:
        try:
            user = auth.create_user_with_email_and_password(email, password)
            st.sidebar.success("User account created successfully!")
        except Exception as e:
            st.sidebar.error(f"Error creating user account: {e}")
    else:
        st.sidebar.error("Passwords do not match")

# Sign In form
st.sidebar.title("Sign In")
login_email = st.sidebar.text_input("Login Email")
login_password = st.sidebar.text_input("Login Password", type="password")
sign_in = st.sidebar.button("Sign In")

if sign_in:
    try:
        user = auth.sign_in_with_email_and_password(login_email, login_password)
        st.sidebar.success("Successfully signed in!")
    except Exception as e:
        st.sidebar.error(f"Error signing in: {e}")

# YouTube URL input
youtube_url = st.text_input("Enter YouTube URL")
generate_summary_button = st.button("Generate Summary")

# Initialize session state variables
if 'questions_and_answers' not in st.session_state:
    st.session_state.questions_and_answers = []
if 'show_answers' not in st.session_state:
    st.session_state.show_answers = False

if generate_summary_button:
    if youtube_url:
        transcription = main(youtube_url)
        if transcription:
            st.subheader("Transcription")
            st.write(transcription)
            st.subheader("Summary")
            prompt_text = f"You are a YouTube video summarizer. You will be taking the transcript text and summarizing the entire video and providing the important summary in points within 250 words. Please provide the summary of the text given: {transcription}"
            response = genai.generate_text(prompt=prompt_text, max_output_tokens=1024)
            summary = response.candidates[0]['output']
            st.write(summary)

            st.session_state.questions_and_answers = generate_questions_and_answers(summary)
            st.session_state.show_answers = False
        else:
            st.error("Could not generate summary. Please check the YouTube URL and try again.")
    else:
        st.error("Please enter a valid YouTube URL.")

if st.session_state.questions_and_answers:
    st.write("### Generated Questions:")
    user_answers = []
    for idx, qa in enumerate(st.session_state.questions_and_answers):
        st.write(f"**Q{idx+1}:** {qa['question']}")
        user_answer = st.text_input(f"Your Answer {idx+1}", key=f"user_answer_{idx}")
        user_answers.append(user_answer)

    check_answers_button = st.button("Check Answers")

    if check_answers_button:
        st.session_state.show_answers = True

    if st.session_state.show_answers:
        st.write("### Correct Answers:")
        for idx, qa in enumerate(st.session_state.questions_and_answers):
            st.write(f"**Q{idx+1}:** {qa['question']}")
            st.write(f"**A{idx+1}:** {qa['answer']}")
