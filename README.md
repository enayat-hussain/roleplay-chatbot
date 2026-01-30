# AI RPG Adventure Game

A real-time streaming RPG chatbot with **multi-provider support** that creates interactive text-based adventures using various AI services.

![UI Preview](https://img.shields.io/badge/UI-Modern%20Dark%20Sidebar-1e1e2e?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.8+-3776ab?style=flat-square&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-2.3-black?style=flat-square&logo=flask&logoColor=white)

## Features

### Core Features
* **Live Streaming**: Watch AI responses generate in real-time with proper Unicode handling
* **Multi-Provider Support**: Works with OpenAI, Anthropic, Ollama, Groq, LM Studio, and more
* **Dynamic Provider Switching**: Change AI providers and models during gameplay
* **Interactive RPG**: Dynamic story with player choices and intelligent final step handling
* **Auto-play Mode**: Watch AI vs AI gameplay with configurable delays
* **Cross-Platform**: Works consistently on Mac, Windows, and Linux
* **Modern UI**: Clean, professional interface inspired by ChatGPT/Claude with dark sidebar

### Supported AI Providers
* **OpenAI** (GPT-4, GPT-4o, GPT-3.5-turbo)
* **Anthropic** (Claude-3.5 Sonnet, Claude-3 Haiku, Claude-3 Opus)
* **Google** (Gemini 2.5 Flash-Lite, Gemini 2.0 Flash)
* **DeepSeek** (DeepSeek Chat, DeepSeek Coder, DeepSeek Reasoner)
* **Ollama** (Local: Llama 3.1, Mistral, CodeLlama, Vicuna, Gemma)
* **Groq** (Fast inference: Llama, Mixtral, Gemma models)
* **LM Studio** (Local model server)
* **Custom Providers** (Any OpenAI-compatible API)

## Quick Start

### Prerequisites

**Choose Your AI Provider:**

**For Local AI (Recommended for beginners):**
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull a model
ollama pull llama3.1

# Start the server
ollama serve
```

**For Cloud AI:**
- Get API keys from OpenAI, Anthropic, Google, DeepSeek, or Groq
- No local setup required

### Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/enayat-hussain/roleplay-chatbot.git
   cd roleplay-chatbot
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables** (Optional - can set via UI)
   ```bash
   cp .env.example .env
   ```

   Example `.env` configuration:
   ```env
   # OpenAI
   OPENAI_API_KEY=your_openai_key_here

   # Anthropic
   ANTHROPIC_API_KEY=your_anthropic_key_here

   # Groq
   GROQ_API_KEY=your_groq_key_here

   # Generic fallback
   API_KEY=your_api_key_here
   ```

4. **Run the Application**
   ```bash
   python app.py
   ```

5. **Open in Browser**
   * Navigate to [http://127.0.0.1:7860](http://127.0.0.1:7860)
   * Select your AI provider from the sidebar
   * Add API key if required
   * Click "Start Adventure" to begin!

## Usage

### Getting Started
1. **Select Provider**: Choose from OpenAI, Anthropic, Ollama, etc. in the dark sidebar
2. **Select Model**: Pick the specific model you want to use
3. **Add API Key**: Enter your API key (if required by provider)
4. **Set Max Steps**: Choose adventure length (1-20 steps)
5. **Start Playing**: Click "Start Adventure" and make choices!

### Game Modes

#### Manual Mode
* Click "Start Adventure" to begin
* Use "Next Step" to advance step by step
* Watch responses stream in real-time
* Final steps automatically provide conclusions

#### Auto-play Mode
* Click "Auto-play" for hands-free adventure
* Set delay between steps (0-10 seconds)
* Perfect for demonstrations or relaxed gameplay
* Watch AI make choices and respond automatically

#### Controls
* **New Game**: Reset and start fresh with "+ New Game" button
* **Start Adventure**: Begin a new game
* **Next Step**: Take the next step in the adventure
* **Auto-play**: Let the AI play automatically

## Project Structure

```
roleplay-chatbot/
├── app.py                # Main Flask application
├── chatbot.py            # Universal AI client with auto-detection of LLMs
├── game_logic.py         # RPG game state management + intelligent endings
├── config.py             # Configuration settings (paths, constants, defaults)
│
├── templates/            # HTML templates
│   └── index.html        # Main UI template
│
├── static/               # Static assets
│   ├── css/
│   │   └── style.css     # UI styling (dark sidebar, light chat)
│   └── js/
│       └── app.js        # Frontend JavaScript (streaming, interactions)
│
├── requirements.txt      # Python dependencies
├── .env.example          # Template for environment variables
│
├── prompts/              # Customizable prompt templates
│   ├── gm_prompt.txt     # Game Master instructions
│   └── rp_prompt.txt     # Player role instructions
│
├── chat_logs/            # Auto-saved conversation logs (.txt files)
│
└── README.md             # Project documentation
```

## Configuration

### Default Provider URLs and Models

| Provider | Default URL | Default Model | API Key Required |
|----------|-------------|---------------|------------------|
| **OpenAI (GPT)** | `https://api.openai.com/v1/chat/completions` | `gpt-4o-mini` | Yes |
| **Anthropic (Claude)** | `https://api.anthropic.com/v1/messages` | `claude-3-haiku-20240307` | Yes |
| **Google (Gemini)** | `https://generativelanguage.googleapis.com/v1beta/openai/chat/completions` | `gemini-2.0-flash` | Yes |
| **DeepSeek** | `https://api.deepseek.com/chat/completions` | `deepseek-chat` | Yes |
| **Ollama (Local)** | `http://localhost:11434/v1/chat/completions` | `llama3.1` | No |
| **Groq** | `https://api.groq.com/openai/v1/chat/completions` | `llama-3.1-8b-instant` | Yes |
| **LM Studio** | `http://localhost:1234/v1/chat/completions` | `local-model` | No |

### Environment Variables

| Variable            | Default                    | Description                                  |
|---------------------|----------------------------|----------------------------------------------|
| `API_PROVIDER`      | auto                       | API provider (auto-detected)                |
| `API_URL`           | varies by provider         | API endpoint URL                             |
| `MODEL`             | varies by provider         | AI model name                                |
| `API_KEY`           | None                       | API key for authentication                   |
| `SERVER_HOST`       | 127.0.0.1                  | Flask server host                            |
| `SERVER_PORT`       | 7860                       | Flask server port                            |
| `DEFAULT_MAX_STEPS` | 5                          | Default number of game steps                 |
| `MAX_STEPS_LIMIT`   | 20                         | Maximum allowed steps                        |
| `DEFAULT_DELAY`     | 2                          | Default delay between steps (seconds)        |
| `MAX_DELAY`         | 10                         | Maximum delay between steps                  |

### Custom Prompts

Customize the game experience by editing:
* `prompts/gm_prompt.txt` - Instructions for the Game Master AI
* `prompts/rp_prompt.txt` - Instructions for the Player AI (auto-play mode)

## Local AI Setup

### Ollama (Recommended)
```bash
# Install and setup
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull llama3.1
ollama serve
```
- URL: `http://localhost:11434/v1/chat/completions`
- No API key required
- Best for privacy and offline use

### LM Studio
1. Download LM Studio from their website
2. Load your preferred model
3. Start the local server
- URL: `http://localhost:1234/v1/chat/completions`
- No API key required

## Troubleshooting

### Common Issues

**Connection Errors**
* Verify API key is correct
* Check if local servers are running (`ollama serve`)
* Try a different provider

**Provider Issues**
* Try switching providers via the sidebar dropdown
* Test different models for your provider
* Check API rate limits and billing status

**Response Quality**
* Try different models within the same provider
* Adjust the number of steps for longer adventures

### Provider-Specific Support

**OpenAI**: Check API billing and rate limits
**Anthropic**: Verify API key and model access
**Google Gemini**: Get API key from Google AI Studio (https://aistudio.google.com)
**DeepSeek**: Get API key from DeepSeek platform (https://platform.deepseek.com)
**Ollama**: Ensure `ollama serve` is running
**Groq**: Check free tier limits

## Requirements

* Python 3.8+
* AI provider access (local server OR cloud API key)
* Modern web browser

## Contributing

Areas for improvement:
* Additional AI provider support
* Enhanced prompt templates
* UI/UX improvements

1. Fork the repository
2. Create a feature branch
3. Test thoroughly with multiple providers
4. Submit a pull request

---

*Built with Flask - Supporting 8+ AI providers!*
