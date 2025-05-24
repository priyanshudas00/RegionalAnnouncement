import dwani
import os
import sys
import hashlib
from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_cors import CORS  # Add CORS support for local development
from bhashaseva_enhanced import AnnouncementSystem, Announcement, PriorityLevel, DeliveryChannel, AnnouncementType, LANGUAGE_CODE_MAP
from shared_state import translate_and_speak
import threading
from datetime import datetime
import json
import time
import uuid

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__, static_folder='.', template_folder='pages')

# Set API key and base URL
dwani.api_key = os.getenv("DWANI_API_KEY")
dwani.api_base = os.getenv("DWANI_API_BASE_URL")

# Initialize the announcement system
announcement_system = AnnouncementSystem()

# Background thread for processing announcements
def process_announcements():
    while True:
        announcement_system.process_queue()
        time.sleep(1)  # Prevent excessive CPU usage

# Start the background thread
announcement_thread = threading.Thread(target=process_announcements, daemon=True)
announcement_thread.start()

@app.route('/')
def serve_admin():
    """Serve the admin interface"""
    return send_from_directory('.', 'index.html')

@app.route('/announcements')
def serve_announcements():
    """Serve the language-specific announcements page"""
    return send_from_directory('pages', 'language_announcements.html')

@app.route('/public')
def serve_public():
    """Serve the public announcements page"""
    return send_from_directory('pages', 'public_announcements.html')

@app.route('/pages/announcement_submission.html')
def serve_announcement_submission():
    """Serve the announcement submission page"""
    return send_from_directory('pages', 'announcement_submission.html')

@app.route('/api/announcements', methods=['GET'])
def get_announcements():
    try:
        with open('announcement_logs.json', 'r') as f:
            announcements = json.load(f)
        return jsonify(announcements)
    except FileNotFoundError:
        return jsonify([])

