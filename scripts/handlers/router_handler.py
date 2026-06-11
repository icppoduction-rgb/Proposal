from rich.console import Console

from config import manage_commands
from scripts.handlers.analyze_dataset.router_analyze import router_analyze
from scripts.handlers.sort.router_sort import router_sort
from scripts.handlers.save_sort.router_save import router_save
from scripts.handlers.filter_dataset.router_filter import router_filter
from scripts.handlers.host_analyze.router_host import router_host
from scripts.handlers.dns_analyze.router_dns import router_dns

console = Console()

def router_commands_handlers(service: str, action: str):

    if service == "analyze-dataset":

        router_analyze(action)

    elif service == "sort":

        router_sort(action)

    elif service == "save-sort":

        router_save(action)

    elif service == "filter-dataset":

        router_filter(action)

    elif service == "dns-analyze":

        router_dns(action)

    elif service == "host-analyze":

        router_host(action)

    else:
        console.print(manage_commands)