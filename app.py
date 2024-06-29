import streamlit as st
from dotenv import load_dotenv
import os
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound
import google.generativeai as genai
from googletrans import Translator, LANGUAGES
import yt_dlp
import logging
import speech_recognition as sr
from gtts import gTTS
from PIL import Image, ImageDraw, ImageFont
import moviepy.editor as mp
from moviepy.editor import AudioFileClip
# import firebase_admin
# from firebase_admin import credentials
import pyrebase
import requests
import time
import random

PICTORY_API_BASE_URL = "https://api.pictory.ai/pictoryapis/v1"
CLIENT_ID = "j9983f57c757ritr4f6foevt9"
CLIENT_SECRET = "AQICAHjtl6afq+Dz8KvujCJm3q4HNVx1a/BcrSNX03hZtWiWYAHgFUyO4CnSXTPk+3kOqnl4AAAAlTCBkgYJKoZIhvcNAQcGoIGEMIGBAgEAMHwGCSqGSIb3DQEHATAeBglghkgBZQMEAS4wEQQMn3M946kMa9W3fAOYAgEQgE82IbWzyYIQ63KXEoTSjjtOhqCkhlh4UNWK7/ZOnveh7azsKxBvylcinyKiP32PbzI3oieLXCtNHXwvRxcqYEE6tamKBl//FyZqr5ZpA0l8"
PICTORY_USER_ID = "MohammadImran"

save_path = "output/video.mp4"
def get_jobid(token,summary):
    url = "https://api.pictory.ai/pictoryapis/v1/video/storyboard"

    try:
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
        "Authorization":token,
        "content-type": "application/json",
        "X-Pictory-User-Id":PICTORY_USER_ID
}
        # st.write("in download")

        response = requests.post(url, json=payload, headers=headers)
        job_id = response.json().get("jobId")

        # st.write(job_id)
        response.raise_for_status()
        # with open(save_path, "wb") as file:
        #     file.write(response.content)
        return job_id
    except requests.exceptions.RequestException as e:
        print(f"Error downloading video: {e}")
        return None

# # Example usage
# video_url = "https://d3uryq9bhgb5qr.cloudfront.net/EnterpriseSubscription/PICTORY-USER-ID/702f8260-c56a-4fbc-9741-ddc44df24aa2/VIDEO/testvideo.mp4"


# Download video from URL to local file


def get_video_download_url(job_id, access_token):
    url = f'https://api.pictory.ai/pictoryapis/v1/jobs/{job_id}'
    headers = {
        "accept": "application/json",
        "Authorization":access_token,
        "X-Pictory-User-Id": PICTORY_USER_ID
        }

    try:
        response =requests.get(url, headers=headers)
        # response.raise_for_status()  # Raise exception for bad responses
        data =response.json()
        # st.write(data)
        if 'data' in data and 'preview' in data['data']:
                video_url = data['data']['preview']
                # st.write(video_url)
                return video_url
        else:
                raise KeyError("'preview' key not found in the response data")
    except requests.exceptions.HTTPError as err:
        print(f"HTTP Error occurred: {err}")
        return None
    
    
def get_pictory_access_token():
    token_url = "https://api.pictory.ai/pictoryapis/v1/oauth2/token"
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
        response.raise_for_status()  # Raise exception for bad responses
        token_data = response.json()
        access_token = token_data.get("access_token")
        if access_token:
            return access_token
        else:
            print("Failed to obtain access token.")
            return None

    except requests.exceptions.HTTPError as err:
        print(f"HTTP Error occurred: {err}")
        return None

def generate_video_with_pictory(summary, target_language): 
    try:
        token = get_pictory_access_token()
        # st.write(token)
        job_id = get_jobid(token,summary)
        # st.write(job_id)
        # Extract video URL from the response
        # video_url = response.json().get("videoURL")
        time.sleep(60)
        if job_id:
            video_url=get_video_download_url(job_id,token)
        # video_url="https://video.pictory.ai/preview/b99eb706-ad2d-452d-89dd-30fd20d1dd05"
        # st.write(video_url)
        if video_url:
            return video_url
        
    except requests.exceptions.RequestException as e:
        return f"Request Error: {e}"


