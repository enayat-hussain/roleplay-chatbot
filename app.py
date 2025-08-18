import gradio as gr
import time
from typing import Generator, Tuple, List, Any

from config import Config, StatusMessages, ErrorMessages
from prompts import PromptManager
from game_logic import GameState, ConversationFormatter
from chatbot import OllamaClient


class RPGApp:
    """Main RPG Application class"""

    def __init__(self):
        self.validate_setup()

    def validate_setup(self):
        """Validate application setup"""
        # Validate configuration
        config_status = Config.validate_config()
        if not config_status["valid"]:
            print("⚠️ Configuration issues found:")
            for issue in config_status["issues"]:
                print(f"  - {issue}")

        # Test Ollama connection
        client = OllamaClient()
        connection_test = client.test_connection()
        if not connection_test["connected"]:
            print(f"⚠️ Ollama connection issue: {connection_test['error']}")
        else:
            print(f"✅ Connected to Ollama: {connection_test['status']}")

    def start_game_streaming(self, max_steps: int) -> Generator:
        """Start game with streaming display"""
        try:
            gm_prompt, player_prompt = PromptManager.load_all_prompts()
            game = GameState(gm_prompt, player_prompt)

            # Initial loading message
            yield [], None, False, StatusMessages.STARTING

            # Stream the game start
            for success, conversation, response in game.start_game_streaming():
                if success:
                    gradio_conv = ConversationFormatter.to_gradio_format(conversation)
                    status = StatusMessages.format_in_progress(max_steps)
                    yield gradio_conv, game, False, status
                else:
                    yield [], None, False, f"{ErrorMessages.GAME_START}: {response}"
                    return

            # Final state
            final_status = StatusMessages.format_started(max_steps)
            yield ConversationFormatter.to_gradio_format(game.conversation), game, False, final_status

        except Exception as e:
            yield [], None, False, f"{ErrorMessages.GAME_START}: {str(e)}"

    def next_step_streaming(self, game: GameState, max_steps: int, processing: bool) -> Generator:
        """Take next step with streaming display"""
        if not game or processing:
            status = StatusMessages.PROCESSING
            conversation = ConversationFormatter.to_gradio_format(game.conversation) if game else []
            yield conversation, game, False, status
            return

        if game.step_count >= max_steps:
            status = StatusMessages.format_game_completed(game.step_count, max_steps)
            yield ConversationFormatter.to_gradio_format(game.conversation), game, False, status
            return

        try:
            # Set processing state
            yield ConversationFormatter.to_gradio_format(game.conversation), game, True, StatusMessages.NEXT_STEP

            # Stream the game step
            for success, conversation, choice, response in game.take_step_streaming():
                if success:
                    gradio_conv = ConversationFormatter.to_gradio_format(conversation)
                    if choice is not None:
                        status = f"**Status:** 🎲 Step {game.step_count}/{max_steps} | Last choice: {choice}"
                    else:
                        status = "**Status:** 🎲 Generating response..."
                    yield gradio_conv, game, True, status
                else:
                    yield ConversationFormatter.to_gradio_format(
                        game.conversation), game, False, f"{ErrorMessages.GAME_STEP}: {response}"
                    return

            # Final state
            final_status = StatusMessages.format_step_completed(game.step_count, max_steps)
            yield ConversationFormatter.to_gradio_format(game.conversation), game, False, final_status

        except Exception as e:
            yield ConversationFormatter.to_gradio_format(
                game.conversation), game, False, f"{ErrorMessages.GAME_STEP}: {str(e)}"

    def auto_play_streaming(self, max_steps: int, delay: int) -> Generator:
        """Auto-play with live streaming of each step"""
        try:
            gm_prompt, player_prompt = PromptManager.load_all_prompts()
            game = GameState(gm_prompt, player_prompt)

            # Start the game with streaming
            yield [], None, False, StatusMessages.AUTO_PLAY_START

            # Stream the initial game start
            for success, conversation, response in game.start_game_streaming():
                if not success:
                    yield [], None, False, f"{ErrorMessages.GAME_START}: {response}"
                    return
                gradio_conv = ConversationFormatter.to_gradio_format(conversation)
                status = StatusMessages.format_auto_play_step(0, max_steps, "Setting the scene...")
                yield gradio_conv, game, True, status

            # Wait after initial setup
            time.sleep(delay)

            # Auto-play loop with streaming
            while game.step_count < max_steps:
                step_num = game.step_count + 1

                # Stream each step
                for success, conversation, choice, response in game.take_step_streaming():
                    if not success:
                        yield ConversationFormatter.to_gradio_format(
                            game.conversation), game, False, f"{ErrorMessages.GAME_STEP}: {response}"
                        return

                    gradio_conv = ConversationFormatter.to_gradio_format(conversation)
                    if choice is not None:
                        action = f"Player chose: {choice}"
                    else:
                        action = "GM responding..."
                    status = StatusMessages.format_auto_play_step(step_num, max_steps, action)
                    yield gradio_conv, game, True, status

                # Pause between steps (except for the last one)
                if game.step_count < max_steps:
                    time.sleep(delay)

            # Final state
            final_status = StatusMessages.format_auto_play_completed(game.step_count, max_steps)
            yield ConversationFormatter.to_gradio_format(game.conversation), game, False, final_status

        except Exception as e:
            yield [], None, False, f"**Status:** ❌ Auto-play error: {str(e)}"

    def reset_game(self) -> Tuple:
        """Reset the game state"""
        return [], None, False, StatusMessages.RESET_COMPLETE

    def create_interface(self) -> gr.Blocks:
        """Create the Gradio interface"""
        with gr.Blocks(title=Config.UI_CONFIG["title"],
                       theme=getattr(gr.themes, Config.UI_CONFIG["theme"].title())()) as demo:

            # Header
            gr.Markdown(f"# {Config.UI_CONFIG['title']}")
            gr.Markdown(Config.UI_CONFIG["description"])

            # Configuration section
            with gr.Row():
                with gr.Column(scale=1):
                    max_steps_slider = gr.Slider(
                        1, Config.MAX_STEPS_LIMIT,
                        value=Config.DEFAULT_MAX_STEPS,
                        step=1,
                        label="Max Steps",
                        info="Number of story steps"
                    )
                    delay_slider = gr.Slider(
                        1, Config.MAX_DELAY,
                        value=Config.DEFAULT_DELAY,
                        step=1,
                        label="Delay Between Steps (seconds)",
                        info="Pause between player choices"
                    )

                with gr.Column(scale=2):
                    status_text = gr.Markdown(StatusMessages.READY)

            # Main chat interface
            chatbot = gr.Chatbot(
                type="messages",
                label="Adventure Log - Live Streaming",
                height=Config.UI_CONFIG["chatbot_height"],
                show_copy_button=Config.UI_CONFIG["show_copy_button"]
            )

            # State management
            game_state = gr.State(None)
            is_processing = gr.State(False)

            # Control buttons
            with gr.Row():
                start_btn = gr.Button("🚀 Start Adventure", variant="primary")
                next_btn = gr.Button("➡️ Next Step", variant="secondary")
                auto_btn = gr.Button("🎬 Auto-play (Live Streaming)", variant="secondary")
                reset_btn = gr.Button("🔄 Reset", variant="stop")

            # Additional features
            with gr.Accordion("📊 Game Info & Export", open=False):
                with gr.Row():
                    info_btn = gr.Button("📋 Show Game Info")
                    export_md_btn = gr.Button("📄 Export as Markdown")
                    export_txt_btn = gr.Button("📝 Export as Text")

                game_info_display = gr.JSON(label="Current Game Information")
                export_output = gr.Textbox(
                    label="Export Output",
                    lines=10,
                    max_lines=20,
                    show_copy_button=True
                )

            # Connection status
            with gr.Accordion("🔧 System Status", open=False):
                connection_btn = gr.Button("🔍 Test Ollama Connection")
                connection_status = gr.JSON(label="Connection Status")

            # Event handlers
            start_btn.click(
                self.start_game_streaming,
                [max_steps_slider],
                [chatbot, game_state, is_processing, status_text],
                show_progress="hidden"
            )

            next_btn.click(
                self.next_step_streaming,
                [game_state, max_steps_slider, is_processing],
                [chatbot, game_state, is_processing, status_text],
                show_progress="hidden"
            )

            auto_btn.click(
                self.auto_play_streaming,
                [max_steps_slider, delay_slider],
                [chatbot, game_state, is_processing, status_text],
                show_progress="hidden"
            )

            reset_btn.click(
                self.reset_game,
                [],
                [chatbot, game_state, is_processing, status_text]
            )

            # Info and export handlers
            def show_game_info(game):
                if game:
                    return game.get_game_info()
                return {"error": "No active game"}

            def export_markdown(game):
                if game and game.conversation:
                    return ConversationFormatter.to_markdown(game.conversation)
                return "No conversation to export"

            def export_text(game):
                if game and game.conversation:
                    return ConversationFormatter.to_plain_text(game.conversation)
                return "No conversation to export"

            def test_connection():
                client = OllamaClient()
                return client.test_connection()

            info_btn.click(show_game_info, [game_state], [game_info_display])
            export_md_btn.click(export_markdown, [game_state], [export_output])
            export_txt_btn.click(export_text, [game_state], [export_output])
            connection_btn.click(test_connection, [], [connection_status])

            # Footer
            gr.Markdown("---")
            gr.Markdown(
                "*🎥 **Live Streaming Mode** - Watch each message appear in real-time as the AI generates them!*")
            gr.Markdown(f"*🔧 Using model: `{Config.MODEL}` | Server: `{Config.API_URL}`*")

        return demo


def main():
    """Main application entry point"""
    try:
        # Create and validate application
        app = RPGApp()

        # Create Gradio interface
        demo = app.create_interface()

        # Print startup information
        print("🚀 Starting Live Streaming RPG Chatbot...")
        print(f"🔗 Server will run on: http://{Config.SERVER_HOST}:{Config.SERVER_PORT}")
        print(f"🤖 Using model: {Config.MODEL}")
        print(f"📁 Prompts directory: {Config.PROMPTS_DIR}")
        print("📋 Make sure Ollama is running: ollama serve")
        print("🎬 Click 'Auto-play' to see live streaming in action!")

        # Launch the application
        demo.launch(
            server_name=Config.SERVER_HOST,
            server_port=Config.SERVER_PORT,
            show_error=True,
            share=Config.SHARE_GRADIO
        )

    except Exception as e:
        print(f"❌ Failed to start application: {e}")
        print("🔧 Check that all dependencies are installed and Ollama is running")


if __name__ == "__main__":
    main()