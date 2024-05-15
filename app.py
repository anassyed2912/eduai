# import streamlit as st
# from dotenv import load_dotenv
# import os
# from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound
# import google.generativeai as genai

# load_dotenv()  # Load environment variables

# genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# prompt = """You are YouTube video summarizer. You will be taking the transcript text
# and summarizing the entire video and providing the important summary in points
# within 250 words. Please provide the summary of the text given here:"""

# # Language codes mapping for user-friendly display
# LANGUAGE_CODES = {
#     "English": "en",
#     "Spanish": "es",
#     "French": "fr",
#     "German": "de",
#     "Chinese": "zh",
#     "Hindi": "hi",
#     # Add more languages as needed
# }

# def extract_transcript_details(youtube_video_url, language_code):
#     try:
#         video_id = youtube_video_url.split("v=")[1]
#         transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

#         transcript_text = None
#         for transcript in transcript_list:
#             if transcript.language_code == language_code:
#                 transcript_text = transcript.fetch()
#                 break

#         if not transcript_text:
#             raise NoTranscriptFound("Transcript not found for the selected language.")
        
#         transcript = " ".join([t["text"] for t in transcript_text])
#         return transcript

#     except NoTranscriptFound as e:
#         st.error(f"No transcript found for the video in {language_code}.")
#     except Exception as e:
#         st.error("Error occurred while fetching transcript. Please check the video URL.")
#         st.error(str(e))

# def generate_gemini_content(transcript_text, prompt):
#     try:
#         model = genai.GenerativeModel("gemini-pro")
#         response = model.generate_content(prompt + transcript_text)
#         return response.text
#     except Exception as e:
#         st.error("Error occurred while generating notes.")
#         st.error(str(e))

# st.title("YouTube Transcript to Detailed Notes Converter")

# youtube_link = st.text_input("Enter YouTube Video Link:")
# language = st.selectbox("Select Transcript Language:", options=list(LANGUAGE_CODES.keys()))

# if st.button("Get Detailed Notes"):
#     if youtube_link:
#         video_id = youtube_link.split("v=")[1]
#         st.image(f"http://img.youtube.com/vi/{video_id}/0.jpg", use_column_width=True)
#         language_code = LANGUAGE_CODES.get(language, "en")
#         transcript_text = extract_transcript_details(youtube_link, language_code)

#         if transcript_text:
#             summary = generate_gemini_content(transcript_text, prompt)
#             if summary:
#                 st.markdown("## Detailed Notes:")
#                 st.write(summary)





import streamlit as st
from dotenv import load_dotenv
import os
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound
import google.generativeai as genai
from googletrans import Translator, LANGUAGES

# Load environment variables
load_dotenv()

# Configure Generative AI
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Prompt for the generative model
prompt = """You are YouTube video summarizer. You will be taking the transcript text
and summarizing the entire video and providing the important summary in points
within 250 words. Please provide the summary of the text given here:"""

# Initialize Google Translate client
translator = Translator()

# Language codes mapping for user-friendly display
LANGUAGE_CODES = {name: code for code, name in LANGUAGES.items()}

def extract_transcript_details(youtube_video_url, language_code):
    try:
        video_id = youtube_video_url.split("v=")[1]
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

        transcript_text = None
        for transcript in transcript_list:
            if transcript.language_code == language_code:
                transcript_text = transcript.fetch()
                break

        if not transcript_text:
            raise NoTranscriptFound("Transcript not found for the selected language.")
        
        transcript = " ".join([t["text"] for t in transcript_text])
        return transcript

    except NoTranscriptFound as e:
        st.error(f"No transcript found for the video in {LANGUAGES.get(language_code, 'the selected language')}.")
        return None
    except Exception as e:
        st.error("Error occurred while fetching transcript. Please check the video URL.")
        st.error(str(e))
        return None


def translate_to_english(text):
    try:
        if not text:
            raise ValueError("No text provided for translation.")
        
        summary = generate_gemini_content(text, prompt)
        
        # Debug: Print text to be translated
        # st.write("Original Transcript Text: ", summary)
        
        translated = translator.translate(summary, dest='en')
        
        # Debug: Print translated text
        st.write("Translated Text: ", translated.text)
        
        if translated and translated.text:
            return translated.text
        else:
            raise ValueError("Translation returned no text.")
    except Exception as e:
        # st.error("Error occurred while translating transcript.")
        # st.error(str(e))
        return None



def generate_gemini_content(transcript_text, prompt):
    try:
        model = genai.GenerativeModel("gemini-pro")
        
        # Debug: Print prompt and transcript text
        # st.write("Prompt: ", prompt)
        # st.write("Transcript Text: ", transcript_text)
        
        response = model.generate_content(prompt + transcript_text)
        
        # Debug: Print generated content
        st.write("Generated Content: ", response.text)
        
        return response.text
    except Exception as e:
        st.error("Error occurred while generating notes.")
        st.error(str(e))
        return None

# Streamlit UI
st.title("YouTube Transcript to Detailed Notes Converter")

youtube_link = st.text_input("Enter YouTube Video Link:")
language = st.selectbox("Select Transcript Language:", options=list(LANGUAGE_CODES.keys()))

if st.button("Get Detailed Notes"):
    if youtube_link:
        video_id = youtube_link.split("v=")[1]
        st.image(f"http://img.youtube.com/vi/{video_id}/0.jpg", use_column_width=True)
        language_code = LANGUAGE_CODES.get(language, "en")
        transcript_text = extract_transcript_details(youtube_link, language_code)

        if transcript_text:
            if language_code != 'en':
                transcript_text = translate_to_english(transcript_text)
            if language_code == 'en':
                summary = generate_gemini_content(transcript_text, prompt)
                if summary:
                    st.markdown("## Detailed Notes:")
                    st.write(summary)
