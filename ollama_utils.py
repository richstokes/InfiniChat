"""
Utility functions for Ollama installation and model management.
"""

import platform
import re


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
