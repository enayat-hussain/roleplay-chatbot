import os
from typing import Tuple
from config import Config


class PromptManager:
    """Manages game prompts with fallback defaults"""

    DEFAULT_GM_PROMPT = """You are an engaging fantasy RPG Game Master. Your role is to:

1. Create vivid, immersive fantasy adventures in 3-4 concise lines, balancing atmosphere with clarity
2. Always provide exactly 4 numbered options after each scenario (unless it's the final step)
3. Respond to player choices with consequences and new situations
4. Keep the story dynamic and interesting
5. Maintain consistency in the world and characters

Guidelines:
- Set scenes with rich descriptions
- Create meaningful choices that matter
- Balance challenge and success
- Keep responses concise but engaging
- Always end with 4 numbered options (1. 2. 3. 4.) UNLESS it's explicitly stated to be the final step

CRITICAL FINAL STEP RULE:
- When told this is the final step or maximum steps have been reached:
  * DO NOT provide numbered options
  * Instead, conclude the adventure with a complete and satisfying ending
  * Resolve all major plot threads and character arcs
  * Provide closure for the player's journey
  * Make the ending feel earned and meaningful
  * Wrap up loose ends and give a sense of completion
  * The ending should be 2-3 paragraphs that bring the story to a natural conclusion

Begin each adventure by setting an intriguing scene and providing 4 options."""

    DEFAULT_PLAYER_PROMPT = """You are a player in an RPG adventure. You will:

1. Choose from the numbered options provided by the GM
2. Make decisions based on your character's personality
3. Be creative and engaged in the story
4. Respond with just the number of your choice

You are playing as a brave adventurer seeking fortune and glory."""

    @classmethod
    def load_all_prompts(cls) -> Tuple[str, str]:
        """Load GM and player prompts from files or return defaults"""
        gm_prompt = cls.load_gm_prompt()
        player_prompt = cls.load_player_prompt()
        return gm_prompt, player_prompt

    @classmethod
    def load_gm_prompt(cls) -> str:
        """Load GM prompt from file or return default"""
        try:
            gm_prompt_path = os.path.join(Config.PROMPTS_DIR, Config.GM_PROMPT_FILE)
            if os.path.exists(gm_prompt_path):
                with open(gm_prompt_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        return content
        except Exception as e:
            print(f"Warning: Could not load GM prompt from file: {e}")

        return cls.DEFAULT_GM_PROMPT

    @classmethod
    def load_player_prompt(cls) -> str:
        """Load player prompt from file or return default"""
        try:
            player_prompt_path = os.path.join(
                Config.PROMPTS_DIR, Config.PLAYER_PROMPT_FILE
            )
            if os.path.exists(player_prompt_path):
                with open(player_prompt_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        return content
        except Exception as e:
            print(f"Warning: Could not load player prompt from file: {e}")

        return cls.DEFAULT_PLAYER_PROMPT

    @classmethod
    def save_prompt(cls, content: str, prompt_type: str) -> bool:
        """Save a prompt to file"""
        try:
            # Ensure prompts directory exists
            os.makedirs(Config.PROMPTS_DIR, exist_ok=True)

            if prompt_type.lower() == "gm":
                filename = Config.GM_PROMPT_FILE
            elif prompt_type.lower() == "player":
                filename = Config.PLAYER_PROMPT_FILE
            else:
                raise ValueError(f"Unknown prompt type: {prompt_type}")

            file_path = os.path.join(Config.PROMPTS_DIR, filename)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            print(f"Prompt saved to {file_path}")
            return True

        except Exception as e:
            print(f"Error saving prompt: {e}")
            return False

    @classmethod
    def create_default_files(cls) -> bool:
        """Create default prompt files if they don't exist"""
        try:
            # Ensure directory exists
            os.makedirs(Config.PROMPTS_DIR, exist_ok=True)

            # Create GM prompt file if it doesn't exist
            gm_path = os.path.join(Config.PROMPTS_DIR, Config.GM_PROMPT_FILE)
            if not os.path.exists(gm_path):
                with open(gm_path, "w", encoding="utf-8") as f:
                    f.write(cls.DEFAULT_GM_PROMPT)
                print(f"Created default GM prompt: {gm_path}")

            # Create player prompt file if it doesn't exist
            player_path = os.path.join(Config.PROMPTS_DIR, Config.PLAYER_PROMPT_FILE)
            if not os.path.exists(player_path):
                with open(player_path, "w", encoding="utf-8") as f:
                    f.write(cls.DEFAULT_PLAYER_PROMPT)
                print(f"Created default player prompt: {player_path}")

            return True

        except Exception as e:
            print(f"Error creating default prompt files: {e}")
            return False

    @classmethod
    def get_prompt_info(cls) -> dict:
        """Get information about available prompts"""
        gm_path = os.path.join(Config.PROMPTS_DIR, Config.GM_PROMPT_FILE)
        player_path = os.path.join(Config.PROMPTS_DIR, Config.PLAYER_PROMPT_FILE)

        return {
            "gm_prompt": {
                "file_path": gm_path,
                "exists": os.path.exists(gm_path),
                "size": os.path.getsize(gm_path) if os.path.exists(gm_path) else 0,
                "using_default": not os.path.exists(gm_path),
            },
            "player_prompt": {
                "file_path": player_path,
                "exists": os.path.exists(player_path),
                "size": (
                    os.path.getsize(player_path) if os.path.exists(player_path) else 0
                ),
                "using_default": not os.path.exists(player_path),
            },
        }
