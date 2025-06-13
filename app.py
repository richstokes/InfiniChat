from llm_client import OllamaClient
from console_utils import console
from prompts import *
from rich.panel import Panel
from rich.box import ROUNDED
from rich.text import Text
from rich.live import Live
from rich import print as rprint
from rich.markup import escape
import argparse
import sys
import time

# MODEL_A_NAME = "deepseek-r1:latest"
# MODEL_A_NAME = "qwen:latest"
MODEL_A_NAME = "llama3:latest"
MODEL_B_NAME = "gemma3:12b"

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
    delay=0.00,  # Delay between streaming chunks
    stats=False,  # Show statistics in panel titles
):
    """
    Simulate a conversation between two LLM clients with rich formatting.

    :param client_a: First OllamaClient instance
    :param client_b: Second OllamaClient instance
    :param initial_prompt: Optional initial prompt to start the conversation
    :param max_turns: Maximum number of conversation turns
    :param max_tokens: Maximum tokens per response
    :param delay: Delay between streaming chunks
    :param stats: Show message history statistics in panel titles
    :return: The complete conversation history as a string
    """
    conversation_history = []

    if debug_mode:
        console.print(
            f"[bold yellow]Debug mode enabled![/bold yellow] Max turns: {max_turns}, Max tokens: {max_tokens}, History limit: {client_a.history_limit}"
        )
        console.print(
            f"[bold yellow]Model A:[/bold yellow] {client_a.model_name}, [bold yellow]Model B:[/bold yellow] {client_b.model_name}"
        )
        console.print(
            f"[bold yellow]Initial prompt:[/bold yellow] {initial_prompt if initial_prompt else 'None'}"
        )
        console.print(
            f"[bold yellow]Model A Prompt:[/bold yellow] {client_a.system_prompt}"
        )
        console.print(
            f"[bold yellow]Model B Prompt:[/bold yellow] {client_b.system_prompt}"
        )

    # Display a title for the conversation
    console.print(
        Panel.fit(
            f"[bold yellow]AI Conversation Beginning![/bold yellow] 🤖\nWatch as [bold]{escape(args.model_a)}[/bold] and [bold]{escape(args.model_b)}[/bold] have a conversation.",
            box=ROUNDED,
            border_style="yellow",
            padding=(1, 2),
        )
    )

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
                f"[bold white on bright_black]Round {turn+1}/{max_turns}[/bold white on bright_black]",
                justify="center",
            )

            # Client A's turn
            console.print(
                f"\n[{CLIENT_A_STYLE}]🤖 {client_a.model_name} is thinking...[/{CLIENT_A_STYLE}]"
            )

            # Create a buffer to collect the streamed text
            response_buffer = ""
            start_time = time.time()

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

                    # Generate title with optional stats
                    title = (
                        f"[{CLIENT_A_STYLE}]{client_a.model_name}[/{CLIENT_A_STYLE}]"
                    )
                    if stats:
                        msg_count = len(client_a.message_history)
                        title += f" [dim]({msg_count} msgs)[/dim]"

                    live.update(
                        Panel(
                            Text(response_buffer, no_wrap=False),
                            title=title,
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
                )

                # Calculate response time
                end_time = time.time()
                response_time = end_time - start_time

                # Update the panel with final response and timing info
                final_title = (
                    f"[{CLIENT_A_STYLE}]{client_a.model_name}[/{CLIENT_A_STYLE}]"
                )
                if stats:
                    msg_count = len(client_a.message_history)
                    final_title += (
                        f" [dim]({msg_count} msgs, {response_time:.1f}s)[/dim]"
                    )

                live.update(
                    Panel(
                        Text(response_buffer, no_wrap=False),
                        title=final_title,
                        title_align="left",
                        border_style=CLIENT_A_PANEL_STYLE,
                        box=ROUNDED,
                        padding=(1, 2),
                    )
                )

                # Trim history to prevent it from growing too large
                client_a.trim_message_history(
                    max_messages=client_a.history_limit, keep_system_prompt=True
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
            start_time = time.time()

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

                    # Generate title with optional stats
                    title = (
                        f"[{CLIENT_B_STYLE}]{client_b.model_name}[/{CLIENT_B_STYLE}]"
                    )
                    if stats:
                        msg_count = len(client_b.message_history)
                        title += f" [dim]({msg_count} msgs)[/dim]"

                    live.update(
                        Panel(
                            Text(response_buffer, no_wrap=False),
                            title=title,
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
                )

                # Calculate response time
                end_time = time.time()
                response_time = end_time - start_time

                # Update the panel with final response and timing info
                final_title = (
                    f"[{CLIENT_B_STYLE}]{client_b.model_name}[/{CLIENT_B_STYLE}]"
                )
                if stats:
                    msg_count = len(client_b.message_history)
                    final_title += (
                        f" [dim]({msg_count} msgs, {response_time:.1f}s)[/dim]"
                    )

                live.update(
                    Panel(
                        Text(response_buffer, no_wrap=False),
                        title=final_title,
                        title_align="left",
                        border_style=CLIENT_B_PANEL_STYLE,
                        box=ROUNDED,
                        padding=(1, 2),
                    )
                )

                # Trim history to prevent it from growing too large
                client_b.trim_message_history(
                    max_messages=client_b.history_limit, keep_system_prompt=True
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
        description="InfiniChat: Two LLMs, having a chat.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--max_turns",
        type=int,
        default=9000,
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
        "--show_json",
        action="store_true",
        help="Show raw JSON responses from the models",
    )
    parser.add_argument(
        "--log_history",
        action="store_true",
        help="Log message_history state to a file (for debugging)",
    )
    parser.add_argument(
        "--history_limit",
        type=int,
        default=500,
        help="Maximum number of messages to keep in conversation history for each model before summarizing and trimming",
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
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show message history statistics in panel titles",
    )
    parser.add_argument(
        "--debate_topic",
        type=str,
        default="",
        help="Set a topic for the debate between the two AI models. If set, will override the prompts.",
    )
    parser.add_argument(
        "--model_a_prompt",
        type=str,
        default="",
        help="Custom system prompt for model A. If provided, will override the default MODEL_A_PROMPT.",
    )
    parser.add_argument(
        "--model_b_prompt",
        type=str,
        default="",
        help="Custom system prompt for model B. If provided, will override the default MODEL_B_PROMPT.",
    )
    args = parser.parse_args()

    if args.debate_topic:
        console.print(
            f"[bold yellow]Debate mode enabled! Topic: {args.debate_topic}[/bold yellow]"
        )
        # If a debate topic is provided, override the system prompts
        MODEL_A_PROMPT = DEBATE_PROMPT.format(
            name="Joe", debate_topic=args.debate_topic, for_or_against="for"
        )
        MODEL_B_PROMPT = DEBATE_PROMPT.format(
            name="Jannet", debate_topic=args.debate_topic, for_or_against="against"
        )

    # Handle custom prompts - these override default prompts and debate prompts
    if args.model_a_prompt:
        MODEL_A_PROMPT = args.model_a_prompt
        console.print("[bold blue]Using custom prompt for Model A[/bold blue]")

    if args.model_b_prompt:
        MODEL_B_PROMPT = args.model_b_prompt
        console.print("[bold green]Using custom prompt for Model B[/bold green]")

    # Initialize clients with parsed arguments
    client_A = OllamaClient(
        model_name=args.model_a,
        debug_mode=args.debug,
        show_json=args.show_json,
        system_prompt=MODEL_A_PROMPT,
        history_limit=args.history_limit,
        log_history=args.log_history,
    )
    client_B = OllamaClient(
        model_name=args.model_b,
        debug_mode=args.debug,
        show_json=args.show_json,
        system_prompt=MODEL_B_PROMPT,
        history_limit=args.history_limit,
        log_history=args.log_history,
    )

    # Print welcome message
    console.print("")
    console.rule(
        "[bold yellow]InfiniChat - github.com/richstokes/InfiniChat[/bold yellow]"
    )
    console.print("")

    try:
        # Example of a simulated conversation between the two models
        conversation_history = simulate_conversation(
            client_A,
            client_B,
            max_turns=args.max_turns,
            max_tokens=args.max_tokens + 50,
            initial_prompt=INITIAL_PROMPT,
            debug_mode=args.debug,
            delay=args.delay,
            stats=args.stats,
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
