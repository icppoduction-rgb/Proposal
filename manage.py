# -*- coding: utf-8 -*-

import argparse
import sys

parser = argparse.ArgumentParser()

parser.add_argument("module", nargs="?")
parser.add_argument("service", nargs="?")
parser.add_argument("action", nargs="?")
parser.add_argument("extra_args", nargs=argparse.REMAINDER)


# Функция управления
def manage() -> None:
    """
    Управляет запуском скриптов проекта через аргументы командной строки.
    """

    from scripts.router_script import router_commands

    raw_args = sys.argv[1:]
    if raw_args and raw_args[0] == "stage-three":
        service = raw_args[1] if len(raw_args) > 1 else None
        router_commands("stage-three", service, None, raw_args[2:])
        return

    args, unknown = parser.parse_known_args()

    router_commands(args.module, args.service, args.action, [*args.extra_args, *unknown])

if __name__ == "__main__":
    manage()
