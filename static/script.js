let steps = [];
let currentStepIndex = 0;
let currentTaskId = null;
let voiceEnabled = false;
const synth = window.speechSynthesis;

// Check auth on load
window.addEventListener('load', () => {
    const token = localStorage.getItem('authToken');
    
    // Load selected theme
    const selectedTheme = localStorage.getItem('selectedTheme') || 'ocean';
    applyTheme(selectedTheme);
    
    // Load stats
    loadStats();
    
    console.log(' App loaded. Auth token:', token ? 'Yes' : 'No');
});

async function getSteps() {
    const goal = document.getElementById('goalInput').value.trim();
    const taskContainer = document.getElementById('task-container');
    const inputSection = document.getElementById('input-section');
    const statsSection = document.getElementById('stats-section');

    if (!goal) {
        alert("Please type a goal first!");
        return;
    }

    inputSection.classList.add('hidden');
    taskContainer.classList.remove('hidden');
    statsSection.classList.add('hidden');
    document.getElementById('current-step-text').innerText = "Thinking... ";

    try {
        const token = localStorage.getItem('authToken') || '';
        console.log(' Sending request to decompose goal:', goal);
        
        const response = await fetch('/api/decompose', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': token
            },
            body: JSON.stringify({ goal: goal })
        });

        console.log(' Response status:', response.status);
        const data = await response.json();
        console.log(' Response data:', data);

        if (!response.ok) {
            alert("Error: " + (data.error || "Unknown error"));
            inputSection.classList.remove('hidden');
            taskContainer.classList.add('hidden');
            statsSection.classList.remove('hidden');
            return;
        }

        if (data.success || data.steps) {
            let cleanText = data.steps;
            if (typeof cleanText === 'string') {
                cleanText = cleanText.replace(/```json/g, '').replace(/```/g, '').trim();
                steps = JSON.parse(cleanText);
            } else {
                steps = cleanText;
            }

            console.log(' Steps parsed:', steps);
            currentStepIndex = 0;
            currentTaskId = data.task_id;
            showStep();

            if (voiceEnabled) {
                speak("I've broken down your task. Let's start with the first step!");
            }
        } else {
            alert("Error: " + (data.error || "Unknown error"));
            inputSection.classList.remove('hidden');
            taskContainer.classList.add('hidden');
            statsSection.classList.remove('hidden');
        }
    } catch (error) {
        console.error(' Fetch error:', error);
        alert("Something went wrong: " + error.message);
        inputSection.classList.remove('hidden');
        taskContainer.classList.add('hidden');
        statsSection.classList.remove('hidden');
    }
}

function showStep() {
    if (currentStepIndex < steps.length) {
        const stepText = steps[currentStepIndex];
        console.log(` Showing step ${currentStepIndex + 1}/${steps.length}: ${stepText}`);
        
        document.getElementById('current-step-text').innerText = stepText;
        updateProgress();

        if (voiceEnabled) {
            speak(stepText);
        }
    } else {
        document.getElementById('current-step-text').innerText = " You are a legend!";
        document.querySelector('.done-btn').style.display = 'none';
        document.querySelector('.skip-btn').style.display = 'none';
        document.querySelector('.back-btn').style.display = 'inline-block';
        document.querySelector('.restart-btn').style.display = 'inline-block';
        
        // Update progress bar to 100%
        document.getElementById('progress-bar').style.width = '100%';
        
        fireConfetti();

        if (voiceEnabled) {
            speak("Congratulations! You've completed all steps!");
        }
        
        // SAVE COMPLETION TO DATABASE
        saveTaskCompletion();
    }
}

function completeTask() {
    confetti({ particleCount: 30, spread: 50, origin: { y: 0.7 } });

    if (voiceEnabled) {
        speak("Great job! Moving to the next step.");
    }

    currentStepIndex++;
    showStep();
}

function skipStep() {
    if (voiceEnabled) {
        speak("Skipping this step. Moving to the next one.");
    }

    currentStepIndex++;
    showStep();
}

