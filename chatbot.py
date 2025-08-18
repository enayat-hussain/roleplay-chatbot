import requests
import json
from typing import List, Dict, Generator, Any
from config import Config, ErrorMessages


class OllamaClient:
    """Client for interacting with Ollama API"""

    def __init__(self):
        self.api_url = Config.API_URL
        self.model = Config.MODEL
        self.ai_settings = Config.AI_SETTINGS
        self.timeout = Config.REQUEST_TIMEOUT

    def chat_streaming(self, messages: List[Dict[str, str]]) -> Generator[str, None, None]:
        """
        Stream conversation messages from Ollama API and yield chunks in real-time.
        Yields accumulated text content as it streams from the API.
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "options": self.ai_settings
        }

        try:
            response = requests.post(
                self.api_url,
                json=payload,
                stream=True,
                timeout=self.timeout
            )
            response.raise_for_status()

            full_content = ""

            # Process streaming response
            for line in response.iter_lines():
                if line:
                    try:
                        # Each line is a JSON object
                        chunk_data = json.loads(line.decode('utf-8'))

                        # Extract content from the chunk
                        if "message" in chunk_data and "content" in chunk_data["message"]:
                            chunk_text = chunk_data["message"]["content"]
                            full_content += chunk_text

                            # Yield the accumulated text so far
                            yield full_content

                        # Check if stream is done
                        if chunk_data.get("done", False):
                            break

                    except json.JSONDecodeError:
                        continue

            # Validate and enhance response if needed
            if not self._validate_gm_response(full_content):
                full_content = self._ensure_options_in_response(full_content)
                yield full_content

        except requests.exceptions.ConnectionError:
            error_msg = ErrorMessages.format_connection_error()
            yield error_msg
        except requests.exceptions.Timeout:
            error_msg = ErrorMessages.format_timeout_error()
            yield error_msg
        except requests.exceptions.HTTPError as e:
            error_msg = f"{ErrorMessages.REQUEST}: HTTP {e.response.status_code}"
            yield error_msg
        except Exception as e:
            error_msg = f"{ErrorMessages.REQUEST}: {str(e)}"
            yield error_msg

    def chat(self, messages: List[Dict[str, str]]) -> str:
        """Non-streaming version for compatibility"""
        full_response = ""
        for chunk in self.chat_streaming(messages):
            full_response = chunk
        return full_response

    def test_connection(self) -> Dict[str, Any]:
        """Test connection to Ollama API"""
        try:
            # Try a simple request to check if Ollama is running
            test_url = self.api_url.replace('/api/chat', '/api/tags')
            response = requests.get(test_url, timeout=5)

            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [model.get('name', 'unknown') for model in models]

                return {
                    "connected": True,
                    "status": "Ollama is running",
                    "available_models": model_names,
                    "current_model": self.model,
                    "model_available": self.model in model_names
                }
            else:
                return {
                    "connected": False,
                    "status": f"Ollama responded with status {response.status_code}",
                    "error": "Unexpected response"
                }

        except requests.exceptions.ConnectionError:
            return {
                "connected": False,
                "status": "Cannot connect to Ollama",
                "error": ErrorMessages.format_connection_error()
            }
        except Exception as e:
            return {
                "connected": False,
                "status": "Connection test failed",
                "error": str(e)
            }

    def get_client_info(self) -> Dict[str, Any]:
        """Get client configuration information"""
        return {
            "api_url": self.api_url,
            "model": self.model,
            "timeout": self.timeout,
            "ai_settings": self.ai_settings
        }

    def _validate_gm_response(self, response: str) -> bool:
        """Ensure GM response has 4 options"""
        if not response:
            return False

        option_count = 0
        for i in range(1, 5):
            if f"{i}." in response or f"{i})" in response:
                option_count += 1

        return option_count >= 4

    def _ensure_options_in_response(self, response: str) -> str:
        """Add default options if response doesn't have them"""
        if not self._validate_gm_response(response):
            additional_text = ("\n\nYour options now:\n"
                               "1. Continue exploring\n"
                               "2. Think carefully\n"
                               "3. Look around\n"
                               "4. Make a decision")
            return response + additional_text
        return response