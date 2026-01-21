# AI RPG Adventure Game

A real-time streaming RPG chatbot with **multi-provider support** that creates interactive text-based adventures using various AI services.

![UI Preview](https://img.shields.io/badge/UI-Modern%20Dark%20Sidebar-1e1e2e?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.8+-3776ab?style=flat-square&logo=python&logoColor=white)
![Gradio](https://img.shields.io/badge/Gradio-4.0-orange?style=flat-square)

## Features

### Core Features
* **Live Streaming**: Watch AI responses generate in real-time with proper Unicode handling
* **Multi-Provider Support**: Works with OpenAI, Anthropic, Ollama, Groq, LM Studio, and more
* **Dynamic Provider Switching**: Change AI providers and models during gameplay
* **Interactive RPG**: Dynamic story with player choices and intelligent final step handling
* **Auto-play Mode**: Watch AI vs AI gameplay with configurable delays
* **Export Options**: Save adventures as Markdown or plain text
* **Connection Testing**: Built-in API connection diagnostics for all providers
* **Modern UI**: Clean, professional interface inspired by ChatGPT/Claude with dark sidebar

### Supported AI Providers
* **OpenAI** (GPT-4, GPT-4o, GPT-3.5-turbo)
* **Anthropic** (Claude-3.5 Sonnet, Claude-3 Haiku, Claude-3 Opus)
* **Ollama** (Local: Llama 3.1, Mistral, CodeLlama, Vicuna, Gemma)
* **Groq** (Fast inference: Llama, Mixtral, Gemma models)
* **LM Studio** (Local model server)
* **Text Generation WebUI** (oobabooga)
* **VLLM** (High-performance local serving)
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
- Get API keys from OpenAI, Anthropic, or Groq
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
4. **Set Max Steps**: Choose adventure length (1-100 steps)
5. **Start Playing**: Click "Start Adventure" and make choices!

### Game Modes

#### Manual Mode
* Click "Start Adventure" to begin
* Use "Next Step" to advance step by step
* Watch responses stream in real-time
* Final steps automatically provide 8-9 line conclusions

#### Auto-play Mode
* Click "Auto-play" for hands-free adventure
* Set delay between steps (0-10 seconds)
* Perfect for demonstrations or relaxed gameplay
* Watch AI make choices and respond automatically

#### Advanced Features
* **New Game**: Reset and start fresh with "+ New Game" button
* **Export & Save**: Save memorable adventures as Markdown/text
* **Game Statistics**: View detailed game information and progress

## Project Structure

```
roleplay-chatbot/
├── app.py                # Main Gradio application (UI + provider selection)
├── chatbot.py            # Universal AI client with auto-detection of LLMs
├── game_logic.py         # RPG game state management + intelligent endings
├── config.py             # Configuration settings (paths, constants, defaults)
├── prompts.py            # Centralized prompt definitions (optional helper)
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

The application comes with pre-configured settings for each provider:

| Provider | Default URL | Default Model | API Key Required |
|----------|-------------|---------------|------------------|
| **OpenAI (GPT)** | `https://api.openai.com/v1/chat/completions` | `gpt-4o-mini` | Yes |
| **Anthropic (Claude)** | `https://api.anthropic.com/v1/messages` | `claude-3-haiku-20240307` | Yes |
| **Ollama (Local)** | `http://localhost:11434/v1/chat/completions` | `llama3.1` | No |
| **Groq** | `https://api.groq.com/openai/v1/chat/completions` | `llama-3.1-8b-instant` | Yes |
| **LM Studio** | `http://localhost:1234/v1/chat/completions` | `local-model` | No |
| **Text Generation WebUI** | `http://localhost:5000/v1/chat/completions` | `local-model` | No |
| **VLLM** | `http://localhost:8000/v1/chat/completions` | `local-model` | No |

### Available Models by Provider

**OpenAI Models:**
- `gpt-4o` (latest GPT-4 Omni)
- `gpt-4o-mini` (cost-efficient, recommended)
- `gpt-4-turbo` (previous generation)
- `gpt-3.5-turbo` (legacy, cost-effective)

**Anthropic Models:**
- `claude-3-5-sonnet-20241022` (latest, most capable)
- `claude-3-haiku-20240307` (fast, cost-effective)
- `claude-3-opus-20240229` (most powerful, expensive)

**Groq Models:**
- `llama-3.1-8b-instant` (recommended, very fast)
- `meta-llama/llama-4-scout-17b-16e-instruct` (experimental)
- `gemma2-9b-it` (Google's Gemma model)

**Ollama Models:** (depends on what you have installed)
- `llama3.1` (recommended)
- `llama3:latest`
- `mistral`
- `codellama`
- `vicuna`
- `gemma:2b`

### Environment Variables

| Variable            | Default                    | Description                                  |
|---------------------|----------------------------|----------------------------------------------|
| `API_PROVIDER`      | auto                       | API provider (auto-detected)                |
| `API_URL`           | varies by provider         | API endpoint URL                             |
| `MODEL`             | varies by provider         | AI model name                                |
| `API_KEY`           | None                       | API key for authentication                   |
| `SERVER_HOST`       | 127.0.0.1                  | Gradio server host                           |
| `SERVER_PORT`       | 7860                       | Gradio server port                           |
| `DEFAULT_MAX_STEPS` | 5                          | Default number of game steps                 |
| `MAX_STEPS_LIMIT`   | 100                        | Maximum allowed steps                        |
| `DEFAULT_DELAY`     | 2                          | Default delay between steps (seconds)        |
| `MAX_DELAY`         | 10                         | Maximum delay between steps                  |
| `AI_TEMPERATURE`    | 0.8                        | AI creativity level (0.0-2.0)               |
| `AI_MAX_TOKENS`     | 500                        | Maximum tokens per response                  |

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

### Text Generation WebUI
```bash
git clone https://github.com/oobabooga/text-generation-webui.git
cd text-generation-webui
./start_linux.sh --api --listen
```
- URL: `http://localhost:5000/v1/chat/completions`

## Troubleshooting

### Recent Fixes Applied
* **Fixed Unicode/spelling issues** - Proper UTF-8 encoding handling
* **Improved streaming reliability** - Better error handling and fallbacks
* **Chat logs saving** - Each conversation now saved as a `.txt` file
* **Multi-LLM support** - App now works seamlessly with different LLM providers
* **Step-limited endings** - Story automatically ends after reaching max number of steps
* **UI overhaul** - Modern dark sidebar design with Catppuccin color scheme
* **Fixed alignment issues** - Chat box, status bar, and buttons properly aligned
* **Compact buttons** - Appropriately sized action buttons

### Common Issues

**Connection Errors**
* Verify API key is correct
* Check if local servers are running (`ollama serve`)
* Use Advanced Options to test connections

**Provider Issues**
* Try switching providers via the sidebar dropdown
* Test different models for your provider
* Check API rate limits and billing status

**Response Quality**
* Adjust temperature settings for creativity
* Try different models within the same provider
* Use the export feature to save good adventures

### System Status
Use the built-in connection testing features:
* **"Test Connection"** - Check current configuration in Advanced Options
* **"Show Game Info"** - View current game state and provider details

## Requirements

* Python 3.8+
* AI provider access (local server OR cloud API key)
* 4GB+ RAM (for local models)
* Internet connection (for cloud providers)

## Contributing

Areas for improvement:
* Additional AI provider support
* Enhanced prompt templates
* Better error handling
* UI/UX improvements

1. Fork the repository
2. Create a feature branch
3. Test thoroughly with multiple providers
4. Submit a pull request

## Support

If you encounter issues:

1. **Check troubleshooting section** above
2. **Use built-in connection testing** via Advanced Options
3. **Try different providers** - some may work better than others
4. **Review console output** for detailed error messages
5. **Open GitHub issue** with provider details and error logs

### Provider-Specific Support

**OpenAI**: Check API billing and rate limits
**Anthropic**: Verify API key and model access
**Ollama**: Ensure `ollama serve` is running
**Groq**: Check free tier limits
**Local Models**: Verify server status and model loading

---

*Built with Gradio and configurable AI APIs - Supporting 8+ providers!*
