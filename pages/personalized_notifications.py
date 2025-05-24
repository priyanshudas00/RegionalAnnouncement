import streamlit as st
import json
import os
from datetime import datetime, timedelta
import time
import base64
from bhashaseva_enhanced import LANGUAGE_CODE_MAP
from shared_state import initialize_session_state, get_announcements, cleanup_temp_files

# Page configuration
st.set_page_config(
    page_title="BhashaSeva - Personalized Notifications",
    page_icon="🔔",
    layout="wide"
)

# Initialize session state
initialize_session_state()

# Custom CSS with enhanced styling
st.markdown("""
<style>
    .notification-card {
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        transition: transform 0.2s;
    }
    .notification-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .emergency {
        background-color: #ffebee;
        border-left: 6px solid #f44336;
    }
    .health {
        background-color: #e8f5e9;
        border-left: 6px solid #4caf50;
    }
    .welfare {
        background-color: #e3f2fd;
        border-left: 6px solid #2196f3;
    }
    .general {
        background-color: #f5f5f5;
        border-left: 6px solid #9e9e9e;
    }
    .language-selector {
        padding: 1.2rem;
        background-color: #f8f9fa;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        box-shadow: 0 1px 4px rgba(0,0,0,0.05);
    }
    .audio-player {
        width: 100%;
        margin: 12px 0;
        border-radius: 8px;
    }
    .stMarkdown h4 {
        margin-bottom: 0.5rem;
        color: #333;
    }
    .priority-tag {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: bold;
        margin-right: 0.5rem;
    }
    .emergency-tag {
        background-color: #f44336;
        color: white;
    }
    .health-tag {
        background-color: #4caf50;
        color: white;
    }
    .welfare-tag {
        background-color: #2196f3;
        color: white;
    }
    .district-tag {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        font-size: 0.8rem;
        background-color: #e0e0e0;
        margin-right: 0.5rem;
        margin-bottom: 0.5rem;
    }
    .timestamp {
        font-size: 0.85rem;
        color: #666;
        margin-top: 0.5rem;
    }
    .no-notifications {
        text-align: center;
        padding: 3rem;
        color: #666;
    }
    .refresh-button {
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar for preferences
with st.sidebar:
    st.title("🌐 Language & Preferences")
    
    # Language selection
    st.subheader("Preferred Languages")
    available_languages = sorted(list(LANGUAGE_CODE_MAP.keys()), key=lambda x: x.title())
    selected_languages = st.multiselect(
        "Select languages for notifications",
        available_languages,
        default=st.session_state.get("preferred_languages", ["english"]),
        format_func=lambda x: x.title()
    )
    st.session_state.preferred_languages = selected_languages or ["english"]
    
    # Notification filters
    st.markdown("---")
    st.subheader("🔔 Notification Filters")
    st.checkbox("Emergency Alerts", value=st.session_state.get("enable_emergency", True), key="enable_emergency")
    st.checkbox("Health Updates", value=st.session_state.get("enable_health", True), key="enable_health")
    st.checkbox("Welfare Schemes", value=st.session_state.get("enable_welfare", True), key="enable_welfare")
    st.checkbox("General Announcements", value=st.session_state.get("enable_general", True), key="enable_general")
    
    # Delivery preferences
    st.markdown("---")
    st.subheader("📢 Delivery Options")
    st.checkbox("Enable Audio", value=st.session_state.get("enable_audio", True), key="enable_audio")
    st.checkbox("Enable SMS", value=st.session_state.get("enable_sms", False), key="enable_sms")
    st.checkbox("Enable Push Notifications", value=st.session_state.get("enable_push", True), key="enable_push")
    
    # Auto-refresh
    st.markdown("---")
    st.subheader("🔄 Auto Refresh")
    auto_refresh = st.checkbox("Enable Auto-refresh", value=st.session_state.get("auto_refresh", False), key="auto_refresh")
    if auto_refresh:
        refresh_rate = st.slider("Refresh rate (seconds)", 5, 60, 15)
        time.sleep(refresh_rate)
        st.rerun()

# Main content area
st.title("🔔 Personalized Notifications")

# Add a manual refresh button
if st.button("🔄 Refresh Notifications", use_container_width=True, key="refresh_button"):
    st.rerun()

# Add filters in main content
col1, col2, col3 = st.columns(3)
with col1:
    time_filter = st.selectbox(
        "Time Period",
        ["Last 24 hours", "Last week", "Last month", "All time"],
        index=0
    )
with col2:
    district_filter = st.multiselect(
        "Filter by District",
        ["All"] + ["Bengaluru", "Mumbai", "Chennai", "Hyderabad", "Kolkata"],
        default=["All"]
    )
with col3:
    sort_order = st.selectbox(
        "Sort by",
        ["Newest first", "Oldest first", "Priority"],
        index=0
    )

def display_notification(notification):
    """Display a notification card with enhanced UI"""
    notification_type = notification.get('announcement_type', 'general').lower()
    
    # Determine card style based on type
    if 'emergency' in notification_type:
        card_class = "emergency"
        priority_tag = "<span class='priority-tag emergency-tag'>🚨 EMERGENCY</span>"
    elif 'health' in notification_type:
        card_class = "health"
        priority_tag = "<span class='priority-tag health-tag'>⚠️ HEALTH</span>"
    elif 'welfare' in notification_type:
        card_class = "welfare"
        priority_tag = "<span class='priority-tag welfare-tag'>ℹ️ WELFARE</span>"
    else:
        card_class = "general"
        priority_tag = ""
    
    # Format timestamp
    timestamp = notification.get('timestamp', '')
    if isinstance(timestamp, str):
        try:
            timestamp = datetime.fromisoformat(timestamp)
        except ValueError:
            timestamp = datetime.now()
    
    # Format districts
    districts = notification.get('districts', ['All districts'])
    district_tags = "".join([f"<span class='district-tag'>{d}</span>" for d in districts])
    
    # Create the card
    st.markdown(f"""
    <div class="notification-card {card_class}">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <h4>{notification.get('type', 'Announcement').title()}</h4>
            <div>{priority_tag}</div>
        </div>
        <div style="margin: 0.5rem 0;">
            {district_tags}
        </div>
        <p><strong>Original ({notification.get('source_lang', 'english').title()}):</strong><br/>
        {notification.get('text', '')}</p>
    """, unsafe_allow_html=True)
    
    # Display translations for preferred languages
    for lang in st.session_state.preferred_languages:
        if lang in notification.get('translations', {}):
            with st.expander(f"{lang.title()} Translation"):
                st.markdown(notification['translations'][lang])
                
                # Display audio if available and enabled
                if (st.session_state.enable_audio and 
                    lang in notification.get('audio_paths', {}) and 
                    os.path.exists(notification['audio_paths'][lang])):
                    st.audio(notification['audio_paths'][lang])
    
    # Show timestamp and delivery options
    st.markdown(f"""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 1rem;">
            <span class="timestamp">Posted: {timestamp.strftime('%Y-%m-%d %H:%M')}</span>
            <div>
                <small>{"🔊" if st.session_state.enable_audio else ""} 
                {"📱" if st.session_state.enable_push else ""} 
                {"✉️" if st.session_state.enable_sms else ""}</small>
            </div>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# Filter and sort announcements
def filter_and_sort_announcements():
    announcements = get_announcements()
    filtered = []
    
    # Time filter
    now = datetime.now()
    if time_filter == "Last 24 hours":
        cutoff = now - timedelta(hours=24)
    elif time_filter == "Last week":
        cutoff = now - timedelta(weeks=1)
    elif time_filter == "Last month":
        cutoff = now - timedelta(days=30)
    else:
        cutoff = datetime.min
    
    # District filter
    if "All" not in district_filter and district_filter:
        district_filter_set = set(district_filter)
    
    for ann in announcements:
        # Check timestamp
        ann_time = ann.get('timestamp', '')
        if isinstance(ann_time, str):
            try:
                ann_time = datetime.fromisoformat(ann_time)
            except ValueError:
                continue
        
        if ann_time < cutoff:
            continue
        
        # Check district
        if "All" not in district_filter and district_filter:
            ann_districts = set(ann.get('districts', []))
            if not ann_districts.intersection(district_filter_set):
                continue
        
        # Check notification type preferences
        ann_type = ann.get('announcement_type', 'general').lower()
        if ('emergency' in ann_type and not st.session_state.enable_emergency):
            continue
        if ('health' in ann_type and not st.session_state.enable_health):
            continue
        if ('welfare' in ann_type and not st.session_state.enable_welfare):
            continue
        if (ann_type == 'general' and not st.session_state.enable_general):
            continue
        
        # Check language preferences
        if not any(lang in ann.get('target_langs', []) + [ann.get('source_lang')] 
                  for lang in st.session_state.preferred_languages):
            continue
            
        filtered.append(ann)
    
    # Sort announcements
    if sort_order == "Newest first":
        filtered.sort(key=lambda x: datetime.fromisoformat(x['timestamp']) if isinstance(x['timestamp'], str) else x['timestamp'], reverse=True)
    elif sort_order == "Oldest first":
        filtered.sort(key=lambda x: datetime.fromisoformat(x['timestamp']) if isinstance(x['timestamp'], str) else x['timestamp'])
    elif sort_order == "Priority":
        priority_order = {'emergency': 1, 'health': 2, 'welfare': 3, 'general': 4}
        filtered.sort(key=lambda x: priority_order.get(x.get('announcement_type', 'general').lower(), 4))
    
    return filtered

# Display filtered notifications
filtered_announcements = filter_and_sort_announcements()

if filtered_announcements:
    st.markdown(f"### 📌 Showing {len(filtered_announcements)} notifications")
    
    for notification in filtered_announcements:
        display_notification(notification)
        
    # Add a "back to top" button if many notifications
    if len(filtered_announcements) > 5:
        st.markdown("---")
        if st.button("⬆️ Back to Top", use_container_width=True):
            st.rerun()
else:
    st.markdown("""
    <div class="no-notifications">
        <h3>No notifications found</h3>
        <p>Try adjusting your filters or check back later</p>
    </div>
    """, unsafe_allow_html=True)

# Cleanup old files
cleanup_temp_files()

# Add a small footer
st.markdown("---")
st.markdown("""
<small>
BhashaSeva - Multilingual Public Announcement System | 
[Privacy Policy](#) | [Terms of Service](#) | 
© 2023 Digital India Initiative
</small>
""", unsafe_allow_html=True)