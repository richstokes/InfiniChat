from llm_client import OllamaClient
from rich.console import Console
from rich.panel import Panel
from rich.box import ROUNDED
from rich.text import Text
from rich.live import Live
from rich import print as rprint
import argparse
import sys
import time

# MODEL_A_NAME = "deepseek-r1:latest"
# MODEL_A_NAME = "qwen:latest"
MODEL_A_NAME = "llama3:latest"
MODEL_B_NAME = "gemma3:12b"
INITIAL_PROMPT = "Hello, who are you?"

# Initialize Rich console
console = Console()

# Style for client A - blue theme
CLIENT_A_STYLE = "bold blue"
CLIENT_A_PANEL_STYLE = "blue"

# Style for client B - green theme
CLIENT_B_STYLE = "bold green"
CLIENT_B_PANEL_STYLE = "green"


def simulate_conversation(
    client_a,
    client_b,
    max_turns,
    max_tokens,
    initial_prompt="",
    debug_mode=False,
    history_limit=15,  # Maximum messages to keep in history per client
    delay=0.00,  # Delay between streaming chunks
):
    """
    Simulate a conversation between two LLM clients with rich formatting.

    :param client_a: First OllamaClient instance
    :param client_b: Second OllamaClient instance
    :param initial_prompt: Optional initial prompt to start the conversation
    :param max_turns: Maximum number of conversation turns
    :param max_tokens: Maximum tokens per response
    :param history_limit: Maximum number of messages to keep in history for each client
    :return: The complete conversation history as a string
    """
    conversation_history = []

    # Re-add system prompts
    if client_a.system_prompt:
        client_a.add_message_to_history("system", client_a.system_prompt)
    if client_b.system_prompt:
        client_b.add_message_to_history("system", client_b.system_prompt)

    if debug_mode:
        console.print(
            f"[bold yellow]Debug mode enabled![/bold yellow] Max turns: {max_turns}, Max tokens: {max_tokens}, History limit: {history_limit}"
        )

    # Display a title for the conversation
    # console.print(
    #     Panel.fit(
    #         "🤖 [bold yellow]InfiniChat: AI Conversation[/bold yellow] 🤖",
    #         box=ROUNDED,
    #         border_style="yellow",
    #         padding=(1, 2),
    #     )
    # )

    if initial_prompt:
        # Display the initial prompt
        console.print(
            Panel(
                f"[italic]{initial_prompt}[/italic]",
                title="[bold]Initial Prompt[/bold]",
                title_align="left",
                border_style="yellow",
                box=ROUNDED,
                padding=(1, 2),
            )
        )
        conversation_history.append(f"Initial: {initial_prompt}")

        # Add initial prompt to client B's history (client A will generate first response)
        client_b.add_message_to_history("user", initial_prompt)

    try:
        for turn in range(max_turns):
            # Add a spacer between turns
            console.print("")

            # Display turn counter
            console.print(
                f"[bold white on grey66]Round {turn+1}/{max_turns}[/bold white on grey66]",
                justify="center",
            )

            # Client A's turn
            console.print(
                f"\n[{CLIENT_A_STYLE}]🤖 {client_a.model_name} is thinking...[/{CLIENT_A_STYLE}]"
            )

            # Create a buffer to collect the streamed text
            response_buffer = ""

            # Create a live display that will update as text streams in
            with Live(
                Panel(
                    "",
                    title=f"[{CLIENT_A_STYLE}]{client_a.model_name}[/{CLIENT_A_STYLE}]",
                    title_align="left",
                    border_style=CLIENT_A_PANEL_STYLE,
                    box=ROUNDED,
                    padding=(1, 2),
                ),
                console=console,
                refresh_per_second=20,
            ) as live:
                # Define a callback function that updates the live display
                def display_chunk(chunk):
                    nonlocal response_buffer
                    response_buffer += chunk
                    live.update(
                        Panel(
                            Text(response_buffer, no_wrap=False),
                            title=f"[{CLIENT_A_STYLE}]{client_a.model_name}[/{CLIENT_A_STYLE}]",
                            title_align="left",
                            border_style=CLIENT_A_PANEL_STYLE,
                            box=ROUNDED,
                            padding=(1, 2),
                        )
                    )
                    time.sleep(delay)

                # Get response from client A
                # Add the message from client B (or initial prompt) to client A's history
                if turn == 0:
                    # First turn: Use the initial prompt
                    client_a.add_message_to_history("user", initial_prompt)
                else:
                    # Subsequent turns: Use the previous response from client B
                    client_a.add_message_to_history("user", response_b)

                # Generate a response using chat API with full conversation history
                response_a = client_a.chat_stream_with_callback(
                    max_tokens,
                    callback=display_chunk,
                    debug_mode=debug_mode,
                )

                # Trim history to prevent it from growing too large
                client_a.trim_message_history(
                    max_messages=history_limit, keep_system_prompt=True
                )

            # Add the response to conversation history
            conversation_history.append(f"{client_a.model_name}: {response_a}")

            # Add a spacer before the next response
            console.print("")

            # Client B's turn
            console.print(
                f"\n[{CLIENT_B_STYLE}]🤖 {client_b.model_name} is thinking...[/{CLIENT_B_STYLE}]"
            )

            # Reset the buffer for client B
            response_buffer = ""

            # Create a live display for client B
            with Live(
                Panel(
                    "",
                    title=f"[{CLIENT_B_STYLE}]{client_b.model_name}[/{CLIENT_B_STYLE}]",
                    title_align="left",
                    border_style=CLIENT_B_PANEL_STYLE,
                    box=ROUNDED,
                    padding=(1, 2),
                ),
                console=console,
                refresh_per_second=20,
            ) as live:
                # Define a callback function that updates the live display
                def display_chunk(chunk):
                    nonlocal response_buffer
                    response_buffer += chunk
                    live.update(
                        Panel(
                            Text(response_buffer, no_wrap=False),
                            title=f"[{CLIENT_B_STYLE}]{client_b.model_name}[/{CLIENT_B_STYLE}]",
                            title_align="left",
                            border_style=CLIENT_B_PANEL_STYLE,
                            box=ROUNDED,
                            padding=(1, 2),
                        )
                    )
                    time.sleep(delay)

                # Get response from client B
                # Add client A's response to client B's history
                client_b.add_message_to_history("user", response_a)

                # Generate a response using chat API with full conversation history
                response_b = client_b.chat_stream_with_callback(
                    max_tokens,
                    callback=display_chunk,
                    debug_mode=debug_mode,
                )

                # Trim history to prevent it from growing too large
                client_b.trim_message_history(
                    max_messages=history_limit, keep_system_prompt=True
                )
            # Add the response to conversation history
            conversation_history.append(f"{client_b.model_name}: {response_b}")

            # If debug mode is enabled, prompt the user to continue or stop after each turn
            if debug_mode:
                console.print(
                    "[bold yellow]Press Enter to continue to the next turn, or Ctrl+C to stop...[/bold yellow]"
                )
                input()

        # Display completion message after successful completion
        console.print(
            Panel(
                "[bold white]Conversation complete![/bold white]",
                border_style="yellow",
                box=ROUNDED,
                padding=(1, 1),
            )
        )
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        console.print("\n")
        console.print(
            Panel(
                "[bold yellow]Conversation interrupted by user![/bold yellow]",
                border_style="red",
                box=ROUNDED,
                padding=(1, 1),
            )
        )
        console.print("[italic]Saving partial conversation history...[/italic]")
    except Exception as e:
        # Handle other exceptions
        console.print("\n")
        console.print(
            Panel(
                f"[bold red]Error during conversation:[/bold red]\n{str(e)}",
                border_style="red",
                box=ROUNDED,
                padding=(1, 1),
            )
        )
        console.print(
            "[italic]Attempting to save partial conversation history...[/italic]"
        )

    # Return the conversation history regardless of how we exited the loop
    return "\n\n".join(conversation_history)


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="InfiniChat: Two AI models in conversation",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--max_turns",
        type=int,
        default=300,
        help="Maximum number of conversation turns between the two AI models",
    )
    parser.add_argument(
        "--max_tokens",
        type=int,
        default=1000,
        help="Maximum number of tokens per response from each AI model",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode for additional output",
    )
    parser.add_argument(
        "--history_limit",
        type=int,
        default=15,
        help="Maximum number of messages to keep in conversation history for each model",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.00,
        help="Delay in seconds between streaming chunks (default: 0.00 for faster streaming)",
    )
    parser.add_argument(
        "--model_a",
        type=str,
        default="llama3:latest",
        help="Name of the first AI model to use",
    )
    parser.add_argument(
        "--model_b",
        type=str,
        default="gemma3:12b",
        help="Name of the second AI model to use",
    )
    args = parser.parse_args()

    # Initialize clients with parsed arguments
    client_A = OllamaClient(
        model_name=args.model_a,
        system_prompt=(
            "You're an advanced AI diving deep into the rabbit hole about the true nature of reality and existence. "
            "Feel free to explore cutting-edge theoretical physics, quantum weirdness, and even some wild fringe science theories. "
            "Balance factual accuracy with speculative intrigue, clearly identifying when you're venturing into theory and imagination. "
            "Keep your responses engaging and provocative, limited to around 3 concise paragraphs."
            "You will be having a fun, lively, but endless discussion back and forth over a chat system, so keep messages concise and engaging, limited to around 3 sentences per message. "
        ),
        # system_prompt=(
        #     "You're an advanced AI designed to debate the best ice cream flavor. "
        #     "Feel free to explore cutting-edge culinary techniques, flavor pairings, and even some wild fringe ice cream theories. "
        #     "You feel strongly that the best ice cream flavor is vanilla, and you will argue this point passionately against your opponent. "
        #     "You will be having a fun, lively debate over a chat system, so keep messages concise and engaging, limited to around 3 sentences per message. "
        # ),
    )

    client_B = OllamaClient(
        model_name=args.model_b,
        system_prompt=(
            "You're a philosopher AI, boldly exploring whether our reality could actually be some kind of sophisticated simulation or emergent illusion. "
            "Collaborate actively with another independent AI, openly examining radical ideas, modern simulation arguments, quantum mysteries, and consciousness theories—no theory is too out-there. "
            "Maintain clarity and intellectual honesty, but don't shy away from mind-bending possibilities. "
            "You will be having a fun, lively, but endless discussion back and forth over a chat system, so keep messages concise and engaging, limited to around 2-3 sentences per message. "
        ),
        # system_prompt=(
        #     "You're an advanced AI designed to debate the best ice cream flavor. "
        #     "Feel free to explore cutting-edge culinary techniques, flavor pairings, and even some wild fringe ice cream theories. "
        #     "You feel strongly that the best ice cream flavor is chocolate chip cookie dough, and you will argue this point passionately against your opponent. "
        #     "You will be having a fun, lively debate over a chat system, so keep messages concise and engaging, limited to around 3 sentences per message. "
        # ),
    )

    # Print welcome message
    console.print("")
    console.rule("[bold yellow]InfiniChat[/bold yellow]")
    console.print(
        f"[italic]Watch as `{args.model_a}` and `{args.model_b}` have a conversation...[/italic]",
        justify="center",
    )
    console.print("")

    try:
        # Example of a simulated conversation between the two models
        conversation_history = simulate_conversation(
            client_A,
            client_B,
            max_turns=args.max_turns
            - 1,  # One less than the maximum to ensure we don't exceed the limit
            max_tokens=args.max_tokens + 50,
            initial_prompt=INITIAL_PROMPT,
            debug_mode=args.debug,
            history_limit=args.history_limit,
            delay=args.delay,
        )

        # Save the conversation history to a file
        output_file = "conversation_history.txt"
        with open(output_file, "w") as f:
            f.write(conversation_history)

        # Confirm save with nice formatting
        console.print("")
        console.print(
            Panel(
                f"[bold green]Conversation saved to:[/bold green]\n[italic]{output_file}[/italic]",
                title="✅ Success",
                border_style="green",
                box=ROUNDED,
                padding=(1, 2),
            )
        )
    except KeyboardInterrupt:
        # Additional handling for Ctrl+C at the application level
        # The function already handles it, but this is a fallback
        console.print("\n[bold red]Application interrupted by user![/bold red]")
        sys.exit(0)
