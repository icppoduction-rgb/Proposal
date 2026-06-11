# -*- coding: utf-8 -*-

import argparse

parser = argparse.ArgumentParser()

parser.add_argument("module", nargs="?")
parser.add_argument("service", nargs="?")
parser.add_argument("action", nargs="?")


# Функция управления
def manage() -> None:
    """
    Управляет запуском скриптов проекта через аргументы командной строки.
    """

    from scripts.router_script import router_commands

    args, _unknown = parser.parse_known_args()

    router_commands(args.module, args.service, args.action)

if __name__ == "__main__":
    manage()
