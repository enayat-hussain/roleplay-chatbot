import os
from dotenv import load_dotenv
from typing import Dict, Any

# Load environment variables
load_dotenv()


class Config:
    """Centralized configuration class for the RPG application"""

    # API Configuration
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "localhost")
    OLLAMA_PORT = os.getenv("OLLAMA_PORT", "11434")
    API_URL = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}/api/chat"
    MODEL = os.getenv("OLLAMA_MODEL", "llama3")

    # Server Configuration
    SERVER_HOST = os.getenv("SERVER_HOST", "127.0.0.1")
    SERVER_PORT = int(os.getenv("SERVER_PORT", "7860"))
    SHARE_GRADIO = os.getenv("SHARE_GRADIO", "false").lower() == "true"

    # Game Settings
    DEFAULT_MAX_STEPS = int(os.getenv("DEFAULT_MAX_STEPS", "5"))
    MAX_STEPS_LIMIT = int(os.getenv("MAX_STEPS_LIMIT", "20"))
    DEFAULT_DELAY = int(os.getenv("DEFAULT_DELAY", "2"))
    MAX_DELAY = int(os.getenv("MAX_DELAY", "5"))

    # AI Model Parameters
    AI_SETTINGS = {
        "temperature": float(os.getenv("AI_TEMPERATURE", "0.8")),
        "top_k": int(os.getenv("AI_TOP_K", "40")),
        "top_p": float(os.getenv("AI_TOP_P", "0.9")),
        "num_ctx": int(os.getenv("AI_NUM_CTX", "6000")),
        "num_predict": int(os.getenv("AI_NUM_PREDICT", "500")),
        "repeat_penalty": float(os.getenv("AI_REPEAT_PENALTY", "1.1")),
    }

    # File Paths
    PROMPTS_DIR = os.getenv("PROMPTS_DIR", ".")  # Current directory by default
    GM_PROMPT_FILE = os.getenv("GM_PROMPT_FILE", "gm_prompt.txt")  # Your existing file
    PLAYER_PROMPT_FILE = os.getenv("PLAYER_PROMPT_FILE", "rp_prompt.txt")  # Your existing file

    # Request Timeouts
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "120"))

    # UI Configuration
    UI_CONFIG = {
        "title": "🎲 AI RPG Adventure Game",
        "description": "*Watch the adventure unfold in real-time as the AI writes the story*",
        "chatbot_height": 500,
        "theme": "soft",
        "show_copy_button": True,
    }

    @classmethod
    def validate_config(cls) -> Dict[str, Any]:
        """Validate configuration and return status"""
        issues = []

        # Check if prompts directory exists
        if not os.path.exists(cls.PROMPTS_DIR):
            try:
                os.makedirs(cls.PROMPTS_DIR)
            except Exception as e:
                issues.append(f"Cannot create prompts directory: {e}")

        # Validate AI settings
        if not (0.0 <= cls.AI_SETTINGS["temperature"] <= 2.0):
            issues.append("AI temperature should be between 0.0 and 2.0")

        if not (0.0 <= cls.AI_SETTINGS["top_p"] <= 1.0):
            issues.append("AI top_p should be between 0.0 and 1.0")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "config": {
                "api_url": cls.API_URL,
                "model": cls.MODEL,
                "server": f"{cls.SERVER_HOST}:{cls.SERVER_PORT}",
                "prompts_dir": cls.PROMPTS_DIR
            }
        }


# Error Messages
class ErrorMessages:
    """Centralized error messages"""

    CONNECTION = "⚠️ Connection failed - is Ollama running on {host}:{port}?"
    TIMEOUT = "⚠️ Request timed out after {timeout} seconds"
    REQUEST = "⚠️ Failed to complete API request"
    EMPTY_RESPONSE = "⚠️ Received empty response from API"
    INVALID_FORMAT = "⚠️ Invalid response format"
    RATE_LIMIT = "⚠️ Rate limit exceeded"
    GAME_START = "⚠️ Failed to start game"
    GAME_STEP = "⚠️ Error during game step"
    FILE_NOT_FOUND = "⚠️ File not found: {filename}"
    PERMISSION_ERROR = "⚠️ Permission denied accessing: {filename}"

    @classmethod
    def format_connection_error(cls) -> str:
        return cls.CONNECTION.format(
            host=Config.OLLAMA_HOST,
            port=Config.OLLAMA_PORT
        )

    @classmethod
    def format_timeout_error(cls) -> str:
        return cls.TIMEOUT.format(timeout=Config.REQUEST_TIMEOUT)


# Status Messages
class StatusMessages:
    """Centralized status messages"""

    READY = "**Status:** Ready to start adventure"
    STARTING = "**Status:** 🔄 Starting adventure..."
    IN_PROGRESS = "**Status:** 🎮 Adventure in progress... (Max steps: {max_steps})"
    STARTED = "**Status:** 🎮 Adventure started! Step 0/{max_steps}"
    NEXT_STEP = "**Status:** 🎲 Taking next step..."
    STEP_COMPLETED = "**Status:** ✅ Step {step}/{max_steps} completed"
    GAME_COMPLETED = "**Status:** 🏁 Game completed ({step}/{max_steps} steps)"
    AUTO_PLAY_START = "**Status:** 🎬 Starting auto-play adventure..."
    AUTO_PLAY_STEP = "**Status:** 🎬 Auto-play Step {step}/{max_steps} - {action}"
    AUTO_PLAY_COMPLETED = "**Status:** 🎬 Auto-play completed! {step}/{max_steps} steps finished"
    RESET_COMPLETE = "**Status:** 🔄 Reset complete. Ready for new adventure!"
    PROCESSING = "**Status:** ⚠️ No active game or already processing"

    @classmethod
    def format_in_progress(cls, max_steps: int) -> str:
        return cls.IN_PROGRESS.format(max_steps=max_steps)

    @classmethod
    def format_started(cls, max_steps: int) -> str:
        return cls.STARTED.format(max_steps=max_steps)

    @classmethod
    def format_step_completed(cls, step: int, max_steps: int) -> str:
        return cls.STEP_COMPLETED.format(step=step, max_steps=max_steps)

    @classmethod
    def format_game_completed(cls, step: int, max_steps: int) -> str:
        return cls.GAME_COMPLETED.format(step=step, max_steps=max_steps)

    @classmethod
    def format_auto_play_step(cls, step: int, max_steps: int, action: str) -> str:
        return cls.AUTO_PLAY_STEP.format(step=step, max_steps=max_steps, action=action)

    @classmethod
    def format_auto_play_completed(cls, step: int, max_steps: int) -> str:
        return cls.AUTO_PLAY_COMPLETED.format(step=step, max_steps=max_steps)