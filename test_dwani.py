import os
import dwani
from dotenv import load_dotenv
import hashlib
from datetime import datetime

# Load environment variables
load_dotenv()

# Set API key and base URL
dwani.api_key = os.getenv("DWANI_API_KEY")
dwani.api_base = os.getenv("DWANI_API_BASE_URL")

def translate_and_speak(text, src_lang="english", tgt_lang="kannada"):
    """
    Translate text and generate audio using Dwani API.
    Returns: tuple (translated_text, audio_file_path)
    """
    try:
        # Step 1: Translate the text
        print(f"\nTranslating from {src_lang} to {tgt_lang}...")
        translation = dwani.Translate.run_translate(
            sentences=[text],
            src_lang=src_lang,
            tgt_lang=tgt_lang
        )
        print(f"Raw translation response: {translation}")

        # Extract translated text
        translated_text = None
        if isinstance(translation, dict) and "translations" in translation and translation["translations"]:
            translated_text = translation["translations"][0]
        elif isinstance(translation, str):
            translated_text = translation
        
        if not translated_text:
            print("Translation failed")
            return None, None

        print(f"Translated Text: {translated_text}")

        # Step 2: Convert translated text to speech
        print("\nGenerating audio...")
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
            
            return translated_text, filepath
        else:
            print("Audio generation failed")
            return translated_text, None

    except Exception as e:
        print(f"Error in Translate and Speech module: {e}")
        return None, None

def test_translation():
    """Interactive testing of translation and speech synthesis"""
    print("Translation and Speech Test")
    print("=========================")
    print("\nAvailable languages: kannada, hindi, tamil, telugu, marathi, bengali, gujarati, malayalam, punjabi")
    
    while True:
        # Get input from user
        text = input("\nEnter Announcement Text (or 'q' to quit): ")
        if text.lower() == 'q':
            break
        
        # Get source language
        src_lang = input("Enter source language: ").lower() or "english"
        
        # Get target language
        tgt_lang = input("Enter target language (default: kannada): ").lower() or "kannada"
        
        # Perform translation
        print("\nTranslating...")
        translated_text, audio_file = translate_and_speak(text, src_lang, tgt_lang)
        
        if translated_text:
            print(f"\nTranslation successful!")
            print(f"Original ({src_lang}): {text}")
            print(f"Translated ({tgt_lang}): {translated_text}")
            if audio_file:
                print(f"Audio file saved as: {audio_file}")
            else:
                print("Audio generation failed")
        else:
            print("\nTranslation failed!")

if __name__ == "__main__":
    test_translation()
