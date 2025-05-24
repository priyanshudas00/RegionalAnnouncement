// Test translation functionality
document.addEventListener('DOMContentLoaded', function() {
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

    // Recording state
    const recordingState = {
        mediaRecorder: null,
        audioChunks: [],
        isRecording: false
    };

    // Test translation click handler
    testTranslationBtn.onclick = async function() {
        const text = document.getElementById('announcementText').value;
        const srcLang = document.getElementById('sourceLanguage').value;
        const targetLangs = Array.from(document.getElementById('targetLanguages').selectedOptions).map(opt => opt.value);
        
        if (!text || targetLangs.length === 0) {
            alert('Please enter text and select target languages');
            return;
        }

        let translationContainer = document.getElementById('testTranslationContainer');
        if (!translationContainer) {
            translationContainer = document.createElement('div');
            translationContainer.id = 'testTranslationContainer';
            translationContainer.className = 'translation-content show';
            testTranslationBtn.parentNode.insertBefore(translationContainer, testTranslationBtn.nextSibling);
        }
        
        try {
            translationContainer.innerHTML = `
                <div class="loading-container">
                    <div class="loading-spinner"></div>
                    <p>Processing translations...</p>
                </div>
            `;
            
            for (const tgtLang of targetLangs) {
                const response = await fetch('/api/translate-announcement', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text, srcLang, tgtLang })
                });
                
                const result = await response.json();
                if (result.status === 'success') {
                    const div = document.createElement('div');
                    div.className = 'translation-item';
                    div.innerHTML = `
                        <h4><i class="fas fa-language"></i> ${tgtLang.charAt(0).toUpperCase() + tgtLang.slice(1)}</h4>
                        <div class="translation-text">${result.translatedText}</div>
                        <div class="audio-controls">
                            <button class="audio-btn" onclick="playAudio('${result.audioFile}')" title="Play Audio">
                                <i class="fas fa-play"></i> Play
                            </button>
                            <button class="audio-btn mic-btn" onclick="recordTranslation('${tgtLang}')" title="Record Voice">
                                <i class="fas fa-microphone"></i> Record
                            </button>
                            <audio id="audio-${tgtLang}" src="/announcements/${result.audioFile}"></audio>
                        </div>
                    `;
                    translationContainer.appendChild(div);
                }
            }
        } catch (error) {
            translationContainer.innerHTML = `<p class="error">Error: ${error.message}</p>`;
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

    // Recording functionality
    window.recordTranslation = async function(language) {
        const micBtn = event.currentTarget;
        
        if (!recordingState.isRecording) {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                recordingState.mediaRecorder = new MediaRecorder(stream);
                recordingState.audioChunks = [];
                
                recordingState.mediaRecorder.ondataavailable = (event) => {
                    recordingState.audioChunks.push(event.data);
                };
                
                recordingState.mediaRecorder.onstop = async () => {
                    const audioBlob = new Blob(recordingState.audioChunks, { type: 'audio/wav' });
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
                            micBtn.innerHTML = '<i class="fas fa-microphone"></i> Record';
                            micBtn.classList.remove('recording', 'loading');
                            // Update the audio element and play it
                            const audioEl = micBtn.parentElement.querySelector('audio');
                            audioEl.src = `/announcements/${result.audioFile}`;
                            playAudio(result.audioFile);
                        }
                    } catch (error) {
                        console.error('Error processing voice:', error);
                        micBtn.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Error';
                        setTimeout(() => {
                            micBtn.innerHTML = '<i class="fas fa-microphone"></i> Record';
                            micBtn.classList.remove('recording', 'loading');
                        }, 2000);
                    }
                };
                
                recordingState.mediaRecorder.start();
                recordingState.isRecording = true;
                micBtn.innerHTML = '<i class="fas fa-stop-circle"></i> Stop Recording';
                micBtn.classList.add('recording');
                
                // Auto-stop after 10 seconds
                setTimeout(() => {
                    if (recordingState.isRecording) {
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
        if (recordingState.mediaRecorder && recordingState.isRecording) {
            recordingState.mediaRecorder.stop();
            recordingState.isRecording = false;
            recordingState.mediaRecorder.stream.getTracks().forEach(track => track.stop());
        }
    }
});
