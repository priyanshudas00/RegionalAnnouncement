"""
Test script to demonstrate the complete announcement flow:
1. Create an announcement
2. Translate it to multiple languages
3. Generate audio files
4. Save to JSON
5. Verify it appears in the web interface
"""

import requests
import json
from time import sleep

def test_announcement_flow():
    # Test announcement data
    announcement_data = {
        "announcementText": "Important: COVID-19 vaccination drive starting tomorrow at all primary health centers. Free for all citizens above 18 years.",
        "sourceLanguage": "english",
        "targetLanguages": ["kannada", "hindi", "tamil"],
        "announcementType": "health",
        "priority": "high",
        "districts": ["Bengaluru", "Chennai"],
        "enableAudio": True
    }

    print("\nStep 1: Creating announcement...")
    try:
        response = requests.post(
            'http://localhost:5000/api/announcements',
            json=announcement_data
        )
        if response.status_code == 200:
            print("✓ Announcement created successfully")
            print(response.json())
        else:
            print("✗ Failed to create announcement")
            print(response.json())
            return
    except Exception as e:
        print(f"Error creating announcement: {str(e)}")
        return

    # Wait for processing
    print("\nStep 2: Waiting for translations and audio generation...")
    sleep(5)  # Give time for background processing

    print("\nStep 3: Verifying announcement in logs...")
    try:
        response = requests.get('http://localhost:5000/api/announcements')
        announcements = response.json()
        
        if announcements:
            latest = announcements[-1]  # Get most recent announcement
            print("\nLatest announcement:")
            print(f"Text: {latest['text']}")
            print(f"Type: {latest.get('announcement_type') or latest.get('type')}")
            print(f"Priority: {latest.get('priority') or latest.get('urgency')}")
            print("\nTranslations available in:")
            if 'translations' in latest:
                for lang, text in latest['translations'].items():
                    print(f"- {lang.title()}: {text[:50]}...")
                    if latest.get('audio_paths', {}).get(lang):
                        print(f"  Audio: {latest['audio_paths'][lang]}")
            print("\n✓ Announcement verification complete")
        else:
            print("✗ No announcements found in logs")
    except Exception as e:
        print(f"Error verifying announcement: {str(e)}")

if __name__ == "__main__":
    print("Starting Announcement Flow Test")
    print("==============================")
    test_announcement_flow()
    print("\nTest complete. Please check:")
    print("1. Admin interface at: http://localhost:5000")
    print("2. Public interface at: http://localhost:5000/public")
