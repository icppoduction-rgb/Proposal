from handlers.handler_router import handler_router_commands

def main_router_commands(module: str, service: str, action: str):

    if module == "handlers":
        handler_router_commands(module, service, action)

    else:
        print(f"Module {module} not implemented.")