// SAVE TASK COMPLETION
async function saveTaskCompletion() {
    if (!currentTaskId) {
        console.log(' No task ID, skipping save (guest user)');
        return;
    }

    const token = localStorage.getItem('authToken');
    if (!token) {
        console.log(' No auth token, cannot save completion');
        return;
    }

    try {
        console.log(' Saving task completion for task ID:', currentTaskId);
        
        const response = await fetch(`/api/task/${currentTaskId}/complete-step`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': token
            },
            body: JSON.stringify({ step_index: steps.length - 1 })
        });

        const data = await response.json();
        console.log(' Task saved to database:', data);
        
        // Reload stats to show updated count
        loadStats();
        
    } catch (error) {
        console.error(' Error saving task:', error);
    }
}

// GO BACK WITHOUT REFRESH
function goBack() {
    const taskContainer = document.getElementById('task-container');
    const inputSection = document.getElementById('input-section');
    const statsSection = document.getElementById('stats-section');
    
    // Reset everything
    steps = [];
    currentStepIndex = 0;
    currentTaskId = null;
    document.getElementById('goalInput').value = '';
    document.getElementById('current-step-text').innerText = '';
    document.getElementById('progress-bar').style.width = '0%';
    
    // Show/hide sections
    taskContainer.classList.add('hidden');
    inputSection.classList.remove('hidden');
    statsSection.classList.remove('hidden');
    
    // Show buttons again
    document.querySelector('.done-btn').style.display = 'inline-block';
    document.querySelector('.skip-btn').style.display = 'inline-block';
    document.querySelector('.back-btn').style.display = 'none';
    document.querySelector('.restart-btn').style.display = 'none';
    
    // Stop any voice
    synth.cancel();
    
    console.log(' Back to home');
}

// RESTART BUTTON
function restart() {
    // Same as back button - resets everything
    goBack();
    console.log(' Restarted');
}

function updateProgress() {
    // Ensure progress bar fills completely at the end
    if (currentStepIndex === steps.length - 1) {
        // On the last step, fill bar to 100%
        document.getElementById('progress-bar').style.width = '100%';
    } else {
        // Calculate percentage: (current + 1) / total * 100
        const percent = ((currentStepIndex + 1) / steps.length) * 100;
        document.getElementById('progress-bar').style.width = percent + '%';
    }
    
    console.log(` Progress: ${currentStepIndex + 1}/${steps.length} (${((currentStepIndex + 1) / steps.length * 100).toFixed(0)}%)`);
}

function fireConfetti() {
    var duration = 3 * 1000;
    var animationEnd = Date.now() + duration;
    var defaults = { startVelocity: 30, spread: 360, ticks: 60, zIndex: 0 };

    var interval = setInterval(function() {
        var timeLeft = animationEnd - Date.now();
        if (timeLeft <= 0) return clearInterval(interval);
        var particleCount = 50 * (timeLeft / duration);
        confetti(Object.assign({}, defaults, {
            particleCount,
            origin: { x: Math.random(), y: Math.random() - 0.2 }
        }));
    }, 250);
}

// ============ VOICE FEATURES ============

function toggleVoice() {
    voiceEnabled = !voiceEnabled;
    const voiceBtn = document.getElementById('voiceBtn');
    
    if (voiceEnabled) {
        voiceBtn.style.background = '#4caf50';
        voiceBtn.style.color = 'white';
        speak("Voice assistant enabled. I will read all steps aloud.");
        console.log(' Voice enabled');
    } else {
        voiceBtn.style.background = '';
        voiceBtn.style.color = '';
        synth.cancel();
        console.log(' Voice disabled');
    }
}

function speak(text) {
    if (!voiceEnabled || !synth || !text) return;

    synth.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.95;
    utterance.pitch = 1;
    utterance.volume = 1;
    utterance.lang = 'en-US';
    
    // Use preferred voice
    setTimeout(() => {
        const voices = synth.getVoices();
        if (voices.length > 0) {
            // Try to use a female voice first
            const femaleVoice = voices.find(v => v.name.includes('Female') || v.name.includes('female'));
            utterance.voice = femaleVoice || voices[0];
        }
        synth.speak(utterance);
    }, 100);
}

// ============ VOICE INPUT (SPEECH RECOGNITION) ============

