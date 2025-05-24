import streamlit as st
import json
from datetime import datetime
import os
import glob
import time
import dwani
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bhashaseva_enhanced import LANGUAGE_CODE_MAP
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set API key and base URL
dwani.api_key = os.getenv("DWANI_API_KEY")
dwani.api_base = os.getenv("DWANI_API_BASE_URL")

MAX_RETRIES = 10
RETRY_DELAY = 2  # seconds between retries
CONNECTION_TIMEOUT = 30  # seconds

# Configure retry strategy for requests
retry_strategy = Retry(
    total=3,  # number of retries
    backoff_factor=0.5,  # wait 0.5, 1, 2... seconds between retries
    status_forcelist=[500, 502, 503, 504, 429]  # HTTP status codes to retry on
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session = requests.Session()
session.mount("http://", adapter)
session.mount("https://", adapter)

def translate_and_speak(text, src_lang="english", tgt_lang="kannada"):
    """Translate text and generate audio using Dwani API with retries"""
    for attempt in range(MAX_RETRIES):
        try:
            # Add delay between attempts
            if attempt > 0:
                delay = RETRY_DELAY * (2 ** attempt)  # exponential backoff
                print(f"Waiting {delay} seconds before attempt {attempt + 1}")
                time.sleep(delay)
                print(f"\nAttempt {attempt + 1}/{MAX_RETRIES}:")
            # Step 1: Translate the text
            src_code = LANGUAGE_CODE_MAP[src_lang.lower()]
            tgt_code = LANGUAGE_CODE_MAP[tgt_lang.lower()]
            print(f"Translating from {src_lang} ({src_code}) to {tgt_lang} ({tgt_code})...")
            translation = dwani.Translate.run_translate(
                sentences=[text],
                src_lang=src_code,
                tgt_lang=LANGUAGE_CODE_MAP[tgt_lang],
                timeout=CONNECTION_TIMEOUT
            )
            print(f"Raw translation response: {translation}")
              # Handle different response formats from Dwani API
            translated_text = None
            if translation == 0:
                print("Translation API returned 0, retrying...")
                continue
            elif isinstance(translation, dict):
                if "translations" in translation and isinstance(translation["translations"], list):
                    if len(translation["translations"]) > 0:
                        translated_text = translation["translations"][0]
                    else:
                        print("Empty translations list in response")
                elif "translation" in translation:
                    translated_text = translation["translation"]
                else:
                    print(f"Unexpected dictionary format: {translation}")
            elif isinstance(translation, list):
                if len(translation) > 0:
                    translated_text = translation[0]
                else:
                    print("Empty list in response")
            elif isinstance(translation, str):
                translated_text = translation
            else:
                print(f"Unexpected response type: {type(translation)}")

            if not translated_text:
                print("Could not extract translation, retrying...")
                continue

            print(f"Translated Text: {translated_text}")            # Step 2: Convert translated text to speech
            print("Generating audio...")
            
            # Try different parameter combinations for audio generation
            audio_attempts = [
                lambda: dwani.Audio.speech(input=translated_text, response_format="mp3"),
                lambda: dwani.Audio.speech(text=translated_text, response_format="mp3"),
                lambda: dwani.Audio.speech(input=translated_text, format="mp3"),
                lambda: dwani.Audio.speech(text=translated_text, format="mp3")
            ]
            
            response = None
            for audio_func in audio_attempts:
                try:
                    response = audio_func()
                    if response and isinstance(response, (bytes, bytearray)) and len(response) > 0:
                        break
                except Exception as e:
                    print(f"Audio generation attempt failed: {e}")
                    continue
            
            if response and isinstance(response, (bytes, bytearray)) and len(response) > 0:
                # Save audio file
                timestamp = int(datetime.now().timestamp())
                filename = f"announcements/voice_{timestamp}.mp3"
                os.makedirs("announcements", exist_ok=True)
                
                with open(filename, "wb") as f:
                    f.write(response)
                print("Speech synthesis complete: saved to", filename)
                
                return translated_text, filename
            else:
                print("Audio generation failed, retrying...")
                continue

        except (ConnectionError, ConnectionResetError, requests.exceptions.ConnectionError) as e:
            print(f"Connection error on attempt {attempt + 1}: {str(e)}")
            if attempt < MAX_RETRIES - 1:
                continue
            print("Max connection retries reached.")
        except Exception as e:
            print(f"Unexpected error on attempt {attempt + 1}: {str(e)}")
            if attempt < MAX_RETRIES - 1:
                continue
            print("Max retries reached.")
    
    return None, None

def save_announcement(announcement_data):
    """Save announcement with translations and audio files"""
    try:
        # Add timestamp if not present
        if 'timestamp' not in announcement_data:
            announcement_data['timestamp'] = datetime.now().isoformat()
            
        # Generate translations and audio for each target language
        translations = {}
        audio_paths = {}
        
        st.write("🔄 Starting translations and audio generation...")
        progress_bar = st.progress(0)
        
        for i, lang in enumerate(announcement_data.get('target_langs', [])):
            st.write(f"🌐 Processing {lang.title()}...")
            trans_text, audio_path = translate_and_speak(
                announcement_data['text'],
                announcement_data['source_lang'],
                lang
            )
            
            if trans_text:
                translations[lang] = trans_text
                st.success(f"✅ Translation successful for {lang.title()}")
                
                if audio_path:
                    audio_paths[lang] = audio_path
                    st.success(f"✅ Audio generated for {lang.title()}")
                else:
                    st.warning(f"⚠️ Audio generation failed for {lang.title()}")
            else:
                st.error(f"❌ Translation failed for {lang.title()}")
            
            # Update progress
            progress_bar.progress((i + 1) / len(announcement_data.get('target_langs', [])))
        
        # Add translations and audio paths to announcement data
        announcement_data['translations'] = translations
        announcement_data['audio_paths'] = audio_paths
        
        # Load existing announcements
        announcements = []
        if os.path.exists('announcement_logs.json'):
            with open('announcement_logs.json', 'r', encoding='utf-8') as f:
                announcements = json.load(f)
        
        # Add new announcement
        announcements.append(announcement_data)
        
        # Save updated announcements
        with open('announcement_logs.json', 'w', encoding='utf-8') as f:
            json.dump(announcements, f, ensure_ascii=False, indent=2)
        
        st.success("✅ Announcement saved successfully!")
        return True
        
    except Exception as e:
        st.error(f"❌ Error saving announcement: {str(e)}")
        return False

def cleanup_temp_files(keep_last_n=10):
    """Cleanup temporary audio files, keeping the n most recent files"""
    try:
        # Keep track of audio files referenced in announcements
        audio_files = set()
        announcements = get_announcements()
        
        for announcement in announcements:
            for audio_path in announcement.get('audio_paths', {}).values():
                audio_files.add(audio_path)
        
        # Remove unused audio files
        for file in glob.glob('announcements/*.mp3'):
            if file not in audio_files:
                try:
                    os.remove(file)
                except:
                    pass
    except Exception as e:
        print(f"Error cleaning up temp files: {str(e)}")

def get_announcements():
    """Get all announcements"""
    try:
        if os.path.exists('announcement_logs.json'):
            with open('announcement_logs.json', 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading announcements: {str(e)}")
    return []

def initialize_session_state():
    """Initialize shared session state variables"""
    if 'notifications' not in st.session_state:
        st.session_state.notifications = get_announcements()
    if 'preferred_languages' not in st.session_state:
        st.session_state.preferred_languages = ["english"]
    if 'last_update' not in st.session_state:
        st.session_state.last_update = datetime.now()
    if 'enable_audio' not in st.session_state:
        st.session_state.enable_audio = True
    if 'enable_emergency' not in st.session_state:
        st.session_state.enable_emergency = True
    if 'enable_health' not in st.session_state:
        st.session_state.enable_health = True
