# 🎲 AI RPG Adventure Game

A real-time streaming RPG chatbot powered by Ollama and Gradio that creates interactive text-based adventures.

## ✨ Features

- **Live Streaming**: Watch AI responses generate in real-time
- **Interactive RPG**: Dynamic story with player choices
- **Auto-play Mode**: Watch AI vs AI gameplay
- **Configurable**: Easy customization through environment variables
- **Export Options**: Save adventures as Markdown or plain text
- **Connection Testing**: Built-in Ollama connection diagnostics

## 🚀 Quick Start

### Prerequisites

1. **Install Ollama**
   ```bash
   # Download from https://ollama.ai or use package manager
   curl -fsSL https://ollama.ai/install.sh | sh
   ```

2. **Pull Required Model**
   ```bash
   ollama pull llama3
   ```

3. **Start Ollama Server**
   ```bash
   ollama serve
   ```

### Installation

1. **Clone the Repository**
   ```bash
   git clone <your-repo-url>
   cd roleplay-chatbot
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment** (Optional)
   ```bash
   cp .env.example .env
   # Edit .env file with your preferences
   ```

4. **Run the Application**
   ```bash
   python app.py
   ```

5. **Open in Browser**
   - Navigate to http://127.0.0.1:7860
   - Click "🚀 Start Adventure" to begin!

## 📁 Project Structure

```
rpg-chatbot/
├── app.py              # Main application entry point
├── config.py           # Configuration and settings
├── prompts.py          # Prompt management
├── game_logic.py       # Game state and logic
├── chatbot.py          # Ollama API client
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variables template
├── README.md          # This file
```

## ⚙️ Configuration

### Environment Variables

Copy `.env.example` to `.env` and customize:

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_HOST` | localhost | Ollama server host |
| `OLLAMA_PORT` | 11434 | Ollama server port |
| `OLLAMA_MODEL` | llama3 | AI model to use |
| `SERVER_HOST` | 127.0.0.1 | Gradio server host |
| `SERVER_PORT` | 7860 | Gradio server port |
| `DEFAULT_MAX_STEPS` | 5 | Default number of game steps |
| `AI_TEMPERATURE` | 0.8 | AI creativity level (0.0-2.0) |

### Custom Prompts

Customize the game by editing files

- `gm_prompts.txt` - Instructions for the Game Master AI
- `rp_prompts.txt` - Instructions for the Player AI

## 🎮 Usage

### Manual Mode
1. Click "🚀 Start Adventure" to begin
2. Use "➡️ Next Step" to advance the story step by step
3. Watch AI responses stream in real-time

### Auto-play Mode
1. Set desired number of steps and delay
2. Click "🎬 Auto-play" to watch AI vs AI gameplay
3. Enjoy the automated storytelling experience

### Additional Features
- **📊 Game Info**: View current game statistics
- **📄 Export**: Save adventures as Markdown or text files
- **🔧 System Status**: Test Ollama connection and view settings

## 🛠️ Development

### Code Organization

The codebase is organized into focused modules:

- **`config.py`**: All configuration, URLs, and settings
- **`prompts.py`**: Prompt loading, saving, and management
- **`game_logic.py`**: Game state, validation, and formatting
- **`chatbot.py`**: Ollama API client and communication
- **`app.py`**: Main application and Gradio interface

### Key Classes

- `Config`: Centralized configuration management
- `PromptManager`: Handle prompt files and defaults
- `GameState`: Manage game progression and history
- `OllamaClient`: Handle API communication
- `RPGApp`: Main application orchestration

## 🔧 Troubleshooting

### Common Issues

1. **Connection Error**
   - Ensure Ollama is running: `ollama serve`
   - Check if model is installed: `ollama list`
   - Verify host/port in `.env` file

2. **Model Not Found**
   - Install required model: `ollama pull llama3`
   - Check available models: `ollama list`

3. **Slow Responses**
   - Reduce `AI_NUM_PREDICT` in `.env`
   - Use a smaller model if available
   - Check system resources

### System Status

Use the built-in "🔍 Test Ollama Connection" feature to diagnose issues.

## 📋 Requirements

- Python 3.8+
- Ollama installed and running
- At least 4GB RAM (for llama3 model)
- Internet connection (for initial model download)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📜 License

This project is open source. Please check the license file for details.

## 🆘 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Use the built-in connection test feature
3. Review the console output for error messages
4. Open an issue on GitHub with detailed information

---

*Built with ❤️ using Gradio and Ollama*