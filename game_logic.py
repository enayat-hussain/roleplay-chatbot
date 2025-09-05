import random
from typing import List, Tuple, Generator, Dict, Any, Optional
from config import Config, StatusMessages, ErrorMessages
from pathlib import Path
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChatLogger:
    """Handles writing chat messages"""

    def __init__(self, log_dir: str = "chat_logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.session_file = None

    def start_new_session(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_file = self.log_dir / f"chat_session_{timestamp}.txt"
        with open(self.session_file, "a", encoding="utf-8") as f:
            f.write(f"=== New Chat Session: {timestamp} ===\n\n")

    def append_message(self, role: str, message: str):
        if not self.session_file:
            self.start_new_session()
        with open(self.session_file, "a", encoding="utf-8") as f:
            f.write(f"[{role}] {message}\n")


class GameState:
    """Manages RPG game state"""

    def __init__(
        self,
        gm_prompt: str,
        player_prompt: str,
        model_name: Optional[str] = None,
        chat_client=None,
    ):
        self.gm_history = [{"role": "system", "content": gm_prompt}]
        self.conversation = []
        self.step_count = 0
        self.chat_logger = ChatLogger()
        self.chat_logger.start_new_session()

        if chat_client:
            self.chat_client = chat_client
        else:
            from chatbot import ChatClient

            self.chat_client = ChatClient(model=model_name)

    def start_game_streaming(self) -> Generator[Tuple[bool, List, str], None, None]:
        """Starts the game by setting the scene and giving 4 options"""
        try:
            self.gm_history.append(
                {
                    "role": "user",
                    "content": "Begin the adventure. Set the scene and give me 4 options to choose from.",
                }
            )

            # Set is_final_step to False for game start
            self.chat_client.is_final_step = False

            streamed_response = ""
            for chunk in self.chat_client.chat_streaming(self.gm_history):
                streamed_response += chunk
                temp_conversation = self.conversation + [("GM", streamed_response)]
                yield True, temp_conversation, chunk

            # Ensure fallback if empty
            if not streamed_response.strip():
                streamed_response = (
                    "The adventure begins, though the GM gave no details."
                )

            self.gm_history.append({"role": "assistant", "content": streamed_response})
            self.conversation.append(("GM", streamed_response))
            self.chat_logger.append_message("GM", streamed_response)

            # Yield final complete message to Gradio
            yield True, self.conversation, streamed_response

        except Exception as e:
            yield False, [], f"{ErrorMessages.GAME_START}: {str(e)}"

    def take_step_streaming(
        self, player_choice: Optional[int] = None, max_steps: int = 50
    ) -> Generator[Tuple[bool, List, int, str], None, None]:
        """Streaming player step with robust final step handling"""

        try:
            if player_choice is None:
                player_choice = random.choice([1, 2, 3, 4])

            self.conversation.append(("Player", str(player_choice)))
            self.chat_logger.append_message("Player", str(player_choice))
            yield True, self.conversation, player_choice, ""

            self.step_count += 1
            logger.info(
                f"Step {self.step_count} of {max_steps} - Choice: {player_choice}"
            )
            is_final_step = self.step_count >= max_steps
            logger.info(
                f"Is final step: {is_final_step} (step_count: {self.step_count}, max_steps: {max_steps})"
            )

            # CRITICAL: Set the flag in chat_client BEFORE making the request
            self.chat_client.is_final_step = is_final_step

            # --- Build prompt ---
            if is_final_step:
                final_prompt = f"""I choose option {player_choice}.

THIS IS THE ABSOLUTE FINAL STEP OF OUR ADVENTURE (step {self.step_count} of {max_steps}). 

CRITICAL INSTRUCTIONS FOR YOUR FINAL RESPONSE:
1. RESOLVE the story completely based on choice {player_choice}
2. PROVIDE a satisfying conclusion with full closure
3. WRAP UP all story threads and character arcs
4. DO NOT include any numbered options or choices
5. DO NOT leave the story open-ended
6. WRITE a complete narrative ending (3 maximum)
7. BEGIN your response with proper narrative, NOT with "You", "As", or other incomplete sentence starters
8. END with a definitive statement that the adventure is complete
9. MAKE SURE the response is a complete, well-formed story conclusion

Write the final conclusion of our adventure now:"""
            else:
                final_prompt = f"I choose option {player_choice}. Describe the result and give me 4 new numbered options to continue the adventure."

            self.gm_history.append({"role": "user", "content": final_prompt})

            # --- Stream the GM response ---
            streamed_response = ""

            if is_final_step:
                # For final steps, we get the complete response at once
                logger.info("Processing final step with complete response")
                for chunk in self.chat_client.chat_streaming(self.gm_history):
                    streamed_response += chunk
                    # Update the conversation with the accumulated response
                    temp_conversation = self.conversation + [("GM", streamed_response)]
                    yield True, temp_conversation, player_choice, chunk
            else:
                # For regular steps, stream normally
                for chunk in self.chat_client.chat_streaming(self.gm_history):
                    streamed_response += chunk
                    temp_conversation = self.conversation + [("GM", streamed_response)]
                    yield True, temp_conversation, player_choice, chunk

            # --- Post-processing ONLY for final step ---
            if is_final_step:
                import re

                # Clean up the response
                cleaned_response = streamed_response.strip()

                # Remove any numbered options that might have appeared
                cleaned_response = re.sub(
                    r"\n?\d+[\.\):][^\n]*", "", cleaned_response
                ).strip()

                # Check if response is too short or starts with problematic words
                problematic_starts = [
                    "you",
                    "as",
                    "the",
                    "and",
                    "but",
                    "or",
                    "while",
                    "when",
                    "if",
                ]
                is_problematic = (
                    len(cleaned_response.split()) < 20  # Adjusted for 8-9 lines
                    or any(
                        cleaned_response.lower().startswith(word + " ")
                        for word in problematic_starts
                    )
                    or not cleaned_response
                )

                # If the response is problematic, use a fallback
                if is_problematic:
                    logger.warning(
                        f"Final response appears problematic (length: {len(cleaned_response.split())} words). Using fallback."
                    )
                    fallback_endings = [
                        f"With choice {player_choice}, the adventure takes its final turn. The hero faces the ultimate "
                        f"challenge with courage and determination. All the skills learned throughout the journey come "
                        f"together in this decisive moment. The conflict reaches its resolution as allies rally to help. "
                        f"Peace returns to the land as the threat is finally overcome. The hero is celebrated by all who "
                        f"were saved. The quest is complete, and the legend begins. The adventure ends with triumph and "
                        f"the promise of new tales to come.",
                        f"Option {player_choice} leads to the climactic finale. The mysteries unraveled throughout the "
                        f"journey finally make sense as the pieces fall into place. The hero's wisdom and bravery shine "
                        f"through in this crucial hour. Friends and allies unite for the final push against darkness. "
                        f"Victory comes at last, though not without sacrifice and growth. The world is forever changed "
                        f"by the choices made along the way. Stories will be told of this great adventure. The tale "
                        f"concludes, but its impact will echo through the ages.",
                        f"The final choice of {player_choice} brings everything to its destined conclusion. All the "
                        f"characters met along the way play their part in the grand finale. The hero's journey transforms "
                        f"not just themselves, but everyone they encountered. The evil is vanquished through cleverness "
                        f"and collaboration rather than force alone. The kingdom celebrates as peace is restored to all "
                        f"the lands. New friendships forged in adventure will last a lifetime. The hero returns home "
                        f"changed and wiser. The adventure ends, leaving behind a legacy of hope and courage.",
                    ]
                    cleaned_response = random.choice(fallback_endings)

                # Ensure proper ending punctuation
                if not cleaned_response.endswith((".", "!", "?")):
                    cleaned_response += "."

                streamed_response = cleaned_response
                logger.info(
                    f"Final response processed (length: {len(streamed_response.split())} words)"
                )

                # Update the conversation with the cleaned response
                if self.conversation and self.conversation[-1][0] == "GM":
                    self.conversation[-1] = ("GM", streamed_response)
                else:
                    self.conversation.append(("GM", streamed_response))

            # --- Save final response ---
            self.gm_history.append({"role": "assistant", "content": streamed_response})

            # Add to conversation if not already added (for non-final steps)
            if not is_final_step:
                self.conversation.append(("GM", streamed_response))

            self.chat_logger.append_message("GM", streamed_response)

            # Reset the flag after processing
            self.chat_client.is_final_step = False

            # Always yield the final full response at end
            yield True, self.conversation, player_choice, streamed_response

        except Exception as e:
            logger.error(f"Error in take_step_streaming: {e}")
            yield False, self.conversation, None, f"{ErrorMessages.GAME_STEP}: {str(e)}"

    def reset(self):
        self.conversation.clear()
        self.step_count = 0
        self.gm_history = self.gm_history[:1]
        self.chat_logger.start_new_session()

    def get_game_info(self) -> Dict[str, Any]:
        return {
            "step_count": self.step_count,
            "total_messages": len(self.conversation),
            "gm_history_length": len(self.gm_history),
            "last_message": self.conversation[-1] if self.conversation else None,
            "chat_client_info": {
                "api_url": getattr(self.chat_client, "api_url", "unknown"),
                "model": getattr(self.chat_client, "model", "unknown"),
                "provider": getattr(self.chat_client, "api_provider", "unknown"),
            },
        }


class ConversationFormatter:
    @staticmethod
    def to_gradio_format(conversation: List[Tuple[str, str]]) -> List[Dict[str, str]]:
        messages = []
        for speaker, content in conversation:
            messages.append(
                {"role": "assistant" if speaker == "GM" else "user", "content": content}
            )
        return messages

    @staticmethod
    def to_markdown(conversation: List[Tuple[str, str]]) -> str:
        markdown = "# RPG Adventure Log\n\n"
        for speaker, content in conversation:
            prefix = "**Game Master:**" if speaker == "GM" else "**Player:**"
            markdown += f"{prefix}\n{content}\n\n"
        return markdown

    @staticmethod
    def to_plain_text(conversation: List[Tuple[str, str]]) -> str:
        text = "RPG Adventure Log\n" + "=" * 50 + "\n\n"
        for speaker, content in conversation:
            text += f"{speaker}: {content}\n\n"
        return text