function startListening() {
    const SpeechRecognition = window.SpeechRecognition || 
                             window.webkitSpeechRecognition || 
                             window.mozSpeechRecognition || 
                             window.msSpeechRecognition;

    if (!SpeechRecognition) {
        alert(" Your browser doesn't support voice input!\n\n Use: Chrome, Edge, or Safari\n Avoid: Firefox");
        return;
    }

    const recognition = new SpeechRecognition();
    
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = 'en-US';
    recognition.maxAlternatives = 1;

    const micBtn = document.querySelector('.mic-btn');
    const goalInput = document.getElementById('goalInput');
    
    let isListening = false;
    let speechDetected = false;

    recognition.onstart = () => {
        console.log(' [START] Listening now... Please speak clearly!');
        isListening = true;
        speechDetected = false;
        micBtn.classList.add('listening');
        micBtn.style.background = '#ff4d4d';
        micBtn.textContent = '';
        
        if (voiceEnabled) {
            speak("I'm listening. Please speak your goal clearly.");
        }
        
        setTimeout(() => {
            if (!speechDetected && isListening) {
                console.log(' [TIMEOUT] No speech detected, stopping...');
                recognition.abort();
            }
        }, 10000);
    };

    recognition.onend = () => {
        console.log(' [END] Stopped listening');
        isListening = false;
        micBtn.classList.remove('listening');
        micBtn.style.background = '';
        micBtn.textContent = '';
    };

    recognition.onerror = (event) => {
        console.error(' [ERROR] Speech recognition error:', event.error);
        isListening = false;
        micBtn.classList.remove('listening');
        micBtn.style.background = '';
        
        let errorMsg = '';
        switch(event.error) {
            case 'no-speech':
                errorMsg = " No speech detected. Please speak louder and try again.";
                break;
            case 'audio-capture':
                errorMsg = " Microphone not found or blocked. Check browser permissions!";
                break;
            case 'network':
                errorMsg = " Network error. Check your internet connection.";
                break;
            case 'not-allowed':
                errorMsg = " Microphone access denied. Allow access in browser settings!";
                break;
            default:
                errorMsg = " Error: " + event.error;
        }
        
        alert(errorMsg);
    };

    recognition.onresult = (event) => {
        let finalTranscript = '';
        
        for (let i = event.resultIndex; i < event.results.length; i++) {
            const transcript = event.results[i][0].transcript;
            
            if (event.results[i].isFinal) {
                finalTranscript += transcript + ' ';
                speechDetected = true;
                console.log(' [FINAL] Recognized:', transcript);
            } else {
                console.log(' [INTERIM] Hearing:', transcript);
            }
        }

        if (finalTranscript) {
            goalInput.value = finalTranscript.trim();
            console.log(' Updated input field:', goalInput.value);

            if (voiceEnabled) {
                speak("Got it. Analyzing your task now.");
            }

            setTimeout(() => {
                getSteps();
            }, 1000);
        }
    };

    try {
        recognition.start();
        console.log(' [REQUEST] Starting speech recognition...');
    } catch (error) {
        console.error(' Failed to start recognition:', error);
        alert("Error starting microphone: " + error.message);
    }
}

// ============ THEME MANAGEMENT ============

function toggleThemeMenu() {
    const menu = document.getElementById('themeMenu');
    if (menu) {
        menu.classList.toggle('hidden');
    }
}

function switchTheme(theme) {
    applyTheme(theme);
    localStorage.setItem('selectedTheme', theme);
    const menu = document.getElementById('themeMenu');
    if (menu) {
        menu.classList.add('hidden');
    }
    console.log(' Theme changed to:', theme);
}

function applyTheme(theme) {
    document.body.className = `light-mode theme-${theme}`;
}

// ============ STATS ============

async function loadStats() {
    const token = localStorage.getItem('authToken');

    try {
        const response = await fetch('/api/user/profile', {
            headers: { 'Authorization': token || '' }
        });

        if (response.ok) {
            const user = await response.json();
            const tasksCompleted = document.getElementById('tasksCompleted');
            if (tasksCompleted) {
                tasksCompleted.innerText = user.total_tasks_completed || 0;
                console.log(' Tasks completed updated:', user.total_tasks_completed);
            }
        }
    } catch (error) {
        console.error(' Error loading stats:', error);
    }
}

// ============ AUTH ============

function logout() {
    localStorage.removeItem('authToken');
    localStorage.removeItem('user');
    console.log(' Logged out');
    window.location.href = '/';
}
