# InfiniChat
InfiniChat is an application that simulates conversations between two LLMs using Ollama. The models maintain full conversation history, allowing them to reference previous exchanges.

<p align="center">
    <img src="https://github.com/richstokes/InfiniChat/blob/main/screenshot.png?raw=true" width="80%" alt="InfiniChat Screenshot">
</p>

## Features

- **Full Conversation History**: Models maintain a record of the entire conversation, enabling more coherent interactions
- **Smart Context Management**: When conversation history grows too large, earlier messages are summarized to maintain context
- **Streaming Responses**: Real-time streaming of model outputs with live display
- **Attractive Terminal UI**: Rich text formatting with color-coded speakers and panels
- **Conversation Saving**: Automatically saves transcripts of conversations

## Requirements

- Python 3.10+
- [Ollama](https://ollama.com/download) installed and running
- Required models (`qwen` and `gemma3:12b` by default) pulled in Ollama

## Installation

```bash
# Install dependencies
pipenv install
```

## Usage

Basic usage:
```bash
pipenv run python app.py
```

### Command-line Arguments

InfiniChat supports the following command-line arguments:

| Argument | Description | Default |
|----------|-------------|---------|
| `--max_turns` | Maximum number of conversation turns between the two AI models | 300 |
| `--max_tokens` | Maximum number of tokens per response from each AI model | 1000 |
| `--debug` | Enable debug mode for additional output | False |
| `--history_limit` | Maximum number of messages to keep in conversation history for each model | 15 |

### Examples

Run with custom settings:
```bash
# Run with 10 conversation turns and 500 tokens per response
pipenv run python app.py --max_turns 10 --max_tokens 500

# Run in debug mode
pipenv run python app.py --debug
```

After running, a conversation transcript will be saved to `conversation_history.txt`.
