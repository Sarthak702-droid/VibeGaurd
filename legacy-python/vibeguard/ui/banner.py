import os
from pathlib import Path
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

TAGLINE = "Guardrails for vibe-coded software"
FEATURES = "Context • Prompts • Verification • Risk Detection"


def banner_disabled(project: Path | None = None) -> bool:
    # 1. Environment variable check
    if os.getenv("VIBEGUARD_NO_BANNER", "").lower() in {"1", "true", "yes"}:
        return True

    # 2. Config file check
    project_path = project or Path(".")
    config_file = project_path / ".vibeguard" / "config.yaml"
    if config_file.exists():
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f)
                if isinstance(config_data, dict):
                    ui_config = config_data.get("ui")
                    if isinstance(ui_config, dict):
                        show_banner = ui_config.get("show_banner")
                        if show_banner is False:
                            return True
        except Exception:
            # Silently ignore errors during banner printing to prevent crashes
            pass

    return False


def print_banner(console: Console | None = None, compact: bool = False, project: Path | None = None) -> None:
    if banner_disabled(project):
        return

    console = console or Console()

    if compact:
        text = Text()
        text.append("Vibe", style="bold cyan")
        text.append("Guard", style="bold magenta")
        text.append(" — ", style="dim")
        text.append(TAGLINE, style="dim")
        console.print(text)
        console.print()
        return

    brand = Text()
    brand.append("Vibe", style="bold cyan")
    brand.append("Guard", style="bold magenta")
    brand.append("\n")
    brand.append(TAGLINE, style="white")
    brand.append("\n")
    brand.append(FEATURES, style="dim cyan")

    console.print(
        Panel(
            brand,
            border_style="cyan",
            padding=(1, 4),
            title="[bold cyan]VBG[/bold cyan]",
        )
    )
    console.print()
