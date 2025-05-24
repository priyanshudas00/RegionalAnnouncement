import os
import time
import logging
import hashlib
from geopy.geocoders import Nominatim
import pandas as pd
from queue import PriorityQueue
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import cachetools

# ======================
# CONSTANTS & ENUMS
# ======================
class PriorityLevel(Enum):
    EMERGENCY = 1
    HEALTH_ALERT = 2
    WELFARE_SCHEME = 3
    GENERAL = 4

class DeliveryChannel(Enum):
    VOICE = "voice"
    SMS = "sms"

class AnnouncementType(Enum):
    WEATHER_ALERT = "weather_alert"
    HEALTH = "health"
    WELFARE = "welfare"
    GENERAL = "general"
    SECURITY = "security"

# ======================
# DATA STRUCTURES
# ======================
@dataclass
class Announcement:
    text: str
    src_lang: str = "english"
    target_langs: List[str] = None
    channels: List[DeliveryChannel] = None
    priority: PriorityLevel = PriorityLevel.GENERAL
    announcement_type: AnnouncementType = AnnouncementType.GENERAL
    districts: List[str] = None
    metadata: dict = None

@dataclass
class EmergencyAlert:
    message: str
    affected_districts: List[str]
    alert_type: str
    severity: str
    coordinates: Optional[Tuple[float, float]] = None
    valid_until: Optional[float] = None

# ======================
# LOGGING CONFIGURATION
# ======================
import sys
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bhashaseva.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# ======================
# CORE CONFIGURATION
# ======================
LANGUAGE_CODE_MAP = {
    "kannada": "kan_Knda",
    "hindi": "hin_Deva",
    "tamil": "tam_Taml",
    "telugu": "tel_Telu",
    "marathi": "mar_Deva",
    "english": "eng_Latn",
    "bengali": "ben_Beng",
    "gujarati": "guj_Gujr",
    "malayalam": "mal_Mlym",
    "punjabi": "pan_Guru"
}

DISTRICT_LANGUAGE_MAPPING = {
    "Bengaluru": ["kannada"],
    "Mumbai": ["marathi", "hindi"],
    "Chennai": ["tamil"],
    "Hyderabad": ["telugu"],
    "Kolkata": ["bengali", "hindi"],
    "Delhi": ["hindi", "punjabi"],
    "Ahmedabad": ["gujarati", "hindi"],
    "Pune": ["marathi", "hindi"],
    "Kochi": ["malayalam"]
}

# ======================
# CACHE CONFIGURATION
# ======================
translation_cache = cachetools.LRUCache(maxsize=1000)
tts_cache = cachetools.LRUCache(maxsize=500)

