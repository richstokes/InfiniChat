import requests
import json
import platform
import subprocess
import sys


class OllamaClient:
    def __init__(self, model_name: str, system_prompt: str = None):
        self.model_name = model_name
        self.system_prompt = system_prompt
        self.base_url = "http://localhost:11434/api"
        self.message_history = (
            []
        )  # Initialize an empty message history, used for chat models

        # Check if Ollama is installed and running
        self._check_ollama_availability()

        # Check if the requested model is available
        self._check_model_availability()

        print(f"✅ OllamaClient initialized with model: {self.model_name}")

    def _check_ollama_availability(self):
        """
        Check if Ollama is installed and running.
        Provide installation instructions if not available.
        """
        try:
            response = requests.get(f"{self.base_url}/tags", timeout=5)
            response.raise_for_status()
            print("✅ Ollama server is available.")
        except requests.RequestException as e:
            print(f"❌ Error connecting to Ollama server: {e}")
            self._provide_ollama_installation_guide()
            self._try_start_ollama_service()  # Attempt to start the service
            raise RuntimeError(
                "Ollama server is not available. Please follow the installation instructions above."
            )

    def _check_model_availability(self):
        """
        Check if the requested model is available.
        Provide pull instructions if the model is not available.
        """
        try:
            response = requests.get(f"{self.base_url}/tags")
            models_data = response.json()

            # Check if the model exists in the list of available models
            model_exists = any(
                model["name"] == self.model_name
                for model in models_data.get("models", [])
            )

            if model_exists:
                print(f"✅ Model '{self.model_name}' is available.")
            else:
                print(f"❌ Model '{self.model_name}' is not available locally.")
                self._provide_model_pull_guide()
                raise RuntimeError(
                    f"Model '{self.model_name}' is not available. Please pull the model first."
                )

        except requests.RequestException as e:
            print(f"❌ Error checking model availability: {e}")
            raise RuntimeError(
                f"Could not check if model '{self.model_name}' exists. Please check your connection."
            )

    def _provide_ollama_installation_guide(self):
        """Provide platform-specific instructions for installing Ollama."""
        os_name = platform.system().lower()

        print("\n=== Ollama Installation Guide ===")

        if os_name == "darwin":  # macOS
            print("To install Ollama on macOS:")
            print("1. Download Ollama from https://ollama.com/download")
            print(
                "2. Open the downloaded file and follow the installation instructions"
            )
            print("3. Start Ollama from your Applications folder")
            print("\nAlternatively, install via Homebrew:")
            print("   brew install ollama")
            print("   ollama serve")
        elif os_name == "linux":
            print("To install Ollama on Linux:")
            print("1. Run the following command:")
            print("   curl -fsSL https://ollama.com/install.sh | sh")
            print("2. Start the Ollama service:")
            print("   ollama serve")
        elif os_name == "windows":
            print("To install Ollama on Windows:")
            print("1. Download Ollama from https://ollama.com/download")
            print("2. Run the installer and follow the installation instructions")
            print("3. Start Ollama from the Start menu")
        else:
            print(
                f"Please visit https://ollama.com/download for instructions on installing Ollama on {os_name}"
            )

        print(
            "\nAfter installation, make sure the Ollama service is running before trying again."
        )
        print("===================================\n")

    def _provide_model_pull_guide(self):
        """Provide instructions for pulling the requested model."""
        print(f"\n=== How to Pull Model '{self.model_name}' ===")
        print(f"To download the '{self.model_name}' model, run:")
        print(f"   ollama pull {self.model_name}")
        print(
            "\nIf using the desktop app, you can also pull models from the library tab."
        )

    def generate_text(self, prompt: str, max_tokens: int = 100) -> str:
        """
        Generate text using the specified model and prompt.

        :param prompt: The input text to generate a response for.
        :param max_tokens: The maximum number of tokens to generate.
        :return: The generated text.
        """
        # Send the prompt to ollama and get the response
        print(f"Generating text with prompt: {prompt} and max_tokens: {max_tokens}")

        # Build the request payload
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "options": {"num_predict": max_tokens},
        }

        # Add system prompt if available
        if self.system_prompt:
            payload["system"] = self.system_prompt

        # Set stream to False explicitly for non-streaming requests
        payload["stream"] = False

        response = requests.post(
            f"{self.base_url}/generate",
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        generated_text = data.get("response", "")
        print(f"Generated text: {generated_text}")
        return generated_text

    def generate_stream(self, prompt: str, max_tokens: int = 100, debug_mode=False):
        """
        Generate streaming text using the specified model and prompt.

        :param prompt: The input text to generate a response for.
        :param max_tokens: The maximum number of tokens to generate.
        :return: A generator yielding chunks of generated text.
        """
        # print(f"Streaming text with prompt: {prompt}[max_tokens: {max_tokens}]")

        # Build the request payload
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "options": {"num_predict": max_tokens},
            "stream": True,
        }

        # Add system prompt if available
        if self.system_prompt:
            payload["system"] = self.system_prompt

        if debug_mode:
            print(
                f"\n****\nPayload for streaming: {json.dumps(payload, indent=2)} \n****"
            )  # For debugging

        response = requests.post(
            f"{self.base_url}/generate",
            json=payload,
            stream=True,
        )
        response.raise_for_status()

        for line in response.iter_lines():
            if line:
                try:
                    data = json.loads(line)
                    chunk = data.get("response", "")
                    if chunk:
                        yield chunk

                    # Check if done
                    if data.get("done", False):
                        break
                except json.JSONDecodeError:
                    print(f"Error decoding JSON: {line}")
                    continue
                    break

    def generate_text_stream(self, prompt: str, max_tokens: int = 100) -> str:
        """
        Generate text using streaming but return the complete output as a single string.

        :param prompt: The input text to generate a response for.
        :param max_tokens: The maximum number of tokens to generate.
        :return: The complete generated text as a string.
        """
        result = ""
        for chunk in self.generate_stream(prompt, max_tokens):
            result += chunk
        return result

    def generate_stream_with_callback(
        self, prompt: str, max_tokens: int = 100, callback=None, debug_mode=False
    ):
        """
        Generate streaming text and apply a callback function to each chunk.
        Also returns the complete response as a single string.

        :param prompt: The input text to generate a response for.
        :param max_tokens: The maximum number of tokens to generate.
        :param callback: A function to call with each chunk (e.g., to display it).
        :return: The complete generated text as a string.
        """
        result = ""
        for chunk in self.generate_stream(prompt, max_tokens, debug_mode=debug_mode):
            # Apply the callback to each chunk if provided
            if callback:
                callback(chunk)

            # Accumulate the result
            result += chunk

        # Strip think tags if they exist
        result = self._strip_think_tag(result)

        return result

    def _try_start_ollama_service(self):
        """
        Attempt to start the Ollama service if it's installed but not running.

        :return: True if successfully started, False otherwise
        """
        os_name = platform.system().lower()

        try:
            if os_name == "darwin" or os_name == "linux":  # macOS or Linux
                print("Attempting to start Ollama service...")

                # Check if ollama command is available
                try:
                    subprocess.run(
                        ["which", "ollama"],
                        check=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                    )

                    # Try to start the service in the background
                    subprocess.Popen(
                        ["ollama", "serve"],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                    )

                    # Wait a moment for the service to start
                    import time

                    time.sleep(3)

                    # Check if the service is now running
                    try:
                        response = requests.get(f"{self.base_url}/models", timeout=2)
                        if response.status_code == 200:
                            print("✅ Successfully started Ollama service!")
                            return True
                    except requests.RequestException:
                        pass

                except subprocess.CalledProcessError:
                    # ollama command not found
                    return False

            # For Windows or if the above failed
            return False

        except Exception as e:
            print(f"Error trying to start Ollama: {e}")
            return False

    def _strip_think_tag(self, text: str) -> str:
        """
        Strip the <think> thinking text here </think> tags from the generated text.
        :param text: The generated text containing think tags.
        :return: The text with think tags and everything between them removed.

        Needed for DeepSeek models which return text with <think> tags.
        """
        import re

        # First attempt to remove complete think tags with content between them
        # Use non-greedy matching to handle multiple think tags in the same text
        cleaned_content = re.sub(r"<think>[\s\S]*?</think>", "", text, flags=re.DOTALL)

        # Then handle any orphaned opening tags (in case the closing tag is missing)
        cleaned_content = re.sub(
            r"<think>[\s\S]*?($|(?=<think>))", "", cleaned_content, flags=re.DOTALL
        )

        # Remove any standalone closing tags that might remain
        cleaned_content = re.sub(r"</think>", "", cleaned_content)

        # Clean up any extra whitespace or newlines that might have been left behind
        cleaned_content = re.sub(r"\n{3,}", "\n\n", cleaned_content)

        return cleaned_content.strip()
