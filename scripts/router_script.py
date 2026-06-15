from collections.abc import Sequence

try:
    from rich.console import Console
except ModuleNotFoundError:
    class Console:  # type: ignore[no-redef]
        """Minimal console fallback when rich is not installed."""

        def print(self, value: object) -> None:
            print(value)

from config import manage_commands

console = Console()

def router_commands(
    module: str | None,
    service: str | None,
    action: str | None,
    extra_args: Sequence[str] | None = None,
) -> None:

    if module == "handlers":
        from scripts.handlers.router_handler import router_commands_handlers

        router_commands_handlers(service, action)

    elif module == "stage-two":
        from scripts.stage_two.cli import router_stage_two

        router_stage_two(service, action, extra_args=extra_args)

    else:
        console.print(manage_commands)
