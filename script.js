const announcements = [
            {
                id: 1,
                type: "Emergency Alert",
                announcementType: "emergency",
                priority: "urgent",
                text: "Severe weather alert: Heavy rainfall and flooding expected in coastal areas. Please move to higher ground immediately.",
                sourceLanguage: "english",
                targetLanguages: ["kannada", "hindi", "tamil"],
                districts: ["Bengaluru", "Chennai"],
                timestamp: "2023-06-15T14:30:00",
                translations: {
                    kannada: "ತೀವ್ರ ಹವಾಮಾನ ಎಚ್ಚರಿಕೆ: ತೀವ್ರ ಮಳೆ ಮತ್ತು ಬಂಡೆಕಲ್ಲಿನ ಪ್ರವಾಹದ ಅಪಾಯವಿದೆ. ದಯವಿಟ್ಟು ತಕ್ಷಣವೇ ಹೆಚ್ಚಿನ ನೆಲಕ್ಕೆ ಸರಿಸಿ.",
                    hindi: "गंभीर मौसम चेतावनी: तटीय क्षेत्रों में भारी बारिश और बाढ़ की आशंका है। कृपया तुरंत ऊंचे स्थान पर चले जाएं।",
                    tamil: "கடுமையான வானிலை எச்சரிக்கை: கடலோர பகுதிகளில் கனமழை மற்றும் வெள்ளம் எதிர்பார்க்கப்படுகிறது. உடனடியாக உயரமான இடத்திற்கு செல்லவும்."
                },
                audioPaths: {
                    kannada: "audio/kannada_alert.mp3",
                    hindi: "audio/hindi_alert.mp3",
                    tamil: "audio/tamil_alert.mp3"
                }
            },
            {
                id: 2,
                type: "Health Update",
                announcementType: "health",
                priority: "high",
                text: "New vaccination center opened at Community Health Center, Koramangala. All adults eligible for booster dose.",
                sourceLanguage: "english",
                targetLanguages: ["kannada", "hindi"],
                districts: ["Bengaluru"],
                timestamp: "2023-06-14T10:15:00",
                translations: {
                    kannada: "ಕೋರಮಂಗಲದ ಸಮುದಾಯ ಆರೋಗ್ಯ ಕೇಂದ್ರದಲ್ಲಿ ಹೊಸ ಲಸಿಕಾ ಕೇಂದ್ರ ತೆರೆಯಲಾಗಿದೆ. ಎಲ್ಲಾ ವಯಸ್ಕರಿಗೂ ಬೂಸ್ಟರ್ ಡೋಸ್ ಅರ್ಹತೆ ಇದೆ.",
                    hindi: "कोरमंगला में सामुदायिक स्वास्थ्य केंद्र पर नया टीकाकरण केंद्र खोला गया। सभी वयस्क बूस्टर खुराक के लिए पात्र हैं।"
                },
                audioPaths: {
                    kannada: "audio/kannada_health.mp3",
                    hindi: "audio/hindi_health.mp3"
                }
            },
            {
                id: 3,
                type: "Welfare Scheme",
                announcementType: "welfare",
                priority: "general",
                text: "Applications open for Gruha Lakshmi scheme. Women heads of households can apply with Aadhaar and ration card.",
                sourceLanguage: "english",
                targetLanguages: ["kannada", "hindi", "telugu"],
                districts: ["Bengaluru", "Hyderabad"],
                timestamp: "2023-06-12T09:00:00",
                translations: {
                    kannada: "ಗೃಹ ಲಕ್ಷ್ಮಿ ಯೋಜನೆಗೆ ಅರ್ಜಿಗಳು ತೆರೆದಿವೆ. ಮನೆತಲೆಯ ಮಹಿಳೆಯರು ಆಧಾರ್ ಮತ್ತು ರೇಷನ್ ಕಾರ್ಡ್ನೊಂದಿಗೆ ಅರ್ಜಿ ಸಲ್ಲಿಸಬಹುದು.",
                    hindi: "गृह लक्ष्मी योजना के लिए आवेदन खुले हैं। घर की महिला मुखिया आधार और राशन कार्ड के साथ आवेदन कर सकती हैं।",
                    telugu: "గృహ లక్ష్మి పథకం కోసం దరఖాస్తులు తెరవబడ్డాయి. గృహిణులు ఆధార్ మరియు రేషన్ కార్డుతో దరఖాస్తు చేసుకోవచ్చు."
                },
                audioPaths: {
                    kannada: "audio/kannada_welfare.mp3",
                    hindi: "audio/hindi_welfare.mp3",
                    telugu: "audio/telugu_welfare.mp3"
                }
            }
        ];
        
        // DOM elements
        const createAnnouncementBtn = document.getElementById('createAnnouncementBtn');
        const createEmergencyBtn = document.getElementById('createEmergencyBtn');
        const createAnnouncementForm = document.getElementById('createAnnouncementForm');
        const cancelAnnouncementBtn = document.getElementById('cancelAnnouncementBtn');
        const announcementForm = document.getElementById('announcementForm');
        
        // Add test translation button with FontAwesome icon
        const testTranslationBtn = document.createElement('button');
        testTranslationBtn.type = 'button';
        testTranslationBtn.className = 'test-translation-btn';
        testTranslationBtn.innerHTML = '<i class="fas fa-language"></i> Test Translation';
        
        // Test translation click handler