# ======================
# CORE SYSTEM
# ======================
class AnnouncementSystem:
    def __init__(self, api_config: dict = None):
        """
        Initialize the announcement system with optional API configuration.
        
        Args:
            api_config: Dictionary containing API configuration (base_url, api_key, etc.)
        """
        self.geolocator = Nominatim(user_agent="bhasha_seva")
        self.announcement_queue = PriorityQueue()
        self.counter = 0
        self.recent_alerts = []
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.setup_api_config(api_config)
        self._load_configurations()
        self._init_metrics()
        
    def _init_metrics(self):
        """Initialize system metrics tracking"""
        self.metrics = {
            "announcements_processed": 0,
            "languages_served": {},
            "emergency_alerts": 0,
            "failures": 0,
            "last_processed": None
        }
        
    def _load_configurations(self):
        """Load system configurations from file or environment"""
        try:
            with open('config/system_config.json') as f:
                self.config = json.load(f)
                logger.info("System configuration loaded successfully")
        except FileNotFoundError:
            self.config = {
                "default_languages": ["hindi", "english"],
                "rate_limit": 10,  # requests per minute
                "retry_policy": {
                    "max_retries": 3,
                    "backoff_factor": 2
                }
            }
            logger.warning("Using default configuration as config file not found")
            
    def setup_api_config(self, api_config: dict = None):
        """Initialize API configurations"""
        if api_config:
            self.api_config = api_config
        else:
            # Fallback to environment variables
            self.api_config = {
                "api_key": os.getenv("DWANI_API_KEY"),
                "api_base": os.getenv("DWANI_API_BASE", "https://api.dwani.ai/v1")
            }
        
        if not self.api_config.get("api_key"):
            logger.error("API key not configured!")
            raise ValueError("API key must be provided either through config or environment variables")
            
    def get_languages_for_region(self, district: str) -> List[str]:
        """Get target languages for a district with fallback to defaults"""
        return DISTRICT_LANGUAGE_MAPPING.get(district, self.config["default_languages"])
    
    def translate_and_deliver(
        self,
        announcement: Announcement,
        priority: PriorityLevel = None,
        channels: List[DeliveryChannel] = None
    ) -> None:
        """
        Queue an announcement for translation and delivery.
        
        Args:
            announcement: Announcement object containing message details
            priority: Override priority level if needed
            channels: Override delivery channels if needed
        """
        if announcement.target_langs is None:
            announcement.target_langs = list(LANGUAGE_CODE_MAP.keys())
            
        if priority:
            announcement.priority = priority
            
        if channels:
            announcement.channels = channels
            
        self.counter += 1
        self.announcement_queue.put((
            announcement.priority.value,
            self.counter,
            announcement
        ))
        logger.info(f"Queued announcement with priority {announcement.priority.name}")
    
    def process_queue(self, max_items: int = None) -> None:
        """
        Process announcements in priority order.
        
        Args:
            max_items: Maximum number of items to process (None for all)
        """
        processed = 0
        while not self.announcement_queue.empty() and (max_items is None or processed < max_items):
            _, _, announcement = self.announcement_queue.get()
            self._execute_announcement(announcement)
            processed += 1
            self.metrics["announcements_processed"] += 1
            self.metrics["last_processed"] = time.time()
            
    def _execute_announcement(self, announcement: Announcement) -> None:
        """Internal method to handle actual announcement processing"""
        futures = []
        for lang in announcement.target_langs:
            future = self.executor.submit(
                self._process_language_announcement,
                announcement,
                lang
            )
            futures.append(future)
            
        # Wait for all language versions to complete
        for future in as_completed(futures):
            try:
                result = future.result()
                if not result:
                    logger.error(f"Failed to process one of the language announcements")
            except Exception as e:
                logger.error(f"Error in announcement processing: {str(e)}")
                
    def _process_language_announcement(self, announcement: Announcement, lang: str) -> bool:
        """
        Process announcement for a specific language with retry logic.
        
        Args:
            announcement: The announcement to process
            lang: Target language
            
        Returns:
            bool: True if successful, False otherwise
        """
        retry_count = 0
        max_retries = self.config["retry_policy"]["max_retries"]
        backoff_factor = self.config["retry_policy"]["backoff_factor"]
        
        logger.info(f"Processing {lang} announcement (Priority: {announcement.priority.name})")
        
        tgt_lang_code = LANGUAGE_CODE_MAP.get(lang, lang)
        
        while retry_count < max_retries:
            try:
                # Generate cache key
                cache_key = self._generate_cache_key(
                    announcement.text,
                    announcement.src_lang,
                    tgt_lang_code
                )
                
                # Check cache first
                audio_response = tts_cache.get(cache_key)
                translated_text = None
                
                if not audio_response:
                    # First translate the text
                    translated_text = self._translate_text(
                        announcement.text,
                        announcement.src_lang,
                        tgt_lang_code
                    )
                    
                    # Then convert to speech if voice channel is enabled
                    if DeliveryChannel.VOICE in announcement.channels:
                        audio_response = self._text_to_speech(translated_text, tgt_lang_code)
                        tts_cache[cache_key] = audio_response
                        
                        # Save audio file
                        audio_filename = f"voice_{hash(translated_text)}_{lang}.mp3"
                        audio_path = os.path.join("announcements", audio_filename)
                        with open(audio_path, "wb") as f:
                            f.write(audio_response)
                
                # Save translations and audio paths
                if not hasattr(announcement, 'translations'):
                    announcement.translations = {}
                if not hasattr(announcement, 'audio_paths'):
                    announcement.audio_paths = {}
                    
                announcement.translations[lang] = translated_text
                if audio_response:
                    announcement.audio_paths[lang] = audio_path
                
                # Deliver through all specified channels
                for channel in announcement.channels:
                    self._deliver(
                        channel,
                        audio_response if channel == DeliveryChannel.VOICE else translated_text,
                        lang_code=tgt_lang_code
                    )
                
                # Update metrics
                self.metrics["languages_served"][lang] = self.metrics["languages_served"].get(lang, 0) + 1
                
                # Save to JSON file
                self._save_announcement_to_json(announcement)
                
                logger.info(f"Successfully processed {lang} announcement")
                return True
                
            except Exception as e:
                error_msg = str(e)
                if "Rate limit" in error_msg:
                    wait_time = (backoff_factor ** retry_count) * 5  # Exponential backoff
                    logger.warning(f"Rate limited. Retrying in {wait_time} seconds... ({retry_count + 1}/{max_retries})")
                    time.sleep(wait_time)
                retry_count += 1
                continue
                
        self.metrics["failures"] += 1
        return False

    def _save_announcement_to_json(self, announcement: Announcement) -> None:
        """Save the announcement to the JSON file"""
        try:
            # Load existing announcements
            try:
                with open('announcement_logs.json', 'r') as f:
                    announcements = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                announcements = []
            
            # Convert announcement to dict
            announcement_dict = {
                'text': announcement.text,
                'src_lang': announcement.src_lang,
                'target_langs': announcement.target_langs,
                'channels': [ch.value for ch in announcement.channels],
                'priority': announcement.priority.name,
                'announcement_type': announcement.announcement_type.name,
                'districts': announcement.districts,
                'metadata': announcement.metadata,
                'translations': getattr(announcement, 'translations', {}),
                'audio_paths': getattr(announcement, 'audio_paths', {})
            }
            
            # Add to list and save
            announcements.append(announcement_dict)
            with open('announcement_logs.json', 'w', encoding='utf-8') as f:
                json.dump(announcements, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving announcement to JSON: {str(e)}")

# ======================
# EMERGENCY BROADCAST SYSTEM
# ======================
class EmergencyBroadcastSystem(AnnouncementSystem):
    def __init__(self, api_config: dict = None):
        super().__init__(api_config)
        self.emergency_protocols = self._load_emergency_protocols()
        
    def _load_emergency_protocols(self) -> dict:
        """Load emergency response protocols"""
        try:
            with open('config/emergency_protocols.json') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning("Emergency protocols file not found, using defaults")
            return {
                "natural_disaster": {
                    "channels": ["voice", "sms", "ivr", "mobile_app"],
                    "priority": "emergency",
                    "additional_actions": ["activate_sirens", "notify_authorities"]
                },
                "health_emergency": {
                    "channels": ["voice", "sms", "mobile_app"],
                    "priority": "health_alert",
                    "additional_actions": ["notify_hospitals"]
                }
            }
    
    def trigger_emergency_alert(self, alert_data: EmergencyAlert) -> None:
        """Special handling for emergency alerts"""
        protocol = self.emergency_protocols.get(alert_data.alert_type, {})
        
        logger.info(f"\n🚨 EMERGENCY ALERT: {alert_data.alert_type.upper()}")
        logger.info(f"Affected Districts: {', '.join(alert_data.affected_districts)}")
        logger.info(f"Message: ⚠️ {alert_data.message}")
        
        # Add to recent alerts log
        self.recent_alerts.append({
            "timestamp": time.time(),
            "type": alert_data.alert_type,
            "districts": alert_data.affected_districts,
            "message": alert_data.message,
            "severity": alert_data.severity
        })
        
        # Create and queue announcement
        announcement = Announcement(
            text=alert_data.message,
            target_langs=[],
            priority=PriorityLevel.EMERGENCY,
            announcement_type=AnnouncementType.WEATHER_ALERT if alert_data.alert_type == "natural_disaster" else AnnouncementType.GENERAL,
            districts=alert_data.affected_districts,
            metadata={
                "severity": alert_data.severity,
                "valid_until": alert_data.valid_until
            }
        )
        
        # Get languages for all affected districts (unique union)
        languages = set()
        for district in alert_data.affected_districts:
            languages.update(self.get_languages_for_region(district))
        
        announcement.target_langs = list(languages)
        announcement.channels = [DeliveryChannel(ch) for ch in protocol.get("channels", ["voice", "sms", "ivr"])]
        
        self.translate_and_deliver(announcement)
        
        # Execute additional emergency actions
        for action in protocol.get("additional_actions", []):
            try:
                if action == "activate_sirens":
                    self.activate_sirens(alert_data.affected_districts)
                elif action == "notify_authorities":
                    self.notify_emergency_services(alert_data.affected_districts)
                elif action == "notify_hospitals":
                    self.notify_hospitals(alert_data.affected_districts)
            except Exception as e:
                logger.error(f"Failed to execute emergency action {action}: {str(e)}")
        
        self.metrics["emergency_alerts"] += 1
    
    def activate_sirens(self, districts: List[str]) -> None:
        """Simulate IoT siren activation"""
        logger.info(f"EMERGENCY: Activating sirens in {', '.join(districts)}")
        # In a real system, this would trigger IoT devices
    
    def notify_emergency_services(self, districts: List[str]) -> None:
        """Notify local authorities"""
        logger.info(f"Notifying emergency services in {len(districts)} districts")
        # Integration with emergency service APIs would go here
    
    def notify_hospitals(self, districts: List[str]) -> None:
        """Notify nearby hospitals"""
        logger.info(f"Alerting hospitals in {len(districts)} districts")
        # Integration with health system would go here
    
    def get_recent_alerts(self, limit: int = 5) -> List[dict]:
        """Get recent emergency alerts"""
        return sorted(self.recent_alerts, key=lambda x: x["timestamp"], reverse=True)[:limit]

# ======================
# FEEDBACK SYSTEM
# ======================
class FeedbackAnalyzer:
    def __init__(self):
        self.feedback_data = pd.DataFrame(columns=[
            "timestamp", 
            "language", 
            "feedback", 
            "sentiment", 
            "confidence",
            "source",
            "location"
        ])
        self.sentiment_model = self._load_sentiment_model()
        
    def _load_sentiment_model(self):
        """Load or initialize sentiment analysis model"""
        # In a real implementation, this would load a proper ML model
        return {
            "positive_keywords": ["good", "thank", "helpful", "excellent", "great"],
            "negative_keywords": ["not", "bad", "wrong", "poor", "fail"]
        }
    
    def process_audio_feedback(self, audio_path: str, language: str, location: str = None) -> Optional[dict]:
        """
        Process voice feedback from citizens.
        
        Args:
            audio_path: Path to audio file containing feedback
            language: Language of the feedback
            location: Optional location information
            
        Returns:
            dict: Analysis results including sentiment and confidence
        """
        try:
            # In a real implementation, this would call ASR API
            transcription = f"Simulated transcription of {audio_path} in {language}"
            
            # Analyze sentiment
            sentiment_result = self._analyze_sentiment(transcription)
            
            # Store results
            feedback_record = {
                "timestamp": time.time(),
                "language": language,
                "feedback": transcription,
                "sentiment": sentiment_result["sentiment"],
                "confidence": sentiment_result["confidence"],
                "source": "voice",
                "location": location
            }
            
            self.feedback_data.loc[len(self.feedback_data)] = feedback_record
            logger.info(f"Processed feedback from {location or 'unknown location'}")
            
            return feedback_record
        except Exception as e:
            logger.error(f"Feedback processing error: {str(e)}")
            return None
    
    def _analyze_sentiment(self, text: str) -> dict:
        """
        Analyze sentiment of feedback text.
        
        Args:
            text: The feedback text to analyze
            
        Returns:
            dict: Contains 'sentiment' and 'confidence' values
        """
        text = text.lower()
        positive_count = sum(1 for word in self.sentiment_model["positive_keywords"] if word in text)
        negative_count = sum(1 for word in self.sentiment_model["negative_keywords"] if word in text)
        
        if positive_count > negative_count:
            return {"sentiment": "positive", "confidence": positive_count / (positive_count + 1)}
        elif negative_count > positive_count:
            return {"sentiment": "negative", "confidence": negative_count / (negative_count + 1)}
        else:
            return {"sentiment": "neutral", "confidence": 0.5}
    
    def get_feedback_summary(self) -> dict:
        """Generate summary statistics of feedback received"""
        if self.feedback_data.empty:
            return {"total": 0}
            
        return {
            "total": len(self.feedback_data),
            "by_sentiment": self.feedback_data["sentiment"].value_counts().to_dict(),
            "by_language": self.feedback_data["language"].value_counts().to_dict(),
            "average_confidence": self.feedback_data["confidence"].mean()
        }

# ======================
# MAIN EXECUTION
# ======================
if __name__ == "__main__":
    # Example configuration (in production, this would come from config files or env vars)
    config = {
        "api_key": "your_api_key_here",
        "api_base": "https://api.dwani.ai/v1"
    }
    
    try:
        # Initialize systems
        emergency_system = EmergencyBroadcastSystem(config)
        feedback_analyzer = FeedbackAnalyzer()
        
        logger.info("\nTesting Normal Announcement...")
        # Example 1: Normal announcement
        normal_announcement = Announcement(
            text="The new vaccination center will open tomorrow at the community hall",
            target_langs=["kannada", "hindi"],
            priority=PriorityLevel.HEALTH_ALERT,
            channels=[DeliveryChannel.VOICE, DeliveryChannel.SMS],
            announcement_type=AnnouncementType.HEALTH
        )
        emergency_system.translate_and_deliver(normal_announcement)
        
        logger.info("\nTesting Emergency Alert...")
        # Example 2: Emergency alert
        emergency_alert = EmergencyAlert(
            message="Severe weather alert: Heavy rainfall and flooding expected. Please move to higher ground immediately.",
            affected_districts=["Bengaluru", "Chennai"],
            alert_type="natural_disaster",
            severity="high"
        )
        emergency_system.trigger_emergency_alert(emergency_alert)
        
        # Process all queued announcements
        logger.info("\nProcessing Announcement Queue...")
        emergency_system.process_queue()
        
        # Simulate feedback processing
        logger.info("\nProcessing sample feedback...")
        feedback_result = feedback_analyzer.process_audio_feedback(
            audio_path="sample_feedback.wav",
            language="hindi",
            location="Bengaluru"
        )
        logger.info(f"Feedback analysis result: {feedback_result}")
        
        # Display system metrics
        logger.info("\nSystem Metrics:")
        logger.info(json.dumps(emergency_system.get_system_metrics(), indent=2))
        
        logger.info("\nFeedback Summary:")
        logger.info(json.dumps(feedback_analyzer.get_feedback_summary(), indent=2))
        
        logger.info("\n✅ System test completed successfully.")
        
    except Exception as e:
        logger.error(f"System error: {str(e)}", exc_info=True)
    finally:
        emergency_system.cleanup()