# Function to generate video from summary
def generate_video(summary, target_language):
    text = summary
    tts = gTTS(text, lang=target_language)
    audio_path = 'output.mp3'
    tts.save(audio_path)
    if not os.path.exists(audio_path):
        return "Error generating audio file."
    images = ['output/image.png']
    
    def get_audio_duration_moviepy(audio_path):
        audio = AudioFileClip(audio_path)
        return audio.duration

    durations = [get_audio_duration_moviepy(audio_path)]
    clips = []
    for img, duration in zip(images, durations):
        img_clip = mp.ImageClip(img).set_duration(duration)
        clips.append(img_clip)
    video = mp.concatenate_videoclips(clips, method="compose")
    audio = mp.AudioFileClip(audio_path)
    video = video.set_audio(audio)
    video_path = 'output.mp4'
    video.write_videofile(video_path, codec="libx264", fps=24, audio_codec="aac")
    return video_path

# Function to download audio from YouTube
def download_audio(youtube_url, output_path):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
            'preferredquality': '192',
        }],
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
        if not os.path.exists(audio_file) and os.path.exists(audio_file + '.wav'):
            os.rename(audio_file + '.wav', audio_file)
    except Exception as e:
        logging.error(f"Error during download: {e}")
        return
    transcription = transcribe_audio(audio_file)
    if os.path.exists(audio_file):
        os.remove(audio_file)
    return transcription

# Load environment variables
load_dotenv()

# Firebase configuration for pyrebase
firebase_config = {
    "apiKey": os.getenv("FIREBASE_API_KEY"),
    "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN"),
    "databaseURL": os.getenv("FIREBASE_DATABASE_URL"),
    "projectId": os.getenv("FIREBASE_PROJECT_ID"),
    "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET"),
    "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
    "appId": os.getenv("FIREBASE_APP_ID"),
    # "measurementId": os.getenv("FIREBASE_MEASUREMENT_ID")
}

# Initialize pyrebase
firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
# Configure Generative AI
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Prompt for the generative model
prompt = """You are a YouTube video summarizer. You will be taking the transcript text
and summarizing the entire video and providing the important summary in points
within 250 words. Please provide the summary of the text given """

# Initialize Google Translate client
translator = Translator()

# Language codes mapping for user-friendly display
LANGUAGE_CODES = {name: code for code, name in LANGUAGES.items()}

# Function to extract transcript details
def extract_transcript_details(youtube_video_url):
    try:
        video_id = youtube_video_url.split("v=")[1]
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        transcript_text = None
        first_transcript = next(iter(transcript_list))
        transcript_text = first_transcript.fetch()
        if not transcript_text:
            raise NoTranscriptFound("Transcript not found for the selected language.")
        transcript = " ".join([t["text"] for t in transcript_text])
        return transcript
    except NoTranscriptFound as e:
        return main(youtube_video_url)
    except Exception as e:
        return main(youtube_video_url)

# Function to generate content with generative AI
def generate_gemini_content(transcript_text, prompt, target_language_code, question_type):
    try:
        model = genai.GenerativeModel("gemini-pro")
        question_prompt = "Provide questions and answers" if question_type == "Q&A" else "Provide multiple choice questions"
        response = model.generate_content(prompt + f" and translate the summary into the {LANGUAGES.get(target_language_code)} language and also {question_prompt} on it in the translated language only before displaying and do not display the summary in transcript language" + transcript_text)
        return response.text
    except Exception as e:
        st.error("Error occurred while generating notes.")
        st.error(str(e))
        return None
    
# ////////////////////////////////////////////////////////////////////////////
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

def generate_answers(questions):
    answer_prompt = f"Provide answers for the following questions: {questions}"
    model = "models/text-bison-001"
    try:
        response = genai.generate_text(
            model=model,
            prompt=answer_prompt,
            temperature=0.2,
            candidate_count=1,
            top_k=40,
            top_p=0.95
        )
        answers = response.candidates[0]['output']
        return answers
    except Exception as e:
        st.error(f"Error generating answers: {e}")
        return None


