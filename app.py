# import streamlit as st
# from dotenv import load_dotenv
# import os
# from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound
# import google.generativeai as genai
# from googletrans import Translator, LANGUAGES
# import yt_dlp
# import logging
# import speech_recognition as sr
# from gtts import gTTS
# from PIL import Image, ImageDraw, ImageFont
# import moviepy.editor as mp
# from moviepy.editor import AudioFileClip

# def generate_video(summary):
#     text = summary

#     # Generate audio from text with a different language/voice
#     tts = gTTS(text, lang='ur')  # 'en-au' for Australian English accent
#     audio_path = 'output.mp3'
#     tts.save(audio_path)

#     # Verify audio file is created correctly
#     if not os.path.exists(audio_path):
#         return "Error generating audio file."

#     # Use the specified images
#     images = ['output/image.png']
#     def get_audio_duration_moviepy(audio_path):
#         audio = AudioFileClip(audio_path)
#         return audio.duration

#     # Set duration for each image (in seconds)
#     durations = [get_audio_duration_moviepy(audio_path)]  # Adjust the durations as needed

#     # Create video from images and audio
#     clips = []
#     for img, duration in zip(images, durations):
#         img_clip = mp.ImageClip(img).set_duration(duration)
#         clips.append(img_clip)

#     video = mp.concatenate_videoclips(clips, method="compose")
#     print("clips done")

#     # Load the audio file
#     audio = mp.AudioFileClip(audio_path)

#     # Set the audio on the video
#     video = video.set_audio(audio)
#     print("audio done")

#     video_path = 'output.mp4'
#     video.write_videofile(video_path, codec="libx264", fps=24, audio_codec="aac")

#     return video_path

# def download_audio(youtube_url, output_path):
#     ydl_opts = {
#         'format': 'bestaudio/best',
#         'postprocessors': [{
#             'key': 'FFmpegExtractAudio',
#             'preferredcodec': 'wav',
#             'preferredquality': '192',
#         }],
#         'outtmpl': output_path.rsplit('.', 1)[0],  # Remove the extension from outtmpl
#         'ffmpeg_location': 'C:/ProgramData/chocolatey/bin/',  # Update this path to the correct location of ffmpeg
#         'nocheckcertificate': True,  # Bypass SSL verification
#     }
#     try:
#         with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#             ydl.download([youtube_url])
#     except Exception as e:
#         logging.error(f"Error downloading audio: {e}")
#         raise

# def transcribe_audio(audio_file):
#     recognizer = sr.Recognizer()
#     with sr.AudioFile(audio_file) as source:
#         audio_data = recognizer.record(source)
#     try:
#         transcription = recognizer.recognize_sphinx(audio_data)
#         print("transcription done")
#         return transcription
#     except sr.UnknownValueError:
#         return "Speech recognition could not understand audio"
#     except sr.RequestError as e:
#         return f"Speech recognition error: {e}"

# def main(youtube_url):
#     audio_file = 'audio.wav'
    
#     # Download the audio from YouTube
#     try:
#         download_audio(youtube_url, audio_file)
#         # Ensure the file has the correct extension after download
#         if not os.path.exists(audio_file) and os.path.exists(audio_file + '.wav'):
#             os.rename(audio_file + '.wav', audio_file)
#     except Exception as e:
#         logging.error(f"Error during download: {e}")
#         return

#     # Transcribe the downloaded audio
#     transcription = transcribe_audio(audio_file)
#     print("Transcription:", transcription)
   
#     # Clean up the audio file
#     if os.path.exists(audio_file):
#         os.remove(audio_file)
#     return transcription

# # Load environment variables
# load_dotenv()

# # Configure Generative AI
# genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# # Prompt for the generative model
# prompt = """You are a YouTube video summarizer. You will be taking the transcript text
# and summarizing the entire video and providing the important summary in points
# within 250 words. Please provide the summary of the text given """

# # Initialize Google Translate client
# translator = Translator()

# # Language codes mapping for user-friendly display
# LANGUAGE_CODES = {name: code for code, name in LANGUAGES.items()}

# def extract_transcript_details(youtube_video_url):
#     try:
#         video_id = youtube_video_url.split("v=")[1]
#         transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

#         transcript_text = None
#         first_transcript = next(iter(transcript_list))
#         transcript_text = first_transcript.fetch()

#         if not transcript_text:
#             raise NoTranscriptFound("Transcript not found for the selected language.")
        
#         transcript = " ".join([t["text"] for t in transcript_text])
#         return transcript

#     except NoTranscriptFound as e:
#         return main(youtube_video_url)
#     except Exception as e:
#         return main(youtube_video_url)

# def generate_gemini_content(transcript_text, prompt, target_language_code, question_type):
#     try:
#         model = genai.GenerativeModel("gemini-pro")
        
#         question_prompt = "Provide questions and answers" if question_type == "Q&A" else "Provide multiple choice questions"
#         response = model.generate_content(prompt + f" and translate the summary into the {LANGUAGES.get(target_language_code)} language and also {question_prompt} on it in the translated language only before displaying and do not display the summary in transcript language" + transcript_text)
        
#         return response.text
#     except Exception as e:
#         st.error("Error occurred while generating notes.")
#         st.error(str(e))
#         return None

