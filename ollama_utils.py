"""
Utility functions for Ollama installation and model management.
"""

import platform
import re
import requests
import subprocess
import time
from console_utils import console


def provide_ollama_installation_guide():
    """Provide platform-specific instructions for installing Ollama."""
    os_name = platform.system().lower()

    print("\n=== Ollama Installation Guide ===")

    if os_name == "darwin":  # macOS
        print("To install Ollama on macOS:")
        print("1. Download Ollama from https://ollama.com/download")
        print("2. Open the downloaded file and follow the installation instructions")
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


def provide_model_pull_guide(model_name):
    """Provide instructions for pulling the requested model."""
    print(f"\n=== How to Pull Model '{model_name}' ===")
    print(f"To download the '{model_name}' model, run:")
    print(f"   ollama pull {model_name}")
    print("\nIf using the desktop app, you can also pull models from the library tab.")


def strip_think_tag(text: str) -> str:
    """
    Strip the <think> thinking text here </think> tags from the generated text.
    :param text: The generated text containing think tags.
    :return: The text with think tags and everything between them removed.

    Needed for DeepSeek models which return text with <think> tags.
    """
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


def check_model_availability(
    model_name: str,
    base_url: str = "http://localhost:11434/api",
    quiet_mode: bool = False,
):
    """
    Check if the requested model is available.
    Provide pull instructions if the model is not available.

    :param model_name: The name of the model to check
    :param base_url: The base URL for the Ollama API
    :param quiet_mode: Whether to suppress success messages
    :raises RuntimeError: If the model is not available or there's a connection error
    """
    try:
        response = requests.get(f"{base_url}/tags")
        models_data = response.json()

        # Check if the model exists in the list of available models
        model_exists = any(
            model["name"] == model_name for model in models_data.get("models", [])
        )

        if model_exists:
            if not quiet_mode:
                console.print(
                    f"[bold green]Model '{model_name}' is available locally.[/bold green]"
                )
        else:
            console.print(
                "[bold red]Model not found. Please pull the model first.[/bold red]"
            )
            provide_model_pull_guide(model_name)
            raise RuntimeError(
                f"Model '{model_name}' is not available. Please pull the model first."
            )

    except requests.RequestException as e:
        console.print(
            "[bold red]Could not check model availability. Please check your connection.[/bold red]"
        )
        raise RuntimeError(
            f"Could not check if model '{model_name}' exists. Please check your connection."
        )


def try_start_ollama_service(base_url: str = "http://localhost:11434/api"):
    """
    Attempt to start the Ollama service if it's installed but not running.

    :param base_url: The base URL for the Ollama API
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
                time.sleep(3)

                # Check if the service is now running
                try:
                    response = requests.get(f"{base_url}/models", timeout=2)
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


def check_ollama_availability(
    base_url: str = "http://localhost:11434/api", quiet_mode: bool = False
):
    """
    Check if Ollama is installed and running.
    Provide installation instructions if not available.

    :param base_url: The base URL for the Ollama API
    :param quiet_mode: Whether to suppress success messages
    :raises RuntimeError: If Ollama server is not available
    """
    try:
        response = requests.get(f"{base_url}/tags", timeout=5)
        response.raise_for_status()
    except requests.RequestException as e:
        console.print(
            "[bold red]Ollama server is not available. Please install Ollama first.[/bold red]"
        )
        provide_ollama_installation_guide()
        try_start_ollama_service(base_url)  # Attempt to start the service
        raise RuntimeError(
            "Ollama server is not available. Please follow the installation instructions above."
        )