# Streamlit UI
st.title("Video Summarizer")

# Authentication mode selector
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    auth_mode = st.selectbox("Select Authentication Mode:", ["Login", "Sign Up"])
    
    if auth_mode == "Login":
        st.subheader("Login")
        username = st.text_input("Email")
        password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            try:
                user = auth.sign_in_with_email_and_password(username, password)
                st.session_state["authenticated"] = True
                st.session_state['user_email'] = user['email']
                st.success("Login successful!")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Login failed: {e}")

    else:  # Sign Up form
        st.subheader("Sign Up")
        new_username = st.text_input("Email")
        new_password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        if new_password != confirm_password:
            st.warning("Passwords do not match.")
        else:
            if st.button("Sign Up"):
                try:
                    user = auth.create_user_with_email_and_password(new_username, new_password)
                    st.success("Sign up successful! Please login.")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Sign up failed: {e}")

if st.session_state["authenticated"]:
    if 'questions_and_answers' not in st.session_state:
        st.session_state.questions_and_answers = []
    if 'show_answers' not in st.session_state:
        st.session_state.show_answers = False
    st.write(f"Logged in as: {st.session_state.get('user_email')}")
    youtube_link = st.text_input("Enter Video Link:")
    target_language = st.selectbox("Select Target Language for Translation:", options=list(LANGUAGE_CODES.keys()))
    question_type = st.selectbox("Select Type of Questions:", options=["Q&A", "MCQ"])

    if st.button("Get Detailed Notes"):
        if youtube_link:
            video_id = youtube_link.split("v=")[1]
            target_language_code = LANGUAGE_CODES.get(target_language, "en")
            transcript_text = extract_transcript_details(youtube_link)
            if transcript_text:
                summary = generate_gemini_content(transcript_text, prompt, target_language_code, question_type)
                if summary:
                    st.session_state["summary"] = summary
                    st.markdown("## Detailed Notes:")
                    st.write(summary)
                    st.session_state.questions_and_answers = generate_questions_and_answers(summary)
                    st.session_state.show_answers = False

       
    if st.session_state.questions_and_answers:
        st.write("### Generated Questions:")
        user_answers = []
        for idx, qa in enumerate(st.session_state.questions_and_answers):
            st.write(f"*Q{idx+1}:* {qa['question']}")
            user_answer = st.text_input(f"Your Answer {idx+1}", key=f"user_answer_{idx}")
            user_answers.append(user_answer)

        check_answers_button = st.button("Check Answers")

        if check_answers_button:
            st.session_state.show_answers = True

        if st.session_state.show_answers:
            st.write("### Correct Answers:")
            for idx, qa in enumerate(st.session_state.questions_and_answers):
                st.write(f"*Q{idx+1}:* {qa['question']}")
                st.write(f"*A{idx+1}:* {qa['answer']}")
# Streamlit UI for generating questions and checking answers

    # fsdfsdfffffffffffffffffffffffffff
    if st.button("Generate Video"):
            st.info("Generating video... Please wait.")
            target_language_code = LANGUAGE_CODES.get(target_language, "en")
            video_path=generate_video_with_pictory(st.session_state["summary"], target_language)
            # video_path = generate_video(summary, target_language_code)
            if video_path:
                st.session_state["video_path"] = video_path
                print(video_path)
                st.success("Video generated successfully!")
                st.write(video_path)
                response = requests.head(video_path, allow_redirects=True)
                direct_video_url = response.url
                with requests.get(direct_video_url, stream=True) as r:
                    r.raise_for_status()
                    with open("temp_video.mp4", "wb") as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                            temp_video_path = f.name
                
                # st.video(temp_video_path)

    # if "video_path" in st.session_state:
    #     video_path = st.session_state["video_path"]
    #     with open(video_path, "rb") as gile:
    #         btn = st.download_button(
    #             label="Download Video",
    #             data=file,
    #             file_name="summary_video.mp4",
    #             mime="video/mp4"
    #         )

    if st.button("Logout"):
        st.session_state["authenticated"] = False
        st.experimental_rerun()