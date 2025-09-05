import asyncio
import time
from typing import Generator, Tuple, List

import gradio as gr

from config import Config, StatusMessages, ErrorMessages
from game_logic import GameState, ConversationFormatter
from chatbot import ChatClient


# --- PromptManager fallback ---
def _default_gm_prompt() -> str:
    return (
        "You are a vivid and safety-conscious RPG Game Master. "
        "Set each scene with clear, engaging description (about 3–4 lines). "
        "Always end your response with exactly four numbered choices (1–4), "
        "each being concise, meaningful, and distinct."
    )


def _default_player_prompt() -> str:
    return (
        "You are the Player. Your choices are numbers 1-4 responding to the GM options."
    )


class PromptManager:
    @staticmethod
    def load_all_prompts() -> Tuple[str, str]:
        import os

        gm_path = os.path.join(Config.PROMPTS_DIR, Config.GM_PROMPT_FILE)
        player_path = os.path.join(Config.PROMPTS_DIR, Config.PLAYER_PROMPT_FILE)

        def _read_or_default(path: str, fallback: str) -> str:
            try:
                if os.path.exists(path):
                    with open(path, "r", encoding="utf-8") as f:
                        text = f.read().strip()
                        return text if text else fallback
                return fallback
            except Exception:
                return fallback

        return _read_or_default(gm_path, _default_gm_prompt()), _read_or_default(
            player_path, _default_player_prompt()
        )


# ---------------------------------------------------------------------------