@app.route('/api/announcements/<timestamp>', methods=['DELETE'])
def delete_announcement(timestamp):
    """Delete an announcement by its timestamp"""
    try:
        # Read current announcements
        with open('announcement_logs.json', 'r') as f:
            announcements = json.load(f)
        
        # Filter out the announcement with matching timestamp
        filtered_announcements = [a for a in announcements if a['timestamp'] != timestamp]
        
        # If no announcements were filtered out, return 404
        if len(filtered_announcements) == len(announcements):
            return jsonify({
                'status': 'error',
                'message': 'Announcement not found'
            }), 404
        
        # Write back the filtered announcements
        with open('announcement_logs.json', 'w') as f:
            json.dump(filtered_announcements, f, indent=2)
        
        return jsonify({
            'status': 'success',
            'message': 'Announcement deleted successfully'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/announcements', methods=['POST'])
def create_announcement():
    try:
        data = request.json
        
        # Map priority levels
        priority_map = {
            'urgent': PriorityLevel.EMERGENCY,
            'high': PriorityLevel.HEALTH_ALERT,
            'general': PriorityLevel.GENERAL
        }
        
        # Map announcement types
        type_map = {
            'emergency': AnnouncementType.WEATHER_ALERT,
            'health': AnnouncementType.HEALTH,
            'welfare': AnnouncementType.WELFARE,
            'general': AnnouncementType.GENERAL
        }
        
        # Create Announcement object
        announcement = Announcement(
            text=data['announcementText'],
            src_lang=data['sourceLanguage'],
            target_langs=data['targetLanguages'],
            channels=[DeliveryChannel.VOICE] if data.get('enableAudio') else [],
            priority=priority_map.get(data['priority'], PriorityLevel.GENERAL),
            announcement_type=type_map.get(data['announcementType'], AnnouncementType.GENERAL),
            districts=data['districts'],
            metadata={
                'timestamp': datetime.now().isoformat(),
                'type': data['announcementType']
            }
        )
        
        # Queue the announcement
        announcement_system.translate_and_deliver(announcement)
        
        return jsonify({'status': 'success', 'message': 'Announcement queued for processing'})
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/audio/<path:filename>')
def serve_audio(filename):
    """Serve audio files"""
    # Remove 'announcements/' from the start of the filename if it exists
    if filename.startswith('announcements/'):
        filename = filename.replace('announcements/', '', 1)
    return send_from_directory('announcements', filename)

def translate_and_speak(text, src_lang="english", tgt_lang="kannada"):
    try:
        # Convert language names to codes
        src_code = LANGUAGE_CODE_MAP[src_lang.lower()]
        tgt_code = LANGUAGE_CODE_MAP[tgt_lang.lower()]
        
        # Step 1: Translate the text
        translation = dwani.Translate.run_translate(
            sentences=[text],
            src_lang=src_code,
            tgt_lang=tgt_code
        )
        print(f"Raw translation response: {translation}")
        
        # Extract translated text
        if isinstance(translation, dict) and "translations" in translation and translation["translations"]:
            translated_text = translation["translations"][0]
        elif isinstance(translation, str):
            translated_text = translation
        else:
            raise ValueError("Invalid translation response format")

        if not translated_text:
            raise ValueError("Empty translation result")

        print(f"Translated Text: {translated_text}")

        # Step 2: Convert translated text to speech
        response = dwani.Audio.speech(input=translated_text, response_format="mp3")
        
        if response and isinstance(response, (bytes, bytearray)) and len(response) > 0:
            # Generate unique filename
            hash_value = hashlib.md5(translated_text.encode()).hexdigest()[:10]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"voice_{timestamp}_{hash_value}_{tgt_lang}.mp3"
            filepath = os.path.join("announcements", filename)
            
            # Ensure announcements directory exists
            os.makedirs("announcements", exist_ok=True)
            
            # Save audio file
            with open(filepath, "wb") as f:
                f.write(response)
            print(f"Speech synthesis complete: saved to {filepath}")
            
            return translated_text, filename
            
        return translated_text, None

    except Exception as e:
        print(f"Error in Translate and Speech module: {e}")

@app.route('/test')
def serve_test():
    """Serve the translation test interface"""
    return send_from_directory('pages', 'test_translation.html')

@app.route('/api/test-translation', methods=['POST'])
def test_translation():
    """Handle translation test requests"""
    try:
        data = request.json
        text = data['text']
        src_lang = data['srcLang']
        tgt_lang = data['tgtLang']

        # Use the translate_and_speak function from test_dwani.py
        from test_dwani import translate_and_speak
        translated_text, audio_file = translate_and_speak(text, src_lang, tgt_lang)

        if translated_text:
            return jsonify({
                'status': 'success',
                'translatedText': translated_text,
                'audioFile': audio_file
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Translation failed'
            }), 400

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/translate-announcement', methods=['POST'])
def translate_announcement():
    """Handle translation requests with audio generation"""
    try:
        data = request.json
        text = data['text']
        src_lang = data['srcLang']
        tgt_lang = data['tgtLang']
        
        # Validate input
        if not text.strip():
            raise ValueError("Translation text cannot be empty")        # Validate languages against supported languages
        src_lang = src_lang.lower()
        tgt_lang = tgt_lang.lower()
        
        if src_lang not in LANGUAGE_CODE_MAP:
            raise ValueError(f"Invalid source language: {src_lang}")
        if tgt_lang not in LANGUAGE_CODE_MAP:
            raise ValueError(f"Invalid target language: {tgt_lang}")

        # Use the translate_and_speak function
        translated_text, audio_file = translate_and_speak(text, src_lang, tgt_lang)
        
        if translated_text and audio_file:
            return jsonify({
                'status': 'success',
                'translatedText': translated_text,
                'audioFile': audio_file
            })
        else:
            raise ValueError("Translation or audio generation failed")
            
    except ValueError as e:
        print(f"Validation error in translation endpoint: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
    except Exception as e:
        print(f"Error in translation endpoint: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/process-voice', methods=['POST'])
def process_voice():
    """Process recorded voice and generate audio response"""
    try:
        # Get audio file and language from request
        audio_file = request.files.get('audio')
        language = request.form.get('language')
        
        if not audio_file or not language:
            return jsonify({
                'status': 'error',
                'message': 'Missing audio file or language'
            }), 400
            
        # Generate a unique filename
        filename = f"voice_{int(time.time())}_{uuid.uuid4().hex[:8]}.mp3"
        filepath = os.path.join('announcements', filename)
        
        # Save the uploaded audio temporarily
        temp_filepath = os.path.join('announcements', 'temp_' + filename)
        audio_file.save(temp_filepath)
        
        # Process using dwani
        try:
            # Convert to text using speech recognition
            with open(temp_filepath, 'rb') as f:
                audio_bytes = f.read()
            
            text_response = dwani.Speech.recognize(
                audio=audio_bytes,
                language=language
            )
            
            if not text_response or not text_response.get('text'):
                raise Exception('Speech recognition failed')
                
            recognized_text = text_response['text']
            
            # Generate audio response
            audio_response = dwani.Audio.speech(
                input=recognized_text,
                response_format="mp3"
            )
            
            if audio_response and isinstance(audio_response, (bytes, bytearray)):
                with open(filepath, "wb") as f:
                    f.write(audio_response)
            else:
                raise Exception('Audio generation failed')
            
            return jsonify({
                'status': 'success',
                'audioFile': filename,
                'text': recognized_text
            })
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_filepath):
                os.remove(temp_filepath)
                
    except Exception as e:
        print(f"Error processing voice: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
