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
            "Google (Gemini)",
            "DeepSeek",
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
            "Google (Gemini)": {
                "api_url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
                "default_model": "gemini-2.0-flash",
                "models": [
                    "gemini-2.5-flash-lite",
                    "gemini-2.0-flash",
                    "gemini-2.0-flash-lite",
                ],
                "requires_key": True,
                "provider": "gemini",
            },
            "DeepSeek": {
                "api_url": "https://api.deepseek.com/chat/completions",
                "default_model": "deepseek-chat",
                "models": [
                    "deepseek-chat",
                    "deepseek-coder",
                    "deepseek-reasoner",
                ],
                "requires_key": True,
                "provider": "deepseek",
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
        """Create a professional, clean UI like ChatGPT/Claude"""

        # Professional minimal CSS - Clean dark sidebar
        custom_css = """
        /* Base container */
        .gradio-container {
            max-width: 100% !important;
            padding: 0 !important;
            margin: 0 !important;
            background: #f8fafc !important;
            height: 100vh !important;
        }

        /* ========== SIDEBAR ========== */
        .sidebar {
            background: #1e1e2e !important;
            padding: 16px !important;
        }

        /* All text in sidebar white */
        .sidebar, .sidebar * {
            color: #cdd6f4 !important;
        }

        /* Fix vertical spacing in sidebar for Windows */
        .sidebar .block {
            margin: 0 !important;
            padding: 4px 0 !important;
        }
        .sidebar .form {
            gap: 8px !important;
        }
        .sidebar > div {
            gap: 4px !important;
        }

        /* Section labels */
        .settings-label {
            font-size: 10px !important;
            text-transform: uppercase !important;
            letter-spacing: 1px !important;
            color: #6c7086 !important;
            margin: 12px 0 6px 0 !important;
        }

        /* Divider */
        .divider {
            height: 1px;
            background: #313244;
            margin: 12px 0;
        }
        
        /* New Game button */
        .new-chat-btn {
            background: #cba6f7 !important;
            color: #1e1e2e !important;
            border: none !important;
            padding: 10px !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
        }
        .new-chat-btn:hover {
            background: #b4befe !important;
        }

        /* Slider labels - muted color, no box */
        .sidebar label,
        .sidebar label span,
        .sidebar .label-wrap,
        .sidebar .label-wrap span,
        .sidebar [class*="label"],
        .sidebar .head,
        .sidebar .head * {
            color: #6c7086 !important;
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }

        /* Target all possible slider wrapper elements */
        .sidebar [data-testid="slider"] > div,
        .sidebar [data-testid="slider"] .head,
        .sidebar [data-testid="slider"] span {
            background: transparent !important;
            border: none !important;
        }

        /* All inputs dark background */
        .sidebar input[type="text"],
        .sidebar input[type="password"],
        .sidebar textarea {
            background: #313244 !important;
            border: 1px solid #45475a !important;
            color: #cdd6f4 !important;
        }
        .sidebar input::placeholder {
            color: #6c7086 !important;
        }

        /* All .wrap elements dark by default */
        .sidebar .wrap {
            background: #313244 !important;
            border: 1px solid #45475a !important;
        }

        /* But sliders should be transparent - override with higher specificity */
        .sidebar .form .wrap {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }

        /* Remove box around slider form */
        .sidebar .block,
        .sidebar .form {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }

        /* ========== MAIN CHAT AREA ========== */
        .main-chat {
            background: #ffffff !important;
            height: 100vh !important;
            max-height: 100vh !important;
            display: flex !important;
            flex-direction: column !important;
            overflow: hidden !important;
            padding: 0 24px !important;
        }

        /* Chat container */
        .chat-container {
            flex: 1 !important;
            display: flex !important;
            flex-direction: column !important;
            padding: 0 !important;
            max-width: 100% !important;
            min-height: 0 !important;
            overflow: hidden !important;
        }

        /* Chatbot styling */
        .chatbot-box {
            border: none !important;
            background: #f8fafc !important;
            background-color: #f8fafc !important;
            box-shadow: none !important;
            flex: 1 !important;
            min-height: 0 !important;
            overflow-y: auto !important;
            overflow-x: hidden !important;
        }

        .chatbot-box > div {
            padding: 16px !important;
            overflow-y: auto !important;
            overflow-x: hidden !important;
        }

        /* Chat messages */
        .chatbot-box .message-wrap {
            gap: 20px !important;
        }

        .chatbot-box .message {
            padding: 14px 18px !important;
            border-radius: 16px !important;
            max-width: 70% !important;
            border: none !important;
            line-height: 1.6 !important;
            font-size: 14px !important;
            margin-bottom: 8px !important;
        }

        /* Copy button - position below message */
        .chatbot-box button[title="Copy"] {
            margin-top: 8px !important;
            opacity: 0.6 !important;
        }
        .chatbot-box button[title="Copy"]:hover {
            opacity: 1 !important;
        }

        /* Bot messages - LEFT side */
        .chatbot-box .bot,
        .chatbot-box .bot * {
            background: #f1f5f9 !important;
            background-color: #f1f5f9 !important;
            color: #1e293b !important;
        }
        .chatbot-box .bot {
            align-self: flex-start !important;
            margin-right: auto !important;
            margin-left: 0 !important;
            border-bottom-left-radius: 4px !important;
        }

        /* User messages - RIGHT side, fixed position */
        .chatbot-box .user,
        .chatbot-box .user * {
            background: #3b82f6 !important;
            background-color: #3b82f6 !important;
            color: #ffffff !important;
        }
        .chatbot-box .user {
            align-self: flex-end !important;
            margin-left: auto !important;
            margin-right: 0 !important;
            border-bottom-right-radius: 4px !important;
            max-width: fit-content !important;
            min-width: 40px !important;
            text-align: center !important;
            padding: 8px 16px !important;
            position: relative !important;
            right: 0 !important;
        }

        /* Status bar */
        .status-bar {
            background: #f1f5f9 !important;
            border: 1px solid #e2e8f0 !important;
            border-left: 3px solid #3b82f6 !important;
            border-radius: 6px !important;
            padding: 8px 12px !important;
            font-size: 13px !important;
            color: #64748b !important;
            margin: 8px 0 !important;
            flex-shrink: 0 !important;
            overflow: hidden !important;
            line-height: 1.4 !important;
            height: 38px !important;
            min-height: 38px !important;
            max-height: 38px !important;
            display: flex !important;
            align-items: center !important;
        }

        .status-bar p,
        .status-bar span,
        .status-bar div {
            margin: 0 !important;
            padding: 0 !important;
            border: none !important;
            height: auto !important;
        }

        /* Button row */
        .button-row {
            padding: 16px 0 24px 0 !important;
            background: #ffffff !important;
            border-top: 1px solid #e2e8f0 !important;
            flex-shrink: 0 !important;
        }

        /* Action buttons */
        .action-btn {
            background: #3b82f6 !important;
            color: white !important;
            border: none !important;
            border-radius: 6px !important;
            padding: 8px 18px !important;
            font-weight: 500 !important;
            font-size: 13px !important;
            transition: background 0.15s ease !important;
        }
        .action-btn:hover {
            background: #2563eb !important;
        }

        .secondary-action {
            background: #f8fafc !important;
            color: #334155 !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 6px !important;
            padding: 8px 18px !important;
            font-weight: 500 !important;
            font-size: 13px !important;
        }
        .secondary-action:hover {
            background: #f1f5f9 !important;
            border-color: #cbd5e1 !important;
        }

        /* Header */
        .app-header {
            border-bottom: 1px solid #e2e8f0;
            padding: 18px 24px;
            background: white;
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-shrink: 0 !important;
        }
        .app-title {
            font-size: 18px;
            font-weight: 600;
            color: #1e293b;
            margin: 0;
        }
        .model-badge {
            background: #f1f5f9;
            padding: 6px 14px;
            border-radius: 6px;
            font-size: 13px;
            color: #64748b;
        }

        /* Hide gradio footer */
        footer {
            display: none !important;
        }

        /* Accordion styling */
        .gr-accordion {
            border: 1px solid #e2e8f0 !important;
            border-radius: 8px !important;
            margin: 16px 24px !important;
        }
        """

        # Custom theme to fix Windows black background issue
        custom_theme = gr.themes.Soft(
            primary_hue="blue",
            secondary_hue="slate",
            neutral_hue="slate",
        )

        with gr.Blocks(
            title="RPG Adventure",
            theme=custom_theme,
            css=custom_css,
        ) as demo:
            # State
            game_state = gr.State(None)
            is_processing = gr.State(False)

            with gr.Row(equal_height=True):
                # Left Sidebar (dark)
                with gr.Column(scale=1, min_width=260, elem_classes="sidebar"):
                    # New Game button
                    reset_btn = gr.Button(
                        "+ New Game",
                        elem_classes="new-chat-btn",
                    )

                    gr.HTML('<div class="divider"></div>')

                    # Provider settings
                    gr.HTML('<p class="settings-label">AI Provider</p>')
                    available_providers = self.get_available_providers()
                    provider_dropdown = gr.Dropdown(
                        choices=available_providers,
                        value="Groq",
                        show_label=False,
                        container=False,
                    )

                    initial_config = self.get_provider_config("Groq")
                    model_dropdown = gr.Dropdown(
                        choices=initial_config["models"],
                        value=initial_config["default_model"],
                        show_label=False,
                        container=False,
                        allow_custom_value=True,
                    )

                    # API Key input
                    custom_api_key = gr.Textbox(
                        show_label=False,
                        placeholder="API Key",
                        type="password",
                        container=False,
                        elem_classes="api-input",
                    )
                    custom_api_url = gr.Textbox(
                        show_label=False,
                        placeholder="Custom API URL (optional)",
                        container=False,
                        visible=False,
                    )

                    gr.HTML('<div class="divider"></div>')

                    # Game settings
                    gr.HTML('<p class="settings-label">Game Settings</p>')
                    max_steps_slider = gr.Slider(
                        1,
                        Config.MAX_STEPS_LIMIT,
                        value=Config.DEFAULT_MAX_STEPS,
                        step=1,
                        label="Steps",
                        info="",
                    )
                    delay_slider = gr.Slider(
                        0,
                        Config.MAX_DELAY,
                        value=Config.DEFAULT_DELAY,
                        step=1,
                        label="Auto-play delay",
                        info="",
                    )

                # Main Chat Area
                with gr.Column(scale=4, elem_classes="main-chat"):
                    # Header
                    gr.HTML('''
                        <div class="app-header">
                            <h1 class="app-title">RPG Adventure</h1>
                            <span class="model-badge" id="model-display">Select a provider to start</span>
                        </div>
                    ''')

                    # Chat area - fills entire space
                    with gr.Column(elem_classes="chat-container"):
                        chatbot = gr.Chatbot(
                            label="",
                            height=550,
                            show_copy_button=True,
                            render_markdown=True,
                            elem_classes="chatbot-box",
                            container=False,
                        )

                    # Status bar
                    status_box = gr.Markdown(
                        "Ready to start your adventure. Configure your AI provider and click **Start**.",
                        elem_classes="status-bar"
                    )

                    # Action buttons at bottom
                    with gr.Row(elem_classes="button-row"):
                        start_btn = gr.Button(
                            "Start Adventure",
                            elem_classes="action-btn",
                        )
                        next_btn = gr.Button(
                            "Next Step",
                            elem_classes="secondary-action",
                        )
                        auto_btn = gr.Button(
                            "Auto-play",
                            elem_classes="secondary-action",
                        )

            # Hidden components for other tabs functionality
            with gr.Accordion("Advanced Options", open=False):
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### Export")
                        with gr.Row():
                            export_md_btn = gr.Button("Export Markdown")
                            export_txt_btn = gr.Button("Export Text")
                        export_output = gr.Textbox(label="Export", lines=8, show_copy_button=True)

                    with gr.Column():
                        gr.Markdown("### Debug")
                        info_btn = gr.Button("Show Game Info")
                        game_info_display = gr.JSON(label="Game State")
                        connection_btn = gr.Button("Test Connection")
                        connection_status = gr.JSON(label="Connection")

            # Hidden test components
            test_provider_dropdown = gr.Dropdown(visible=False)
            test_model_dropdown = gr.Dropdown(visible=False)
            test_results = gr.JSON(visible=False)

            # Event Handlers
            def update_provider_settings(selected_provider):
                provider_config = self.get_provider_config(selected_provider)
                models = provider_config["models"]
                default_model = provider_config["default_model"]
                show_custom = (
                    selected_provider == "Custom Provider"
                    or provider_config["requires_key"]
                )
                return (
                    gr.update(choices=models, value=default_model),
                    gr.update(visible=show_custom),
                    gr.update(value=provider_config["api_url"]),
                )

            provider_dropdown.change(
                update_provider_settings,
                [provider_dropdown],
                [model_dropdown, custom_api_key, custom_api_url],
            )

            start_btn.click(
                self.start_game_streaming,
                [max_steps_slider, provider_dropdown, model_dropdown, custom_api_url, custom_api_key],
                [chatbot, game_state, is_processing, status_box],
                show_progress="hidden",
            )

            next_btn.click(
                self.next_step_streaming,
                [game_state, max_steps_slider, is_processing, provider_dropdown, model_dropdown, custom_api_url, custom_api_key],
                [chatbot, game_state, is_processing, status_box],
                show_progress="hidden",
            )

            auto_btn.click(
                self.auto_play_streaming,
                [max_steps_slider, delay_slider, provider_dropdown, model_dropdown, custom_api_url, custom_api_key],
                [chatbot, game_state, is_processing, status_box],
                show_progress="minimal",
            )

            reset_btn.click(
                self.reset_game, [], [chatbot, game_state, is_processing, status_box]
            )

            def show_game_info(game):
                if game:
                    info = game.get_game_info()
                    info["current_provider"] = getattr(game.chat_client, "api_provider", "unknown")
                    info["current_model"] = getattr(game.chat_client, "model", "unknown")
                    return info
                return {"status": "No active game"}

            def export_markdown(game):
                return ConversationFormatter.to_markdown(game.conversation) if game and game.conversation else "No conversation"

            def export_text(game):
                return ConversationFormatter.to_plain_text(game.conversation) if game and game.conversation else "No conversation"

            def test_connection():
                client = ChatClient()
                return client.test_connection()

            info_btn.click(show_game_info, [game_state], [game_info_display])
            export_md_btn.click(export_markdown, [game_state], [export_output])
            export_txt_btn.click(export_text, [game_state], [export_output])
            connection_btn.click(test_connection, [], [connection_status])

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
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        print(
            "Check that all dependencies are installed and your API endpoint is reachable"
        )


if __name__ == "__main__":
    main()