# # Streamlit UI
# st.title("YouTube Transcript to Detailed Notes Converter")

# youtube_link = st.text_input("Enter YouTube Video Link:")
# target_language = st.selectbox("Select Target Language for Translation:", options=list(LANGUAGE_CODES.keys()))
# question_type = st.selectbox("Select Type of Questions:", options=["Q&A", "MCQ"])

# if st.button("Get Detailed Notes"):
#     if youtube_link:
#         video_id = youtube_link.split("v=")[1]
#         target_language_code = LANGUAGE_CODES.get(target_language, "en")
#         transcript_text = extract_transcript_details(youtube_link)

#         if transcript_text:
#             summary = generate_gemini_content(transcript_text, prompt, target_language_code, question_type)
#             if summary:
#                 st.session_state["summary"] = summary
#                 st.markdown("## Detailed Notes:")
#                 st.write(summary)

# if "summary" in st.session_state:
#     summary = st.session_state["summary"]
#     st.markdown("## Detailed Notes:")
#     st.write(summary)
#     if st.button("Generate Video"):
#         st.info("Generating video... Please wait.")
#         video_path = generate_video(summary)
#         if video_path and os.path.exists(video_path):
#             st.success("Video generated successfully!")
#             st.video(video_path)
#             with open(video_path, "rb") as file:
#                 btn = st.download_button(
#                     label="Download Video",
#                     data=file,
#                     file_name="summary_video.mp4",
#                     mime="video/mp4"
#                 )
#         else:
#             st.error("Error generating video.")

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

def generate_video(summary,target_language):
    text = summary

    # Generate audio from text with a different language/voice
    tts = gTTS(text, lang=target_language)  # 'en-au' for Australian English accent
    audio_path = 'output.mp3'
    tts.save(audio_path)

    # Verify audio file is created correctly
    if not os.path.exists(audio_path):
        return "Error generating audio file."

    # Use the specified images
    images = ['output/image.png']
    def get_audio_duration_moviepy(audio_path):
        audio = AudioFileClip(audio_path)
        return audio.duration

    # Set duration for each image (in seconds)
    durations = [get_audio_duration_moviepy(audio_path)]  # Adjust the durations as needed

    # Create video from images and audio
    clips = []
    for img, duration in zip(images, durations):
        img_clip = mp.ImageClip(img).set_duration(duration)
        clips.append(img_clip)

    video = mp.concatenate_videoclips(clips, method="compose")
    print("clips done")

    # Load the audio file
    audio = mp.AudioFileClip(audio_path)

    # Set the audio on the video
    video = video.set_audio(audio)
    print("audio done")

    video_path = 'output.mp4'
    video.write_videofile(video_path, codec="libx264", fps=24, audio_codec="aac")

    return video_path

def download_audio(youtube_url, output_path):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
            'preferredquality': '192',
        }],
        'outtmpl': output_path.rsplit('.', 1)[0],  # Remove the extension from outtmpl
        'ffmpeg_location': 'C:/ProgramData/chocolatey/bin/',  # Update this path to the correct location of ffmpeg
        'nocheckcertificate': True,  # Bypass SSL verification
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])
    except Exception as e:
        logging.error(f"Error downloading audio: {e}")
        raise

def transcribe_audio(audio_file):
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_file) as source:
        audio_data = recognizer.record(source)
    try:
        transcription = recognizer.recognize_sphinx(audio_data)
        print("transcription done")
        return transcription
    except sr.UnknownValueError:
        return "Speech recognition could not understand audio"
    except sr.RequestError as e:
        return f"Speech recognition error: {e}"

def main(youtube_url):
    audio_file = 'audio.wav'
    
    # Download the audio from YouTube
    try:
        download_audio(youtube_url, audio_file)
        # Ensure the file has the correct extension after download
        if not os.path.exists(audio_file) and os.path.exists(audio_file + '.wav'):
            os.rename(audio_file + '.wav', audio_file)
    except Exception as e:
        logging.error(f"Error during download: {e}")
        return

    # Transcribe the downloaded audio
    transcription = transcribe_audio(audio_file)
    print("Transcription:", transcription)
   
    # Clean up the audio file
    if os.path.exists(audio_file):
        os.remove(audio_file)
    return transcription

# Load environment variables
load_dotenv()

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

# Streamlit UI
st.title("YouTube Transcript to Detailed Notes Converter")

youtube_link = st.text_input("Enter YouTube Video Link:")
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

if "summary" in st.session_state:
    summary = st.session_state["summary"]
    st.markdown("## Detailed Notes:")
    st.write(summary)
    if st.button("Generate Video"):
        st.info("Generating video... Please wait.")
        target_language_code = LANGUAGE_CODES.get(target_language, "en")
        video_path = generate_video(summary,target_language_code)
        if video_path and os.path.exists(video_path):
            st.session_state["video_path"] = video_path
            st.success("Video generated successfully!")
            st.video(video_path)

if "video_path" in st.session_state:
    video_path = st.session_state["video_path"]
    with open(video_path, "rb") as file:
        btn = st.download_button(
            label="Download Video",
            data=file,
            file_name="summary_video.mp4",
            mime="video/mp4"
        )
