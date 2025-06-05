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

        # Add system prompt to message history if provided
        if self.system_prompt:
            self.message_history.append(
                {"role": "system", "content": self.system_prompt}
            )

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

    def add_message_to_history(self, role: str, content: str):
        """
        Add a message to the message history for chat models.
        :param role: The role of the message sender ('user' or 'assistant').
        :param content: The content of the message.
        """
        self.message_history.append({"role": role, "content": content})
        # print(f"✅ Added message to history: {role} - {content}")

    def chat(self, max_tokens: int = 100, debug_mode=False) -> str:
        """
        Generate a chat response using the specified model and the current message history.

        :param max_tokens: The maximum number of tokens to generate.
        :param debug_mode: Whether to print debug information.
        :return: The generated chat response.
        """
        if not self.message_history:
            raise ValueError(
                "Message history is empty. Add messages before calling chat()."
            )

        # Build the request payload
        payload = {
            "model": self.model_name,
            "messages": self.message_history,
            "options": {"num_predict": max_tokens},
            "stream": False,
        }

        if debug_mode:
            print(f"\n****\nPayload for chat: {json.dumps(payload, indent=2)} \n****")

        response = requests.post(
            f"{self.base_url}/chat",
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        chat_response = data.get("message", {}).get("content", "")

        # Add the assistant's response to the message history
        self.message_history.append({"role": "assistant", "content": chat_response})

        if debug_mode:
            print(f"Chat response: {chat_response}")

        return chat_response

    def chat_stream(self, max_tokens: int = 100, debug_mode=False):
        """
        Generate a streaming chat response using the specified model and the current message history.

        :param max_tokens: The maximum number of tokens to generate.
        :param debug_mode: Whether to print debug information.
        :return: A generator yielding chunks of the generated chat response.
        """
        if not self.message_history:
            raise ValueError(
                "Message history is empty. Add messages before calling chat_stream()."
            )

        # Build the request payload
        payload = {
            "model": self.model_name,
            "messages": self.message_history,
            "options": {"num_predict": max_tokens},
            "stream": True,
        }

        if debug_mode:
            print(
                f"\n****\nPayload for streaming chat: {json.dumps(payload, indent=2)} \n****"
            )

        response = requests.post(
            f"{self.base_url}/chat",
            json=payload,
            stream=True,
        )
        response.raise_for_status()

        full_response = ""
        for line in response.iter_lines():
            if line:
                try:
                    data = json.loads(line)
                    message = data.get("message", {})
                    chunk = message.get("content", "")
                    if chunk:
                        full_response += chunk
                        yield chunk

                    # Check if done
                    if data.get("done", False):
                        break
                except json.JSONDecodeError:
                    print(f"Error decoding JSON: {line}")
                    continue

        # After streaming is complete, add the full response to message history
        self.message_history.append({"role": "assistant", "content": full_response})

    def chat_stream_with_callback(
        self, max_tokens: int = 100, callback=None, debug_mode=False
    ):
        """
        Generate a streaming chat response and apply a callback function to each chunk.
        Also returns the complete response as a single string.

        :param max_tokens: The maximum number of tokens to generate.
        :param callback: A function to call with each chunk (e.g., to display it).
        :param debug_mode: Whether to print debug information.
        :return: The complete generated chat response as a string.
        """
        result = ""
        for chunk in self.chat_stream(max_tokens, debug_mode=debug_mode):
            # Apply the callback to each chunk if provided
            if callback:
                callback(chunk)

            # Accumulate the result (not needed since we already add to history in chat_stream)
            result += chunk

        # Strip think tags if they exist
        result = self._strip_think_tag(result)

        return result

    def trim_message_history(self, max_messages=10, keep_system_prompt=True):
        """
        Trim the message history to prevent it from growing too large.
        Adds a summary of the trimmed messages to maintain conversation context.

        :param max_messages: Maximum number of messages to keep (excluding system prompt)
        :param keep_system_prompt: Whether to always keep the system prompt
        """
        if len(self.message_history) <= max_messages:
            return  # No need to trim

        # Determine which messages to trim
        if (
            keep_system_prompt
            and self.message_history
            and self.message_history[0].get("role") == "system"
        ):
            system_prompt = self.message_history[0]
            # Messages to be removed (excluding system prompt)
            messages_to_trim = self.message_history[1 : -(max_messages - 2)]
            # Messages to keep (most recent ones)
            recent_messages = self.message_history[-(max_messages - 2) :]

            # Create a summary of the trimmed messages
            summary = self._create_conversation_summary(messages_to_trim)

            # Add the summary as a user message
            summary_message = {
                "role": "user",
                "content": f"Summary of previous conversation: {summary}",
            }

            # Reconstruct the message history with: system prompt + summary + recent messages
            self.message_history = [system_prompt, summary_message] + recent_messages
        else:
            # Messages to be removed
            messages_to_trim = self.message_history[: -max_messages + 1]
            # Messages to keep
            recent_messages = self.message_history[-max_messages + 1 :]

            # Create a summary of the trimmed messages
            summary = self._create_conversation_summary(messages_to_trim)

            # Add the summary as a user message
            summary_message = {
                "role": "user",
                "content": f"Summary of previous conversation: {summary}",
            }

            # Reconstruct the message history with: summary + recent messages
            self.message_history = [summary_message] + recent_messages

    def _create_conversation_summary(self, messages):
        """
        Create a concise summary of the provided messages using the LLM itself.

        :param messages: List of message objects to summarize
        :return: A string containing a concise summary generated by the LLM
        """
        # If there are no messages to summarize
        if not messages:
            return "No previous messages."

        # Create a temporary client with the same model for summarization
        # We don't want to modify the main client's message history
        summarizer = OllamaClient(self.model_name)

        # Prepare the prompt for summarization
        summarization_prompt = {
            "role": "system",
            "content": (
                "You are a helpful assistant tasked with creating a concise summary of a conversation. "
                "The summary should capture the main topics, key points, and any important information "
                "from the conversation. Be brief but comprehensive. Your summary will be used to provide "
                "context for a continuing conversation."
            ),
        }

        # Prepare the conversation to summarize
        conversation_to_summarize = {
            "role": "user",
            "content": (
                "Please summarize the following conversation in a concise but informative way. "
                "Focus on the key points, questions, and conclusions:\n\n"
            ),
        }

        # Format the conversation as a readable text for the summarizer
        conversation_text = ""
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")

            # Skip system messages in the conversation text
            if role == "system":
                continue

            conversation_text += f"{role.capitalize()}: {content}\n\n"

        conversation_to_summarize["content"] += conversation_text

        # Set up the summarizer's message history
        summarizer.message_history = [summarization_prompt, conversation_to_summarize]

        try:
            # Get the summary from the LLM (with a reasonable token limit)
            summary = summarizer.chat(max_tokens=300)
            return summary
        except Exception as e:
            # Fallback to a simpler summary approach if the LLM summarization fails
            print(
                f"Error generating LLM summary: {e}. Falling back to simple summarization."
            )
            return self._create_simple_summary(messages)

    def _create_simple_summary(self, messages):
        """
        Create a concise bullet-point summary of the provided messages.
        This is used as a fallback if the LLM summarization fails.

        :param messages: List of message objects to summarize
        :return: A string containing a bullet-point summary
        """
        # Create a simple bullet point summary
        summary_points = []
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")

            # Skip system messages
            if role == "system":
                continue

            # Truncate very long messages
            if len(content) > 100:
                content = content[:97] + "..."

            if role == "user":
                summary_points.append(f"• User asked: {content}")
            elif role == "assistant":
                summary_points.append(f"• Assistant responded about: {content}")

        # If we have too many points, keep only the first and last few
        if len(summary_points) > 8:
            first_points = summary_points[:3]
            last_points = summary_points[-3:]
            summary_points = (
                first_points
                + [f"• ... ({len(summary_points) - 6} more exchanges) ..."]
                + last_points
            )

        return "\n".join(summary_points)
