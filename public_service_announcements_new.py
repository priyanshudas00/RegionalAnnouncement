import app
import time
import json
import os
from datetime import datetime
from shared_state import save_announcement, add_audio_path

LANGUAGE_CODE_MAP = {
    "kannada": "kan_Knda",
    "hindi": "hin_Deva",
    "tamil": "tam_Taml",
    "telugu": "tel_Telu",
    "marathi": "mar_Deva",
    "english": "eng_Latn"  # Added English for completeness
}

# Announcement types and their priorities
ANNOUNCEMENT_TYPES = {
    "emergency": 1,
    "health": 2,
    "general": 3
}

def announce_in_languages(text, src_lang="english", target_langs=None, announcement_type="general", max_retries=3, retry_delay=5):
    """
    Translate and generate speech for the given text in multiple target languages.
    
    Args:
        text (str): The text to translate and speak.
        src_lang (str): Source language of the text.
        target_langs (list): List of target languages to translate and generate speech.
        announcement_type (str): Type of announcement (emergency/health/general).
        max_retries (int): Number of retries for rate limit or connection errors.
        retry_delay (int): Delay in seconds between retries.
    
    Returns:
        dict: Announcement data including translations and audio paths
    """
    if target_langs is None:
        target_langs = ["kannada", "hindi", "tamil", "telugu", "marathi"]

    # Create announcement data
    announcement_data = {
        "timestamp": datetime.now().isoformat(),
        "text": text,
        "source_lang": src_lang,
        "target_langs": target_langs,
        "type": announcement_type.title(),
        "urgency": "High" if announcement_type == "emergency" else "Normal",
        "audio_paths": {},
        "translations": {}
    }

    # Save announcement first to get it in the system
    save_announcement(announcement_data)

    audio_dir = "audio_cache"
    os.makedirs(audio_dir, exist_ok=True)

    for lang in target_langs:
        print(f"\nProcessing announcement in {lang}...")
        tgt_lang_code = LANGUAGE_CODE_MAP.get(lang, lang)
        retries = 0
        
        while retries <= max_retries:
            try:
                # First translate the text
                translation = app.dwani.Translate.run_translate(
                    sentences=[text],
                    src_lang=LANGUAGE_CODE_MAP[src_lang],
                    tgt_lang=tgt_lang_code
                )
                
                if translation and isinstance(translation, dict) and "translations" in translation:
                    translated_text = translation["translations"][0]
                    announcement_data["translations"][lang] = translated_text
                    
                    # Then generate audio
                    audio_data = app.dwani.Audio.speech(
                        input=translated_text,
                        response_format="mp3"
                    )
                    
                    if audio_data:
                        # Save audio file
                        audio_path = os.path.join(audio_dir, f"announcement_{announcement_data['timestamp']}_{lang}.mp3")
                        with open(audio_path, "wb") as f:
                            f.write(audio_data)
                            
                        # Update audio path in announcement
                        announcement_data["audio_paths"][lang] = audio_path
                        add_audio_path(announcement_data["timestamp"], lang, audio_path)
                        
                        print(f"✓ Successfully processed {lang} translation and audio")
                        break  # success, exit retry loop
                        
            except Exception as e:
                error_msg = str(e)
                if "Rate limit exceeded" in error_msg or "ConnectionResetError" in error_msg:
                    retries += 1
                    if retries > max_retries:
                        print(f"Failed after {max_retries} retries: {error_msg}")
                        announcement_data["errors"] = announcement_data.get("errors", {})
                        announcement_data["errors"][lang] = error_msg
                        break
                    print(f"Error: {error_msg}. Retrying in {retry_delay} seconds... (Attempt {retries}/{max_retries})")
                    time.sleep(retry_delay)
                else:
                    print(f"Error in Translate and Speech module: {error_msg}")
                    announcement_data["errors"] = announcement_data.get("errors", {})
                    announcement_data["errors"][lang] = error_msg
                    break
    
    # Save final announcement state
    save_announcement(announcement_data)
    return announcement_data

def make_announcement(text, announcement_type="general", src_lang="english", target_langs=None):
    """
    High-level function to create and broadcast an announcement
    
    Args:
        text (str): The announcement text
        announcement_type (str): Type of announcement (emergency/health/general)
        src_lang (str): Source language
        target_langs (list): Target languages
    
    Returns:
        dict: Announcement data with translations and audio paths
    """
    # Validate announcement type
    if announcement_type not in ANNOUNCEMENT_TYPES:
        raise ValueError(f"Invalid announcement type. Must be one of: {list(ANNOUNCEMENT_TYPES.keys())}")
    
    # Validate languages
    if src_lang not in LANGUAGE_CODE_MAP:
        raise ValueError(f"Invalid source language. Must be one of: {list(LANGUAGE_CODE_MAP.keys())}")
    
    if target_langs:
        invalid_langs = [lang for lang in target_langs if lang not in LANGUAGE_CODE_MAP]
        if invalid_langs:
            raise ValueError(f"Invalid target language(s): {invalid_langs}")
    
    # Create announcement
    result = announce_in_languages(
        text=text,
        src_lang=src_lang,
        target_langs=target_langs,
        announcement_type=announcement_type
    )
    
    return result

if __name__ == "__main__":
    print("🔊 BhashaSeva Public Service Announcement System")
    print("=" * 50)
    
    # Get announcement details
    announcement_type = input("Enter announcement type (emergency/health/general): ").lower()
    announcement_text = input("Enter announcement text: ")
    src_lang = input("Enter source language (default: english): ") or "english"
    
    # Get target languages
    print("\nAvailable languages:", ", ".join(LANGUAGE_CODE_MAP.keys()))
    target_input = input("Enter target languages (comma-separated, leave empty for all): ")
    target_langs = [lang.strip() for lang in target_input.split(",")] if target_input else None
    
    try:
        result = make_announcement(
            text=announcement_text,
            announcement_type=announcement_type,
            src_lang=src_lang,
            target_langs=target_langs
        )
        
        print("\n✅ Announcement processed successfully!")
        print(f"Timestamp: {result['timestamp']}")
        print(f"Type: {result['type']}")
        print(f"Languages processed: {len(result.get('translations', {}))}")
        
        if "errors" in result:
            print("\n⚠️ Some languages had errors:")
            for lang, error in result["errors"].items():
                print(f"- {lang}: {error}")
                
    except Exception as e:
        print(f"\n❌ Error creating announcement: {str(e)}")
