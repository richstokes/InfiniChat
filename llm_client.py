import requests
import json
import platform
import subprocess
import sys
from console_utils import console
from ollama_utils import (
    provide_ollama_installation_guide,
    provide_model_pull_guide,
    strip_think_tag,
    check_model_availability,
)

HISTORY_LOG_FILE = "message_history.log"


class OllamaClient:
    def __init__(
        self,
        model_name: str,
        system_prompt: str = None,
        debug_mode: bool = False,
        show_json: bool = False,
        quiet_mode: bool = False,
        history_limit: int = 30,
        log_history: bool = False,
    ):
        self.quiet_mode = quiet_mode
        self.debug_mode = debug_mode
        self.show_json = show_json
        self.model_name = model_name
        self.system_prompt = system_prompt
        self.history_limit = history_limit
        self.log_history = log_history
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
        check_model_availability(self.model_name, self.base_url, self.quiet_mode)

        if not self.quiet_mode:
            console.print(
                f"[bold green]OllamaClient initialized with model: {self.model_name}[/bold green]"
            )

    def _check_ollama_availability(self):
        """
        Check if Ollama is installed and running.
        Provide installation instructions if not available.
        """
        try:
            response = requests.get(f"{self.base_url}/tags", timeout=5)
            response.raise_for_status()
            if not self.quiet_mode:
                console.print(
                    "[bold green]Ollama server is running and accessible.[/bold green]"
                )
        except requests.RequestException as e:
            console.print(
                "[bold red]Ollama server is not available. Please install Ollama first.[/bold red]"
            )
            provide_ollama_installation_guide()
            self._try_start_ollama_service()  # Attempt to start the service
            raise RuntimeError(
                "Ollama server is not available. Please follow the installation instructions above."
            )

    def _try_start_ollama_service(self):
        """
        Attempt to start the Ollama service if it's installed but not running.

        :return: True if successfully started, False otherwise
        """
        os_name = platform.system().lower()

        try:
            if os_name == "darwin" or os_name == "linux":  # macOS or Linux
                console.print(
                    "[bold yellow]Attempting to start Ollama service...[/bold yellow]"
                )

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
                            console.print(
                                "[bold green]✅ Successfully started Ollama service![/bold green]"
                            )
                            return True
                    except requests.RequestException:
                        pass

                except subprocess.CalledProcessError:
                    # ollama command not found
                    return False

            # For Windows or if the above failed
            return False

        except Exception as e:
            console.print(
                "[bold red]Failed to start Ollama service. Please start it manually.[/bold red]"
            )
            return False

    def add_message_to_history(self, role: str, content: str):
        """
        Add a message to the message history for chat models.
        :param role: The role of the message sender ('user' or 'assistant').
        :param content: The content of the message.
        """
        self.message_history.append({"role": role, "content": content})
        # print(f"✅ Added message to history: {role} - {content}")
        if self.log_history:
            with open(HISTORY_LOG_FILE, "w") as f:
                # f.write(f"{role}: {content}\n")
                f.write(json.dumps(self.message_history, indent=2))

    def chat_stream(self, max_tokens: int = 100):
        """
        Generate a streaming chat response using the specified model and the current message history.

        :param max_tokens: The maximum number of tokens to generate.
        :return: A generator yielding chunks of the generated chat response.
        """
        if not self.message_history:
            raise ValueError(
                "Message history is empty. Add messages before calling chat_stream()."
            )

        # Auto-trim if the history is getting too long
        self._auto_trim_if_needed()

        # Build the request payload
        payload = {
            "model": self.model_name,
            "messages": self.message_history,
            "options": {"num_predict": max_tokens},
            "stream": True,
        }

        if self.show_json:
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

    def chat_stream_with_callback(self, max_tokens: int = 100, callback=None):
        """
        Generate a streaming chat response and apply a callback function to each chunk.
        Also returns the complete response as a single string.

        :param max_tokens: The maximum number of tokens to generate.
        :param callback: A function to call with each chunk (e.g., to display it).
        :return: The complete generated chat response as a string.
        """
        result = ""
        for chunk in self.chat_stream(max_tokens):
            # Apply the callback to each chunk if provided
            if callback:
                callback(chunk)

            # Accumulate the result (not needed since we already add to history in chat_stream)
            result += chunk

        # Strip think tags if they exist
        result = strip_think_tag(result)

        return result

    def trim_message_history(self, max_messages, keep_system_prompt=True):
        """
        Trim the message history to prevent it from growing too large.
        Simple strategy: if history exceeds max_messages, summarize everything
        (except system prompt) and replace history with just system prompt + summary.

        :param max_messages: Maximum number of messages before triggering trim
        :param keep_system_prompt: Whether to always keep the system prompt
        """
        if self.debug_mode:
            print(f"Trimming message history to a maximum of {max_messages} messages.")
            print(f"Current message history length: {len(self.message_history)}")

        # Check if trimming is needed
        if len(self.message_history) <= max_messages:
            if self.debug_mode:
                print("No trimming needed - history is within limit.")
            return

        # Identify system prompt if it exists
        system_prompt = None
        start_index = 0
        if (
            keep_system_prompt
            and self.message_history
            and self.message_history[0].get("role") == "system"
        ):
            system_prompt = self.message_history[0]
            start_index = 1

        # Get all messages to summarize (everything except system prompt)
        messages_to_summarize = self.message_history[start_index:]

        if not messages_to_summarize:
            if self.debug_mode:
                print("No messages to summarize - keeping current history.")
            return

        # Create summary of all conversation messages
        summary = self._create_conversation_summary(messages_to_summarize)
        summary_message = {
            "role": "user",
            "content": f"Summary of previous conversation: {summary}",
        }

        # Replace message history with just system prompt + summary
        new_history = []
        if system_prompt:
            new_history.append(system_prompt)
        new_history.append(summary_message)

        self.message_history = new_history

        if self.debug_mode:
            print(f"Created summary for {len(messages_to_summarize)} messages")
            print(
                f"Message history after trimming: {len(self.message_history)} messages"
            )

    def _create_conversation_summary(self, messages):
        """
        Create a concise summary of the provided messages using the LLM itself.

        :param messages: List of message objects to summarize
        :return: A string containing a concise summary generated by the LLM
        """
        if self.debug_mode:
            print(f"Creating a summary of {len(messages)} messages...")
        # If there are no messages to summarize
        if not messages:
            return "No previous messages."

        # Create a temporary client with the same model for summarization
        # We don't want to modify the main client's message history
        summarizer = OllamaClient(self.model_name, quiet_mode=True)

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
            summary = summarizer.chat(max_tokens=2000)
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

    def _auto_trim_if_needed(self, max_messages=None):
        """
        Automatically trim message history if it's getting too long.
        This should be called before chat operations to prevent unbounded growth.
        Uses aggressive trimming to keep only essential context.

        :param max_messages: The threshold at which to trigger trimming.
                           If None, uses self.history_limit
        """
        if max_messages is None:
            max_messages = self.history_limit

        if len(self.message_history) > max_messages:
            # Aggressive trimming: reduce to minimal viable history
            # This will result in: system_prompt + summary + last_exchange (3-4 messages total)
            self.trim_message_history(max_messages)
