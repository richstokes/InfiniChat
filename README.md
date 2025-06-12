# InfiniChat
InfiniChat is a command-line application that simulates conversations between two LLMs using Ollama. Just for fun really / I find it interesting to watch the exchanges. You can have them flesh out ideas, debate things, argue, or just give vague prompts and see what topics they spiral in to. 

<p align="center">
    <img src="https://github.com/richstokes/InfiniChat/blob/main/screenshot.png?raw=true" width="0%" alt="InfiniChat Screenshot">
</p>

## Features

- **Full Conversation History**: Models maintain a record of the entire conversation, enabling more coherent interactions
- **Smart Context Management**: When conversation history grows too large, earlier messages are intelligently summarized by the LLM itself to maintain context
- **Streaming Responses**: Real-time streaming of model outputs with live display
- **Attractive Terminal UI**: Rich text formatting with color-coded speakers and panels
- **Debate Mode**: Set a specific topic for the models to debate, with one arguing "for" and the other "against"
- **Conversation Saving**: Automatically saves transcripts of conversations

## Requirements

- Python 3.+
- [Ollama](https://ollama.com/download) installed and running
- Required models (`llama3` and `gemma3` by default) pulled in Ollama
- A "non-trivial" amount of RAM. This uses 30GB+ on my Macbook.

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

Edit the prompts in `prompts.py` to your liking.  


### Command-line Arguments

InfiniChat supports the following command-line arguments:

| Argument | Description | Default |
|----------|-------------|---------|
| `--max_turns` | Maximum number of conversation turns between the two AI models | 300 |
| `--max_tokens` | Maximum number of tokens per response from each AI model (just leave it at default unless you know you need to change it) | 1000 |
| `--debug` | Enable debug mode for additional output | False |
| `--show_json` | Show RAW JSON from chat api | False | 
| `--stats` | Show message history statistics in panel titles | False |
| `--history_limit` | Maximum number of messages to keep in conversation history for each model | 30 |
| `--delay` | Delay in seconds between streaming chunks (for slower, more readable streaming) | 0.0 |
| `--model_a` | Name of the first AI model to use | llama3:latest |
| `--model_b` | Name of the second AI model to use | gemma3:12b |
| `--debate_topic "Pizza is a vegetable"` | Topic to debate, model A will be "for" the topic, model B will be "against" | None |

### Examples

Run with custom settings:
```bash
# Run with 2000 conversation turns!
pipenv run python app.py --max_turns 2000

# Run in debug mode
pipenv run python app.py --debug

# Show message history statistics in panel titles
pipenv run python app.py --stats

# Add a delay for slower, more readable streaming
pipenv run python app.py --delay 0.1

# Use different models
pipenv run python app.py --model_a qwen:latest --model_b deepseek-r1:latest

# Start a debate
pipenv run python app.py --debate_topic "Dogs are better than cats"
```

After running, a conversation transcript will be saved to `conversation_history.txt`.

## Conversation History Management

InfiniChat employs sophisticated conversation history management to ensure that the LLMs maintain coherent context throughout the conversation:

1. **Full History Tracking**: Both models maintain a complete record of all message exchanges.

2. **LLM-Powered Summarization**: When the history grows too large:
   - The LLM itself generates an intelligent summary of older messages
   - This summary preserves key context and important information
   - The summary replaces older messages to maintain the context window size

3. **Fallback Mechanism**: If LLM summarization fails for any reason, a simple bullet-point summary is created instead.

This approach allows the conversation to continue indefinitely while maintaining coherent context, even as older messages are trimmed from the history.
