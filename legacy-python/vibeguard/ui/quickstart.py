from rich.console import Console
from rich.panel import Panel
from rich.text import Text


def print_quick_start(console: Console | None = None) -> None:
    console = console or Console()

    text = Text()
    text.append("Guardrails for vibe-coded software\n\n", style="italic")
    
    text.append("Common commands:\n", style="bold cyan")
    text.append("  vibeguard init          ", style="green")
    text.append("Initialize VibeGuard in a project\n", style="dim")
    text.append("  vibeguard doctor        ", style="green")
    text.append("Check project health & dependencies\n", style="dim")
    text.append("  vibeguard scan          ", style="green")
    text.append("Scan project structure and files\n", style="dim")
    text.append("  vibeguard all --goal    ", style="green")
    text.append("Run the full end-to-end MVP workflow\n", style="dim")
    text.append("  vibeguard risks         ", style="green")
    text.append("Audit uncommitted changes for risks\n", style="dim")
    text.append("  vibeguard next-prompt   ", style="green")
    text.append("Generate next prompt to fix risks\n\n", style="dim")

    text.append("Examples:\n", style="bold cyan")
    text.append("  cd my-project\n", style="dim")
    text.append("  vibeguard init\n", style="green")
    text.append("  vibeguard all --goal \"add OTP login without changing existing architecture\"\n\n", style="green")

    text.append("Run: ", style="bold")
    text.append("vibeguard --help", style="bold yellow")
    text.append(" to see all commands and options.", style="dim")

    console.print(
        Panel(
            text,
            border_style="magenta",
            title="[bold magenta]Quick Start Guide[/bold magenta]",
            padding=(1, 2)
        )
    )
