// RPG Adventure - Flask Frontend JavaScript

const sessionId = 'session_' + Date.now();
let isProcessing = false;
let gameStarted = false;

// DOM Elements
const providerSelect = document.getElementById('providerSelect');
const modelSelect = document.getElementById('modelSelect');
const apiKeyInput = document.getElementById('apiKey');
const apiUrlInput = document.getElementById('apiUrl');
const stepsSlider = document.getElementById('stepsSlider');
const stepsValue = document.getElementById('stepsValue');
const delaySlider = document.getElementById('delaySlider');
const delayValue = document.getElementById('delayValue');
const chatbox = document.getElementById('chatbox');
const statusBar = document.getElementById('statusBar');
const modelBadge = document.getElementById('modelBadge');
const startBtn = document.getElementById('startBtn');
const nextBtn = document.getElementById('nextBtn');
const autoplayBtn = document.getElementById('autoplayBtn');
const newGameBtn = document.getElementById('newGameBtn');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadProviderModels(providerSelect.value);
    updateSliderLabels();
    setupEventListeners();
});

function setupEventListeners() {
    // Provider change
    providerSelect.addEventListener('change', () => {
        loadProviderModels(providerSelect.value);
    });

    // Slider updates
    stepsSlider.addEventListener('input', updateSliderLabels);
    delaySlider.addEventListener('input', updateSliderLabels);

    // Buttons
    startBtn.addEventListener('click', startGame);
    nextBtn.addEventListener('click', nextStep);
    autoplayBtn.addEventListener('click', autoplay);
    newGameBtn.addEventListener('click', resetGame);
}

function updateSliderLabels() {
    stepsValue.textContent = stepsSlider.value;
    delayValue.textContent = delaySlider.value;
}

async function loadProviderModels(provider) {
    try {
        const response = await fetch(`/api/provider/${encodeURIComponent(provider)}`);
        const config = await response.json();

        modelSelect.innerHTML = '';
        config.models.forEach(model => {
            const option = document.createElement('option');
            option.value = model;
            option.textContent = model;
            if (model === config.default_model) {
                option.selected = true;
            }
            modelSelect.appendChild(option);
        });

        // Show/hide API key based on requirement
        apiKeyInput.style.display = config.requires_key ? 'block' : 'none';

        // Update model badge
        modelBadge.textContent = `${provider} - ${config.default_model}`;
    } catch (error) {
        console.error('Error loading provider config:', error);
    }
}

function setStatus(message) {
    statusBar.innerHTML = message;
}

function setProcessing(processing) {
    isProcessing = processing;
    startBtn.disabled = processing;
    nextBtn.disabled = processing || !gameStarted;
    autoplayBtn.disabled = processing;
}

function addMessage(role, content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    messageDiv.innerHTML = formatContent(content);
    chatbox.appendChild(messageDiv);
    chatbox.scrollTop = chatbox.scrollHeight;
    return messageDiv;
}

function updateLastBotMessage(content) {
    const messages = chatbox.querySelectorAll('.message.bot');
    if (messages.length > 0) {
        const lastMessage = messages[messages.length - 1];
        lastMessage.innerHTML = formatContent(content);
        chatbox.scrollTop = chatbox.scrollHeight;
    }
}

function formatContent(content) {
    // Basic markdown-like formatting
    return content
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/\n/g, '<br>');
}

function clearChat() {
    chatbox.innerHTML = '';
}

function getRequestData() {
    return {
        provider: providerSelect.value,
        model: modelSelect.value,
        api_key: apiKeyInput.value,
        api_url: apiUrlInput.value,
        max_steps: parseInt(stepsSlider.value),
        delay: parseInt(delaySlider.value),
        session_id: sessionId
    };
}

