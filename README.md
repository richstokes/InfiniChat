# InfiniChat
InfiniChat is a command-line application that simulates conversations between two LLMs running locally using Ollama. Just for fun really - I find it interesting to watch the chats! You can have them flesh out ideas, debate things, argue, or just give vague prompts and see what topics they spiral in to. 

<p align="center">
    <img src="https://github.com/richstokes/InfiniChat/blob/main/screenshot.png?raw=true" width="95%" alt="InfiniChat Screenshot">
</p>

## Features

- **Full Conversation History**: Models maintain a record of the entire conversation, enabling more coherent interactions
- **Streaming Responses**: Real-time streaming of model outputs with live display
- **Attractive Terminal UI**: Rich text formatting with color-coded speakers and panels
- **Debate Mode**: Set a specific topic for the models to debate, with one arguing "for" and the other "against"
- **Conversation Saving**: Automatically saves transcripts of conversations

## Requirements

- Python 3.+
- [Ollama](https://ollama.com/download) installed and running
- Required models (`llama3:latest` and `gemma3:12b` by default) pulled in Ollama
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
| `--max_turns` | Maximum number of conversation turns between the two AI models | 9000 |
| `--max_tokens` | Maximum number of tokens per response from each AI model (just leave it at default unless you know you need to change it) | 1000 |
| `--debug` | Enable debug mode for additional output | False |
| `--show_json` | Show RAW JSON from chat api | False | 
| `--stats` | Show message history statistics in panel titles | False |
| `--history_limit` | Maximum number of messages to keep in conversation history for each model before truncating | 500 |
| `--delay` | Delay in seconds between streaming chunks (for slower, more readable streaming) | 0.0 |
| `--model_a` | Name of the first AI model to use | llama3:latest |
| `--model_b` | Name of the second AI model to use | gemma3:12b |
| `--debate_topic "Pizza is a vegetable"` | Topic to debate, model A will be "for" the topic, model B will be "against" | None |
| `--model_a_prompt "Your custom prompt"` | Custom system prompt for model A (overrides default from `prompts.py`) | None |
| `--model_b_prompt "Your custom prompt"` | Custom system prompt for model B (overrides default from `prompts.py`) | None |

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
pipenv run python app.py --debate_topic "Coffee is better than tea"

# Use custom prompts for both models
pipenv run python app.py --model_a_prompt "You are a cheerful assistant who loves to help people" --model_b_prompt "You are a serious academic who prefers formal language"

# Override just one model's prompt
pipenv run python app.py --model_a_prompt "You are a pirate who speaks in nautical terms"
```

After running, a conversation transcript will be saved to `conversation_history.txt`. This will be overwritten each run, so copy it somewhere if you wish to keep it. 
