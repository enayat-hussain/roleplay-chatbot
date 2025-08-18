import random
import time
from typing import List, Tuple, Generator, Dict, Any
from config import Config, StatusMessages, ErrorMessages


class GameState:
    """Manages the state of the RPG game"""

    def __init__(self, gm_prompt: str, player_prompt: str):
        """Initialize game state with prompts"""
        self.gm_history = [{"role": "system", "content": gm_prompt}]
        self.player_history = [{"role": "system", "content": player_prompt}]
        self.conversation = []
        self.step_count = 0
        # Import here to avoid circular import
        from chatbot import OllamaClient
        self.ollama_client = OllamaClient()

    def start_game_streaming(self) -> Generator[Tuple[bool, List, str], None, None]:
        """Start game with streaming response"""
        try:
            self.gm_history.append({
                "role": "user",
                "content": "Begin the adventure. Set the scene and give me 4 options to choose from."
            })

            # Use streaming response
            full_response = ""
            for chunk in self.ollama_client.chat_streaming(self.gm_history):
                full_response = chunk
                # Yield intermediate state for real-time display
                temp_conversation = [("GM", chunk)]
                yield True, temp_conversation, chunk

            # Final state
            self.gm_history.append({"role": "assistant", "content": full_response})
            self.conversation.append(("GM", full_response))
            yield True, self.conversation, full_response

        except Exception as e:
            error_msg = f"{ErrorMessages.GAME_START}: {str(e)}"
            yield False, [], error_msg

    def take_step_streaming(self) -> Generator[Tuple[bool, List, int, str], None, None]:
        """Take a game step with streaming response"""
        try:
            # Random choice between 1-4
            player_choice = random.choice([1, 2, 3, 4])
            choice_text = f"I choose option {player_choice}"

            # Add player choice to conversation immediately
            self.conversation.append(("Player", f"{player_choice}"))
            yield True, self.conversation, player_choice, ""

            # Add player's choice to GM history with clear instruction
            choice_prompt = (f"{choice_text}. Now describe what happens as a result of this choice, "
                             f"then give me 4 new numbered options to choose from.")
            self.gm_history.append({"role": "user", "content": choice_prompt})

            # Stream GM response
            full_gm_response = ""
            for chunk in self.ollama_client.chat_streaming(self.gm_history):
                full_gm_response = chunk
                # Update conversation with streaming GM response
                temp_conversation = self.conversation.copy()
                temp_conversation.append(("GM", chunk))
                yield True, temp_conversation, player_choice, chunk

            # Final state
            self.gm_history.append({"role": "assistant", "content": full_gm_response})
            self.conversation.append(("GM", full_gm_response))
            self.step_count += 1

            yield True, self.conversation, player_choice, full_gm_response

        except Exception as e:
            error_msg = f"{ErrorMessages.GAME_STEP}: {str(e)}"
            yield False, self.conversation, None, error_msg

    def reset(self):
        """Reset the game state"""
        self.conversation.clear()
        self.step_count = 0
        # Keep only system prompts
        self.gm_history = self.gm_history[:1]
        self.player_history = self.player_history[:1]

    def get_game_info(self) -> Dict[str, Any]:
        """Get current game information"""
        return {
            "step_count": self.step_count,
            "total_messages": len(self.conversation),
            "gm_history_length": len(self.gm_history),
            "last_message": self.conversation[-1] if self.conversation else None
        }


class GameValidator:
    """Validates game responses and choices"""

    @staticmethod
    def validate_gm_response(response: str) -> bool:
        """Ensure GM response has 4 options"""
        if not response:
            return False

        option_count = 0
        for i in range(1, 5):
            if f"{i}." in response or f"{i})" in response:
                option_count += 1

        return option_count >= 4

    @staticmethod
    def validate_player_choice(choice: int) -> bool:
        """Validate player choice is between 1-4"""
        return isinstance(choice, int) and 1 <= choice <= 4

    @staticmethod
    def ensure_options_in_response(response: str) -> str:
        """Add default options if response doesn't have them"""
        if not GameValidator.validate_gm_response(response):
            additional_text = ("\n\nYour options now:\n"
                               "1. Continue exploring\n"
                               "2. Think carefully\n"
                               "3. Look around\n"
                               "4. Make a decision")
            return response + additional_text
        return response


class ConversationFormatter:
    """Handles conversation formatting for different interfaces"""

    @staticmethod
    def to_gradio_format(conversation: List[Tuple[str, str]]) -> List[Dict[str, str]]:
        """Convert conversation to Gradio messages format"""
        messages = []
        for speaker, content in conversation:
            if speaker == "GM":
                messages.append({"role": "assistant", "content": content})
            elif speaker == "Player":
                messages.append({"role": "user", "content": content})
        return messages

    @staticmethod
    def to_markdown(conversation: List[Tuple[str, str]]) -> str:
        """Convert conversation to markdown format"""
        markdown = "# RPG Adventure Log\n\n"
        for speaker, content in conversation:
            if speaker == "GM":
                markdown += f"**🎭 Game Master:**\n{content}\n\n"
            elif speaker == "Player":
                markdown += f"**🎮 Player:** {content}\n\n"
        return markdown

    @staticmethod
    def to_plain_text(conversation: List[Tuple[str, str]]) -> str:
        """Convert conversation to plain text"""
        text = "RPG Adventure Log\n" + "=" * 50 + "\n\n"
        for speaker, content in conversation:
            text += f"{speaker}: {content}\n\n"
        return text