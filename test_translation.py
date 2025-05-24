from shared_state import translate_and_speak

def test_translation():
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
            print("\nTranslation failed!")

if __name__ == "__main__":
    print("Translation Test Script")
    print("----------------------")
    test_translation()
