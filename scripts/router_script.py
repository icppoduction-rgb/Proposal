from rich.console import Console

from config import manage_commands
from scripts.handlers.router_handler import router_commands_handlers
from scripts.stage_two.cli import router_stage_two

console = Console()

def router_commands(module: str, service: str, action: str):

    if module == "handlers":
        router_commands_handlers(service, action)

    elif module == "stage-two":
        router_stage_two(service, action)

    else:
        console.print(manage_commands)