async function startGame() {
    if (isProcessing) return;

    setProcessing(true);
    clearChat();
    setStatus('<strong>Status:</strong> Starting adventure...');
    modelBadge.textContent = `${providerSelect.value} - ${modelSelect.value}`;

    let currentContent = '';
    addMessage('bot', '');

    try {
        const response = await fetch('/api/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(getRequestData())
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const text = decoder.decode(value);
            const lines = text.split('\n');

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));

                        if (data.type === 'chunk') {
                            currentContent += data.content;
                            updateLastBotMessage(currentContent);
                        } else if (data.type === 'done') {
                            gameStarted = true;
                            setStatus(`<strong>Status:</strong> Game started. Step ${data.step}/${stepsSlider.value}`);
                        } else if (data.type === 'error') {
                            setStatus(`<strong>Error:</strong> ${data.message}`);
                        }
                    } catch (e) {
                        // Ignore parse errors for incomplete chunks
                    }
                }
            }
        }
    } catch (error) {
        setStatus(`<strong>Error:</strong> ${error.message}`);
    }

    setProcessing(false);
}

async function nextStep() {
    if (isProcessing || !gameStarted) return;

    setProcessing(true);
    setStatus('<strong>Status:</strong> Taking next step...');

    let currentContent = '';
    let choice = null;

    try {
        const response = await fetch('/api/step', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(getRequestData())
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let messageAdded = false;

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const text = decoder.decode(value);
            const lines = text.split('\n');

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));

                        if (data.type === 'chunk') {
                            if (data.choice && !messageAdded) {
                                // Add player choice
                                addMessage('user', data.choice.toString());
                                addMessage('bot', '');
                                messageAdded = true;
                            }
                            currentContent += data.content;
                            updateLastBotMessage(currentContent);
                        } else if (data.type === 'done') {
                            const status = data.complete
                                ? `<strong>Status:</strong> Adventure complete! (${data.step} steps)`
                                : `<strong>Status:</strong> Step ${data.step}/${stepsSlider.value}`;
                            setStatus(status);
                        } else if (data.type === 'error') {
                            setStatus(`<strong>Error:</strong> ${data.message}`);
                        }
                    } catch (e) {
                        // Ignore parse errors
                    }
                }
            }
        }
    } catch (error) {
        setStatus(`<strong>Error:</strong> ${error.message}`);
    }

    setProcessing(false);
}

async function autoplay() {
    if (isProcessing) return;

    setProcessing(true);
    clearChat();
    setStatus('<strong>Status:</strong> Auto-play starting...');
    modelBadge.textContent = `${providerSelect.value} - ${modelSelect.value}`;

    let currentContent = '';
    let currentStep = 0;

    try {
        const response = await fetch('/api/autoplay', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(getRequestData())
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let lastMessageType = null;

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const text = decoder.decode(value);
            const lines = text.split('\n');

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));

                        if (data.type === 'status') {
                            setStatus(`<strong>Status:</strong> ${data.message}`);
                        } else if (data.type === 'chunk') {
                            if (data.choice && lastMessageType !== 'user') {
                                // Add player choice
                                addMessage('user', data.choice.toString());
                                addMessage('bot', '');
                                currentContent = '';
                                lastMessageType = 'user';
                            } else if (!lastMessageType || lastMessageType === 'step_done') {
                                // Start new bot message
                                addMessage('bot', '');
                                currentContent = '';
                                lastMessageType = 'bot';
                            }
                            currentContent += data.content;
                            updateLastBotMessage(currentContent);
                        } else if (data.type === 'step_done') {
                            currentStep = data.step;
                            setStatus(`<strong>Status:</strong> Auto-play Step ${currentStep}/${stepsSlider.value}`);
                            lastMessageType = 'step_done';
                            currentContent = '';
                            gameStarted = true;
                        } else if (data.type === 'complete') {
                            setStatus(`<strong>Status:</strong> Auto-play complete! (${data.step} steps)`);
                        } else if (data.type === 'error') {
                            setStatus(`<strong>Error:</strong> ${data.message}`);
                        }
                    } catch (e) {
                        // Ignore parse errors
                    }
                }
            }
        }
    } catch (error) {
        setStatus(`<strong>Error:</strong> ${error.message}`);
    }

    setProcessing(false);
}

async function resetGame() {
    try {
        await fetch('/api/reset', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId })
        });
    } catch (e) {
        // Ignore reset errors
    }

    clearChat();
    gameStarted = false;
    setStatus('Ready to start your adventure. Configure your AI provider and click <strong>Start</strong>.');
    setProcessing(false);
}
