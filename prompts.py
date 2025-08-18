import os
from typing import Tuple
from config import Config, ErrorMessages


class PromptManager:
    """Manages loading and saving of game prompts"""

    # Default prompts as class constants
    DEFAULT_GM_PROMPT = """You are a Game Master for a text-based RPG adventure. You MUST follow this exact format for EVERY response:

CRITICAL RULES:
1. When the player makes a choice, describe what happens as a result
2. ALWAYS end every response with exactly 4 numbered options
3. Each response should be 8 sentences describing the outcome, then 4 options
4. Never continue the story without giving the player choices
5. Make each choice lead to different consequences

RESPONSE FORMAT (use this EVERY time):
[Describe what happens based on the player's choice in 3-4 sentences]

Your options now:
1. [First option]
2. [Second option] 
3. [Third option]
4. [Fourth option]

Remember: EVERY response must end with 4 numbered options. No exceptions!"""

    DEFAULT_PLAYER_PROMPT = """You are a player in an RPG adventure game. 

When given a story scenario with 4 numbered options, you must:
- Choose one option by responding with ONLY the number (1, 2, 3, or 4)
- Make interesting choices that advance the story
- Never explain your reasoning, just give the number"""

    @classmethod
    def load_prompt(cls, filepath: str, default_content: str) -> str:
        """Load a prompt from file, create with default if not exists"""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    return content
                else:
                    print(f"Warning: {filepath} is empty, using default content")
                    return default_content
        except FileNotFoundError:
            print(f"Warning: {filepath} not found, creating with default content")
            cls._create_default_file(filepath, default_content)
            return default_content
        except PermissionError:
            print(f"Error: Permission denied accessing {filepath}")
            return default_content
        except Exception as e:
            print(f"Error loading {filepath}: {e}")
            return default_content

    @classmethod
    def _create_default_file(cls, filepath: str, content: str) -> None:
        """Create a default file with given content"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Created default file: {filepath}")
        except Exception as e:
            print(f"Failed to create {filepath}: {e}")

    @classmethod
    def load_all_prompts(cls) -> Tuple[str, str]:
        """Load both GM and Player prompts"""
        gm_prompt = cls.load_prompt(
            Config.GM_PROMPT_FILE,
            cls.DEFAULT_GM_PROMPT
        )

        player_prompt = cls.load_prompt(
            Config.PLAYER_PROMPT_FILE,
            cls.DEFAULT_PLAYER_PROMPT
        )

        return gm_prompt, player_prompt

    @classmethod
    def save_prompt(cls, filepath: str, content: str) -> bool:
        """Save a prompt to file"""
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Failed to save {filepath}: {e}")
            return False

    @classmethod
    def save_gm_prompt(cls, content: str) -> bool:
        """Save Game Master prompt"""
        return cls.save_prompt(Config.GM_PROMPT_FILE, content)

    @classmethod
    def save_player_prompt(cls, content: str) -> bool:
        """Save Player prompt"""
        return cls.save_prompt(Config.PLAYER_PROMPT_FILE, content)

    @classmethod
    def get_prompt_info(cls) -> dict:
        """Get information about current prompts"""
        return {
            "gm_file": Config.GM_PROMPT_FILE,
            "player_file": Config.PLAYER_PROMPT_FILE,
            "gm_exists": os.path.exists(Config.GM_PROMPT_FILE),
            "player_exists": os.path.exists(Config.PLAYER_PROMPT_FILE),
            "prompts_dir": Config.PROMPTS_DIR
        }