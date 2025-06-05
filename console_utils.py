"""
Shared console instance for consistent Rich formatting across the application.
"""

from rich.console import Console

# Create a single console instance that can be imported by other modules
console = Console()