class RPGApp:
    """Main RPG Application class"""

    def __init__(self):
        self.validate_setup()

    def validate_setup(self):
        config_status = Config.validate_config()
        if not config_status["valid"]:
            print("Configuration issues found:")
            for issue in config_status["issues"]:
                print(f"  - {issue}")
        for warn in config_status.get("warnings", []):
            print(f"Warning: {warn}")

        client = ChatClient()
        connection_test = client.test_connection()
        if not connection_test["connected"]:
            print(f"API connection issue: {connection_test.get('error')}")
        else:
            print(
                f"Connected to API: {connection_test.get('status')} (provider={connection_test.get('detected_provider')})"
            )

    def get_available_providers(self) -> List[str]:
        return [
            "OpenAI (GPT)",
            "Anthropic (Claude)",
            "Ollama (Local)",
            "Groq",
            "LM Studio",
            "Text Generation WebUI",
            "VLLM",
            "Custom Provider",
        ]

    def get_provider_config(self, provider_name: str) -> dict:
        provider_configs = {
            "OpenAI (GPT)": {
                "api_url": "https://api.openai.com/v1/chat/completions",
                "default_model": "gpt-4o-mini",
                "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
                "requires_key": True,
                "provider": "openai",
            },
            "Anthropic (Claude)": {
                "api_url": "https://api.anthropic.com/v1/messages",
                "default_model": "claude-3-haiku-20240307",
                "models": [
                    "claude-3-5-sonnet-20241022",
                    "claude-3-haiku-20240307",
                    "claude-3-opus-20240229",
                ],
                "requires_key": True,
                "provider": "anthropic",
            },
            "Ollama (Local)": {
                "api_url": "http://localhost:11434/v1/chat/completions",
                "default_model": "llama3.1",
                "models": [
                    "llama3.1",
                    "llama3:latest",
                    "mistral",
                    "codellama",
                    "vicuna",
                    "gemma:2b",
                ],
                "requires_key": False,
                "provider": "ollama",
            },
            "Groq": {
                "api_url": "https://api.groq.com/openai/v1/chat/completions",
                "default_model": "llama-3.1-8b-instant",
                "models": [
                    "llama-3.1-8b-instant",
                    "meta-llama/llama-4-scout-17b-16e-instruct",
                    "gemma2-9b-it",
                ],
                "requires_key": True,
                "provider": "groq",
            },
            "LM Studio": {
                "api_url": "http://localhost:1234/v1/chat/completions",
                "default_model": "local-model",
                "models": ["local-model"],
                "requires_key": False,
                "provider": "lmstudio",
            },
            "Text Generation WebUI": {
                "api_url": "http://localhost:5000/v1/chat/completions",
                "default_model": "local-model",
                "models": ["local-model"],
                "requires_key": False,
                "provider": "textgen",
            },
            "VLLM": {
                "api_url": "http://localhost:8000/v1/chat/completions",
                "default_model": "local-model",
                "models": ["local-model"],
                "requires_key": False,
                "provider": "vllm",
            },
            "Custom Provider": {
                "api_url": Config.API_URL or "",
                "default_model": Config.MODEL or "custom-model",
                "models": ["custom-model"],
                "requires_key": True,
                "provider": "custom",
            },
        }
        return provider_configs.get(provider_name, provider_configs["Custom Provider"])

    def _create_client_from_provider(
        self,
        provider_name: str,
        model_name: str,
        custom_url: str = "",
        custom_key: str = "",
    ) -> "ChatClient":
        """Create a ChatClient configured for the selected provider"""
        provider_config = self.get_provider_config(provider_name)
        api_url = (
            custom_url.strip() if custom_url.strip() else provider_config["api_url"]
        )

        # Get API key from custom input or environment
        api_key = custom_key.strip() if custom_key.strip() else ""

        client = ChatClient(model=model_name)
        client.api_url = api_url
        client.api_key = api_key  # This is crucial!
        client.api_provider = provider_config["provider"]
        return client

    async def _wrap_sync_gen(self, gen):
        """Utility to consume a sync generator in async context"""
        for item in gen:
            yield item
            # Add small async yield to prevent blocking
            await asyncio.sleep(0.01)

    def reset_game(self):
        """Reset the game state"""
        return [], None, False, StatusMessages.RESET_COMPLETE, ""

    # ---------------- Generator functions (streaming) ----------------

    def start_game_streaming(
        self,
        max_steps,
        selected_provider,
        selected_model,
        custom_api_url,
        custom_api_key,
    ):
        try:
            chat_client = self._create_client_from_provider(
                selected_provider, selected_model, custom_api_url, custom_api_key
            )
            gm_prompt, player_prompt = PromptManager.load_all_prompts()
            game = GameState(gm_prompt, player_prompt, chat_client=chat_client)

            provider_info = f"{selected_provider} - {selected_model}"
            yield [], None, False, f"Starting with {provider_info}...", provider_info

            for success, conversation, response in game.start_game_streaming():
                if success:
                    yield ConversationFormatter.to_gradio_format(
                        conversation
                    ), game, True, StatusMessages.format_in_progress(
                        max_steps
                    ), provider_info
                else:
                    yield [], None, False, f"{ErrorMessages.GAME_START}: {response}", provider_info
                    return

            yield ConversationFormatter.to_gradio_format(
                game.conversation
            ), game, False, StatusMessages.format_started(max_steps), provider_info

        except Exception as e:
            yield [], None, False, f"{ErrorMessages.GAME_START}: {str(e)}", ""

    def next_step_streaming(
        self,
        game,
        max_steps,
        processing,
        selected_provider,
        selected_model,
        custom_api_url,
        custom_api_key,
    ):
        if not game or processing:
            status = StatusMessages.PROCESSING
            conversation = (
                ConversationFormatter.to_gradio_format(game.conversation)
                if game
                else []
            )
            current_info = f"{selected_provider} - {selected_model}" if game else ""
            yield conversation, game, False, status, current_info
            return

        try:
            # Create fresh client for this step
            new_client = self._create_client_from_provider(
                selected_provider, selected_model, custom_api_url, custom_api_key
            )
            game.chat_client = new_client
            current_info = f"{selected_provider} - {selected_model}"

            # --- Normal step flow - removed the old final step handling ---
            yield ConversationFormatter.to_gradio_format(
                game.conversation
            ), game, True, StatusMessages.NEXT_STEP, current_info

            # Pass max_steps to the take_step_streaming method
            for success, conversation, choice, response in game.take_step_streaming(
                max_steps=max_steps
            ):
                if success:
                    gr_conv = ConversationFormatter.to_gradio_format(conversation)
                    status = (
                        f"**Status:** Step {game.step_count}/{max_steps} | Last choice: {choice}"
                        if choice
                        else "**Status:** Generating response..."
                    )
                    yield gr_conv, game, True, status
                else:
                    yield ConversationFormatter.to_gradio_format(
                        game.conversation
                    ), game, False, f"{ErrorMessages.GAME_STEP}: {response}"
                    return

            # Final status check
            if game.step_count >= max_steps:
                final_status = StatusMessages.format_game_completed(
                    game.step_count, max_steps
                )
            else:
                final_status = StatusMessages.format_step_completed(
                    game.step_count, max_steps
                )

            yield ConversationFormatter.to_gradio_format(
                game.conversation
            ), game, False, final_status

        except Exception as e:
            current_info = f"{selected_provider} - {selected_model}" if game else ""
            yield ConversationFormatter.to_gradio_format(
                game.conversation
            ), game, False, f"{ErrorMessages.GAME_STEP}: {str(e)}"

    def auto_play_streaming(
        self,
        max_steps,
        delay,
        selected_provider,
        selected_model,
        custom_api_url,
        custom_api_key,
    ):
        """Auto-play RPG adventure, streaming steps automatically with proper final message handling."""
        try:
            # Initialize client and game
            chat_client = self._create_client_from_provider(
                selected_provider, selected_model, custom_api_url, custom_api_key
            )
            gm_prompt, player_prompt = PromptManager.load_all_prompts()
            game = GameState(gm_prompt, player_prompt, chat_client=chat_client)
            provider_info = f"{selected_provider} - {selected_model}"

            yield [], None, False, f"Auto-play starting with {provider_info}..."

            # --- Initial game setup ---
            for success, conversation, response in game.start_game_streaming():
                if not success:
                    yield [], None, False, f"{ErrorMessages.GAME_START}: {response}"
                    return
                gradio_conv = ConversationFormatter.to_gradio_format(conversation)
                status = StatusMessages.format_auto_play_step(
                    0, max_steps, "Setting the scene..."
                )
                yield gradio_conv, game, True, status

            if delay > 0:
                time.sleep(delay)

            # --- Main auto-play loop ---
            while game.step_count < max_steps:
                step_num = game.step_count + 1

                for success, conversation, choice, response in game.take_step_streaming(
                    max_steps=max_steps
                ):
                    if not success:
                        yield ConversationFormatter.to_gradio_format(
                            game.conversation
                        ), game, False, f"{ErrorMessages.GAME_STEP}: {response}"
                        return

                    gradio_conv = ConversationFormatter.to_gradio_format(conversation)

                    # If this is the final step, yield final full response
                    if game.step_count >= max_steps:
                        status = StatusMessages.format_auto_play_completed(
                            game.step_count, max_steps
                        )
                        yield gradio_conv, game, False, status
                        return
                    else:
                        status = StatusMessages.format_auto_play_step(
                            step_num, max_steps, "GM responding..."
                        )
                        yield gradio_conv, game, True, status

                if delay > 0:
                    time.sleep(delay)

        except Exception as e:
            yield [], None, False, f"**Status:** Auto-play error: {str(e)}"

    def create_interface(self) -> gr.Blocks:
        """Create an improved, user-friendly Gradio interface"""

        with gr.Blocks(
            title=Config.UI_CONFIG["title"],
            theme=getattr(gr.themes, Config.UI_CONFIG["theme"].title())(),
        ) as demo:
            # --- State ---
            game_state = gr.State(None)
            is_processing = gr.State(False)

            # --- Header ---
            with gr.Row():
                with gr.Column():
                    gr.Markdown(f"# {Config.UI_CONFIG['title']}")
                    gr.Markdown(Config.UI_CONFIG["description"])

            # --- Main Tabs ---
            with gr.Tab("Game"):
                with gr.Row():
                    # --- Left Column: Controls ---
                    with gr.Column(scale=1, min_width=280):
                        gr.Markdown("### AI Provider Selection")

                        # Provider selection dropdown
                        available_providers = self.get_available_providers()
                        provider_dropdown = gr.Dropdown(
                            choices=available_providers,
                            value="OpenAI (GPT)",
                            label="Select AI Provider",
                            info="Choose your AI service provider",
                        )

                        # Model selection for the chosen provider
                        initial_config = self.get_provider_config("OpenAI (GPT)")
                        model_dropdown = gr.Dropdown(
                            label="Select Model",
                            info="Available models for the selected provider",
                            choices=initial_config["models"],
                            value=initial_config["default_model"],
                            allow_custom_value=True,
                        )

                        # Custom settings (shown when needed)
                        with gr.Group(visible=False) as custom_settings:
                            custom_api_url = gr.Textbox(
                                label="Custom API URL",
                                placeholder="Enter API endpoint URL...",
                                info="Override default API endpoint",
                            )
                            custom_api_key = gr.Textbox(
                                label="API Key",
                                placeholder="Enter your API key...",
                                type="password",
                                info="Required for some providers",
                            )
                        max_steps_slider = gr.Slider(
                            1,
                            Config.MAX_STEPS_LIMIT,
                            value=Config.DEFAULT_MAX_STEPS,
                            step=1,
                            label="Max Steps",
                        )
                        delay_slider = gr.Slider(
                            0,
                            Config.MAX_DELAY,
                            value=Config.DEFAULT_DELAY,
                            step=1,
                            label="Delay Between Steps (Auto-play)",
                        )

                        with gr.Row():
                            start_btn = gr.Button("Start", variant="primary")
                            next_btn = gr.Button("Next", variant="secondary")
                        with gr.Row():
                            auto_btn = gr.Button("Auto-play", variant="secondary")
                            reset_btn = gr.Button("Reset", variant="stop")

                    # --- Right Column: Chat & Logs ---
                    with gr.Column(scale=3):
                        gr.Markdown("### Adventure Log")
                        chatbot = gr.Chatbot(
                            type="messages",
                            label="Live Adventure Stream",
                            height=Config.UI_CONFIG["chatbot_height"],
                            show_copy_button=True,
                            render_markdown=True,
                            layout="bubble",
                        )
                        status_box = gr.Markdown(
                            f"Ready: {StatusMessages.READY}", elem_classes="status-box"
                        )

            # --- Info & Export ---
            with gr.Tab("Info & Export"):
                with gr.Row():
                    info_btn = gr.Button("Show Game Info")
                    export_md_btn = gr.Button("Export Markdown")
                    export_txt_btn = gr.Button("Export Text")

                game_info_display = gr.JSON(label="Current Game Information")
                export_output = gr.Textbox(
                    label="Export Output", lines=10, max_lines=20, show_copy_button=True
                )

            # --- System Status ---
            with gr.Tab("System"):
                connection_btn = gr.Button("Test API Connection")
                connection_status = gr.JSON(label="Connection Status")

                gr.Markdown("### Provider Testing")
                with gr.Row():
                    with gr.Column():
                        test_provider_dropdown = gr.Dropdown(
                            choices=available_providers,
                            value="OpenAI (GPT)",
                            label="Test Provider",
                        )
                        test_model_dropdown = gr.Dropdown(
                            label="Test Model",
                            choices=initial_config["models"],
                            value=initial_config["default_model"],
                        )
                        test_provider_btn = gr.Button("Test Selected Provider")
                        test_results = gr.JSON(label="Provider Test Results")

            # --- Event Handlers ---

            # Update model dropdown and custom settings based on provider selection
            def update_provider_settings(selected_provider):
                provider_config = self.get_provider_config(selected_provider)
                models = provider_config["models"]
                default_model = provider_config["default_model"]

                # Show custom settings for Custom Provider or providers that need API keys
                show_custom = (
                    selected_provider == "Custom Provider"
                    or provider_config["requires_key"]
                )

                return (
                    gr.update(choices=models, value=default_model),  # model_dropdown
                    gr.update(visible=show_custom),  # custom_settings
                    gr.update(value=provider_config["api_url"]),  # custom_api_url
                    gr.update(value=""),  # reset custom_api_key
                )

            provider_dropdown.change(
                update_provider_settings,
                [provider_dropdown],
                [model_dropdown, custom_settings, custom_api_url, custom_api_key],
            )

            # Streaming event handlers
            start_btn.click(
                self.start_game_streaming,
                [
                    max_steps_slider,
                    provider_dropdown,
                    model_dropdown,
                    custom_api_url,
                    custom_api_key,
                ],
                [chatbot, game_state, is_processing, status_box],
                show_progress="hidden",
            )

            next_btn.click(
                self.next_step_streaming,
                [
                    game_state,
                    max_steps_slider,
                    is_processing,
                    provider_dropdown,
                    model_dropdown,
                    custom_api_url,
                    custom_api_key,
                ],
                [chatbot, game_state, is_processing, status_box],
                show_progress="hidden",
            )

            auto_btn.click(
                self.auto_play_streaming,
                [
                    max_steps_slider,
                    delay_slider,
                    provider_dropdown,
                    model_dropdown,
                    custom_api_url,
                    custom_api_key,
                ],
                [chatbot, game_state, is_processing, status_box],
                show_progress="minimal",
            )

            reset_btn.click(
                self.reset_game, [], [chatbot, game_state, is_processing, status_box]
            )

            # Non-streaming event handlers
            def show_game_info(game):
                if game:
                    info = game.get_game_info()
                    info["current_provider"] = getattr(
                        game.chat_client, "api_provider", "unknown"
                    )
                    info["current_model"] = getattr(
                        game.chat_client, "model", "unknown"
                    )
                    info["current_api_url"] = getattr(
                        game.chat_client, "api_url", "unknown"
                    )
                    return info
                return {"error": "No active game"}

            def export_markdown(game):
                return (
                    ConversationFormatter.to_markdown(game.conversation)
                    if game and game.conversation
                    else "No conversation to export"
                )

            def export_text(game):
                return (
                    ConversationFormatter.to_plain_text(game.conversation)
                    if game and game.conversation
                    else "No conversation to export"
                )

            def test_connection():
                client = ChatClient()
                return client.test_connection()

            def test_selected_provider(
                selected_provider, selected_model, custom_url, custom_key
            ):
                try:
                    client = self._create_client_from_provider(
                        selected_provider, selected_model, custom_url, custom_key
                    )
                    result = client.test_connection()
                    result["tested_provider"] = selected_provider
                    result["tested_model"] = selected_model
                    result["api_url_used"] = client.api_url
                    return result
                except Exception as e:
                    return {
                        "connected": False,
                        "error": str(e),
                        "tested_provider": selected_provider,
                        "tested_model": selected_model,
                    }

            info_btn.click(show_game_info, [game_state], [game_info_display])
            export_md_btn.click(export_markdown, [game_state], [export_output])
            export_txt_btn.click(export_text, [game_state], [export_output])
            connection_btn.click(test_connection, [], [connection_status])

            # Update test model dropdown when test provider changes
            def update_test_models(test_provider):
                config = self.get_provider_config(test_provider)
                return gr.update(
                    choices=config["models"], value=config["default_model"]
                )

            test_provider_dropdown.change(
                update_test_models, [test_provider_dropdown], [test_model_dropdown]
            )

            test_provider_btn.click(
                test_selected_provider,
                [
                    test_provider_dropdown,
                    test_model_dropdown,
                    custom_api_url,
                    custom_api_key,
                ],
                [test_results],
            )

            # --- Footer ---
            gr.Markdown("---")
            gr.Markdown("*Live Streaming Mode: Messages appear in real-time*")
            gr.Markdown(
                f"*Default Config: `{Config.MODEL}` | Server: `{Config.API_URL}`*"
            )

            # --- Enhanced CSS for better provider selection display ---
            demo.css = """
            .status-box { 
                padding: 6px 10px;
                border-radius: 6px;
                background: #f0fdf4;
                font-weight: 600;
            }
            .provider-info {
                background: #e0f2fe;
                padding: 8px;
                border-radius: 4px;
                margin: 4px 0;
            }
            """

        return demo


def main():
    """Main application entry point"""
    try:
        # Create and validate application
        app = RPGApp()

        # Create Gradio interface
        demo = app.create_interface()

        # Print startup information
        print("Starting Live Streaming RPG Chatbot with Provider Selection...")
        print(f"Server will run on: http://{Config.SERVER_HOST}:{Config.SERVER_PORT}")
        print(f"Default model: {Config.MODEL}")
        # print(f"Prompts directory: {Config.PROMPTS_DIR}")
        print("Make sure your target API is running (e.g., `ollama serve` for Ollama).")
        print("Try 'Auto-play' to see live streaming in action!")
        print("You can now switch providers dynamically during gameplay!")

        # Launch the application
        demo.launch(
            server_name=Config.SERVER_HOST,
            server_port=Config.SERVER_PORT,
            show_error=True,
            share=Config.SHARE_GRADIO,
        )

    except Exception as e:
        print(
            "Check that all dependencies are installed and your API endpoint is reachable"
        )


if __name__ == "__main__":
    main()