testTranslationBtn.onclick = async function() {
    // On clicking test translation, fetch announcements data and redirect to /test page
    try {
        const response = await fetch('http://localhost:5000/api/announcements');
        if (!response.ok) {
            throw new Error('Failed to fetch announcements');
        }
        const announcements = await response.json();

        // Store announcements data in sessionStorage to access on /test page
        sessionStorage.setItem('announcementsData', JSON.stringify(announcements));

        // Redirect to /test page
        window.location.href = 'http://localhost:5000/test';
    } catch (error) {
        console.error('Error fetching announcements:', error);
        alert('Failed to load announcements for testing.');
    }
};
        
        // Insert test button after submit
        const submitButton = document.querySelector('button[type="submit"]');
        submitButton.parentNode.insertBefore(testTranslationBtn, submitButton.nextSibling);
        
        // Audio playback function
        window.playAudio = function(audioFile) {
            // Stop any currently playing audio
            document.querySelectorAll('audio').forEach(a => a.pause());
            
            const audio = new Audio(`/announcements/${audioFile}`);
            audio.play().catch(err => {
                console.error('Error playing audio:', err);
                alert('Error playing audio. Please try again.');
            });
        };
        
        // Voice recording
        let mediaRecorder;
        let audioChunks = [];
        let isRecording = false;
        
        window.recordTranslation = async function(language) {
            const micBtn = event.currentTarget;
            
            if (!isRecording) {
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                    mediaRecorder = new MediaRecorder(stream);
                    audioChunks = [];
                    
                    mediaRecorder.ondataavailable = (event) => {
                        audioChunks.push(event.data);
                    };
                    
                    mediaRecorder.onstop = async () => {
                        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                        const formData = new FormData();
                        formData.append('audio', audioBlob);
                        formData.append('language', language);
                        
                        try {
                            micBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
                            micBtn.classList.add('loading');
                            
                            const response = await fetch('/api/process-voice', {
                                method: 'POST',
                                body: formData
                            });
                            
                            const result = await response.json();
                            if (result.success) {
                                const audioEl = micBtn.parentElement.querySelector('audio');
                                audioEl.src = `/announcements/${result.audioFile}`;
                                playAudio(result.audioFile);
                            }
                            micBtn.innerHTML = '<i class="fas fa-microphone"></i> Record';
                            micBtn.classList.remove('recording', 'loading');
                        } catch (error) {
                            console.error('Error processing voice:', error);
                            micBtn.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Error';
                            setTimeout(() => {
                                micBtn.innerHTML = '<i class="fas fa-microphone"></i> Record';
                                micBtn.classList.remove('recording', 'loading');
                            }, 2000);
                        }
                    };
                    
                    mediaRecorder.start();
                    isRecording = true;
                    micBtn.innerHTML = '<i class="fas fa-stop-circle"></i> Stop Recording';
                    micBtn.classList.add('recording');
                    
                    // Auto-stop after 10 seconds
                    setTimeout(() => {
                        if (isRecording) {
                            stopRecording();
                        }
                    }, 10000);
                    
                } catch (err) {
                    console.error('Error accessing microphone:', err);
                    alert('Could not access microphone. Please check permissions.');
                }
            } else {
                stopRecording();
            }
        };
        
        function stopRecording() {
            if (mediaRecorder && isRecording) {
                mediaRecorder.stop();
                isRecording = false;
                mediaRecorder.stream.getTracks().forEach(track => track.stop());
            }
        }
        
        // Event Listeners
        createAnnouncementBtn.addEventListener('click', () => {
            createAnnouncementForm.style.display = 'block';
        });
        
        createEmergencyBtn.addEventListener('click', () => {
            createAnnouncementForm.style.display = 'block';
            document.getElementById('announcementType').value = 'emergency';
            document.getElementById('priority').value = 'urgent';
        });
        
        cancelAnnouncementBtn.addEventListener('click', () => {
            createAnnouncementForm.style.display = 'none';
            announcementForm.reset();
        });
        
        announcementForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = {
                announcementText: document.getElementById('announcementText').value,
                announcementType: document.getElementById('announcementType').value,
                priority: document.getElementById('priority').value,
                sourceLanguage: document.getElementById('sourceLanguage').value,
                targetLanguages: Array.from(document.getElementById('targetLanguages').selectedOptions).map(opt => opt.value),
                districts: Array.from(document.getElementById('districts').selectedOptions).map(opt => opt.value),
                enableAudio: document.getElementById('enableAudio').checked
            };

            try {
                const response = await fetch('/api/announcements', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(formData)
                });

                const result = await response.json();
                if (result.status === 'success') {
                    alert('Announcement submitted successfully!');
                    createAnnouncementForm.style.display = 'none';
                    announcementForm.reset();
                    // Refresh the announcements list
                    loadAnnouncements();
                } else {
                    alert('Error submitting announcement: ' + result.message);
                }
            } catch (error) {
                alert('Error submitting announcement: ' + error.message);
            }
        });

        // Function to load announcements from the server
        async function loadAnnouncements() {
            try {
                const response = await fetch('/api/announcements');
                const announcements = await response.json();
                renderAnnouncementsList(announcements);
            } catch (error) {
                console.error('Error loading announcements:', error);
                announcementsList.innerHTML = '<div class="no-announcements"><p>Error loading announcements</p></div>';
            }
        }

        // Update the renderAnnouncements function to use the server data
        function renderAnnouncementsList(announcements) {
            // Get filter values
            const selectedLanguages = Array.from(document.getElementById('languages').selectedOptions)
                .map(option => option.value);
            
            const showEmergency = document.getElementById('emergencyAlerts').checked;
            const showHealth = document.getElementById('healthUpdates').checked;
            const showWelfare = document.getElementById('welfareSchemes').checked;
            const showGeneral = document.getElementById('generalAnnouncements').checked;
            
            const timeFilter = document.getElementById('timeFilter').value;
            const selectedDistricts = Array.from(document.getElementById('districtFilter').selectedOptions)
                .map(option => option.value);
            
            const showAllDistricts = selectedDistricts.includes('all');
            const enableAudio = document.getElementById('enableAudio').checked;
            
            // Filter announcements based on criteria
            const filteredAnnouncements = announcements.filter(announcement => {
                // Add your filtering logic here based on the filters
                return true; // For now, show all announcements
            });

            if (filteredAnnouncements.length === 0) {
                announcementsList.innerHTML = `
                    <div class="no-announcements">
                        <p>No announcements found matching your filters</p>
                    </div>
                `;
                return;
            }

            announcementsList.innerHTML = filteredAnnouncements.map(announcement => {
                // Handle different data structures and provide defaults
                const type = announcement.announcement_type || announcement.type || 'General';
                const priority = announcement.priority || announcement.urgency || 'General';
                const srcLang = announcement.src_lang || announcement.source_lang || 'english';
                const targetLangs = announcement.target_langs || announcement.languages || [];
                const channels = announcement.channels || announcement.delivery_methods || [];
                
                return `
                    <div class="announcement-card">
                        <div class="card-header">
                            <h3 class="card-title">${String(type).replace('_', ' ').toUpperCase()}</h3>
                            <span class="card-priority priority-${String(priority).toLowerCase()}">
                                ${priority === 'EMERGENCY' || priority === 'High' ? '🚨 URGENT' : 
                                  priority === 'HEALTH_ALERT' || priority === 'Medium' ? '⚠️ HIGH' : 'ℹ️ GENERAL'}
                            </span>
                        </div>
                        
                        <div class="card-districts">
                            ${announcement.districts ? announcement.districts.map(district => 
                                `<span class="district-tag">${district}</span>`
                            ).join('') : ''}
                        </div>
                        
                        <div class="card-content">
                            <p><strong>Original (${srcLang}):</strong> ${announcement.text}</p>
                        </div>
                          <div class="card-translations">                            <div class="translation-toggle" 
                                onclick="toggleTranslation(this)"
                                role="button"
                                aria-expanded="false"
                                aria-controls="translation-content-${announcement.id}">
                                ▼ Show Translations (${targetLangs.length} languages)
                            </div>
                            <div class="translation-content translation-animated" 
                                 id="translation-content-${announcement.id}"
                                ${announcement.translations ? Object.entries(announcement.translations).map(([lang, text]) => `
                                    <div class="translation-item">
                                        <h4>${lang.charAt(0).toUpperCase() + lang.slice(1)}</h4>
                                        <div class="translation-text">
                                            ${text}
                                        </div>                                        ${announcement.audio_paths && announcement.audio_paths[lang] ? `
                                            <div style="display: flex; align-items: center; gap: 10px; margin-top: 10px;">
                                                <button class="audio-btn" onclick="playAudio('/audio/${announcement.audio_paths[lang]}')" title="Play Audio">
                                                    🔊 Play
                                                </button>
                                                <button class="audio-btn mic-btn" onclick="startRecording('${lang}', this)" title="Record Voice">
                                                    🎤 Record
                                                </button>
                                                <audio id="audio-${lang}" src="/audio/${announcement.audio_paths[lang]}" style="display: none;"></audio>
                                            </div>
                                        ` : `
                                            <div style="display: flex; align-items: center; gap: 10px; margin-top: 10px;">
                                                <button class="audio-btn" onclick="translateAndGetAudio('${announcement.text}', '${announcement.source_lang || 'english'}', '${lang}', this)" title="Translate & Play">
                                                    🌐 Translate & Play
                                                </button>
                                                <button class="audio-btn mic-btn" onclick="startRecording('${lang}', this)" title="Record Voice">
                                                    🎤 Record
                                                </button>
                                            </div>
                                        `}
                                    </div>
                                `).join('') : ''}
                            </div>
                        </div>
                          <div class="card-footer">
                            <span>${announcement.timestamp ? formatDate(announcement.timestamp) : 'No timestamp'}</span>
                            <div style="display: flex; align-items: center; gap: 15px;">
                                <div class="delivery-methods">
                                    ${channels.includes('voice') ? '<span class="delivery-icon">🔊</span>' : ''}
                                    ${channels.includes('sms') ? '<span class="delivery-icon">📱</span>' : ''}
                                </div>
                                <button class="delete-btn" onclick="deleteAnnouncement('${announcement.timestamp}')">
                                    🗑️ Delete
                                </button>
                            </div>
                        </div>
                    </div>
                `;
            }).join('');
        }        // Helper function to toggle translation visibility with smooth animation
        window.toggleTranslation = function(element) {
            const content = element.nextElementSibling;
            const languageCount = element.textContent.match(/\((\d+)\s+languages\)/)[1];
            
            // Add transition class if not already present
            if (!content.classList.contains('translation-animated')) {
                content.classList.add('translation-animated');
            }
            
            if (content.classList.contains('translation-visible')) {
                content.classList.remove('translation-visible');
                element.classList.remove('translation-active');
                element.setAttribute('aria-expanded', 'false');
                element.innerHTML = `▼ Show Translations (${languageCount} languages)`;
            } else {
                content.classList.add('translation-visible');
                element.classList.add('translation-active');
                element.setAttribute('aria-expanded', 'true');
                element.innerHTML = `▲ Hide Translations (${languageCount} languages)`;
            }
        };
        
        // Helper function to format date
        function formatDate(timestamp) {
            const date = new Date(timestamp);
            return date.toLocaleDateString('en-IN', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        }

        // Function to play audio
        window.playAudio = function(audioSrc) {
            // Stop any currently playing audio
            document.querySelectorAll('audio').forEach(audio => {
                audio.pause();
                audio.currentTime = 0;
            });

            // Find or create audio element
            let audioEl = document.querySelector(`audio[src="${audioSrc}"]`);
            if (!audioEl) {
                audioEl = document.createElement('audio');
                audioEl.src = audioSrc;
                document.body.appendChild(audioEl);
            }

            // Play the audio
            audioEl.play().catch(err => {
                console.error('Error playing audio:', err);
                alert('Error playing audio. Please try again.');
            });
        };

        // Function to translate and get audio
        async function translateAndGetAudio(text, srcLang, tgtLang, buttonElement) {
            try {
                // Show loading state
                const originalText = buttonElement.innerHTML;                buttonElement.innerHTML = '⏳ Translating...';
                buttonElement.classList.add('loading');
                buttonElement.disabled = true;

                const response = await fetch('/api/translate-announcement', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        text: text,
                        srcLang: srcLang,
                        tgtLang: tgtLang
                    })
                });                    const result = await response.json();
                    if (result.status === 'success') {
                        // Update the translation text
                        const translationItem = buttonElement.closest('.translation-item');
                        const translationText = translationItem.querySelector('.translation-text');
                        translationText.textContent = result.translatedText;
                        
                        // Add voice controls
                        const voiceControls = document.createElement('div');
                        voiceControls.className = 'voice-controls';
                        voiceControls.innerHTML = `
                            <button class="mic-btn" title="Record Voice">
                                🎤 Record
                            </button>
                            <button class="audio-btn" onclick="playAudio('/audio/${result.audioFile}')" title="Play Audio">
                                🔊 Play
                            </button>
                            <audio id="audio-${tgtLang}" src="/audio/${result.audioFile}" style="display: none;"></audio>
                        `;

                    // Create audio element and play button
                    buttonElement.innerHTML = '🔊 Play';
                    buttonElement.onclick = () => playAudio(`/audio/${result.audioFile}`);

                    // Create hidden audio element
                    const audio = document.createElement('audio');
                    audio.src = `/audio/${result.audioFile}`;
                    audio.style.display = 'none';
                    audio.id = `audio-${tgtLang}`;
                    buttonElement.parentNode.appendChild(audio);

                    // Play the audio
                    playAudio(`/audio/${result.audioFile}`);
                } else {
                    throw new Error(result.message);
                }
            } catch (error) {
                console.error('Translation error:', error);
                buttonElement.innerHTML = '❌ Error';
                setTimeout(() => {
                    buttonElement.innerHTML = '🔄 Retry';
                    buttonElement.disabled = false;
                }, 2000);
            }
        }

        let mediaRecorder;
        let audioChunks = [];
        let isRecording = false;

        // Function to handle recording
        async function startRecording(language) {
            const micBtn = event.currentTarget;
            
            if (!isRecording) {
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                    mediaRecorder = new MediaRecorder(stream);
                    audioChunks = [];
                    
                    mediaRecorder.ondataavailable = (event) => {
                        audioChunks.push(event.data);
                    };
                    
                    mediaRecorder.onstop = async () => {
                        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                        const formData = new FormData();
                        formData.append('audio', audioBlob);
                        formData.append('language', language);
                        
                        try {
                            micBtn.innerHTML = '⏳ Processing...';
                            micBtn.classList.add('loading');
                            
                            const response = await fetch('/api/process-voice', {
                                method: 'POST',
                                body: formData
                            });
                            
                            const result = await response.json();
                            if (result.success) {
                                // Update the translation text and audio
                                const translationItem = micBtn.closest('.translation-item');
                                const translationText = translationItem.querySelector('.translation-text');
                                const audio = translationItem.querySelector('audio');
                                
                                translationText.textContent = result.translation;
                                audio.src = result.audioUrl;
                                
                                micBtn.innerHTML = '🎤 Record';
                                micBtn.classList.remove('recording', 'loading');
                            }
                        } catch (error) {
                            console.error('Error processing voice:', error);
                            micBtn.innerHTML = '❌ Error';
                            setTimeout(() => {
                                micBtn.innerHTML = '🎤 Record';
                                micBtn.classList.remove('recording', 'loading');
                            }, 2000);
                        }
                    };
                    
                    mediaRecorder.start();
                    isRecording = true;
                    micBtn.innerHTML = '⏺️ Recording...';
                    micBtn.classList.add('recording');
                    
                    // Auto-stop after 10 seconds
                    setTimeout(() => {
                        if (isRecording) {
                            stopRecording();
                        }
                    }, 10000);
                    
                } catch (err) {
                    console.error('Error accessing microphone:', err);
                    alert('Could not access microphone. Please check permissions.');
                }
            } else {
                stopRecording();
            }
        }
        
        function stopRecording() {
            if (mediaRecorder && isRecording) {
                mediaRecorder.stop();
                isRecording = false;
                mediaRecorder.stream.getTracks().forEach(track => track.stop());
            }
        }
        
        // Delete announcement function
        async function deleteAnnouncement(timestamp) {
            if (!confirm('Are you sure you want to delete this announcement?')) {
                return;
            }

            try {
                const response = await fetch(`/api/announcements/${timestamp}`, {
                    method: 'DELETE'
                });
                const result = await response.json();

                if (result.status === 'success') {
                    // Refresh the announcements list
                    loadAnnouncements();
                } else {
                    alert('Error deleting announcement: ' + result.message);
                }
            } catch (error) {
                alert('Error deleting announcement: ' + error.message);
            }
        }

        // Initial load of announcements
        loadAnnouncements();
        
        // Setup periodic refresh
        setInterval(loadAnnouncements, 30000); // Refresh every 30 seconds